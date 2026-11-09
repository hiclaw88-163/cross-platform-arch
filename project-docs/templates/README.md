# {project} 文档导航

> 按"规范 / 设计 / 决策 / 指南 / 计划"五类组织。子目录按项目自身架构分层增建。

| 目录 | 入口 | 用途 |
|------|------|------|
| **conventions/** | [`conventions/规范索引.md`](./conventions/规范索引.md) | 强制开发规范（编号命名，`00-项目配置.md` 为唯一变量入口） |
| **specs/** | `specs/README.md` | 设计规格（架构规划、领域边界、服务详设、横切设计） |
| **adr/** | `adr/` | 架构决策记录（`ADR-编号-结论式标题.md`，一文件一决策） |
| **guides/** | `guides/` | 操作指南（上手、CI/CD、测试策略、标准生成提示词） |
| **plans/** | `plans/` | 交付计划（排期、里程碑、Go/No-Go） |
| **scripts/** | `scripts/` | 文档配套协作脚本（批量拉仓、链接校验） |

## 开发前必读

1. [`conventions/00-项目配置.md`](./conventions/00-项目配置.md) — 唯一变量入口
2. [`conventions/规范索引.md`](./conventions/规范索引.md) — 按任务路由到具体规范
3. [`AGENTS.md`](./AGENTS.md) — AI 进场路由

## 架构治理

| 文档 | 用途 |
|------|------|
| [`TODO.md`](./TODO.md) | 执行待办（管"要做"，与缺口清单互补） |
| `specs/` 下缺口/评审文档 | 架构缺口跟踪（P0/P1/P2）与评审结论 |
| `adr/` | 已定决策及其理由（含被推翻记录：Superseded） |
