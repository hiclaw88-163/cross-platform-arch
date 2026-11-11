---
name: database-design
description: 数据库/表设计/SQL 纪律与 SQLite↔PostgreSQL 双方言桥。TRIGGER when 建表、加字段、写 SQL、设计表结构、配置 Alembic、选择数据库、把 SQLite 演进到 PostgreSQL、审查 DDL；DO NOT TRIGGER when 生成工程脚手架（用 monorepo-scaffold）、多端架构整体设计与技术选型问答（用 cross-platform-design）、验收项目（用 arch-verify）、搭建项目文档体系（用 project-docs）、存量项目重写（用 legacy-rewrite）。
license: MIT
metadata:
  version: "1.0.0"
  author: WorkBuddy Agent
---

# 数据库设计（database-design）

一句话：**表结构是长期资产——命名/字段顺序/审计字段全库统一；schema 只有一处定义（SQLAlchemy metadata）；SQLite 是起点不是终点，从第一天就按"能无痛迁 PostgreSQL"的纪律写。**

## 核心原则（❌ 禁止违反）

1. 金额禁 `float`/`double`，用 `Numeric(18,2)`（或业务约定精度）
2. 禁止无 `WHERE` 的 `UPDATE`/`DELETE`；禁止 `SELECT *` 上生产列表
3. 每表必须有主键；主键由应用侧生成，禁止依赖数据库自增语义（为换库留路）
4. 禁止用方言保留字作表名/字段名/索引名——引号转义规避**同样不合规**，必须改名
5. 歧义字段必须加业务前缀（`status` → `order_status`）；排序列统一 `sort_order`，分页参数统一 `pageNo/pageSize`
6. schema 单一事实来源：**只允许在 server 侧 SQLAlchemy metadata 定义一次**；任何其他位置的 DDL 都是镜像或迁移脚本，不得分叉
7. 结构变更走迁移工具（Alembic）且只追加；禁止手改库结构后不补脚本

## 双方言策略总览

| 决策点 | 规则 |
|---|---|
| 适用边界 | SQLite=演示/桌面离线/单机；出现多用户并发写、行级权限、备份恢复要求 → 升级 PostgreSQL |
| schema 定义 | server 侧 SQLAlchemy 2.0 `Base.metadata` 唯一定义；双方言共用同一份模型 |
| 类型选择 | 只用 SQLAlchemy 通用类型（见 `references/dialect-bridge.md` 类型映射表），双方言可解释 |
| 方言私有特性 | SQLite PRAGMA/JSON1、PG JSONB 操作符等——只允许封装在适配器内，core/业务代码禁止 |
| 结构变更 | Alembic revision 只追加；SQLite 有限 ALTER 用 `batch_alter_table` |
| dev 自举 | `create_all` 仅限开发环境首次建库；正式变更一律走 Alembic |

细节：表设计纪律见 `references/table-design.md`；双方言桥见 `references/dialect-bridge.md`。

## 参考文件

- `references/table-design.md` — 命名/字段顺序/审计字段/枚举注释/SQL 纪律/例外条款/检查清单
- `references/dialect-bridge.md` — schema 单一来源、类型映射表、方言禁用清单、Alembic 纪律、升级信号

## 配套 skill（语义配合，无文件依赖）

- **monorepo-scaffold** — 生成的项目已含 Alembic 骨架与 CLI 自举镜像（本 skill 规范其纪律）
- **arch-verify** — schema 单一来源检查（DDL 白名单位置）是其机器门禁之一
- **cross-platform-design** — 数据库选型（SQLite→PostgreSQL）的架构决策来源
