# SQLite↔PostgreSQL 双方言桥

> 一核多端架构的既定演进路径：SQLite（演示/桌面离线/单机）→ PostgreSQL（生产多用户）。本文规定如何让这条路径"零重写"。

## 1. schema 单一事实来源（❌ 禁止违反）

- **唯一定义点**：server 侧 SQLAlchemy 2.0 `Base`（`orm.py` 的 `DeclarativeBase` 子类）。
- **CLI 裸 SQL 适配器**（stdlib `sqlite3`，零框架）：只允许 DML（`SELECT`/`INSERT`/`UPDATE`/`DELETE`）；如需 dev 自举建表，`CREATE TABLE IF NOT EXISTS` 必须加注释声明"自举镜像，列定义与 server 适配器 orm 模型一致，结构变更走 Alembic"。
- **core 永远无 SQL**：核心纯净性（zero framework）意味着 domain/application 层不出现任何 SQL/ORM 概念，表结构是适配器层的事。
- 结构变更的唯一入口：Alembic revision。禁止手改库结构、禁止在业务代码里跑 DDL。

## 2. 类型映射表（双方言可解释）

| 语义 | SQLAlchemy 类型 | SQLite 行为 | PostgreSQL 行为 |
|------|----------------|------------|----------------|
| 布尔 | `Integer`（1/0）+ 应用层转换 | 无原生 bool，整数存储 | 可用 `Boolean`；统一用 Integer 免转换 |
| 金额 | `Numeric(18,2)` | 存储精确，Python 侧 `Decimal` | `numeric(18,2)`，精确 |
| 时间 | `DateTime(timezone=True)` | 存 TEXT；**比较/排序用 ISO 8601 格式才安全** | `timestamptz` |
| JSON | `JSON`（SQLAlchemy 通用类型） | TEXT 存储 + 应用序列化 | `json`/`jsonb` |
| UUID/雪花 ID | `String(36)` 或 `BigInteger` | 文本/整数 | `char(36)`/`bigint` |
| 主键 | 应用侧生成（uuid4/雪花） | 禁 `AUTOINCREMENT` | 禁依赖 `serial`/identity 语义 |

规则：只允许 SQLAlchemy 通用类型；类型细节差异（时区、精度、排序规则）写入模型 `comment=` 而不是靠方言兜底。

## 3. 方言私有特性（禁用/隔离清单）

| 方言 | 特性 | 处置 |
|------|------|------|
| SQLite | `PRAGMA`（journal_mode/synchronous 等） | 只允许出现在适配器连接初始化函数内，集中一处 |
| SQLite | JSON1 函数（`json_extract`…）、`GLOB`、`ON CONFLICT` 子句差异 | 禁止出现在业务查询；需要时封装为适配器方法 |
| SQLite | `AUTOINCREMENT` | 禁用（主键应用侧生成） |
| PostgreSQL | `JSONB` 操作符（`->>`/`@>`）、数组类型、`ILIKE`、`RETURNING` 扩展 | 禁止散落业务代码；需要时封装为 PG 专用适配器 |
| 通用 | 存储过程、方言函数调用 | 禁用 |

判定口诀：**一条 SQL 换个方言还能跑，才能写在业务代码里；跑不了就得下沉到适配器。**

## 4. Alembic 纪律

1. 路径：`apps/server/alembic.ini` + `apps/server/migrations/`（脚手架已生成骨架，`env.py` 的 `DATABASE_URL` 环境变量优先、SQLite 相对路径解析到仓库根）
2. **revision 只追加**：已提交/已发布的迁移脚本禁止修改；改错了就写新 revision 修正
3. SQLite 的 `ALTER` 能力有限（不能删列/改列类型）：用 `batch_alter_table`（Alembic 原生支持，自动重建表）
4. `alembic revision --autogenerate` 的产物**必须人工审查**后再提交（autogenerate 对 server_default/类型变更常有误判）
5. 回滚 = 写逆向 revision（`downgrade`），不删历史
6. dev 环境可用 `create_all` 首次建库 + `alembic stamp head` 对齐基线；**有数据的库一律走 `alembic upgrade head`**

## 5. 升级信号（SQLite → PostgreSQL 时机）

出现任一信号即规划迁移，继续硬撑属于违规：

- 多用户并发写（SQLite 写锁全库粒度）
- 需要行级权限/租户隔离策略（RLS）
- 备份恢复/时间点恢复要求超出"拷文件"
- 单库体积或连接数逼近 SQLite 实际上限

迁移路径（因 schema 单一来源 + 通用类型，模型层零改动）：PG 建库 → `alembic upgrade head`（换 `DATABASE_URL`）→ 数据搬运脚本（只搬数据不搬结构）→ 适配器连接串切换。**如果这一步需要改模型或改业务 SQL，说明违反了本文第 1/2/3 节，先修规范再迁移。**
