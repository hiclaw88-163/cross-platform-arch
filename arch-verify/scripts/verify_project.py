#!/usr/bin/env python3
"""一核多端架构 · 生成项目验证器

用法:
    python verify_project.py --project /path/to/my-app [--test]

检查项（共 7 项，--test 时加跑第 8 项；全部通过输出 PASS，否则逐条列出 FAIL，
被跳过的项显式输出 SKIP——PASS 行只列真正执行过的检查）:
  1. 结构完整性 —— 必需文件全部存在（含核心/各端/契约流水线/设计决策记录）
  2. 核心纯净性 —— packages/core 只允许 标准库 + 本包自身（白名单制，
     含 importlib.import_module/__import__ 动态导入检测）
  3. 依赖方向性 —— core 源码不得 import 任何端（ast 扫描 import）
  4. 六边形桥 —— 各端只许经 <engine>.bridge 触达引擎；无 packages/engine 的
     项目显式 SKIP
  5. Token 引用闭合 —— web 端引用的 var(--x) 必须有定义（.css/.scss/.vue/
     .html/.ts/.tsx），带兜底值的引用仅 WARN
  6. 契约新鲜度 —— openapi.sha256 指纹重算比对，server 契约变更未重生成 SDK
     即 FAIL（无 uv 时 SKIP）
  7. 无空包残留 —— 改名/重构残留的空目录会被 Python 当命名空间包，
     让导入假成功（真实事故: 空目录吞掉台账写入）
  8. 核心测试通过 —— (--test) 运行 uv run pytest packages/core/tests
"""
from __future__ import annotations

import argparse
import ast
import re
import shutil
import sys
from pathlib import Path

FORBIDDEN_IN_CORE = {
    "fastapi", "sqlalchemy", "typer", "uvicorn", "httpx", "requests",
    "pydantic", "flask", "django", "starlette", "rich", "click", "aiohttp",
}

# 契约探针命令（参数列表形式，不用 shell 拼串）：必须与 monorepo-scaffold 生成的
# packages/sdk/generate.mjs 里的 probeArgs 逐字一致——两端对同一份规范化文本求哈希。
OPENAPI_PROBE_CMD = [
    "uv", "run", "python", "-c",
    "import json; from server.main import app; print(json.dumps(app.openapi()))",
]

# 目录扫描通用排除项：虚拟环境/依赖/缓存不参与结构扫描
EXCLUDED_DIRS = {".venv", "node_modules", "__pycache__", ".git", "dist", "build"}


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
        "packages/sdk/src/gen/schema.d.ts",  # 契约产物必须随仓库走
        "packages/sdk/src/gen/openapi.sha256",  # 契约指纹(新鲜度门禁比对基准)
        "scripts/verify_project.py",
        ".github/workflows/ci.yml",
        ".githooks/commit-msg",        # 提交信息强制校验钩子（README 提交与协作节）
        "scripts/install_hooks.py",    # 钩子启用器（sync.py/setup_hooks.cjs 之外的纯 Python 入口）
        "scripts/setup_hooks.cjs",     # pnpm install 自动启用钩子的 Node 收尾脚本
        "docker-compose.yml", ".env.example",
    ]
    missing = [p for p in required if not (root / p).exists()]
    # 测试目录至少要有一个测试文件(具体文件名随业务命名,不硬编码)
    tests_dir = root / "packages/core/tests"
    if not (tests_dir.is_dir() and any(tests_dir.glob("test_*.py"))):
        missing.append("packages/core/tests/test_*.py")
    return [f"缺少必需文件: {p}" for p in missing]


def _normalize_dep(name: str) -> str:
    """依赖名规范化：小写，``_``/``.`` 统一为 ``-``（PEP 503）。"""
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _dep_base_name(requirement: str) -> str:
    """从需求串提取规范包名：正确处理 extras(pkg[x])、~=、!=、==、>=、
    环境标记（; python_version<...）与 URL（pkg @ file://...）。"""
    req = requirement.split(";", 1)[0]  # 去环境标记
    req = req.split("[", 1)[0]          # 去 extras
    m = re.match(r"\s*([A-Za-z0-9_.\-]+)", req)
    return _normalize_dep(m.group(1)) if m else ""


