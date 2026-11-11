# 设计文档：database-design skill（数据库规范 + SQLite↔PostgreSQL 双方言桥）

日期：2026-11-11
状态：已确认（方案 A：独立 skill + scaffold/verify 配套对齐）
素材来源：keshumai-docs `conventions/04-数据库规范.md`（262 行，唯一 grounding）+ 本仓库架构既有规约（architecture.md / hexagonal-arch.md / output-spec.md）

## 硬规则（沿用）

零杜撰（表设计纪律只从 04 规范提炼）/ 无时间信息 / 无写死路径与项目名（`{占位符}`）/ 独立 skill 禁止 `../` 文件引用

## 问题（本设计要解决）

1. 数据库规范空白：SQLite→PG 演进只有一行文字
2. schema 两处定义：server `orm.py`（SQLAlchemy metadata + create_all）与 CLI 适配器裸 `CREATE TABLE IF NOT EXISTS`
3. 无迁移工具约定（Alembic 缺位）
4. verify 七项门禁无数据库检查
5. 04 规范未提炼（MySQL/Flyway 导向，核心纪律可通用）

## 去化映射（04 规范 → 通用规范）

| 04 原文（MySQL 语境） | 通用化 |
|---|---|
| `tenant_id` 强制 | 仅多租户项目强制（单机/离线场景无租户） |
| 雪花 bigint 主键 | 应用侧生成主键，禁依赖数据库自增语义（为 PG 迁移留路） |
| Flyway `V{ts}__desc.sql` | Alembic revision 只追加 |
| `SET NAMES utf8mb4` / `ENGINE=InnoDB` | 删（方言私有） |
| 保留字清单查 `information_schema.KEYWORDS` | SQLite/PG 各自的保留字比对说明 |
| COMMENT 落 MySQL 列注释 | 模型 `comment=` 参数必填；PG 落 `COMMENT ON COLUMN`；SQLite 无列注释，落 Alembic revision 文档 |
| `mq_tx_outbox` 每库一张（微服务拆库） | 事务 outbox 表（使用事务消息时），拆库原则保留 |

核心纪律原样保留：snake_case + 业务前缀、`idx_/uk_` 索引命名、字段顺序强制、歧义字段加业务前缀、`sort_order` 统一、审计字段成组、枚举注释格式（分号分隔 值-名称）、金额禁 float、禁 `SELECT *` 上列表、禁无 WHERE UPDATE/DELETE、N+1 禁止、批量上限、深分页游标、例外条款表（日志/关联/框架表）、检查清单。

## skill 结构

```
database-design/
├── SKILL.md              # 触发词 + 核心原则 + 双方言策略总览
├── references/
│   ├── table-design.md   # 表设计纪律（提炼自 04 规范）+ 检查清单
│   └── dialect-bridge.md # SQLite↔PG 桥：schema 单一来源、类型映射、方言禁用、Alembic 纪律、适用边界
└── evals/evals.json      # 2 条：建表任务 / SQLite→PG 演进
```

### dialect-bridge 核心决策（架构既定原则的落地）

- **schema 单一事实来源**：server 侧 SQLAlchemy 2.0 `Base.metadata`；CLI 裸 SQL 适配器只允许 DML，`CREATE TABLE` 仅限"dev 自举镜像"且必须注释声明与 orm.py 对齐，结构变更只能走 Alembic
- **Alembic 纪律**：revision 只追加、禁改已发布脚本、SQLite 有限 ALTER 用 `batch_alter_table`、autogenerate 必须人工审查
- **类型映射表**：布尔 `Integer(1/0)`；金额 `Numeric(18,2)`；时间 `DateTime(timezone=True)`（SQLite 存 TEXT 的比较注意）；JSON 用 SQLAlchemy 通用 `JSON`；UUID `Char(36)`
- **方言私有特性禁用/隔离**：SQLite PRAGMA/JSON1/AUTOINCREMENT/GLOB；PG JSONB 操作符/array/ILIKE——只允许封装在适配器内，core/业务代码禁止方言字面 SQL
- **适用边界**（沿用架构既定）：SQLite=演示/桌面离线/单机；升级 PG 信号=多用户并发写、行级权限、备份恢复要求

## 配套改动

1. **scaffold.py**：server 依赖加 `alembic`；生成 `apps/server/alembic.ini`、`migrations/env.py`（DATABASE_URL 环境变量优先，SQLite 相对路径解析到仓库根 dev.db）、`script.py.mako`、`versions/0001_tasks.py`（与 TaskRow 对齐的静态首版）；CLI 自举建表加对齐注释；server orm.py `create_all` 注释"仅 dev 自举"
2. **arch-verify**：verify_project.py 新增第 9 项 `check_schema_source`（DDL 白名单位置）；check_manifest 加 alembic 必需文件；output-spec.md 产出清单 + C9；arch-verify 版本 1.1.0
3. **monorepo-scaffold** 1.2.0；scaffold.md 补 Alembic 说明
4. README 总览表 + CHANGELOG

## 提交信息规范

按 .githooks/commit-msg：`<type>:[0]: <主题>`
