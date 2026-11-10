# 实施手册：拆解步骤 · 演示脚本 · 验收清单

## 1. 可拆解的分阶段实施计划

### P0 骨架（0.5 天）
- [ ] 运行 scaffold.py 生成 monorepo
- [ ] `uv sync` + `pnpm i` 全部可安装
- [ ] server 起得来，`/health` 200；CLI `--help` 正常
- 产出：可运行的空壳，依赖方向已由脚手架固化

### P1 单端闭环（1 天）
- [ ] core：定义 Task 实体 + CreateTask/ListTasks 用例 + TaskRepository Port
- [ ] server：SqliteTaskRepository + tasks 路由
- [ ] CLI：add/list 命令（local 模式）
- [ ] pytest：core 纯单测 + server 集成测试
- 产出：命令行完成一次业务闭环

### P2 契约与 Web（1 天）
- [ ] 生成 TS SDK，web 页面列表 + 新增表单
- [ ] 统一错误码 → 前端提示映射
- [ ] 设计系统生成（按 SKILL.md 阶段 3.5）：frontend-design 定调 → theme-factory 定色覆写 tokens.css → ui-ux-pro-max 查规；记录到 docs/design-decisions.md
- 产出：浏览器可见同一份数据，且视觉不撞默认 AI 风

### P3 桌面端（0.5 天）
- [ ] pywebview 壳加载 web 构建产物，在线模式跑通；或 `--desktop electron` 时 `WEB_URL=... npm start` 跑通
- [ ] （可选）离线模式：pywebview 内嵌 uvicorn / Electron 拉起 sidecar（stdout 端口握手）
- 产出：桌面双击即用的应用

### P4 小程序/App（1-2 天）
- [ ] uniapp 请求层 + 列表/新增页
- [ ] 微信开发者工具跑通（线上域名备案后替换 BASE）
- 产出：小程序与 App 模拟器可见同一份数据

### P5 加固（按需）
- [ ] JWT 鉴权全端打通
- [ ] CI 契约 diff + 构建
- [ ] Docker Compose 生产部署
- [ ] 换 PostgreSQL、加 Redis/后台任务

## 2. 可演示脚本（15 分钟 Demo）

**场景：新增一条任务，各端各自操作，数据同源。**

1. (2min) 打开 IDE 展示 monorepo 结构，指出 core 里"零框架 import"（grep 证明）。
2. (2min) 终端：`my-app-cli add "写周报"` → `my-app-cli list` 显示。
3. (2min) `uv run uvicorn server.main:app` 起服务，开 http://127.0.0.1:8000/docs 展示自动文档；浏览器打开 web 页面，列表里出现"写周报"。
4. (3min) 双击桌面包 exe，pywebview 窗口出现同一列表；关网络再演示离线模式（本地 SQLite）。
5. (3min) HBuilderX 运行 uniapp 到微信开发者工具，同一列表；真机预览 App 端。
6. (3min) 杀手锏：改 core 里一条业务规则（如标题最短 5 字），只重跑 server + CLI —— CLI 立即报错、Web 提交被 422 拦截 —— 证明"一处规则，各端生效"。

## 3. 验收清单（架构完整性）

**分层纯净度**
- [ ] `grep -rE "fastapi|sqlalchemy|httpx" packages/core/src` 零命中
- [ ] server 路由函数 ≤ 15 行，无业务条件分支
- [ ] 前端无手写 API URL，全部来自生成的 SDK

**契约一致性**
- [ ] CI 有 openapi.json diff 检查；破坏性变更走版本号
- [ ] 各端错误提示来自统一错误码映射表

**设计质量**
- [ ] Web 端颜色/字体全部来自 tokens.css 变量，组件零硬编码色值
- [ ] 存在 docs/design-decisions.md（审美方向 + 主题来源记录）
- [ ] ui-ux-pro-max 关键规则通过：对比度 ≥4.5:1、触达目标 ≥44px、焦点态可见、无 emoji 当图标
- [ ] （可选）impeccable `/audit` 无高危项

**多端联通**
- [ ] CLI（local）、CLI（remote）、Web、桌面、小程序/App 至少各跑通一次完整增删查
- [ ] 桌面离线模式可用（如产品需要）

**质量与安全**
- [ ] core 单测覆盖主用例；server 有集成测试
- [ ] JWT 全端生效；密钥走环境变量；小程序域名白名单配置
- [ ] `.env` 在 .gitignore；CI 无明文密钥

**可复用性**
- [ ] 新增一个业务域只需动 core 两层 + server 路由模块（拿"第二个实体"实际演练一次验证）