# 3.9 回退用标准库名单（3.10+ 直接用 sys.stdlib_module_names，无需此表）
_STDLIB_FALLBACK = {
    "__future__", "abc", "argparse", "array", "ast", "asyncio", "atexit",
    "base64", "bdb", "binascii", "bisect", "builtins", "bz2", "calendar",
    "cmath", "cmd", "code", "codecs", "collections", "colorsys", "concurrent",
    "configparser", "contextlib", "contextvars", "copy", "copyreg", "cProfile",
    "csv", "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal",
    "difflib", "dis", "doctest", "email", "encodings", "enum", "errno",
    "faulthandler", "filecmp", "fileinput", "fnmatch", "fractions", "ftplib",
    "functools", "gc", "getopt", "getpass", "gettext", "glob", "graphlib",
    "gzip", "hashlib", "heapq", "hmac", "html", "http", "imaplib", "importlib",
    "inspect", "io", "ipaddress", "itertools", "json", "keyword", "linecache",
    "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math",
    "mimetypes", "mmap", "modulefinder", "multiprocessing", "netrc", "numbers",
    "operator", "optparse", "os", "pathlib", "pdb", "pickle", "pickletools",
    "pipes", "pkgutil", "platform", "plistlib", "poplib", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr", "queue", "quopri",
    "random", "re", "readline", "reprlib", "resource", "rlcompleter", "runpy",
    "sched", "secrets", "select", "selectors", "shelve", "shlex", "shutil",
    "signal", "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver",
    "sqlite3", "ssl", "stat", "statistics", "string", "stringprep", "struct",
    "subprocess", "symtable", "sys", "sysconfig", "tarfile", "telnetlib", "tempfile",
    "termios", "textwrap", "threading", "time", "timeit", "tkinter", "token",
    "tokenize", "trace", "traceback", "tracemalloc", "tty", "turtle", "types",
    "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv",
    "warnings", "wave", "weakref", "webbrowser", "wsgiref", "xml", "xmlrpc",
    "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo",
}


def _stdlib_names() -> set[str]:
    names = getattr(sys, "stdlib_module_names", None)
    return set(names) if names else set(_STDLIB_FALLBACK)


def _core_dep_literals(text: str) -> list[str]:
    """提取 core pyproject 的依赖需求串。优先 tomllib（3.11+）；
    3.9/3.10 回退到手写括号深度解析（兼容单行/多行数组与注释）。"""
    try:
        import tomllib  # noqa: F401  3.11+
    except ModuleNotFoundError:
        deps: list[str] = []
        depth = 0
        for raw in text.splitlines():
            line = raw.split("#", 1)[0]
            if depth == 0 and re.match(r"^\s*(optional-)?dependencies\s*=", line):
                depth += line.count("[") - line.count("]")
                deps += re.findall(r'"([^"]+)"', line)
            elif depth > 0:
                depth += line.count("[") - line.count("]")
                deps += re.findall(r'"([^"]+)"', line)
                if depth <= 0:
                    depth = 0
        return deps
    try:
        data = tomllib.loads(text)
    except Exception:
        return []  # 解析不了就不误报（结构检查另有门禁）
    project = data.get("project", {}) or {}
    deps = list(project.get("dependencies", []) or [])
    for extra in (project.get("optional-dependencies") or {}).values():
        deps.extend(extra or [])
    return deps


