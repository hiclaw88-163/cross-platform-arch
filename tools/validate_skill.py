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
  - 版本一致性: frontmatter metadata.version 必须等于 CHANGELOG.md 中该 skill
    最新条目（第一个 `## <skill名> x.y.z`）的版本号；缺少 metadata.version 判
    FAIL；CHANGELOG.md 不存在时跳过比对，无该 skill 条目时报"无条目"
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


def metadata_version(content: str) -> tuple[bool, str | None]:
    """提取嵌套键 metadata.version（轻量解析，无 PyYAML）。

    定位 `metadata:` 行，收集其后所有缩进更深的行作为该块（遇到缩进回到
    顶层的非空行即结束），在块内找 `version:` 子键——version 不必是第一个
    子键；值两端的单、双引号都剥除；行尾 `# 注释` 剥除（YAML 中空白后的
    # 起注释，值内不带前导空白的 # 不受影响）。返回 (块内是否存在 version, 版本值)。
    """
    in_block = False
    for line in content.split("\n---", 1)[0].splitlines():
        if not in_block:
            if re.match(r"^metadata:\s*$", line):
                in_block = True
            continue
        if line.strip() and not line.startswith((" ", "\t")):
            break  # 缩进回到顶层，metadata 块结束
        m = re.match(r"^[ \t]+version:\s*(.+?)\s*$", line)
        if m:
            val = re.split(r"\s+#", m.group(1).strip(), maxsplit=1)[0].strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            return True, val
    return False, None


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

    # 独立性延伸：scripts/ 里的脚本禁止引用**其它 skill 目录**（skill 名取自仓库
    # 内含 SKILL.md 的兄弟目录；生成项目内部的相对路径如 ../web/dist 不算跨 skill，
    # 予以放行——monorepo-scaffold 曾运行时探测同侧 arch-verify，现已改为自带
    # 同源副本）
    if (root / "scripts").is_dir():
        siblings = sorted(d.name for d in root.parent.iterdir()
                          if d.is_dir() and (d / "SKILL.md").exists() and d != root)
        if siblings:
            sib_re = re.compile(r"\.\./(" + "|".join(re.escape(s) for s in siblings) + r")\b")
            for script in sorted((root / "scripts").glob("*")):
                if script.suffix not in (".py", ".sh", ".mjs", ".js", ".cjs") or not script.is_file():
                    continue
                text = script.read_text(encoding="utf-8", errors="ignore")
                bad = sorted(set(sib_re.findall(text)))
                if bad:
                    return (f"{script.name}: cross-skill path reference(s) forbidden "
                            f"(skills must be self-contained): "
                            + ", ".join(f"../{s}" for s in bad))

    # 同源校验：monorepo-scaffold 自带的 verify_project.py 副本必须与
    # arch-verify 的权威版本字节一致（vendoring 依赖此副本，漂移会让生成项目
    # 跑着旧门禁）
    if name == "monorepo-scaffold":
        authority = root.parent / "arch-verify" / "scripts" / "verify_project.py"
        vendored = root / "scripts" / "verify_project.py"
        if authority.exists() and vendored.exists():
            if authority.read_bytes() != vendored.read_bytes():
                return ("vendored scripts/verify_project.py 与 arch-verify 权威版本"
                        "不一致——两份必须同源（以 arch-verify 为准同步）")

    # 版本一致性：frontmatter metadata.version 必须等于 CHANGELOG 中该 skill
    # 最新条目（第一个 `## <skill名> x.y.z`）的版本号——改版漏更其一即漂移；
    # 缺少 metadata.version 同样 FAIL。CHANGELOG.md 不存在（如校验仓库外目录）
    # 时跳过比对；CHANGELOG 里没有该 skill 条目时报"无条目"
    has_ver, ver = metadata_version(content)
    if not has_ver:
        return "缺少 metadata.version（frontmatter metadata 块内没有 version 子键）"
    changelog = root.parent / "CHANGELOG.md"
    if changelog.exists():
        m = re.search(rf"^## {re.escape(name)} (\d+\.\d+\.\d+)\b",
                      changelog.read_text(encoding="utf-8"), re.M)
        latest = m.group(1) if m else None
        if latest != ver:
            return (f"版本不一致: SKILL.md metadata.version={ver}, "
                    f"CHANGELOG.md 最新 {name} 条目={latest or '无条目'}")

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
