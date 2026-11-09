# leisure-dev-skills（cross-platform-arch 仓库）

开发规范 **skill 集合仓库**（anthropics/skills 形态）：根目录平铺、目录即 skill、按需触发加载，可持续扩展新的开发规范 skill。

> 本仓库前身是单 skill `cross-platform-arch`（v1.8.0），2026-11-10 拆分为 4 个独立 skill（见 CHANGELOG 2.0.0）。

## Skill 总览

| Skill | 职责 | 典型触发场景 |
|---|---|---|
| [cross-platform-design](cross-platform-design/) | 「一核多端」架构设计与评审规约 | 设计/评审多端架构、技术选型问答（Electron 还是 pywebview）、评估新业务复用 |
| [monorepo-scaffold](monorepo-scaffold/) | 从零搭建 Monorepo 项目：脚手架 + SDK 打通 + 演示链路 + 设计系统 | 新建一核多端项目、生成骨架、页面丑要升级设计 |
| [arch-verify](arch-verify/) | 机器门禁验收：verify_project.py 七项检查 + 产出规范 | 验收项目是否符合架构、诊断"样式不完整/token 未定义" |
| [legacy-rewrite](legacy-rewrite/) | 存量项目重写接入：旧项目=协议字典+验收 oracle | 把旧系统功能用一核多端架构重新实现 |

## 安装（整组拷贝）

```bash
tools/sync.sh            # 默认同步到 ~/.claude/skills/
tools/sync.sh /other/dir # 或指定目标目录
```

**必须整组使用**：SKILL.md 之间用 `../<skill名>/` 相对引用，拆开安装会断链。

## 扩展一：新增规范 skill（三步）

1. 新建顶层目录 + `SKILL.md`（frontmatter 含 `name`/`description`，触发词用 TRIGGER / DO NOT TRIGGER 双向声明并与现有 skill 互斥，description 末尾互指邻居）
2. 本 README 总览表加一行
3. `python3 tools/validate_skill.py` 通过后即被 `tools/sync.sh` 自动发现——不设中央注册文件，目录即 skill

## 扩展二：从项目规范提炼 skill（五步）

存量项目（如 `keshumai-docs`）的 conventions/adr/guides 已沉淀大量规范，但耦合项目语境无法跨项目复用。提炼流程：

1. **盘点候选**：扫描项目 docs 中带 frontmatter 或编号体系的规范，按"约束的是技术还是业务"初分——只有技术性约束可泛化，业务性约束（如租户映射、域归属 ADR）留在项目内。
2. **去项目化**：把 `{project}`、`{basePackage}`、域名、公司前缀等抽为占位符（参照 keshumai `00-项目配置.md` 的变量模式），项目特有决策降级为"示例"。
3. **去重归并**：与 ai-dev-spec 现有子 skill（writing-java-code、designing-database、ensuring-quality 等）对照，重叠部分走"合并/升版"而不是新建 skill；确属空白才新建目录。
4. **补充触发词与验证方式**：每条规则标注 TRIGGER/DO NOT TRIGGER 与验证方式（机器检查/人工审查），能写成 verify 脚本的规则优先机器化。
5. **落库**：按"扩展一"三步流程入库，原项目 docs 保留不动（项目内文件仍是项目语境的单一事实来源）。

首批候选：keshumai `02-后端工程结构与类命名规范`、`02a-api契约与ReqResp`、`04-数据库规范`。

## 仓库级文件

| 路径 | 内容 |
|---|---|
| `CHANGELOG.md` | 根级记录整个仓库的版本演进（v1.x 单 skill 时代 + 2.0.0 起拆分后） |
| `docs/anthropic-patterns.md` | 元知识：anthropics/skills 官方模式拆解（讲 skill 写作，非业务） |
| `tools/validate_skill.py` | 批量校验所有 skill：frontmatter 合规 + 引用闭合 + evals 结构 |
| `tools/sync.sh` | 自动发现所有 skill 目录，整组同步到本地 skills 目录 |
| `docs/plans/`、`docs/superpowers/` | 实施计划与设计文档 |

## 技术栈默认组合（一核多端）

uv + FastAPI + SQLAlchemy 2.0 + Typer + Vue3/Vite + uni-app（小程序+App）+ pywebview（桌面，可切 Electron）+ SQLite→PostgreSQL
