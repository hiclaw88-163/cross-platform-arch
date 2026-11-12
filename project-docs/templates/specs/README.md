# specs · 设计规格入口（{project}）

> 命名规范见 [`../conventions/规范索引.md`](../conventions/规范索引.md)：
> `L{层级}-{NN}{分册字母}-{主题}.md`，**层级字母在 NN 前**。
> 概述/实现配对共享数字加 `i`，兄弟子文档 `j/k/l`；跨层引用带 `L{层级}-{NN}` 前缀。

## 层级字母 ↔ 子目录映射

> 下表为 TOGAF 对齐的**默认映射**；子目录按项目自身架构分层增删后同步本表。
> 若项目已有占用 `L{N}` 的语义（如产品能力分层），**必须换前缀字母**并在本表注明理由。

| 前缀 | 子目录 | 含义 | TOGAF 对应 |
|---|---|---|---|
| `L0` | （根） | 项目管理 | — |
| `L1` | `architecture/` | 架构愿景与总体架构 | Architecture Vision |
| `L2` | `application/` | 应用架构（UI/信息架构） | Application Architecture |
| `L3` | `cross-cutting/` | 技术架构与横切 | Technology Architecture |
| `L4` | `services/` | 服务详细设计 | Detailed Design |
| `L5` | （→ `conventions/`） | 实现规范 | Implementation Standards |
| `L6` | `ops/` | 部署运维 | Deployment & Operations |

## 标准起步骨架（一核多端项目推荐）

> 提炼自 Kabao 实战文档结构（2026-11-12 反哺）。新项目先立这五份，再按业务增删；
> `{A}` = 项目选定的层级前缀字母（默认 `L`，Kabao 用 `A`）。

| 起步文档 | 落点 | 一句话职责 |
|---|---|---|
| `{A}1-01-产品定位与能力全景` | `architecture/` | JTBD、能力域分级、里程碑与验收口径 |
| `{A}1-02-一核多端落地` | `architecture/` | 分层与依赖方向、目录规划、门禁与工程纪律（对照 cross-platform-design） |
| `{A}2-01-领域模型与动作模型` | `domain/`* | 聚合根、结果词汇单源、端口契约（一核多端项目建议增设 `domain/` 子目录并同步上方映射表） |
| `{A}3-01-信息架构与核心页面` | `application/` | IA、页面规格、概念翻译表（工程词不外溢 UI） |
| `{A}4-01-横切底座设计` | `cross-cutting/` | 凭据/事件/审计/数据层约定（含 schema 演进纪律） |

## 文档清单

| 文件 | 内容 |
|---|---|
| （新增设计文档后在此登记） | |
