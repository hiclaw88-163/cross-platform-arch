# 六边形架构规约（Hexagonal / Ports & Adapters）

> 本文是**规范性**文档：规则带编号（R1…），标注验证方式与豁免流程。
> 概念来源：Cockburn 六边形架构；分层与命名对照阿里巴巴 COLA 架构与
> 《阿里巴巴 Java 开发手册》（黄山版）应用分层与依赖规约。
> 配套门禁：`scripts/verify_project.py`（结构/纯净/依赖方向/六边形桥）。

## 1. 分层拓扑与 COLA 对照

```
       入站适配器（Cockburn 左侧 / COLA adapter 层）
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐
│ CLI 端  │ │ Web 端  │ │ 桌面端  │ │ 小程序 / App │     ← apps/*
└────┬────┘ └────┬────┘ └────┬────┘ └──────┬───────┘
     │           │ HTTPS/契约 │             │
     ▼           ▼            ▼             ▼
┌─────────────────────────────────────────────────┐
│  应用核心（COLA app + domain 层）                 │     ← packages/core
│  application/（用例编排） domain/（实体+领域词汇）│
└────────────┬────────────────────▲───────────────┘
             │ 端口（Port，核心向外的承诺）
             ▼ 实现                │ 结果以领域词汇回填
┌─────────────────────────────────────────────────┐
│  出站适配器（COLA infrastructure 层）             │     ← packages/engine
│  按能力命名：signin/ ledger/ scheduling/ adapters/│
└─────────────────────────────────────────────────┘
```

| 阿里 COLA | 本架构 | 职责 |
|---|---|---|
| `adapter` 层 | `apps/*` 各端 | 协议转换、UI 渲染、端能力桥接，**零业务** |
| `app` + `domain` 层 | `packages/core` | 用例编排、业务规则、领域词汇单源 |
| `infrastructure` 层 | `packages/engine` | 出站适配器：存储、凭据、外部 API、调度 |
| `client` 层（JAR/SDK） | `packages/sdk` | 契约类型单源，各端消费，字段漂移编译期暴露 |
| `start` 启动装配 | `apps/server` 组合根 / bridge 工厂 | 依赖注入，把适配器接到端口 |

## 2. 规约清单（R = Rule）

### R1 核心纯净（铁律）
`packages/core` 源码只允许 import 标准库；出现任何框架（fastapi/sqlalchemy/
requests/pydantic…）即违规。
**验证**：`verify_project.py` `check_core_purity`（AST 扫描）。
**依据**：《Java 开发手册》6.2 依赖规约"禁止逆向依赖"；COLA domain 层零依赖。

### R2 依赖方向唯一
只允许 `端 → core`、`engine → core`（实现端口、回填词汇）；core 不依赖任何端
或 engine。
**验证**：`check_dep_direction`。

### R3 端口归位
端口（Port）协议定义在 core 的 `application/`（ABC）；纯引擎内部设施（如
本地台账实现细节）可下沉为 `engine/ports/`，但**对外承诺必须收敛在 core**。
引擎包名禁止使用旧业务目录名——必须用**能力词汇**（signin / ledger /
scheduling / adapters / declarative / extensions）。
**验证**：人工评审 + design-decisions 记录；重命名残留由 R1-R2 兜底。

### R4 唯一六边形桥（bridge）
端**只允许** `from <engine>.bridge import ...` 触达引擎；直接 import 引擎
内部模块（signin/ledger/extensions…）即违规。bridge 负责：装配适配器 →
构造用例 → 把引擎原始输出翻译为领域词汇（`classify_outcome`）。
**验证**：`check_hexagonal`（AST 扫描端目录）。

### R5 领域词汇单源
结果/状态词汇（如 CLAIMED/NO_AUTH）只在 `core/domain` 定义与分类；引擎返回
原始字符串，经 bridge 归一为 `outcome_kind`（pass/fail/skip/info）；端只
消费 kind，**禁止在端内重写分类逻辑**（展示文案 LABELS 除外，且全集必须与
core 一一对应）。
**依据**：单源真理 + 防多端各说各话（真实事故：旧项目 TUI 与 Web 分类漂移）。

### R6 用例层是编排唯一入口
跨目标编排（批量、聚合、幂等判定）只写在 core `application/usecases.py`；
端与 engine 都不得私编流程。《手册》7.1 对应：Service 层才是事务与编排边界。

### R7 模型分层（对照手册 §分层领域模型）
| 手册词汇 | 本架构落点 |
|---|---|
| DO（数据对象） | engine/ledger 行对象、引擎原始返回 |
| DTO / AO | core 用例入参与返回（dataclass） |
| VO / 出参 | server `response_model`（Out 后缀）、web 契约类型 |
禁止把 DO 直接透传到端——出站形状必须显式声明 `response_model`（R-契约）。

### R8 测试策略
core 用例纯 pytest（毫秒级、零 mock IO）；engine 适配器用 sqlite 内存库；
契约变更必须重生成 SDK 并让 web 编译通过（类型即集成测试）。
**验证**：`verify_project.py --test` + `gen:sdk` 后 `build:web`。

### R9 豁免流程
任何一条规则需破例：先在 `docs/design-decisions.md` 记录动机与影响面，
再实施；无记录的例外视为违规。规则变更须回写本文并升 verify 门禁。

## 3. 快速自检

```bash
python scripts/verify_project.py --project . --test   # 七项门禁（--test 含测试）
uv run <server-cli> list                              # 冒烟：用例装配成功（按项目实际 CLI 名替换）
pnpm gen:sdk && pnpm build:web                        # 契约新鲜度
```
