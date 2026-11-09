#!/usr/bin/env python3
"""项目 docs 骨架一键生成（project-docs skill）

用法:
    python init_docs.py --name my-app --dir /path/to/my-app-docs [--force]

行为:
    1. 按 templates/ 生成骨架: AGENTS.md、README.md、TODO.md、
       conventions/00-项目配置.md、conventions/规范索引.md、conventions/规范模板.md、
       adr/ADR-模板.md、specs/README.md（层级字母↔子目录映射入口，默认 TOGAF 映射）,
       以及 guides/ plans/ scripts/ 空目录(.gitkeep)
    2. 仅替换 {project}/{projectName} 两个占位符; 其余占位符（{basePackage}、{date}、
       {owners}…）保留原样, 由人按项目事实填写
    3. 默认不覆盖已存在文件; --force 覆盖
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_ROOT / "templates"

# 生成骨架的文件映射: 模板相对路径 -> 目标相对路径
FILES = [
    ("AGENTS.md", "AGENTS.md"),
    ("README.md", "README.md"),
    ("TODO.md", "TODO.md"),
    ("conventions/00-项目配置.md", "conventions/00-项目配置.md"),
    ("conventions/规范索引.md", "conventions/规范索引.md"),
    ("conventions/规范模板.md", "conventions/01-规范模板.md"),
    ("adr/ADR-模板.md", "adr/ADR-001-结论式标题.md"),
    ("specs/README.md", "specs/README.md"),
]
EMPTY_DIRS = ["guides", "plans", "scripts"]

# 只替换这两个; 其余占位符留给人工填写
AUTO_VARS = {"{project}": None, "{projectName}": None}  # 值由 --name 填充
# 00-项目配置.md 是变量定义表：占位符是「变量名」本身，禁止被自动替换
NO_AUTO_REPLACE = {"conventions/00-项目配置.md"}


def main() -> int:
    p = argparse.ArgumentParser(description="生成项目 docs 骨架")
    p.add_argument("--name", required=True, help="项目名（替换 {project}/{projectName}）")
    p.add_argument("--dir", required=True, help="目标目录（docs 仓库根）")
    p.add_argument("--force", action="store_true", help="覆盖已存在文件")
    args = p.parse_args()

    target = Path(args.dir).resolve()
    if target.exists() and not target.is_dir():
        print(f"FAIL: {target} 已存在且不是目录")
        return 1

    replacements = {k: args.name for k in AUTO_VARS}
    created, skipped = [], []

    for tpl_rel, out_rel in FILES:
        src = TEMPLATE_DIR / tpl_rel
        if not src.exists():
            print(f"FAIL: 模板缺失 {src}")
            return 1
        dst = target / out_rel
        if dst.exists() and not args.force:
            skipped.append(out_rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8")
        if out_rel not in NO_AUTO_REPLACE:
            for k, v in replacements.items():
                text = text.replace(k, v)
        dst.write_text(text, encoding="utf-8")
        created.append(out_rel)

    for d in EMPTY_DIRS:
        empty = target / d
        empty.mkdir(parents=True, exist_ok=True)
        keep = empty / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
            created.append(f"{d}/.gitkeep")

    print(f"created: {len(created)} file(s)")
    for f in created:
        print(f"  + {f}")
    if skipped:
        print(f"skipped (已存在, --force 可覆盖): {len(skipped)} file(s)")
        for f in skipped:
            print(f"  = {f}")

    # 提醒剩余占位符
    remaining = sorted({
        m
        for f in created
        for m in __import__("re").findall(r"\{[a-zA-Z][\w-]*\}", (target / f).read_text(encoding="utf-8"))
        if m not in ("{project}", "{projectName}")
    })
    if remaining:
        print("\n待人工填写占位符: " + ", ".join(remaining))
        print("（唯一变量入口 conventions/00-项目配置.md 建好后，逐文件替换）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
