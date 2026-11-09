---
name: cross-platform-design
description: 「一核多端」统一应用架构的设计与评审规约。TRIGGER when 设计或评审支持 CLI/Web/桌面/小程序/App 多端的软件架构、多端技术选型问答（桌面用 Electron 还是 pywebview、小程序框架选型）、评估新业务如何复用这套架构；DO NOT TRIGGER when 要从零搭建新项目（用 monorepo-scaffold）、要验收项目是否符合架构（用 arch-verify）、要把旧项目功能迁移进来（用 legacy-rewrite）。
license: MIT
metadata:
  version: "1.0.0"
  date: "2026-11-10"
  author: WorkBuddy Agent
---

# 一核多端（One Core, Multi-Client）统一应用架构

一句话：**用 Python 写一个纯业务核心包，向内分层、向外开口；所有端（CLI / Web / 桌面 / 小程序 / App）都是核心的"适配器"或"壳"，通过统一 OpenAPI 契约通信。新业务复用 = 换掉核心包，多端骨架原样保留。**

## 核心原则

1. **业务逻辑只写一份**。核心包 `packages/core` 是纯 Python（零框架依赖），CLI 进程内直接调用，Server 经 HTTP 暴露。禁止把业务规则写进路由、写进前端。
2. **契约先行，类型即测试**。FastAPI 自动产出 `openapi.json` → `openapi-typescript` 生成各端 TS SDK。后端改字段，前端编译期报错，而不是上线后崩溃。
3. **依赖方向恒向内**。客户端 → 契约 → 服务层 → 核心包 → 出站适配器（DB/Redis/LLM）。任何一层不得反向 import。
4. **端只是壳**。桌面端是 Web 前端 + pywebview 壳（可离线内嵌 Server）；小程序与 App 用 uni-app 一码双投。新端 = 新增一个壳，核心零改动。
5. **可演示优先于完备**。先用脚手架 30 分钟跑通"一条业务链路在所有端可见"，再逐步加深度。

## 需求定位（先问/先判三件事）

- **哪些端必选、哪些可选？** 决定裁剪：只有 CLI+Web → 跳过 uni-app 与 pywebview；小程序与 App 都要 → uni-app 一码双投；只要小程序 → 仍用 uni-app（留 App 出路）。
- **桌面端要不要离线运行？** 离线 → pywebview 内嵌本地 FastAPI + SQLite；纯在线 → 桌面壳连云端即可。
- **是否有 AI/数据密集逻辑？** 有 → 这正是 Python 核心包的价值点；没有 → 架构同样成立（FastAPI 足够快）。

裁决细节见 `references/tech-stack.md`（含 2025-2026 公开调研结论与来源）。

## 关键决策速查

| 问题 | 默认答案 | 备选 |
|---|---|---|
| Python 包管理 | uv（快、lock 稳定） | poetry |
| API 框架 | FastAPI | Litestar |
| CLI 框架 | Typer（与 Pydantic 同源） | Click |
| Web 前端 | Vue3 + Vite + TS | React（则小程序换 Taro） |
| 小程序+App | uni-app（一码双投，国内生态最全） | Taro（React 栈）+ React Native |
| 桌面端 | pywebview + PyInstaller（默认，纯 Python、8-15MB）；需自动更新/托盘/一致性渲染时用 `--desktop electron`（Electron + Python sidecar） | Tauri/Python sidecar（更小更快，引入 Rust） |
| 数据库 | SQLite（演示/单机）→ PostgreSQL（生产） | — |
| 后台任务 | FastAPI BackgroundTasks → ARQ/Celery（量大后） | — |
| 鉴权 | JWT（python-jose）+ 各端统一 Authorization 头 | — |

## 参考文件

- `references/architecture.md` — 完整架构设计（分层职责、依赖规则、离线/在线双模式、扩展点）
- `references/hexagonal-arch.md` — 六边形架构规约（R1-R9 规则 + verify 门禁映射 + 阿里 COLA/《Java 开发手册》对照）
- `references/clients.md` — apps/ 多端规约（薄壳纪律、端间关系矩阵、共享代码下沉规则、多端一致性验收）
- `references/tech-stack.md` — 技术选型调研结论（附公开资料来源，2026-11 调研）
- `references/reuse.md` — 新业务/新系统复用指南（换"芯"不换"壳"）

## 与其他 skill 的关系

本 skill 定的是"架构长什么样"。落地动作在兄弟 skill（约定整组安装、用 `../` 相对引用）：

- 从零搭新项目：`../monorepo-scaffold/`（脚手架生成 + SDK 打通 + 演示链路 + 设计系统）
- 验收项目是否符合本架构：`../arch-verify/`（机器门禁）
- 旧项目功能重写接入：`../legacy-rewrite/`
