# 新业务/新系统复用指南

## 1. 复用模型：换"芯"不换"壳"

本架构的多端骨架（server 骨架、CLI 框架、web/uniapp 基建、桌面壳、SDK 流水线、CI、Docker）与具体业务无关。孵化新系统时：

1. 复制 monorepo（或维护一个 template 仓库，`Use this template` 一键建仓）。
2. 全局替换包名/应用名。
3. **重写 `packages/core` 的 domain/ 与 application/（业务语义层）**——这是唯一真正的"新开发"。
4. 保留 core 的 bootstrap 组装模式与 Port 约定，出站适配器按新业务挑选（换 DB、加 LLM、加支付）。
5. server 路由、前端页面、uniapp 页面按新用例重写——但请求层、鉴权、错误映射、构建部署全部照旧。

## 2. 多业务并存的两种组织法

| 模式 | 做法 | 适用 |
|---|---|---|
| 单仓多核 | `packages/core-a`、`packages/core-b`，server 挂多个路由模块，前端多入口 | 业务间共享用户/鉴权/部署 |
| 模板复制 | template 仓库 → 新仓库独立演进 | 业务独立交付、独立团队 |

默认单仓多核起步，业务长大再拆。

## 3. 常见复用场景对照

| 新需求 | 动哪里 |
|---|---|
| 给现有系统加一个微信小程序 | 复用 server + SDK，新建 apps/uniapp |
| 给现有系统加内网 CLI 工具 | 复用 core，新建 apps/cli 子命令（remote 模式） |
| 做一个纯本地 AI 桌面工具 | 复用桌面壳 + core（离线模式），不要 server 部署 |
| 接入 LLM 能力 | core 定义 `LLMPort`，适配器实现 OpenAI/本地模型，bootstrap 注入 |
| 对外开放 API | core 不动，server 加一层 API Key 鉴权与限流中间件 |

## 4. 演进护栏（防止复用走形）

- 新端/新适配器必须先在 core 补 Port 与测试，再写壳代码。
- 任何"临时"绕过 SDK 直写 URL 的前端代码 = 架构债，code review 拦截。
- core 出现第一个框架 import 时立即重构，而不是记 TODO。
- 每季度检查：桌面框架（pywebview vs Tauri）、uni-app x、FastAPI 生态是否有值得跟进的代际变化（参考 tech-stack.md 的更新方法重跑一轮调研）。
