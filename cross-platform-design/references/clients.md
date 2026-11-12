# apps/ 多端规约（一核多端的"多"怎么管）

> 解决的真实问题：多端并存时各自膨胀、端间复制代码、一端改了语义另一端不知。
> 分层依据：Cockburn 六边形"左侧适配器"；端职责边界对照《阿里巴巴 Java 开发手册》
> §应用分层（终端显示层 / 开放接口层）与 COLA `adapter` 层；组件组织参考
> 阿里 Ant Design 前端工程实践。
> 六边形总规约见 `hexagonal-arch.md`，本文只讲"端"这一层。

## 1. 端是什么，不是什么

**端 = 某种交互形态的适配器，只做三件事：**

1. **协议转换**：HTTP/CLI/窗口事件 ↔ core 用例调用
2. **呈现**：渲染、文案、交互状态
3. **端能力桥接**：剪贴板、系统通知、本地进程（桌面壳拉起嵌入式 server）

**端禁止做的事（薄壳纪律）：**

- ✗ 业务判断/编排（属于 core 用例）
- ✗ 结果分类、状态语义推导（属于 core 领域词汇，端只消费 `outcome_kind`）
- ✗ 直接 import 引擎内部（只许经 `<engine>.bridge`，R4）
- ✗ 直接操作台账/存储（属于 engine 出站适配器）

## 2. 端间关系矩阵

| | import 对方代码 | 通信方式 |
|---|---|---|
| cli ↔ server | ✗ 禁止 | 各自独立调 core（进程内）；远端模式走契约 API |
| web/desktop/uniapp ↔ server | ✗ 不 import，只按契约请求 | OpenAPI SDK（BASE URL 可配置） |
| desktop → server | ✓ **唯一豁免**：仅允许 import server 的启动装配入口，用于离线模式内嵌 uvicorn | 进程内拉起 |
| 任何端 ← engine 内部 | ✗ 禁止（R4 bridge 单桥） | — |

**验证**：`check_hexagonal`——扫描各端 `*.py` 的 import；白名单
`{"desktop": {"server"}}`。

## 3. 共享代码下沉规则（防"复制粘贴式多端"）

三处同构必须下沉（真实教训：旧项目 CLI 与 Web 各写一份调度预览格式化）：

| 重复的是什么 | 下沉到 |
|---|---|
| 业务规则、编排、分类 | `packages/core`（语义） |
| 请求/响应类型、错误码映射 | `packages/sdk`（契约） |
| 可复用引擎能力 | `packages/engine` 对应能力包，经 bridge 暴露 |
| 纯展示（文案、标签） | 允许各端保留一份，但**全集与 core 词汇一一对应** |

反模式：`apps/cli/utils.py` ↔ `apps/server/helpers.py` 出现同名同构函数。

## 4. 各端目录模板与纪律

```
apps/<end>/
├── pyproject.toml / package.json     # 依赖 packages/core（workspace）与 @x/sdk
└── src/
    ├── <pkg>/routes|commands/        # 入口层：解析请求 → 调用用例 → 映射状态码/输出
    ├── adapters/                     # 端专属适配器（如 desktop 嵌入式 server 启动器）
    └── main.py|app.ts                # 组合根：只装配，不写流程
```

| 端 | 额外纪律 |
|---|---|
| server | 每个查询端点必须 `response_model`（R7）；鉴权/限流/CORS 只在此层；**拆分阈值**：Out 模型 >10 个或端点按域 >2 组 → 拆 `schemas.py` + `routers/{域}.py`——阈值触发才拆，不提前（COLA"精简版起步"演进观） |
| cli | 命令 = 用例的 1:1 映射，禁止命令内私编循环编排；退出码语义来自 core 状态 |
| web | api 层类型**只来自 SDK 生成物**，不手写接口形状。派生范式（字段名/可空性全部继承契约，只做 UI 侧语义窄化）：`type WithSignal<T> = Omit<T, "signal"> & { signal: Signal }`；**嵌套字段同样要窄化**（真实事故：顶层窄化后 `credentials` 里的 signal 仍是宽 string，vue-tsc 才是唯一能抓住它的机器——手写类型永远发现不了）。vue-tsc 已收编 verify 第 9 项，字段漂移门禁当场 FAIL。CSS 变量必须在 tokens.css 定义 |
| desktop | 主进程零业务；离线 = 内嵌 server 组合根，在线 = 契约 + BASE URL |
| uniapp | 占位期也要走契约 SDK，禁止手写重复类型 |

## 5. 多端一致性验收（新端/新用例上线门禁）

1. `verify_project.py --project . --test` 全 PASS（结构/纯净/方向/六边形桥/Token/
   契约/schema 单源/测试 + web 类型）
2. 同一用例在所有可用端行为一致：幂等语义、dry_run 语义、错误提示词一致
   （词表单源在 core，端只做文案映射）
3. 契约新鲜度：`gen:sdk` 重跑后 web 编译通过（vue-tsc 拦截字段漂移）；web DTO
   派生自 SDK 生成物、无手写字段清单；破坏性 diff 必须升 API 版本
4. 新端准入检查单：三件事之外的代码为 0；与既有端无共享文件；能独立演示
   同一演示链路（`playbook.md` 的演示脚本）

## 6. 与阿里规范的逐条对照

| 阿里规范条目 | 本规约落点 |
|---|---|
| 《Java 手册》6.1 应用分层：禁止跨层调用、逆向依赖 | R1/R2/R4（机器验证） |
| 《Java 手册》6.2 分层领域模型 DO/DTO/VO | R7 模型分层表 |
| 《手册》折中方案：Service 可操作数据模型、防逐层转换 | R7 折中条款（Out 显式投影 + web 契约派生两底线） |
| COLA `adapter` 层"薄适配器"原则 | §1 薄壳纪律三件事 |
| COLA `client` 层 SDK 复用 | §3 契约单源下沉 + §4 web 派生范式 |
| COLA `start` 装配层 | §4 组合根只装配 |
| COLA"精简版起步、复杂度上升再拆"演进观 | §4 server 拆分阈值（Out >10 或端点按域 >2 组才拆） |
