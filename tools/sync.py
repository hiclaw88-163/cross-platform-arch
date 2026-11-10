#!/usr/bin/env python3
"""sync.sh 的 Python 便携版（不依赖 rsync/bash，Windows 友好）。

把仓库根下所有含 SKILL.md 的顶层目录整组同步到本地 skills 目录。
镜像语义对齐 rsync -a --delete：多出的文件会被删除（排除缓存/依赖目录）。
用法:
    python tools/sync.py            # 同步到 ~/.claude/skills
    python tools/sync.py [目标目录]
与 tools/sync.sh 行为一致，按环境任选其一。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# 与 sync.sh 的 exclude 等价，另加常见缓存/依赖目录（在本仓库不会出现在产物里）
IGNORE_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache",
               ".ruff_cache", ".mypy_cache", ".idea", ".vscode"}


def _rel_parts(p: Path, base: Path) -> set[str]:
    return set(p.relative_to(base).parts)


def sync_skill(src: Path, dst: Path) -> tuple[int, int]:
    """镜像同步单个 skill 目录，返回 (复制数, 删除数)。"""
    copied = 0
    for f in sorted(src.rglob("*")):
        if not f.is_file() or (IGNORE_DIRS & _rel_parts(f, src)):
            continue
        target = dst / f.relative_to(src)
        if target.parent.is_dir() is False:
            target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.stat().st_mtime != f.stat().st_mtime \
                or target.stat().st_size != f.stat().st_size:
            shutil.copy2(f, target)
            copied += 1
    deleted = 0
    # 镜像清理：目标侧多出的文件删除（对齐 rsync --delete）
    for f in sorted((p for p in dst.rglob("*") if p.is_file()), reverse=True):
        if IGNORE_DIRS & _rel_parts(f, dst):
            continue
        counterpart = src / f.relative_to(dst)
        if not counterpart.exists() or (IGNORE_DIRS & _rel_parts(counterpart, src)):
            f.unlink()
            deleted += 1
    # 清掉变空的目录
    for d in sorted((p for p in dst.rglob("*") if p.is_dir()), reverse=True):
        if IGNORE_DIRS & _rel_parts(d, dst):
            continue
        try:
            d.rmdir()
        except OSError:
            pass  # 非空（尚有排除目录或保留目录）
    return copied, deleted


def main() -> int:
    ap = argparse.ArgumentParser(description="批量同步所有 skill 到本地 skills 目录（Python 便携版）")
    ap.add_argument("dest", nargs="?", default=None,
                    help="目标 skills 目录（默认 ~/.claude/skills）")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    dest = Path(args.dest).expanduser() if args.dest else Path.home() / ".claude" / "skills"
    dest.mkdir(parents=True, exist_ok=True)

    skills = sorted(d for d in repo_root.iterdir()
                    if d.is_dir() and (d / "SKILL.md").exists())
    if not skills:
        print("FAIL: 未发现任何含 SKILL.md 的顶层 skill 目录")
        return 1

    total = 0
    for s in skills:
        c, d = sync_skill(s, dest / s.name)
        total += c
        note = f"（+{c} 更新{f'，-{d} 删除' if d else ''}）" if (c or d) else "（无差异）"
        print(f"synced: {s.name} -> {dest / s.name} {note}")
    print(f"done: {len(skills)} skill(s) synced, {total} file(s) updated -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
