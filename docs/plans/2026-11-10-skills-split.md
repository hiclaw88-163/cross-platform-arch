# 多 Skill 集合仓库拆分实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把单 skill 仓库 `cross-platform-arch` 拆分为 4 个独立 skill 的集合仓库（方案 A），根目录平铺、整组同步到 `~/.claude/skills/`。

**Architecture:** 纯文件重组 + 新写 4 份 SKILL.md + 改造 2 个工具脚本，无运行时行为变更。设计文档：`docs/superpowers/specs/2026-11-10-skills-split-design.md`（本次实施的唯一依据）。

**Tech Stack:** Bash (git mv/rsync)、Python 3（标准库）、Markdown。

**通用约束（每个 Task 都遵守）：**
- 用 `git mv` 移动文件保留历史，不用 cp+rm。
- 原 `SKILL.md` 顶部为 frontmatter（1-9 行），正文核心区 11-112 行；下文「原 SKILL.md L」均指当前仓库根 `SKILL.md` 的行号。
- 每完成一个 Task 提交一次。

---

### Task 1: 目录骨架与文件归位（git mv）

**Files:**
- Create: `cross-platform-design/`、`monorepo-scaffold/`、`arch-verify/`、`legacy-rewrite/`、`docs/`、`tools/`
- Move: references、scripts、design 能力包、validate_skill.py、anthropic-patterns.md

**Step 1: 建目录并 git mv 归位**

```bash
cd /Users/jason.zhuo/codes/leisure/leisure_skill/cross-platform-arch
mkdir -p cross-platform-design monorepo-scaffold arch-verify legacy-rewrite docs tools

# cross-platform-design
git mv references/architecture.md references/hexagonal-arch.md references/clients.md \
       references/tech-stack.md references/reuse.md cross-platform-design/
mkdir -p cross-platform-design/references
git mv cross-platform-design/architecture.md cross-platform-design/hexagonal-arch.md \
       cross-platform-design/clients.md cross-platform-design/tech-stack.md cross-platform-design/reuse.md \
       cross-platform-design/references/

# monorepo-scaffold
git mv references/scaffold.md references/playbook.md monorepo-scaffold/
git mv references/design monorepo-scaffold/references/design
git mv scripts/scaffold.py scripts/install_impeccable.sh monorepo-scaffold/

# arch-verify
git mv references/output-spec.md arch-verify/
git mv scripts/verify_project.py arch-verify/

# legacy-rewrite
git mv references/migration.md legacy-rewrite/

# 仓库级
git mv references/anthropic-patterns.md docs/
git mv scripts/validate_skill.py tools/
```

注意：第一组 mv 把 5 个 md 移到了 `cross-platform-design/` 根，第二条命令再移入其 `references/`——若嫌绕可先 `mkdir -p cross-platform-design/references` 再一次性 `git mv ... cross-platform-design/references/`。

**Step 2: 验证归位结果**

```bash
ls cross-platform-design/references monorepo-scaffold arch-verify legacy-rewrite docs tools
```
Expected: design 下 5 个规约 md；scaffold 下 scaffold.md、playbook.md、references/design/、scripts/；arch-verify 下 output-spec.md、verify_project.py；legacy-rewrite 下 migration.md。

**Step 3: Commit**

```bash
git add -A && git commit -m "refactor: 按 skill 拆分归位 references/scripts（内容不变）"
```

---

### Task 2: evals.json 拆分为 4 份

**Files:**
- Create: `cross-platform-design/evals/evals.json`（eval 2）、`monorepo-scaffold/evals/evals.json`（eval 1、5）、`arch-verify/evals/evals.json`（eval 4、7）、`legacy-rewrite/evals/evals.json`（eval 3、6）
- Delete: 根 `evals/evals.json`

**Step 1:** 按 eval `id` 把根 `evals/evals.json` 的条目分拆到 4 个文件（eval 2→design，1/5→scaffold，4/7→verify，3/6→legacy；id 重新从 1 编号），每份 `skill_name` 改为对应目录名。

