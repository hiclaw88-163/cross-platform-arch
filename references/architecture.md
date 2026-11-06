# 架构设计：一核多端

## 1. 总体拓扑

```
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐
│ CLI 端  │ │ Web 端  │ │ 桌面端  │ │ 小程序 / App │
│ Typer   │ │ Vue3    │ │ pywebview│ │ uni-app     │
└────┬────┘ └────┬────┘ └────┬────┘ └──────┬───────┘
     │进程内      │HTTPS      │HTTPS 或本地  │HTTPS
     │(离线直调)  │           │             │
     ▼           ▼           ▼             ▼
┌─────────────────────────────────────────────────┐
│  统一契约层：OpenAPI 3.x（FastAPI 自动生成）      │
│  → openapi-typescript 生成各端 TS SDK            │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│  apps/server  服务层（入站适配器）                │
│  FastAPI 路由 · JWT 鉴权 · 限流 · SSE/WS · 任务  │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│  packages/core  核心包（纯 Python，零框架依赖）   │
│  domain/（实体+规则） application/（用例+端口）   │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│  出站适配器：SQLite/Postgres · Redis · 外部API ·  │
│  LLM · 文件系统  （由核心的 Port 接口定义）        │
└─────────────────────────────────────────────────┘
```

## 2. 分层职责与依赖规则

### 2.1 packages/core（唯一不许妥协的层）

```
packages/core/src/<pkg>/
├── domain/          # 实体、值对象、领域异常、业务规则。只准 import 标准库
├── application/     # 用例（UseCase）：编排实体；在此定义 Port 接口（ABC）
│   └── ports/       # TaskRepository / Notifier 等抽象，核心"向外的承诺"
└── bootstrap.py     # 组装根：注入具体适配器，返回用例对象
```

规则：
- domain/application 不出现 fastapi、sqlalchemy、requests 等任何框架 import。
- CLI 和 Server 都通过 `bootstrap.py` 拿到同一个用例对象——这就是"一核"的物理保证。
- 测试策略：domain/application 用纯 pytest（毫秒级）；适配器层用 sqlite 内存库做集成测试。

### 2.2 apps/server（入站适配器，只做协议转换）

- 路由函数三件事：解析请求 → 调用用例 → 把结果/异常映射为 HTTP 状态码。
- 鉴权、限流、CORS、日志、OpenAPI 文档都在这一层配置，不进核心。
- 长耗时任务用 BackgroundTasks 起步，量大后换 ARQ/Celery（对核心透明，属于出站适配器）。

### 2.3 各端客户端

| 端 | 技术 | 通信方式 | 要点 |
|---|---|---|---|
| CLI | Typer | 进程内 import core | 离线可用；也可 `--remote` 模式走 API（同一用例两个数据源适配器） |
| Web | Vue3 + Vite + Pinia + 生成的 SDK | HTTPS/JSON | 部署为静态文件，Nginx/Caddy 托管；开发期 vite proxy 到 8000 |
| 桌面 | pywebview（默认）或 Electron + Python sidecar（`--desktop electron`） | ①在线：连云端 API ②离线：pywebview 内嵌 uvicorn / Electron 拉起 sidecar | pywebview 纯 Python 最短路径；Electron 换来自动更新/托盘/一致性渲染 |
| 小程序 | uni-app (Vue3) | HTTPS/JSON | 域名需 ICP 备案 + 微信后台配置 request 合法域名 |
| App | uni-app App 端（同一代码库） | HTTPS/JSON | 需要原生性能时再评估 Flutter/RN 二期投入 |

### 2.4 桌面端双模式（本架构的关键设计）

- **在线模式**：桌面壳 = 打包后的 Web 前端 + pywebview，`API_BASE` 指向云端。发布最简单。
- **离线模式**：pywebview 启动时在子线程拉起嵌入式 FastAPI（`uvicorn.Server(Config(...))`），数据库用本地 SQLite 文件，前端请求 `http://127.0.0.1:<port>`。数据同步（如需要）作为出站适配器后续叠加，不破坏分层。

两种模式代码完全同构——因为前端只认 OpenAPI SDK + 可配置的 BASE URL。

**Electron 变体（`--desktop electron`）**：Electron 主进程不做业务，只负责生命周期管理——离线模式拉起 PyInstaller 打包的 `sidecar_entry.py` exe（API + web 静态资源**同源伺服**，避免 CORS 与 file:// 限制），从 stdout 读取 `SIDECAR_PORT=` 后加载页面，`before-quit` 回收进程；在线模式直接 `WEB_URL` 加载。其余（核心包、契约、部署）与 pywebview 模式完全一致，两模式可共存于同一仓库按产品需要二选一。选型依据见 `tech-stack.md`。

## 3. 契约流水线（类型即集成测试）

```
FastAPI 代码变更
  → /openapi.json
  → packages/sdk: npx openapi-typescript  → schema.d.ts
  → npx openapi-typescript-codegen（或 openapi-fetch）
  → 各端 SDK 使用处编译报错（漏改字段当场暴露）
```

- CI 中加一步 `contract-diff`：openapi.json 与上一版 diff，破坏性变更（删字段/改类型）必须升 API 版本（`/v1` → `/v2`）。
- 各端请求层统一：超时、重试、错误码→用户提示的映射，封装在 `packages/sdk` 一处，各端共用。

## 4. 横向能力（所有端共享）

- **鉴权**：JWT。CLI 存 keyring/配置文件；Web 存内存+refresh token；桌面/uni-app 存各自安全存储。核心包只认识"当前用户 ID"，token 解析发生在 server 入站层。
- **可观测性**：server 挂结构化日志（structlog）+ /health；桌面离线模式本地日志文件滚动。
- **配置**：pydantic-settings（仅 server/桌面层），`Settings` 类集中管理；`.env` 只进 server/桌面，前端用构建时环境变量。核心包不依赖 pydantic。
- **升级**：桌面端用 PyInstaller + GitHub Releases（或 tauri-updater 若二期换 Tauri）；App/小程序走各自商店与平台审核。

## 5. 扩展点（新业务复用的插槽）

1. 新业务域：在 core 加 `domain/<域>/` + `application/<域>/`，server 加路由模块，SDK 重新生成——各端自动获得能力。
2. 新端（如企业微信侧边栏、飞书机器人、浏览器插件）：本质又是一个入站适配器或壳，照 2.3 表格加一行即可。
3. 新存储/新 LLM 供应商：实现 core 里的既有 Port，bootstrap 里换一行注入。
