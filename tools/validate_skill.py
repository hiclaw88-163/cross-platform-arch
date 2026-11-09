#!/usr/bin/env python3
"""Skill 集合仓库校验（对齐 anthropics/skills 官方 quick_validate.py 规则 + 引用闭合检查）

用法:
    python validate_skill.py            # 批量模式：校验仓库根下所有含 SKILL.md 的顶层目录
    python validate_skill.py <skill目录> # 单 skill 校验

官方规则（Agent Skills spec，agentskills.io）:
  - SKILL.md 必须存在且以 YAML frontmatter 开头
  - frontmatter 仅允许键: name, description, license, allowed-tools, metadata, compatibility
  - name: kebab-case，≤64 字符，不得以连字符开头/结尾或含连续连字符
  - description: ≤1024 字符，不得含尖括号（触发匹配靠它，写清"何时使用"）
本仓库附加:
  - 引用闭合: SKILL.md 正文里提到的 references/…、scripts/…、evals/… 相对路径必须存在
    （各 skill 完全独立、互不依赖，禁止 ../ 跨 skill 文件引用）
  - evals/evals.json 存在时校验结构（skill_name 与 frontmatter.name 一致、条目键齐全）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
LOCAL_REF_RE = re.compile(r"(?<![\w.\-/])(?:references|scripts|evals)/[\w\-./]+")
# 各 skill 必须独立：禁止 ../ 跨 skill 文件引用
CROSS_REF_FORBID_RE = re.compile(r"\.\./[\w\-./]+")


def fail(msg: str) -> str:
    return f"FAIL: {msg}"


def parse_frontmatter(content: str) -> tuple[dict[str, str] | None, str | None]:
    """轻量解析 frontmatter（避免依赖 PyYAML），返回 (fm, 错误信息)。"""
    if not content.startswith("---"):
        return None, "No YAML frontmatter found"
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return None, "Invalid frontmatter format"
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.startswith((" ", "\t", "#")):
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm, None


def validate_one(root: Path) -> str | None:
    """校验单个 skill 目录，返回错误信息（None=通过）。"""
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        return "SKILL.md not found"

    content = skill_md.read_text(encoding="utf-8")
    fm, err = parse_frontmatter(content)
    if err:
        return err

    unexpected = set(fm) - ALLOWED_KEYS
    if unexpected:
        return f"Unexpected frontmatter key(s): {', '.join(sorted(unexpected))}"
    if "name" not in fm or "description" not in fm:
        return "Missing 'name' or 'description' in frontmatter"

    name = fm["name"].strip('"')
    if not re.match(r"^[a-z0-9-]+$", name):
        return f"Name '{name}' should be kebab-case"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return f"Name '{name}' has invalid hyphen placement"
    if len(name) > 64:
        return f"Name too long ({len(name)} > 64)"

    desc = fm["description"].strip('"')
    if "<" in desc or ">" in desc:
        return "Description cannot contain angle brackets"
    if len(desc) > 1024:
        return f"Description too long ({len(desc)} > 1024)"

    # 引用闭合：本地相对路径引用必须存在
    body = content.split("\n---", 1)[-1]
    missing = sorted({r.rstrip("/") for r in LOCAL_REF_RE.findall(body)
                      if not (root / r.rstrip("/")).exists()})
    if missing:
        return f"Dangling local reference(s): {', '.join(missing)}"

    # 独立性：禁止 ../ 跨 skill 文件引用（anthropics/skills 形态，skill 互不依赖）
    bad_cross = sorted(set(CROSS_REF_FORBID_RE.findall(body)))
    if bad_cross:
        return f"Cross-skill file reference(s) forbidden (skills must be self-contained): {', '.join(bad_cross)}"

    # evals.json 可选校验
    ev_path = root / "evals/evals.json"
    if ev_path.exists():
        try:
            ev = json.loads(ev_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return f"evals.json invalid JSON: {e}"
        if ev.get("skill_name") != name:
            return f"evals.json skill_name '{ev.get('skill_name')}' != frontmatter name '{name}'"
        for e in ev.get("evals", []):
            for k in ("id", "prompt", "expectations"):
                if k not in e:
                    return f"evals.json eval#{e.get('id', '?')} missing key '{k}'"

    return None


def main() -> int:
    if len(sys.argv) > 2:
        print(__doc__)
        return 2

    if len(sys.argv) == 2:
        targets = [Path(sys.argv[1])]
    else:
        repo_root = Path(__file__).resolve().parent.parent
        targets = [d for d in sorted(repo_root.iterdir())
                   if d.is_dir() and (d / "SKILL.md").exists()]
        if not targets:
            print("FAIL: no skill directory (with SKILL.md) found in repo root")
            return 1

    failed = 0
    for t in targets:
        err = validate_one(t)
        label = t.name if len(sys.argv) == 1 else str(t)
        if err:
            print(f"{label}: {fail(err)}")
            failed += 1
        else:
            print(f"{label}: PASS — frontmatter 合规、引用闭合、evals 结构合法")

    if failed:
        print(f"\n{failed}/{len(targets)} skill(s) FAILED")
        return 1
    print(f"\nall {len(targets)} skill(s) PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