**Step 2:** `git rm evals/evals.json`（顶层 evals/ 目录随之为空删除）。

**Step 3:** 校验 4 份均为合法 JSON 且 `skill_name` 正确：

```bash
for s in cross-platform-design monorepo-scaffold arch-verify legacy-rewrite; do
  python3 -c "import json;d=json.load(open('$s/evals/evals.json'));assert d['skill_name']=='$s',d;print('$s OK')"
done
```

**Step 4: Commit**

```bash
git add -A && git commit -m "refactor: evals 按 skill 拆分"
```

---

### Task 3: cross-platform-design/SKILL.md

**Files:**
- Create: `cross-platform-design/SKILL.md`

**Step 1: 写入完整文件。** frontmatter：

```yaml
---
name: cross-platform-design
description: 「一核多端」统一应用架构的设计与评审规约。TRIGGER when 设计或评审支持 CLI/Web/桌面/小程序/App 多端的软件架构、多端技术选型问答（桌面用 Electron 还是 pywebview、小程序框架选型）、评估新业务如何复用这套架构；DO NOT TRIGGER when 要从零搭建新项目（用 monorepo-scaffold）、要验收项目是否符合架构（用 arch-verify）、要把旧项目功能迁移进来（用 legacy-rewrite）。
license: MIT
metadata:
  version: "1.0.0"
  date: "2026-11-10"
  author: WorkBuddy Agent
---
```

正文结构（按原 SKILL.md 行号迁移，标题层级保持）：
- 一级标题 `# 一核多端（One Core, Multi-Client）统一应用架构` + 一句话定位（原 L11-13 原文照搬）。
- `## 核心原则`：原 L15-21 原文照搬。
- `## 需求定位（先问/先判三件事）`：原 L25-31 原文照搬（含指向 `references/tech-stack.md` 的相对引用，路径不变）。
- `## 关键决策速查`：原 L84-96 表格原文照搬。
- `## 参考文件`：列本 skill 的 references/architecture.md、hexagonal-arch.md、clients.md、tech-stack.md、reuse.md（描述文字沿用原 L100-109 对应条目）。
- 新增 `## 与其他 skill 的关系`（原文如下）：

```markdown
## 与其他 skill 的关系

本 skill 定的是"架构长什么样"。落地动作在兄弟 skill（约定整组安装、用 `../` 相对引用）：

- 从零搭新项目：`../monorepo-scaffold/`（脚手架生成 + SDK 打通 + 演示链路 + 设计系统）
- 验收项目是否符合本架构：`../arch-verify/`（机器门禁）
- 旧项目功能重写接入：`../legacy-rewrite/`
```

**Step 2:** `python3 tools/validate_skill.py cross-platform-design` → PASS（validate_skill.py 若尚未改造完成，先允许旧版对单目录的校验因缺 REQUIRED_FILES 报缺文件——Task 7 会改造；此时可跳过该步）。

**Step 3: Commit**

```bash
git add cross-platform-design/SKILL.md && git commit -m "feat: cross-platform-design skill（架构设计与评审）"
```

---

### Task 4: monorepo-scaffold/SKILL.md

**Files:**
- Create: `monorepo-scaffold/SKILL.md`

**Step 1: 写入完整文件。** frontmatter：

```yaml
---
name: monorepo-scaffold
description: 从零搭建「一核多端」Monorepo 项目：脚手架生成、OpenAPI 契约打通各端 TS SDK、演示链路跑通、设计系统生成。TRIGGER when 新建一核多端项目、生成 Monorepo 骨架、打通 OpenAPI 契约到各端 SDK、页面太丑要升级设计系统；DO NOT TRIGGER when 只做架构设计或选型问答（用 cross-platform-design）、旧项目功能迁移（用 legacy-rewrite）、仅验收已有项目（用 arch-verify）。
license: MIT
metadata:
  version: "1.0.0"
  date: "2026-11-10"
  author: WorkBuddy Agent
---
```

