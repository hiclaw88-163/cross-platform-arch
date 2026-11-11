---
name: project-docs
description: 项目文档体系（docs 仓库）标准结构与脚手架。TRIGGER when 为新项目搭建文档体系/docs 仓库、整改散乱的项目文档、写 AGENTS.md/规范索引/ADR/00-项目配置、决定某份文档该放哪、文档之间冲突不知道以谁为准；DO NOT TRIGGER when 生成代码工程脚手架（用 monorepo-scaffold）、编写单篇业务文档的正文内容、多端架构设计问答（用 cross-platform-design）。
license: MIT
metadata:
  version: "1.2.2"
---

# 项目文档体系（project-docs）

一句话：**项目 docs 是一个有标准结构的仓库，不是一堆散文件——conventions 管强制规范、specs 管设计、adr 管决策、AGENTS.md 管 AI 进场路由；所有项目特定值收敛到唯一变量入口，禁止散落写死。**

## 目录标准总览

| 目录/文件 | 职责 | 放什么 | 不放什么 |
|---|---|---|---|
| `conventions/` | 强制开发规范，编号命名 | 各领域"必须遵守"的规范，`00-项目配置.md` 为唯一变量入口 | 操作指南（→ guides/）、设计（→ specs/） |
| `specs/` | 设计规格，按架构层级分子目录 | 架构规划、领域边界、服务详设、横切设计 | 强制性编码规范（→ conventions/） |
| `adr/` | 架构决策记录，`ADR-编号-标题.md` | 一次一个决策：背景/决策/后果 | 决策的实施细节（→ specs/） |
| `guides/` | 操作指南 | 上手指南、CI/CD、测试策略、标准生成提示词 | 强制规范（→ conventions/） |
| `plans/` | 交付计划 | 排期、里程碑、Go/No-Go | 长期规范 |
| `scripts/` | 文档配套协作脚本 | 批量拉仓/校验链接等 | 业务代码 |
| `AGENTS.md` | AI 进场路由 | 编号任务 → 必读文件映射 | 具体规范内容（只指路） |
| `README.md` | 文档导航 | 目录表 + 开发前必读 | 规范正文 |
| `TODO.md` | 执行待办 | 未完成事项跟踪 | 缺口状态（缺口清单管"缺不缺"，TODO 管"要做"，互补） |

各目录的详细放置规则见 `references/structure.md`。

## 脚手架生成

```bash
python scripts/init_docs.py --name my-app --dir /path/to/my-app-docs
```

生成骨架：`AGENTS.md`、`README.md`、`TODO.md`、`conventions/00-项目配置.md`、`conventions/规范索引.md`、`conventions/08-提交信息规范.md`、`adr/`（含模板）、`guides/`、`specs/`、`plans/`、`scripts/`。`{project}`/`{projectName}` 占位符自动替换；其余占位符（如 `{date}`、`{basePackage}`）保留原样，由人按项目事实填。`--force` 覆盖已存在文件。

## 写法纪律（详见 references/templates.md）

1. **变量唯一入口**：项目特定值（项目名/包名/磁盘路径/机器名/时间节点）只出现在 `00-项目配置.md`，其余文件一律 `{占位符}`。禁止在任何规范里写死路径。
2. **规范 frontmatter**：`name` / `description`（含 TRIGGER）/ `version` / `level`（must/should），内容变更必须升 version。
3. **冲突优先级声明**：每份规范开头写明"本文 > 上级摘要 > 通用默认"。
4. **规范索引三段式**：关系声明 → 使用前必读 → 快速路由表。
5. **AGENTS.md 编号路由**：按任务类型编号（"起模块→读 01"、"写后端代码→读 02"），AI 进场第一步读它。

## 治理规则（详见 references/governance.md）

- 单一事实来源；文档描述与实现不一致 → 先改文档再动代码
- 反引号路径引用需可校验（跑存在性检查，失效即修）
- TODO 双轨：`TODO.md` 管"要做"、缺口清单管"缺不缺"

## 参考文件

- `references/structure.md` — 目录标准：每类目录放什么/不放什么
- `references/templates.md` — 各类文件写法纪律（AGENTS.md/规范索引/ADR/项目配置/规范正文）
- `references/governance.md` — 治理规则：唯一事实来源、冲突优先级、升版、链接有效性
- `templates/` — 可直接拷贝的文件模板（全部占位符化）
- `scripts/init_docs.py` — 一键生成项目 docs 骨架

## 配套 skill（语义配合，无文件依赖）

- **monorepo-scaffold** — 生成代码工程骨架（本 skill 管文档仓库，二者可同项目配套使用）
- **cross-platform-design** — 多端架构设计问答
