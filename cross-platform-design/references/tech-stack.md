# 技术选型调研结论（2026-11 公开资料调研）

> 调研方式：网络公开资料检索与交叉比对。结论以"默认推荐 + 何时改选"给出，避免伪中立。

## 1. 后端与核心（Python）

| 项 | 结论 | 依据要点 |
|---|---|---|
| uv 管理依赖 | **默认** | Rust 实现，解析/安装显著快于 pip/poetry，lockfile 稳定；社区模板（如 fastapi-backend-template、koru-app）已普遍采用 |
| FastAPI | **默认** | 自动 OpenAPI 是本架构契约流水线的基石；生态最全 |
| Litestar | 备选 | 性能与 DI 更强，但生态与 AI 编码语料弱于 FastAPI，团队无强偏好时不值得 |
| 六边形/整洁架构 | **默认** | 多接口（API+CLI+定时任务）场景的标准答案；核心零框架依赖使"一核多端"物理成立（rothl.com、nilmonfort.com 等多源一致） |
| SQLModel/SQLAlchemy 2.0 | 默认 SQLAlchemy 2.0 | SQLModel 上手快但生产复杂场景仍绕回 SQLAlchemy |

## 2. 桌面端（调研重点，三条路线）

| 方案 | 体积 | 启动 | 优点 | 缺点 | 适用 |
|---|---|---|---|---|---|
| **pywebview + PyInstaller（默认）** | ~8-15MB | ~100-400ms | 纯 Python，业务核心零跨语言；js_api 桥直调 Python；内存 ~25-50MB | 社区较小；Linux 需 WebKitGTK；自动更新要自建 | Python 团队、需离线、快速交付 |
| Tauri + Python sidecar | <10MB 壳 | 快 | 体积最小、安全模型好、官方 updater | 引入 Rust 工具链；sidecar 打包 Python 环境繁琐；IPC 隔着两层 | 追求极致体积且团队接受 Rust |
| Electron + Python sidecar | 100-200MB | 慢 | 生态最大 | 体积/内存大；仍要管 Python 进程 | 已有 Electron 资产 |

结论：既然语言已锁定 Python，**pywebview 是最短路径**；公开基准（johal.in 2025 实测）显示其启动/内存/体积全面优于 Electron，优于 Tauri 的部分指标（Tauri 胜在壳更小，但 Python 逻辑仍需 sidecar，总复杂度更高）。

**何时改选 Electron**（脚手架 `--desktop electron` 直接支持）：需要 electron-updater 自动更新、系统托盘/全局快捷键、崩溃上报、跨 OS 完全一致的 Chromium 渲染（Win/mac/Linux 系统 WebView 行为有差异），或团队已有 Electron 资产。代价：安装包 100-200MB、内存 ~150-300MB、需管理 Python sidecar 生命周期（模板已内置 stdout 端口握手 + 进程回收）。

## 3. 小程序 + App（国内生态）

| 方案 | 结论 | 依据要点 |
|---|---|---|
| **uni-app（默认）** | 一码投小程序+H5+App；插件市场 8000+，字节系/鸿蒙适配深，中文资料最多；Vue3 技术栈与本架构 Web 端一致 | 腾讯云 2026 跨端横评、微信公号 2026 深度对比 |
| Taro 4 | React 团队的等价选择；RN 链路成熟、类型系统强 | 同上 |
| uni-app x (UTS) | App 端原生渲染性能更好，但 UTS 是新语言、坑未平；一期不建议，二期性能瓶颈再迁 | 同上 |
| 原生双端 / Flutter | 仅当 App 是产品主体、交互极重时才值得双倍成本 | webridge.co 2026 选型指南 |

注意：小程序 request 域名必须备案 HTTPS；支付/推送等原生 SDK 通过 uni-app 条件编译处理。

## 4. Web 前端

- **Vue3 + Vite + TypeScript（默认）**：与 uni-app 同为 Vue 语法，团队只需一种前端心智；Pinia 状态、TanStack Query(Vue Query) 服务端状态。
- React 备选：若选 React，则小程序框架联动改 Taro，桌面壳不变。

## 5. CLI

- **Typer（默认）**：基于 Click、类型注解即参数定义，与 Pydantic 同源（同作者）；Rich 美化输出。
- CLI 数据源双模式：`--local`（SQLite 直调核心）与 `--remote`（调 API），靠注入不同 Repository 适配器实现，核心不改。

## 6. 数据与基础设施

- SQLite（演示/桌面离线/单机）→ PostgreSQL（生产多用户）。
- 后台任务：FastAPI BackgroundTasks 起步 → ARQ（轻量 Redis 队列）→ Celery（重）。
- 部署：Docker Compose 起步；上量后 server 前置 Nginx/Caddy，静态前端与 API 同域部署可免 CORS。

## 主要资料来源（检索于 2026-11-06）

1. DeepWiki: ship-python-orchestrate-ai —— FastAPI+React API-first 多端分发（Web/PWA/Electron/桌面）
2. dev.to: FastAPI + React + Expo 三仓库模板 —— OpenAPI 生成 TS SDK 的契约流水线实践
3. GitHub: JamDon2/koru-app —— pnpm monorepo + FastAPI + Expo 生产级结构
4. CSDN/51CTO: "一后端多前端" Monorepo 目录组织（apps/ + packages/ 惯例）
5. rothl.com / nilmonfort.com / notechit.com —— Python 六边形架构分层与端口适配器实现
6. gary-yin.com / johal.in —— Electron/Tauri/Wails/PyWebview 桌面框架 2025 横评与实测基准
7. 腾讯云开发者 / 微信公众号 —— Taro 4 vs uni-app x 六维选型、FinClip/mPaaS 横评（2026-01 数据）
8. webridge.co / shipnative.app / ninjatech.agency —— 2026 移动端 React Native vs Flutter 与后端搭配
