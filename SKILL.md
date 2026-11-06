---
name: cross-platform-arch
description: 「一核多端」统一应用架构设计与落地技能。当用户要设计、搭建或评审支持 CLI、Web、桌面、小程序、App（甚至 H5）多端的软件应用架构，要为新业务/新系统选 Python 技术栈、搭 Monorepo 脚手架、打通 OpenAPI 契约到各端类型化 SDK、做可演示原型，或问"多端架构怎么搭/一套代码多端运行/跨端技术选型/桌面端用 Electron 还是 pywebview/小程序框架选型"时使用本技能。输出可操作、可拆解、可演示、可复用的架构方案与脚手架。不用于：纯单端小工具、纯运维部署问题。
license: MIT
metadata:
  version: "1.6.0"
  date: "2026-11-06"
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

## 执行流程（四阶段）

### 阶段 1：需求定位（先问/先判三件事）

- **哪些端必选、哪些可选？** 决定裁剪：只有 CLI+Web → 跳过 uni-app 与 pywebview；小程序与 App 都要 → uni-app 一码双投；只要小程序 → 仍用 uni-app（留 App 出路）。
- **桌面端要不要离线运行？** 离线 → pywebview 内嵌本地 FastAPI + SQLite；纯在线 → 桌面壳连云端即可。
- **是否有 AI/数据密集逻辑？** 有 → 这正是 Python 核心包的价值点；没有 → 架构同样成立（FastAPI 足够快）。

裁决细节见 `references/tech-stack.md`（含 2025-2026 公开调研结论与来源）。

### 阶段 2：脚手架生成

直接运行本技能自带脚本生成 Monorepo 骨架：

```bash
python <skill目录>/scripts/scaffold.py --name my-app --dir /path/to/my-app
# 桌面端想用 Electron：--desktop electron（生成 Electron 主进程 + Python sidecar 模板）
```

生成内容：`apps/server`（FastAPI）、`apps/cli`（Typer）、`apps/web`（Vue3+Vite）、`apps/desktop`（pywebview 壳，或 `--desktop electron` 时生成 Electron 主进程 + sidecar 入口）、`apps/uniapp`（小程序+App 占位）、`packages/core`（六边形分层核心）、`packages/sdk`（OpenAPI 生成脚本）、docker-compose、CI 配置。结构与关键文件说明见 `references/scaffold.md`。

### 阶段 2.5：存量项目移植（可选——把已有项目的功能迁入本架构时必读）

"把旧项目功能用新架构实现"**不等于**把旧代码整体搬进适配器层。必须先产出功能→归属映射表，把领域词汇（结果枚举+分类谓词）、编排语义（硬承诺/空集/校验）提取进 core，技术能力才留适配器；否则 core 会退化成薄壳，业务规则散落外圈。五步流程与"薄壳反模式"对照见 `references/migration.md`——移植类项目在阶段 4 验收时额外执行其"端零映射"检查。

**生成后必须立即验证**（把架构约束交给机器判定）：

```bash
python <skill目录>/scripts/verify_project.py --project /path/to/my-app --test
```

检查项：① 结构完整性（含设计决策记录 `docs/design-decisions.md`）② 核心纯净性（packages/core 禁止 import 任何框架——"一核多端"铁律）③ 依赖方向性（核心不得反向依赖任何端）④ Token 引用闭合（web 引用的 var(--x) 必须在 tokens.css 定义——样式残缺不报错，必须机器判定）⑤ 核心测试通过。任何一项 FAIL 必须先修复再进入阶段 3。产出约束与质量门禁清单见 `references/output-spec.md`。

### 阶段 3：跑通演示链路

按 `references/playbook.md` 的演示脚本执行：实现一个最小用例（示例为"任务管理"），验证各端可见同一份数据：
1. CLI：`my-app task add "hello"` → SQLite 落库
2. Web：页面列表出现该任务
3. 桌面：pywebview/Electron 窗口内同一列表
4. 小程序/App：HBuilderX 运行到模拟器，同一列表
5. 修改核心包一处业务规则 → 所有端行为同时变化（证明"一核"）

### 阶段 3.5：设计系统生成（前端不止于"能用"——必执行,不许跳过）

内置设计能力包（`references/design/`，均为 MIT 许可的提示词知识库），**严格按加载顺序**执行：
1. `frontend-design/` 定审美方向与字体人格（反模板化）
2. `theme-factory/` 选/生成主题 → 覆写 `apps/web/src/styles/tokens.css`
3. `ui-ux-pro-max/` 按优先级查可访问性/交互/布局规则与反模式
4. `improve-animations/`（可选）关键交互动效，尊重 prefers-reduced-motion
5. impeccable 精修（**未内置**，仓库无 LICENSE；需要时运行 `scripts/install_impeccable.sh` 按需克隆后 `/audit` → `/polish`）

**必产物（缺一即 FAIL，verify 会查）**：
- `apps/web/src/styles/tokens.css` —— 颜色/字体/间距/字号 token 全量定义；组件与样式表引用的每个 `var(--x)` 必须在此（或本文件）有定义（verify 检查项 4）
- `docs/design-decisions.md` —— 设计决策记录（主题定位/配色出处/字体/布局/动效/可访问性），保证审美选择是"决策"而非"默认"

防冲突硬约束（token 唯一来源、theme-factory 不碰布局、impeccable 只在最后）见 `references/design/README.md`。uni-app 端仅同步颜色/字号变量。

### 阶段 4：验收 + 复用评估

对照 `references/playbook.md` 末尾的验收清单逐项打勾（分层纯净度、契约同步、测试策略、密钥管理、多端联通）。然后按 `references/reuse.md` 评估：下一个业务只需替换 `packages/core` 的 domain/application 两层，其余骨架、CI、部署、SDK 链路全部复用。

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
- `references/tech-stack.md` — 技术选型调研结论（附公开资料来源，2026-11 调研）
- `references/scaffold.md` — Monorepo 目录结构与关键文件逐个说明
- `references/output-spec.md` — 产出规范：文件清单、硬约束、运行时验收证据链
- `references/migration.md` — 存量项目移植规范：功能归属映射、领域词汇提取、薄壳反模式对照（真实事故复盘）
- `references/anthropic-patterns.md` — anthropics/skills 官方模式拆解（放置/调用/整合/评测）与本 skill 对照
- `references/playbook.md` — 分阶段实施计划、演示脚本、验收清单
- `references/reuse.md` — 新业务/新系统复用指南
- `references/design/` — 设计能力包（frontend-design / theme-factory / ui-ux-pro-max / 动效×2，均 MIT；README 含加载顺序与防冲突规则）
- `scripts/scaffold.py` — 一键生成 Monorepo 骨架（`--desktop electron` 切桌面壳）
- `scripts/install_impeccable.sh` — 按需克隆 impeccable 精修 skill（上游无 LICENSE，不随本 skill 分发）
