# 表设计纪律（含检查清单）

> 提炼自实际项目数据库规范（多租户微服务语境），已去 MySQL 化为通用纪律。

## 命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 表 | snake_case，带业务域前缀 | `ord_order`、`sys_account`、`task_item` |
| 字段 | snake_case | `tenant_id`、`order_status` |
| 索引 | `idx_{表缩写}_{字段}` / `uk_{表缩写}_{字段}` | `idx_ord_tenant_store` |
| 排序列 | 统一 `sort_order`（`int NOT NULL DEFAULT 0`），禁止裸 `sort` | |

业务域前缀由项目自定（如 `sys_` 平台、`ord_` 订单、`wms_` 仓储），写入项目文档体系（project-docs）的 `00-项目配置.md` 或对应命名规范。

## 字段顺序（强制）

| 序 | 字段 | 说明 |
|----|------|------|
| 1 | `id` | 主键，应用侧生成 |
| 2 | `tenant_id` | **仅多租户项目**；单机/离线项目无此字段 |
| 3 | 业务字段 | 含 `{biz}_no` 业务单号、`sort_order` 排序等 |
| 4 | `{biz}_status` / `{biz}_enabled` / `{biz}_type` | 状态类，歧义字段必须加业务前缀 |
| 5 | `version` | 乐观锁，`NOT NULL DEFAULT 1`，全库统一 |
| 6 | `is_deleted` | 逻辑删除，全库统一 |
| 7 | 创建审计组 | `create_user_id` / `create_user_name` / `create_time` / `db_create_time` 整体在前 |
| 8 | 更新审计组 | `update_user_id` / `update_user_name` / `update_time` / `db_update_time` 整体在后 |

细则：

1. 业务字段组在状态类字段之前；审计字段按创建组/更新组**成组排列**，禁止交错
2. `version` 位于状态类之后、`is_deleted` 之前；`is_deleted` 位于 `version` 之后、审计组之前
3. 歧义字段必须加业务前缀：`status`→`order_status`、`type`→`order_type`、`name`→`product_name`；例外：`tenant_id`/`is_deleted`/`version`/审计字段全库统一不加前缀
4. 模型/DDL 字段顺序与基类实体声明顺序保持一致

## 注释纪律（强制）

1. **每个字段必须有 `comment=`（中文）**，含主键、基础设施字段、审计字段；禁止纯英文/拼音/无意义符号
2. 主键注释用业务含义（`用户ID`），禁止 `主键`/`ID`/`雪花ID`
3. 状态/类型/启用字段注释用**枚举格式**：`{Biz}状态：1-启用;0-禁用;`——分号 `;` 分隔，每项 `值-名称`，禁止空格/逗号分隔
4. `is_deleted` 注释固定 `是否删除：1-是;0-否;`
5. 表级注释为具体业务名（`XXX表`），禁止 `common`/`base`/`数据表` 类泛化名
6. 落库形态：PostgreSQL 用 `COMMENT ON COLUMN`（Alembic/SQLAlchemy comment 自动生成）；SQLite 无列注释——注释必须保留在模型定义中，迁移脚本文件头可整表汇总

## SQL 纪律

| 主题 | 规则 |
|------|------|
| 金额 | 禁 `float`/`double`，用 `Numeric(18,2)` |
| 更新删除 | 禁止无 `WHERE`；生产列表禁止 `SELECT *` |
| 批量 | 插入 ≤ 500 条/批；更新/删除 ≤ 200 条/批；禁止循环内逐条调用（N+1）——收集 ID → 批量查 → Map 组装 |
| 分页 | `pageSize` ≤ 200；深分页（OFFSET > 10000）改游标分页 |
| 外键 | 禁物理外键，关系由应用层维护 |
| 计数 | 用 `COUNT(*)` |
| 跨库 | 禁跨库 JOIN；跨服务查数走 API/消息 |

## 例外条款（须显式声明，不视为违规）

| 表类型 | 允许的简化 | 说明 |
|--------|-----------|------|
| 日志表（`*_log`、审计表） | 无 `version`/`is_deleted`（只增不改） | 时间字段用业务语义名 |
| 关联表（多对多） | 可无 `tenant_id`/审计字段/`is_deleted` | 必须有主键；关联键建唯一索引；保留例外须在 DDL 注释声明理由 |
| 框架/中间件表 | 允许简化审计结构 | 文件头注释说明 |
| 事务 outbox 表 | — | 使用事务消息时每库一张（`*_tx_outbox` + 消费幂等表），保证"业务变更+出站消息"同事务 |

## 保留字

- 判定以实际部署版本为准，勿凭记忆：
  - PostgreSQL：`SELECT word FROM pg_get_keywords() WHERE catcode = 'R';`
  - SQLite：以官方关键字表为准；列名命中关键字即改名
- 引号转义规避**不合规**，必须改名（先例：`sort` → `sort_order`、`current_date` → `date_key`）

## 检查清单（建表/加字段后逐项过）

- [ ] 表/字段/索引命名符合规则；无方言保留字（引号规避不算）
- [ ] 主键存在且应用侧生成；主键注释为业务含义
- [ ] 字段顺序符合强制表；审计字段成组；`version DEFAULT 1`、`is_deleted` 全库统一
- [ ] 歧义字段有业务前缀；排序列 `sort_order`；分页 `pageNo/pageSize`
- [ ] 每字段有中文 `comment=`；状态类字段为枚举格式
- [ ] 金额 `Numeric`；无 `SELECT *` 列表查询；更新删除带 `WHERE`
- [ ] 结构变更走 Alembic revision（只追加）；多租户项目 `tenant_id` + 联合索引
- [ ] 例外表类型已按例外条款注释声明
