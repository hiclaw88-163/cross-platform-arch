#!/usr/bin/env bash
# 把仓库根下所有含 SKILL.md 的顶层目录整组同步到本地 skills 目录。
# 用法: tools/sync.sh [目标目录]（默认 ~/.claude/skills）
# 未来新增规范 skill 零改动：目录即 skill，自动发现。
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$HOME/.claude/skills}"
mkdir -p "$DEST"
count=0
for dir in "$REPO_DIR"/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/SKILL.md" ] || continue
  mkdir -p "$DEST/$name"
  rsync -a --delete --exclude '.git' "$dir" "$DEST/$name/"
  echo "synced: $name -> $DEST/$name"
  count=$((count+1))
done
echo "done: $count skill(s) synced"
