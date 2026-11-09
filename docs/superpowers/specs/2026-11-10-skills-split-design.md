# 设计文档：cross-platform-arch 拆分为多 skill 集合仓库

日期：2026-11-10
状态：已确认（方案 A）
背景：参照 github.com/anthropics/skills 的形态，把当前单一大 skill 拆成多个独立 skill，按需触发加载，并使仓库可持续扩展新的开发规范 skill。

## 1. 已确认的关键决策

| 决策点 | 结论 |
|---|---|
| 拆分范围 | 拆分 cross-platform-arch 本身，按工作流职责分成 4 个独立 skill |
| 目录布局 | 仓库根目录平铺 skill 文件夹，目录即 skill |
| 加载方式 | 仓库只做源码管理；用 sync 脚本整组拷贝到 `~/.claude/skills/` |
| 拆分粒度 | 方案 A：按「工作流阶段」拆 4 个（拒绝细拆 6-7 个与粗拆 2 个） |

## 2. 仓库总体结构（拆分后）

```
cross-platform-arch/
├── README.md                 # 重写：skill 总览表 + 同步说明 + 扩展指南
├── CHANGELOG.md              # 根级保留：v1.x 历史 + 2.0.0 拆分记录
├── LICENSE                   # 根级保留（MIT）
├── cross-platform-design/    # skill 1：架构设计与评审
├── monorepo-scaffold/        # skill 2：从零搭建新项目
├── arch-verify/              # skill 3：机器门禁验收
├── legacy-rewrite/           # skill 4：存量项目重写接入
├── docs/
│   └── anthropic-patterns.md # 元知识归档（讲 skill 写作，非业务 skill 内容）
└── tools/
    ├── validate_skill.py     # 原 scripts/validate_skill.py，改为校验根目录下所有 skill
    └── sync.sh               # 新增：rsync 各 skill → ~/.claude/skills/
```

拆分完成后删除顶层 `SKILL.md`、`references/`、`scripts/`、`evals/`（内容全部分配到 4 个 skill，无丢弃；`anthropic-patterns.md` 移入 `docs/`）。

## 3. 四个 skill 的边界与文件归属

| Skill | SKILL.md 收编内容 | references/ | scripts/ | evals/ | metadata.version 起点 |
|---|---|---|---|---|---|
| `cross-platform-design` | 核心原则（5 条）、阶段1 需求定位、关键决策速查表 | architecture.md、hexagonal-arch.md、clients.md、tech-stack.md、reuse.md | — | eval 2 | 1.0.0 |
| `monorepo-scaffold` | 阶段2 脚手架生成、阶段3 演示链路、阶段3.5 设计系统生成 | scaffold.md、playbook.md、design/（整个设计能力包含 README） | scaffold.py、install_impeccable.sh | eval 1、5 | 1.0.0 |
| `arch-verify` | verify 用法 + 七项检查项说明（①结构完整性 … ⑦核心测试） | output-spec.md | verify_project.py | eval 4、7 | 1.0.0 |
| `legacy-rewrite` | 阶段2.5 定性反转（旧项目=协议字典+验收 oracle）+ 五步流程 | migration.md | — | eval 3、6 | 1.0.0 |

每个 skill 的 SKILL.md 均含 MIT license 与 `metadata.version/date/author`（author 沿用 WorkBuddy Agent）。原 evals.json 中的 `skill_name` 字段改为对应 skill 名。

## 4. 触发词设计（互斥）

沿用 ai-dev-spec 的 TRIGGER / DO NOT TRIGGER 双向声明风格，description 末尾互指邻居：

- **cross-platform-design**：TRIGGER 设计/评审多端架构、技术选型问答（如"桌面用 Electron 还是 pywebview"）；DO NOT TRIGGER 搭新项目（→ monorepo-scaffold）、验收项目（→ arch-verify）、旧项目接入（→ legacy-rewrite）
- **monorepo-scaffold**：TRIGGER 搭新项目/生成 Monorepo 骨架/页面丑要升级设计；DO NOT TRIGGER 纯架构问答（→ cross-platform-design）、旧项目接入（→ legacy-rewrite）
- **arch-verify**：TRIGGER 验收/检查项目是否符合架构、"页面样式不完整"类诊断；DO NOT TRIGGER 修改规范本身、生成项目（→ monorepo-scaffold）
- **legacy-rewrite**：TRIGGER 旧项目重写/功能迁移到一核多端；DO NOT TRIGGER 从零新项目（→ monorepo-scaffold）

## 5. 跨 skill 引用约定（拆分最大风险点）

1. **整组拷贝**：4 个 skill 必须同步到同一父目录平级共存（`~/.claude/skills/` 下）。SKILL.md 中跨 skill 引用一律写相对路径 `../<skill名>/…`。README 显式声明"必须整组使用"。
2. **单一事实来源**：scaffold 产出清单与 verify 检查项的对齐，事实来源定为 `arch-verify/references/output-spec.md` 的文件清单。monorepo-scaffold 的 scaffold.md 只概述并指向该清单；两边 SKILL.md 各加同步警示行："改产出清单必须同步 output-spec.md"。
3. 阶段顺序语义（scaffold 后必须 verify）在两个 skill 的 SKILL.md 中各保留一行互相指引（"生成后必须立即运行 ../arch-verify 的 verify_project.py"）。

## 6. 仓库级文件与版本策略

- **README.md**：重写为仓库总览——4 个 skill 的简介表（名称/职责/触发场景）+ 整组拷贝说明 + 三步扩展流程。
- **CHANGELOG.md**：根级不拆，继续记录整个仓库。新增 `2.0.0` 章节（breaking）记录"单 skill 拆分为 4 个独立 skill"。各 skill 从 `1.0.0` 独立起步演进。
- **sync.sh**：自动发现根目录下所有含 SKILL.md 的顶层目录（排除 docs/tools），rsync 到 `~/.claude/skills/`。未来新增规范 skill 零脚本改动。
- **validate_skill.py**：迁入 tools/，遍历校验根目录所有 skill 的 frontmatter 格式（name/license/metadata）。

## 7. 扩展约定

新增规范 skill 三步流程（写进 README）：
1. 新建顶层目录 + SKILL.md（含互斥触发词，TRIGGER/DO NOT TRIGGER）
2. README 总览表加一行
3. `python tools/validate_skill.py` 通过即可被 sync.sh 发现

不设中央注册文件，目录即 skill。

## 8. 错误处理与验证

- 拆分是文件移动 + 新写 4 份 SKILL.md + 改 3 个工具脚本，无运行时行为变更；验证方式：
  1. `python tools/validate_skill.py` 全部 PASS；
  2. `tools/sync.sh` 同步后 `~/.claude/skills/` 下 4 个目录齐全、相对引用路径可达；
  3. 每个新 skill 的 evals 抽查 1 条人工走查（prompt → 该 skill 被触发且引用文件存在）；
  4. `monorepo-scaffold/scripts/scaffold.py` 与 `arch-verify/scripts/verify_project.py` 功能不变（移动位置后可正常独立运行，内部不得依赖原顶层路径）。

## 9. 明确不做（YAGNI）

- 不引入 plugin marketplace / plugin.json 机制（用户选择手动同步）。
- 不保留原 `cross-platform-arch` 名下的导航/索引 skill（避免触发词重叠）。
- 不把 references 再细拆（hexagonal-arch、clients 留在 design skill 内）。
- CHANGELOG 不按 skill 拆分。
