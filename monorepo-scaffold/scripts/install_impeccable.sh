#!/usr/bin/env bash
# 按需安装 impeccable（视觉精修 skill）到本机 skill 目录。
# 注意：impeccable 仓库未附 LICENSE，本脚本只做按需克隆，不随本 skill 分发其内容。
# 用法: bash install_impeccable.sh [目标目录]  (默认 ~/.claude/skills)
set -euo pipefail

DEST="${1:-$HOME/.claude/skills}"
REPO="https://github.com/pbakaus/impeccable.git"

mkdir -p "$DEST"
TMP="$(mktemp -d)"
echo "[1/3] 浅克隆 $REPO ..."
git -c http.schannelCheckRevoke=false clone --depth 1 "$REPO" "$TMP/impeccable"
echo "[2/3] 复制 .agent/skills/impeccable -> $DEST/impeccable"
rm -rf "$DEST/impeccable"
cp -r "$TMP/impeccable/.agent/skills/impeccable" "$DEST/impeccable"
echo "[3/3] 记录来源: $DEST/impeccable/.SOURCE"
cat > "$DEST/impeccable/.SOURCE" <<EOF
source: $REPO
installed: $(date -u +%Y-%m-%dT%H:%M:%SZ)
license: 仓库未附 LICENSE，仅供个人按需使用，勿再分发
EOF
rm -rf "$TMP"
echo "完成。使用方式：对目标前端运行 /audit 体检、/polish 精修。"