def check_core_purity(root: Path, pkg: str) -> list[str]:
    """核心纯净性检查（白名单制）：core 源码仅允许 标准库 + 本包自身 + 相对导入，
    pyproject 依赖不得声明任何第三方包。黑名单 FORBIDDEN_IN_CORE 仅用于把违规
    提示归类为"框架"还是"非标准库第三方"。额外检测 importlib.import_module /
    __import__ 的字符串字面量动态导入。"""
    fails: list[str] = []
    core_src = root / f"packages/core/src/{pkg}_core"
    if not core_src.is_dir():
        return [f"核心目录不存在: {core_src}"]
    allowed = _stdlib_names() | {pkg.lower(), f"{pkg}_core".lower(), "__future__"}
    for py in core_src.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, ValueError, UnicodeDecodeError) as e:
            fails.append(f"语法错误 {py.relative_to(root)}: {e}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:  # 相对导入属于本包内部，放行
                    continue
                mods = [node.module] if node.module else []
            else:
                continue
            for mod in mods:
                top = mod.split(".")[0].lower()
                if top in allowed:
                    continue
                kind = "框架" if _normalize_dep(top) in FORBIDDEN_IN_CORE else "非标准库第三方"
                fails.append(
                    f"核心纯净性违规: {py.relative_to(root)}:{node.lineno} "
                    f"import 了{kind} '{mod}' —— core 只允许标准库"
                )
        # 动态导入：importlib.import_module("x") / __import__("x") 的字符串字面量
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            dynamic = (
                (isinstance(fn, ast.Attribute) and fn.attr == "import_module"
                 and isinstance(fn.value, ast.Name) and fn.value.id == "importlib")
                or (isinstance(fn, ast.Name) and fn.id == "__import__")
            )
            if dynamic and node.args and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str):
                mod = node.args[0].value
                top = mod.split(".")[0].lower()
                if top not in allowed:
                    kind = "框架" if _normalize_dep(top) in FORBIDDEN_IN_CORE else "非标准库第三方"
                    fails.append(
                        f"核心纯净性违规: {py.relative_to(root)}:{node.lineno} "
                        f"动态 import 了{kind} '{mod}' —— core 只允许标准库"
                    )
    # pyproject 依赖检查（tomllib/回退解析，正确处理 extras、~=、==、环境标记）
    proj = root / "packages/core/pyproject.toml"
    if proj.exists():
        for req in _core_dep_literals(proj.read_text(encoding="utf-8")):
            base = _dep_base_name(req)
            if not base:
                continue
            if base in FORBIDDEN_IN_CORE:
                fails.append(f"核心 pyproject 声明了框架依赖: {req}")
            elif base not in _stdlib_names() and base != _normalize_dep(pkg):
                fails.append(f"核心 pyproject 声明了非标准库依赖: {req}")
    return fails


def check_dep_direction(root: Path) -> list[str]:
    """依赖方向检查：core 源码不得 import 任何"端"包（ast 扫描 import，非文本搜索）。

    端包名动态推断，不写死：apps/<端>/src/<包名> 与 apps/<端目录名> 均视为端
    （如 server、cli、desktop、web、uniapp）。core 是领域内核，依赖方向必须是
    端 → core；违规信息给出文件、行号与被引用的端。
    """
    core_dir = root / "packages" / "core" / "src"
    if not core_dir.is_dir():
        return []
    apps_dir = root / "apps"
    end_pkgs: set[str] = set()
    if apps_dir.is_dir():
        for child in sorted(apps_dir.iterdir()):
            if not child.is_dir() or child.name in EXCLUDED_DIRS:
                continue
            end_pkgs.add(child.name.lower())
            src = child / "src"
            if src.is_dir():
                for pkg in sorted(src.iterdir()):
                    if pkg.is_dir():
                        end_pkgs.add(pkg.name.lower())
    if not end_pkgs:
        return []
    failures: list[str] = []
    for py in core_dir.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, ValueError, UnicodeDecodeError) as exc:
            failures.append(f"{py.relative_to(root)}: 语法错误无法解析（{exc}）")
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                # 绝对 import 才可能触达端包；相对导入(level>0)在 core 包内部，放行
                if node.level == 0 and node.module:
                    names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0].lower()
                if top in end_pkgs:
                    failures.append(
                        f"{py.relative_to(root)}:{node.lineno} "
                        f"core 违规引用端包 {name} —— 依赖方向必须是 端 → core"
                    )
    return failures


# 端间互触白名单: desktop 允许 import server 的启动装配入口(离线模式内嵌 uvicorn),
# 这是六边形拓扑里唯一的端间豁免(见 references/clients.md §2 关系矩阵)。
_END_IMPORT_WHITELIST = {"desktop": {"server"}}