正文结构：
- `# 从零搭建「一核多端」Monorepo 项目`
- `## 脚手架生成`：原 L33-42 原文照搬，仅两处路径改写——脚本路径改为 `python scripts/scaffold.py --name my-app --dir /path/to/my-app`（相对本 skill 目录），scaffold.md 引用不变（`references/scaffold.md`）。
- `## 生成后必须立即验证`（原 L48-54 内容前移）：开头保留 `python ../arch-verify/scripts/verify_project.py --project /path/to/my-app --test` 命令，正文压缩为一句"七项检查（结构完整性/核心纯净性/依赖方向/Token 引用闭合/六边形桥+契约新鲜度/无空包残留/核心测试）见 `../arch-verify/`，任何 FAIL 必须先修复再进入下一步"。
- `## 跑通演示链路`：原 L56-63 原文照搬（指向 `references/playbook.md`）。
- `## 设计系统生成`：原 L65-78 原文照搬（`references/design/` 相对引用不变）。
- `## 参考文件`：references/scaffold.md、playbook.md、design/（沿用原 L104、L108、L110 描述），scripts/scaffold.py、install_impeccable.sh（沿用原 L111-112）。
- 新增同步警示 + 跨 skill 段（原文如下）：

```markdown
## 同步警示

本 skill 的脚手架产出清单与 arch-verify 的检查项必须对齐。**单一事实来源是
`../arch-verify/references/output-spec.md` 的文件清单**——改脚手架产出（新增/删除生成文件）
时必须同步该清单，否则机器门禁会误报或漏报。

## 与其他 skill 的关系

- 架构设计与选型问答：`../cross-platform-design/`
- 生成后验收：`../arch-verify/`（生成后必须立即运行其 verify_project.py）
- 旧项目功能重写接入：`../legacy-rewrite/`
```

**Step 2: Commit**

```bash
git add monorepo-scaffold/SKILL.md && git commit -m "feat: monorepo-scaffold skill（脚手架+SDK+演示链路+设计系统）"
```

---

### Task 5: arch-verify/SKILL.md

**Files:**
- Create: `arch-verify/SKILL.md`

**Step 1: 写入完整文件。** frontmatter：

```yaml
---
name: arch-verify
description: 一核多端项目的机器门禁验收：verify_project.py 七项检查 + 产出规范与质量门禁清单。TRIGGER when 验收或检查项目是否符合一核多端架构要求、把架构约束交给机器判定、诊断"页面样式不完整/间距颜色没生效"这类 token 未定义问题；DO NOT TRIGGER when 从零生成新项目（用 monorepo-scaffold）、修改架构规范本身（用 cross-platform-design）。
license: MIT
metadata:
  version: "1.0.0"
  date: "2026-11-10"
  author: WorkBuddy Agent
---
```

正文结构：
- `# 一核多端项目机器门禁验收`
- `## 用法`：原 L50-51 命令，路径改为 `python scripts/verify_project.py --project /path/to/my-app --test`（相对本 skill）。
- `## 七项检查`：原 L54 检查项拆成列表逐条呈现（①结构完整性含设计决策记录 ②核心纯净性 ③依赖方向性 ④Token 引用闭合 ⑤六边形桥闭合+契约新鲜度 ⑥无空包残留 ⑦核心测试），每条保留原文括号内的说明（尤其⑥的空目录假成功事故描述、④的"样式残缺不报错必须机器判定"）。收尾句：任何一项 FAIL 必须先修复。
- `## 产出规范`：指向 `references/output-spec.md`（沿用原 L105 描述），并加一句（原文如下）：

```markdown
本文件清单是**单一事实来源**：`../monorepo-scaffold/` 的脚手架产出必须与本清单对齐，
脚手架变更时同步更新本清单。
```

- `## 与其他 skill 的关系`：从零搭项目用 ../monorepo-scaffold/；存量项目重写接入的项目在验收时额外执行 ../legacy-rewrite/ 的"端零映射 + 行为一致性"检查（原 L46 尾句语义迁移至此）。

**Step 2: Commit**

