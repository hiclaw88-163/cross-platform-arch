#!/usr/bin/env python3
"""一核多端架构 · 生成项目验证器

用法:
    python verify_project.py --project /path/to/my-app [--test]

检查项（全部通过输出 PASS，否则逐条列出 FAIL）:
  1. 结构完整性 —— 必需文件全部存在（含核心/各端/契约流水线/设计决策记录）
  2. 核心纯净性 —— packages/core 源码禁止 import 任何框架
     (fastapi/sqlalchemy/typer/uvicorn/httpx/requests/pydantic/flask/django/starlette/rich/click/aiohttp)
     这是"一核多端"的铁律: 核心只依赖标准库
  3. 依赖方向性 —— 各端依赖核心(core)，核心不得反向依赖任何端
  4. Token 引用闭合 —— web 端引用的 var(--x) 必须在 tokens.css(或本文件)定义,
     防止"样式残缺但不报错"的隐性破损(真实事故: tokens.css 缺 --space-5 等)
  5. 测试通过性 —— (--test) 运行 uv run pytest packages/core/tests
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FORBIDDEN_IN_CORE = {
    "fastapi", "sqlalchemy", "typer", "uvicorn", "httpx", "requests",
    "pydantic", "flask", "django", "starlette", "rich", "click", "aiohttp",
}
def check_manifest(root: Path, pkg: str) -> list[str]:
    required = [
        "pyproject.toml", "pnpm-workspace.yaml", "package.json",
        f"packages/core/pyproject.toml",
        f"packages/core/src/{pkg}_core/__init__.py",
        f"packages/core/src/{pkg}_core/domain/__init__.py",
        f"packages/core/src/{pkg}_core/application/__init__.py",
        "apps/server/pyproject.toml",
        "apps/server/src/server/main.py",
        "apps/server/src/server/routes/__init__.py",
        "apps/cli/pyproject.toml",
        "apps/web/package.json", "apps/web/vite.config.ts",
        "apps/web/src/styles/tokens.css",
        "docs/design-decisions.md",   # 阶段 3.5 设计包流程的必产物(决策可追溯)
        "apps/desktop/main.py" if (root / "apps/desktop/main.py").exists()
        else "apps/desktop/main.js",
        "packages/sdk/generate.mjs",
        "scripts/verify_project.py",
        ".github/workflows/ci.yml",
        "docker-compose.yml", ".env.example",
    ]
    missing = [p for p in required if not (root / p).exists()]
    # 测试目录至少要有一个测试文件(具体文件名随业务命名,不硬编码)
    tests_dir = root / "packages/core/tests"
    if not (tests_dir.is_dir() and any(tests_dir.glob("test_*.py"))):
        missing.append("packages/core/tests/test_*.py")
    return [f"缺少必需文件: {p}" for p in missing]


def check_core_purity(root: Path, pkg: str) -> list[str]:
    fails: list[str] = []
    core_src = root / f"packages/core/src/{pkg}_core"
    if not core_src.is_dir():
        return [f"核心目录不存在: {core_src}"]
    for py in core_src.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError as e:
            fails.append(f"语法错误 {py.relative_to(root)}: {e}")
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for n in names:
                if n in FORBIDDEN_IN_CORE:
                    fails.append(
                        f"核心纯净性违规: {py.relative_to(root)} import 了框架 '{n}'"
                    )
    # pyproject 依赖检查：兼容单行 dependencies = ["x"] 与多行数组
    proj = root / "packages/core/pyproject.toml"
    if proj.exists():
        text = proj.read_text(encoding="utf-8")
        m = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.DOTALL | re.MULTILINE)
        if m:
            for item in re.findall(r'"([^"]+)"', m.group(1)):
                base = item.split(">")[0].split("<")[0].split("=")[0].strip().lower()
                if base in FORBIDDEN_IN_CORE:
                    fails.append(f"核心 pyproject 声明了框架依赖: {item}")
    return fails


def check_dep_direction(root: Path) -> list[str]:
    fails: list[str] = []
    core_meta = root / "packages/core/pyproject.toml"
    if core_meta.exists():
        text = core_meta.read_text(encoding="utf-8")
        for kw in ("apps/", "fastapi", "typer"):
            if f'"{kw}' in text:
                fails.append(f"核心不得依赖任何端（packages/core/pyproject.toml 含 '{kw}'）")
    return fails


_VAR_REF = re.compile(r"var\(\s*(--[\w-]+)")
_VAR_DEF = re.compile(r"^\s*(--[\w-]+)\s*:", re.MULTILINE)


def check_token_closure(root: Path) -> list[str]:
    """web 端引用的每个 var(--x) 必须有定义(tokens.css 或引用所在文件)。

    背景: 该类破损不报错、不崩构建——页面只是"安静地变丑/残缺",
    人工 review 极易漏检,必须机器判定。
    """
    web_src = root / "apps/web/src"
    if not web_src.is_dir():
        return []
    tokens = web_src / "styles/tokens.css"
    defined: set[str] = set()
    if tokens.exists():
        defined |= set(_VAR_DEF.findall(tokens.read_text(encoding="utf-8")))
    fails: list[str] = []
    for f in [*web_src.rglob("*.css"), *web_src.rglob("*.vue")]:
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        local_defs = set(_VAR_DEF.findall(text))
        for name in set(_VAR_REF.findall(text)):
            if name not in defined and name not in local_defs:
                fails.append(
                    f"Token 引用未定义: {f.relative_to(root)} 引用 {name}"
                    f"(tokens.css 缺该变量)")
    return fails


def check_tests(root: Path) -> list[str]:
    import subprocess
    r = subprocess.run(
        ["uv", "run", "pytest", "packages/core/tests", "-q"],
        cwd=root, capture_output=True, text=True, timeout=600,
    )
    tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    return [] if r.returncode == 0 else [f"核心测试未通过: {tail[0]}"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="生成的项目根目录")
    ap.add_argument("--test", action="store_true", help="同时运行核心层测试")
    args = ap.parse_args()
    root = Path(args.project).resolve()
    if not root.is_dir():
        print(f"FAIL: 项目目录不存在: {root}")
        return 2

    # 从 packages/core/src 推断包名
    src = root / "packages/core/src"
    pkgs = [d.name for d in src.iterdir() if d.is_dir() and d.name.endswith("_core")] if src.is_dir() else []
    pkg = pkgs[0].removesuffix("_core") if pkgs else "app"

    fails: list[str] = []
    fails += check_manifest(root, pkg)
    fails += check_core_purity(root, pkg)
    fails += check_dep_direction(root)
    fails += check_token_closure(root)
    if args.test:
        fails += check_tests(root)

    print(f"项目: {root}")
    print(f"包名: {pkg}_core")
    if fails:
        print(f"\nFAIL — {len(fails)} 项违规:")
        for f in fails:
            print(f"  ✗ {f}")
        return 1
    print("\nPASS — 结构完整、核心纯净、依赖方向正确、Token 闭合" + ("、测试通过" if args.test else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