def check_hexagonal(root: Path) -> tuple[bool, list[str]]:
    """六边形门禁(规约 R4 + 端间隔离,见 references/hexagonal-arch.md):

    1. 引擎必须提供 bridge.py 作为唯一出桥模块;
    2. 各端只允许经 bridge 触达引擎(ast 解析)——**规范形式放行**:
       `from <engine> import bridge`、`from <engine>.bridge import ...`、
       `import <engine>.bridge`; **违规**: `import <engine>`、`from <engine>
       import <非bridge名字>`、`from <engine> import bridge, <其他>`、
       `from <engine>.<非bridge子包> import ...`(含 `bridge.<更深子模块>`);
    3. 端之间禁止互相 import(白名单除外)。

    返回 (是否执行, 违规列表)。项目没有 packages/engine(如 monorepo-scaffold
    生成的 core-only 拓扑)时检查**显式 SKIP**——绝不谎报"桥闭合"。
    扫描 apps/* 时排除 .venv/node_modules/__pycache__ 等目录。
    """
    eng_src = root / "packages/engine/src"
    if not eng_src.is_dir():
        return False, []
    inner = sorted(d.name for d in eng_src.iterdir()
                   if d.is_dir() and (d / "__init__.py").exists())
    if not inner:
        return False, []
    if len(inner) > 1:
        # iterdir 顺序不确定，多引擎包时取哪个都无依据——显式报错而不是碰运气
        return True, [f"packages/engine/src 下发现多个引擎包 {inner}——"
                      "应只有一个，无法确定六边形桥检查对象"]
    engpkg = inner[0]
    fails: list[str] = []
    if not (eng_src / engpkg / "bridge.py").exists():
        fails.append(f"引擎缺少 {engpkg}/bridge.py——端与引擎之间必须有唯一六边形桥")

    ends_root = root / "apps"
    end_names = sorted(d.name for d in ends_root.iterdir()
                       if d.is_dir() and d.name not in EXCLUDED_DIRS) if ends_root.is_dir() else []

    for end in end_names:
        for f in (ends_root / end).rglob("*.py"):
            if any(part in EXCLUDED_DIRS for part in f.parts):
                continue
            try:
                tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
            except (SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        parts = alias.name.split(".")
                        if parts[0] == engpkg:
                            # 规范形式放行：import <engine>.bridge；
                            # import <engine> / <engine>.<其他子包> → 违规
                            if alias.name != f"{engpkg}.bridge":
                                fails.append(
                                    f"{f.relative_to(root)}:{node.lineno} 直接 import "
                                    f"{alias.name}——端只允许经 {engpkg}.bridge 触达引擎(规约 R4)")
                        elif parts[0] in end_names and parts[0] != end and \
                                parts[0] not in _END_IMPORT_WHITELIST.get(end, ()):
                            fails.append(
                                f"{f.relative_to(root)}:{node.lineno} import 了端 {parts[0]}"
                                "——端之间禁止互相引用(见 clients.md §2 关系矩阵)")
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    parts = node.module.split(".")
                    if parts[0] == engpkg:
                        # 规范形式放行：from <engine> import bridge（单个名字）
                        # 与 from <engine>.bridge import X；
                        # 违规：from <engine> import bridge, store（多名）/
                        # from <engine>.store import x / from <engine>.bridge.sub import x
                        if node.module == engpkg:
                            bad = [a.name for a in node.names if a.name != "bridge"]
                        elif node.module == f"{engpkg}.bridge":
                            bad = []
                        else:
                            bad = [node.module]
                        for name in bad:
                            fails.append(
                                f"{f.relative_to(root)}:{node.lineno} 直接 import "
                                f"{name}——端只允许经 {engpkg}.bridge 触达引擎(规约 R4)")
                    elif parts[0] in end_names and parts[0] != end and \
                            parts[0] not in _END_IMPORT_WHITELIST.get(end, ()):
                        fails.append(
                            f"{f.relative_to(root)}:{node.lineno} import 了端 {parts[0]}"
                            "——端之间禁止互相引用(见 clients.md §2 关系矩阵)")
    return True, fails


_VAR_REF = re.compile(r"var\(\s*(--[\w-]+)")
_VAR_REF_FALLBACK = re.compile(r"var\(\s*(--[\w-]+)\s*,")
_VAR_DEF = re.compile(r"(--[\w-]+)\s*:")
# .ts/.tsx/.html/.scss 里的 var(--x) 引用同样要闭合（样式散落在模板与组件里）
_TOKEN_SCAN_EXTS = ("*.css", "*.scss", "*.vue", "*.html", "*.ts", "*.tsx")


def _strip_var_calls(text: str) -> str:
    """移除所有 var(...) 调用（含嵌套兜底），防止把 var 内部的 `--x,` 误认为定义。"""
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"var\([^()]*\)", "", text)
    return text