```bash
git add arch-verify/SKILL.md && git commit -m "feat: arch-verify skill（机器门禁验收）"
```

---

### Task 6: legacy-rewrite/SKILL.md

**Files:**
- Create: `legacy-rewrite/SKILL.md`

**Step 1: 写入完整文件。** frontmatter：

```yaml
---
name: legacy-rewrite
description: 存量项目重写接入「一核多端」架构的规约：旧项目是协议字典+行为验收 oracle，不是代码来源。TRIGGER when 把已有项目/旧系统的功能用一核多端架构重新实现、评估旧代码怎么迁移、需要产出功能归属映射表或旧弊端对照表；DO NOT TRIGGER when 从零新项目（用 monorepo-scaffold）、纯架构设计问答（用 cross-platform-design）、常规项目验收（用 arch-verify）。
license: MIT
metadata:
  version: "1.0.0"
  date: "2026-11-10"
  author: WorkBuddy Agent
---
```

正文结构：
- `# 存量项目重写接入`
- 定性反转段：原 L46 原文照搬（含 PROTOCOL.md 提炼与行为一致性对照）。
- `## 五步流程与薄壳反模式`：指向 `references/migration.md`（沿用原 L106 描述），说明此类项目验收时额外执行"端零映射 + 行为一致性"检查（`../arch-verify/` 的 verify_project.py 之外）。
- `## 与其他 skill 的关系`：从零搭新项目用 ../monorepo-scaffold/；落地后的机器验收用 ../arch-verify/。

**Step 2: Commit**

```bash
git add legacy-rewrite/SKILL.md && git commit -m "feat: legacy-rewrite skill（存量项目重写接入）"
```

---

### Task 7: tools/validate_skill.py 改造（批量模式 + 引用闭合）

**Files:**
- Modify: `tools/validate_skill.py`（全文重写，~124 行）

**改造点：**
1. **批量模式**：无参数运行时，遍历脚本所在仓库根下的直接子目录，凡含 `SKILL.md` 的目录逐个校验（docs/tools 无 SKILL.md 自动跳过）；带目录参数时保留单 skill 校验。任一 skill FAIL → 整体退出码 1。
2. **删除硬编码 REQUIRED_FILES**：4 个 skill 结构不同，改为**引用闭合检查**——扫描 SKILL.md 正文中的 `references/…`、`scripts/…`、`evals/…` 相对路径引用（正则 `\b(?:references|scripts|evals)/[\w\-./]+\b`），逐个确认文件存在；SKILL.md 中 `../` 开头的跨 skill 引用仅校验目标目录存在（不校验深路径，允许兄弟 skill 未整组安装）。
3. **evals.json 检查改为可选**：`evals/evals.json` 存在时才校验结构（skill_name 一致、evals 条目键齐全），不存在不报错。
4. frontmatter 规则（ALLOWED_KEYS/kebab-case/description 限长禁尖括号）原样保留。

**验收：**

```bash
cd /Users/jason.zhuo/codes/leisure/leisure_skill/cross-platform-arch && python3 tools/validate_skill.py
```
Expected: 4 个 skill 全部 PASS。随后故意在任一 SKILL.md 里写一个不存在的 `references/foo.md` 引用再跑，应 FAIL（测完还原）。

**Commit:**

```bash
git add tools/validate_skill.py && git commit -m "feat: validate_skill 改造为批量模式+引用闭合检查"
```

---

### Task 8: tools/sync.sh

**Files:**
- Create: `tools/sync.sh`（chmod +x）

**内容：**

```bash
#!/usr/bin/env bash
# 把仓库根下所有含 SKILL.md 的顶层目录整组同步到 ~/.claude/skills/
# 未来新增规范 skill 零改动：目录即 skill。
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
```

**验收：**

```bash
chmod +x tools/sync.sh && bash -n tools/sync.sh && ./tools/sync.sh /tmp/skills-test
```
Expected: 4 个 skill 同步到 /tmp/skills-test/，且 `ls /tmp/skills-test` 恰为 4 个目录（docs/tools 被跳过）。测完 `rm -rf /tmp/skills-test`。

