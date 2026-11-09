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

## 文档清单

| 文件 | 内容 |
|---|---|
| （新增设计文档后在此登记） | |