def check_token_closure(root: Path) -> tuple[list[str], list[str]]:
    """web 端引用的每个 var(--x) 必须有定义(tokens.css 或引用所在文件)。

    背景: 该类破损不报错、不崩构建——页面只是"安静地变丑/残缺",
    人工 review 极易漏检,必须机器判定。
    返回 (违规, 警告): 定义可出现在任意位置(不要求行首)；带兜底值的引用
    `var(--x, #fff)` 即使未定义也只是 WARN（兜底保证可用）。
    """
    web_src = root / "apps/web/src"
    if not web_src.is_dir():
        return [], []
    tokens = web_src / "styles/tokens.css"
    defined: set[str] = set()
    if tokens.exists():
        defined |= set(_VAR_DEF.findall(_strip_var_calls(tokens.read_text(encoding="utf-8"))))
    fails: list[str] = []
    warns: list[str] = []
    files: list[Path] = []
    for ext in _TOKEN_SCAN_EXTS:
        files += [f for f in web_src.rglob(ext) if f.is_file()]
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        local_defs = set(_VAR_DEF.findall(_strip_var_calls(text)))
        refs = set(_VAR_REF.findall(text))
        fallback_refs = set(_VAR_REF_FALLBACK.findall(text))
        for name in refs:
            if name in defined or name in local_defs:
                continue
            if name in fallback_refs:
                warns.append(
                    f"Token 引用未定义(有兜底值): {f.relative_to(root)} 引用 {name}"
                    "——建议在 tokens.css 补定义以统一主题")
            else:
                fails.append(
                    f"Token 引用未定义: {f.relative_to(root)} 引用 {name}"
                    f"(tokens.css 缺该变量)")
    return fails, warns



