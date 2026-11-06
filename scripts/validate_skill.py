#!/usr/bin/env python3
"""Skill 自校验（对齐 anthropics/skills 官方 quick_validate.py 规则 + 本 skill 附加检查）

用法:
    python validate_skill.py <skill目录>

官方规则（Agent Skills spec，agentskills.io）:
  - SKILL.md 必须存在且以 YAML frontmatter 开头
  - frontmatter 仅允许键: name, description, license, allowed-tools, metadata, compatibility
  - name: kebab-case，≤64 字符，不得以连字符开头/结尾或含连续连字符
  - description: ≤1024 字符，不得含尖括号（触发匹配靠它，写清"何时使用"）
本 skill 附加:
  - 必需文件齐全（references/scripts/evals/LICENSE 等）
  - evals/evals.json 结构合法（skill_name 与 frontmatter.name 一致）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
REQUIRED_FILES = [
    "SKILL.md",
    "LICENSE", "LICENSE.txt",
    "scripts/scaffold.py",
    "scripts/verify_project.py",
    "evals/evals.json",
    "references/architecture.md",
    "references/tech-stack.md",
    "references/scaffold.md",
    "references/playbook.md",
    "references/reuse.md",
    "references/output-spec.md",
    "references/design/README.md",
]


def fail(msg: str) -> int:
    print(f"FAIL: {msg}")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1])
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        return fail("SKILL.md not found")

    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return fail("No YAML frontmatter found")
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return fail("Invalid frontmatter format")
    fm_text = m.group(1)

    # 轻量解析（避免依赖 PyYAML）：顶层 key: value
    fm: dict[str, str] = {}
    for line in fm_text.splitlines():
        if not line.strip() or line.startswith((" ", "\t", "#")):
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()

    unexpected = set(fm) - ALLOWED_KEYS
    if unexpected:
        return fail(f"Unexpected frontmatter key(s): {', '.join(sorted(unexpected))}; allowed: {', '.join(sorted(ALLOWED_KEYS))}")
    if "name" not in fm or "description" not in fm:
        return fail("Missing 'name' or 'description' in frontmatter")

    name = fm["name"].strip('"')
    if not re.match(r"^[a-z0-9-]+$", name):
        return fail(f"Name '{name}' should be kebab-case")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return fail(f"Name '{name}' has invalid hyphen placement")
    if len(name) > 64:
        return fail(f"Name too long ({len(name)} > 64)")

    desc = fm["description"].strip('"')
    if "<" in desc or ">" in desc:
        return fail("Description cannot contain angle brackets")
    if len(desc) > 1024:
        return fail(f"Description too long ({len(desc)} > 1024)")

    # 附加检查：必需文件（LICENSE 允许 LICENSE 或 LICENSE.txt 其一）
    missing = []
    seen: set[str] = set()
    for p in REQUIRED_FILES:
        if p.startswith("LICENSE"):
            if "LICENSE" not in seen:
                seen.add("LICENSE")
                if not (root / "LICENSE").exists() and not (root / "LICENSE.txt").exists():
                    missing.append("LICENSE(.txt)")
            continue
        if not (root / p).exists():
            missing.append(p)
    if missing:
        return fail(f"Missing required file(s): {', '.join(missing)}")

    # evals.json 结构
    try:
        ev = json.loads((root / "evals/evals.json").read_text(encoding="utf-8"))
        if ev.get("skill_name") != name:
            return fail(f"evals.json skill_name '{ev.get('skill_name')}' != frontmatter name '{name}'")
        for e in ev.get("evals", []):
            for k in ("id", "prompt", "expectations"):
                if k not in e:
                    return fail(f"evals.json eval#{e.get('id', '?')} missing key '{k}'")
    except json.JSONDecodeError as e:
        return fail(f"evals.json invalid JSON: {e}")

    print(f"PASS — frontmatter 合规（name/description 符合 Agent Skills 规范）、"
          f"{len(REQUIRED_FILES)-1} 个必需文件齐全、evals 结构合法")
    return 0


if __name__ == "__main__":
    sys.exit(main())