**Commit:**

```bash
git add tools/sync.sh && git commit -m "feat: sync.sh 整组同步 skill 到本地 skills 目录"
```

---

### Task 9: README.md 重写 + CHANGELOG 2.0.0

**Files:**
- Modify: `README.md`（全文重写）
- Modify: `CHANGELOG.md`（顶部插入 2.0.0 章节）

**README 结构：**
1. 仓库定位一句话：开发规范 skill 集合仓库（anthropics/skills 形态，目录即 skill）。
2. **Skill 总览表**：4 个 skill 的名称/一句话职责/典型触发场景（从各 SKILL.md description 提炼）。
3. **安装（整组拷贝）**：`tools/sync.sh` 用法 + "必须整组使用，SKILL.md 间用 `../` 相对引用"警示。
4. **扩展：新增 skill 三步流程**（设计文档 §7）：建目录+互斥触发词 SKILL.md → README 表加一行 → validate_skill.py 通过即被 sync.sh 发现。
5. **扩展：从项目规范提炼 skill 五步流程**（设计文档 §7.1 全文迁入：盘点候选→去项目化→去重归并→补触发词与验证→落库；首批候选列 keshumai 三份规范）。
6. 仓库级文件说明：CHANGELOG 根级记录全部版本；docs/ 放元知识（anthropic-patterns.md）；tools/ 放校验与同步脚本。

**CHANGELOG 顶部插入：**

```markdown
## 2.0.0 (2026-11-10) — breaking

单 skill 拆分为 4 个独立 skill（方案 A，按工作流阶段拆分）：

- `cross-platform-design`（架构设计与评审）— 收编原核心原则、阶段1 需求定位、关键决策速查表与 architecture/hexagonal/clients/tech-stack/reuse 五份规约
- `monorepo-scaffold`（从零搭建）— 收编原阶段2 脚手架生成、阶段3 演示链路、阶段3.5 设计系统与 scaffold.py/playbook/design 能力包
- `arch-verify`（机器门禁验收）— 收编原 verify 七项检查、verify_project.py 与 output-spec.md
- `legacy-rewrite`（存量重写接入）— 收编原阶段2.5 定性反转与 migration.md

配套：evals 按 skill 拆分；validate_skill.py 改造为批量模式+引用闭合检查（tools/）；新增 sync.sh（tools/）；
anthropic-patterns.md 移入 docs/；各 skill 版本自 1.0.0 独立起步，本 CHANGELOG 继续记录整个仓库。
```

**Commit:**

```bash
git add README.md CHANGELOG.md && git commit -m "docs: README 重写为 skill 集合仓库总览，CHANGELOG 记录 2.0.0 拆分"
```

---

### Task 10: 清理残留 + 全量验证 + 推送

**Step 1: 删除顶层残留**

```bash
git rm SKILL.md
rmdir references scripts evals 2>/dev/null || true   # 若 Task 1/2 后仍有空壳
git status   # 确认无游离文件
```

**Step 2: 全量验证**

```bash
python3 tools/validate_skill.py          # Expected: 4 skill 全 PASS
./tools/sync.sh /tmp/skills-test && ls /tmp/skills-test && rm -rf /tmp/skills-test
# 抽查跨引用可达：4 个 SKILL.md 中的 ../ 相对目标目录均存在
grep -h '\.\./' */SKILL.md | grep -o '\.\./[a-z-]*' | sort -u
# Expected: ../arch-verify ../cross-platform-design ../legacy-rewrite ../monorepo-scaffold
# 抽查脚本仍可运行：
python3 monorepo-scaffold/scripts/scaffold.py --help | head -5   # --help 正常输出
python3 arch-verify/scripts/verify_project.py 2>&1 | head -5     # 打印用法，无 import 错误
```

**Step 3: Commit + 推送**

```bash
git add -A && git commit -m "chore: 删除拆分后的顶层单 skill 残留" && git push
```