def check_sdk_freshness(root: Path) -> list[str]:
    """契约新鲜度门禁: 重算 server 契约指纹,与 packages/sdk 生成时记录的比对。

    背景(真实事故): generate.mjs 存在却从未被执行,manifest 只查文件存在性,
    前端类型与后端契约静默漂移。此检查让"改了后端没重新生成 SDK"当场 FAIL。
    指纹 = `print(json.dumps(app.openapi()))` 输出的 sha256,
    由 generate.mjs 在生成时写入 src/gen/openapi.sha256。
    """
    gen_dir = root / "packages/sdk/src/gen"
    if not (gen_dir / "schema.d.ts").exists():
        return []  # 缺产物由结构完整性检查负责
    import hashlib
    import subprocess
    try:
        r = subprocess.run(OPENAPI_PROBE_CMD, cwd=root,
                           capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return ["契约探针超时(300s)——无法重算契约指纹，请检查 server.main 导入性能"]
    except FileNotFoundError:
        return ["契约探针无法启动（uv 不在 PATH）——契约新鲜度不可验证"]
    if r.returncode != 0:
        tail = (r.stderr.strip().splitlines() or ["导出失败"])[-1]
        return [f"无法从 server.main 导出 openapi.json,契约新鲜度不可验证: {tail}"]
    # 换行规范化：Windows 下 text=True 已把 \r\n 统一为 \n，这里再兜底一次，
    # 与 generate.mjs 的 .replace(/\r\n/g, "\n") 保持同一份规范化文本口径。
    current = hashlib.sha256(r.stdout.replace("\r\n", "\n").encode()).hexdigest()
    hash_file = gen_dir / "openapi.sha256"
    if not hash_file.exists():
        return ["缺少 packages/sdk/src/gen/openapi.sha256——运行 gen:sdk 记录契约指纹"]
    recorded = hash_file.read_text(encoding="utf-8").strip()
    if recorded != current:
        if re.fullmatch(r"[0-9a-f]{64}", recorded):
            return ["契约漂移: server 契约已变更但 SDK 未重新生成——运行 gen:sdk 后重试"]
        return ["契约指纹仍是脚手架占位值——运行 pnpm gen:sdk 生成 SDK 与真实指纹后重试"]
    return []


def check_tests(root: Path) -> list[str]:
    import subprocess
    try:
        r = subprocess.run(
            ["uv", "run", "pytest", "packages/core/tests", "-q"],
            cwd=root, capture_output=True, text=True, timeout=600,
        )
    except FileNotFoundError:
        return ["uv 不可用（未安装或不在 PATH）: 无法运行核心测试，请安装 uv 或去掉 --test"]
    except subprocess.TimeoutExpired:
        return ["核心测试超时(600s)——存在卡死的测试？"]
    tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    return [] if r.returncode == 0 else [f"核心测试未通过: {tail[0]}"]


def check_empty_packages(root: Path) -> list[str]:
    """检查: 源码树里不许留空目录(改名/重构残留的死包)。

    真实事故复盘: 重构把 ``<engine>/store`` 改名 ``ledger``,旧目录被清空
    但目录还在。Python 3 会把它当成**命名空间包**,于是 ``from <engine>
    import store`` 不报错、里面却什么都没有 —— ``AttributeError`` 落到
    best-effort 的 ``except`` 里被吞,整天的台账静默丢失,dashboard 一片
    空白而 CLI 输出一切正常。

    "空目录让导入假成功"会把断链伪装成健康,必须在自检里拦下。
    """
    fails: list[str] = []
    for src in sorted(p for p in (root / "packages").glob("*/src") if p.is_dir()):
        for d in sorted(p for p in src.rglob("*") if p.is_dir()):
            if "__pycache__" in d.parts:
                continue
            files = [f for f in d.rglob("*")
                     if f.is_file() and "__pycache__" not in f.parts]
            if not files:
                fails.append(f"空包目录(改名/重构残留?): {d.relative_to(root)}")
    return fails


def _safe_stdout() -> None:
    """Windows GBK 控制台防护: ✗/✓/— 等符号无法编码会让 print 崩溃。

    只把不可编码字符降级为 ?（中文正常显示），不改变控制台编码本身。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def main() -> int:
    _safe_stdout()
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

    # 每项检查带"是否真正执行"标记与跳过说明：PASS 行只列真正执行过的检查项，
    # 被跳过的项显式输出 SKIP——绝不谎报(如无 engine 项目谎报"六边形桥闭合")，
    # 也不把"环境缺 uv"当成架构违规 FAIL
    has_uv = shutil.which("uv") is not None
    hexa_done, hexa_fails = check_hexagonal(root)
    token_fails, token_warns = check_token_closure(root)
    results: list[tuple[str, bool, list[str], str | None]] = [
        ("结构完整", True, check_manifest(root, pkg), None),
        ("核心纯净", True, check_core_purity(root, pkg), None),
        ("依赖方向", True, check_dep_direction(root), None),
        ("六边形桥", hexa_done, hexa_fails, "未发现 packages/engine，六边形桥检查未执行"),
        ("Token 闭合", True, token_fails, None),
        ("契约新鲜度", has_uv,
         check_sdk_freshness(root) if has_uv else [],
         "未检测到 uv，契约新鲜度检查跳过（无法重算契约指纹）"),
        ("无空包残留", True, check_empty_packages(root), None),
    ]
    if args.test:
        results.append(("核心测试", has_uv,
                        check_tests(root) if has_uv else [],
                        "未检测到 uv，核心测试跳过"))

    fails = [m for _, done, ms, _ in results if done for m in ms]
    skipped = [(name, note) for name, done, _, note in results if not done]

    print(f"项目: {root}")
    print(f"包名: {pkg}_core")
    for w in token_warns:
        print(f"WARN: {w}")
    if fails:
        print(f"\nFAIL — {len(fails)} 项违规:")
        for f in fails:
            print(f"  ✗ {f}")
        for _, note in skipped:
            print(f"SKIP: {note}")
        return 1
    executed = "、".join(name for name, done, _, _ in results if done)
    print(f"\nPASS — 已执行检查: {executed}")
    for _, note in skipped:
        print(f"SKIP: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
