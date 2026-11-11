# cross-platform-arch

Agent Skills 集合仓库：面向「一核多端」应用架构与工程规范的可复用 skill 库。

- **形态**：对齐 [anthropics/skills](https://github.com/anthropics/skills) —— 根目录平铺、目录即 skill，每个 skill 含 `SKILL.md`（YAML frontmatter + 正文）及可选的 `references/`、`scripts/`、`templates/`、`evals/`
- **独立性**：各 skill 互不依赖，单独安装任意一个均可工作；skill 之间只有语义层面的配合关系，禁止文件级引用
- **扩展性**：新增规范 skill 无需注册——建目录、过校验即被同步脚本发现

## 可用 Skill

| Skill | 职责 | 典型触发场景 |
|---|---|---|
| [cross-platform-design](cross-platform-design/) | 「一核多端」架构设计与评审规约 | 设计/评审多端架构、技术选型问答（Electron 还是 pywebview）、评估新业务复用 |
| [monorepo-scaffold](monorepo-scaffold/) | 从零搭建 Monorepo 项目：脚手架 + SDK 打通 + 演示链路 + 设计系统 | 新建一核多端项目、生成骨架、页面丑要升级设计 |
| [arch-verify](arch-verify/) | 机器门禁验收：verify_project.py 七项检查 + 产出规范 | 验收项目是否符合架构、诊断"样式不完整/token 未定义" |
| [legacy-rewrite](legacy-rewrite/) | 存量项目重写接入：旧项目=协议字典+验收 oracle | 把旧系统功能用一核多端架构重新实现 |
| [project-docs](project-docs/) | 项目文档体系标准 + docs 骨架脚手架 | 新建项目文档体系、整改散乱文档、写 AGENTS.md/规范索引/ADR |
| [database-design](database-design/) | 表设计纪律 + SQLite↔PostgreSQL 双方言桥 | 建表/加字段/写 SQL、配置 Alembic、SQLite 演进到 PostgreSQL |

## 安装

**要求**：Python 3.9+（校验/脚手架/同步脚本仅用标准库）。同步二选一：Unix 用 `sync.sh`（需 rsync）；Windows/无 rsync 环境用 `sync.py`（纯标准库）。

```bash
# 同步所有 skill 到本地 skills 目录（默认 ~/.claude/skills/）
tools/sync.sh              # Unix（rsync）
python tools/sync.py       # Windows / 无 rsync 环境的等价实现

# 或指定目标目录
tools/sync.sh /path/to/skills
python tools/sync.py /path/to/skills
```

同步脚本自动发现根目录下所有含 `SKILL.md` 的顶层目录，无需配置清单。

## Skill 格式约定

每个 skill 的 `SKILL.md` 必须包含：

```yaml
---
name: kebab-case-name          # 与目录名一致
description: <何时使用>。TRIGGER when <触发场景>；DO NOT TRIGGER when <排除场景>
license: MIT
metadata:
  version: "x.y.z"
---
```

- 触发词双向声明（TRIGGER / DO NOT TRIGGER）并与同仓库其他 skill 互斥，`description` 末尾互指邻居
- 无 `date` 元数据、无时间性表述；任何项目特定值（项目名/包名/路径）一律 `{占位符}`，不写死

## 格式约定（本仓库）

- **提交信息（强制）**：`<type>:[<需求单号>]: <中文主题>`——单行、动词开头、≤100 字、不加句号；type 取 feat/fix/refactor/docs/chore/build/test；无关联需求的单号占位 `[0]`，可叠加 scope（`fix(bridge):[OMS--777]: 修复推送丢失`）；一次提交一个意图。`.githooks/commit-msg` 会强制校验（本仓库已启用：`git config core.hooksPath .githooks`），merge/revert 系统提交放行
- 完整课纲（面向生成项目）见 monorepo-scaffold README 模板与 project-docs `08-提交信息规范` 模板

## 校验

```bash
python3 tools/validate_skill.py    # 批量校验全部 skill
python3 tools/validate_skill.py <skill目录>   # 单个校验
```

检查项：frontmatter 合规（Agent Skills 规范）→ 引用闭合（正文中引用的本地文件必须存在）→ 独立性（禁止 `../` 跨 skill 文件引用）→ `evals/evals.json` 结构（存在时）。

## 仓库结构

```
├── cross-platform-design/   # 架构设计与评审
├── monorepo-scaffold/       # 项目脚手架（scaffold.py）
├── arch-verify/             # 机器门禁（verify_project.py）
├── legacy-rewrite/          # 存量重写接入
├── project-docs/            # 文档体系标准（init_docs.py）
├── tools/                   # validate_skill.py / sync.sh / sync.py
├── .githooks/               # 本仓库提交信息强制校验钩子（core.hooksPath 指向此处）
├── docs/                    # 设计文档、实施计划、skill 写作元知识
└── CHANGELOG.md             # 根级版本演进记录
```

## 扩展新 skill

1. 新建顶层目录 + `SKILL.md`（按上方格式约定，触发词互斥）
2. 本 README「可用 Skill」表加一行
3. `python3 tools/validate_skill.py` 通过即完成——`tools/sync.sh` 自动发现

从存量项目 docs 提炼可复用 skill 的五步流程（盘点候选 → 去项目化 → 去重归并 → 补触发词与验证方式 → 落库）见 [docs/superpowers/specs/2026-11-10-skills-split-design.md](docs/superpowers/specs/2026-11-10-skills-split-design.md) §7.1。

## License

[MIT](LICENSE)
