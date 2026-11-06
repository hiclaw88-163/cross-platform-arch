# cross-platform-arch（一核多端统一应用架构）

用 Python 写一个纯业务核心包，各端（CLI / Web / 桌面 / 小程序 / App……数量不限）全部作为核心的"适配器"或"壳"，通过统一 OpenAPI 契约通信。新业务复用 = 换掉核心包，多端骨架原样保留。

## 快速开始

```bash
python scripts/scaffold.py --name my-app --dir /path/to/my-app
# 桌面端换 Electron：--desktop electron
cd /path/to/my-app && cp .env.example .env && uv sync && pnpm install
uv run pytest packages/core/tests
python scripts/verify_project.py --project . --test
uv run uvicorn server.main:app --port 8000        # 根目录直跑
uv run my-app-cli add "hello" && uv run my-app-cli list
```

脚手架已实测通过：core 单测、server 增查 API、业务规则 422 拦截、CLI local 模式增查、Electron sidecar（端口握手 + /health + API）。

## 文档

| 文件 | 内容 |
|---|---|
| SKILL.md | 触发条件、四阶段执行流程、决策速查表 |
| references/architecture.md | 分层职责、依赖规则、桌面离线/在线双模式、扩展点 |
| references/tech-stack.md | 技术选型调研结论（附 2026-11 公开资料来源） |
| references/scaffold.md | Monorepo 目录与关键文件逐个说明 |
| references/playbook.md | P0-P5 实施计划、15 分钟演示脚本、验收清单 |
| references/reuse.md | 新业务复用指南与演进护栏 |
| references/design/ | 设计能力包（frontend-design / theme-factory / ui-ux-pro-max / 动效×2，MIT vendor；含加载顺序与防冲突规则） |
| scripts/scaffold.py | 一键生成 Monorepo 骨架（--desktop electron 切桌面壳） |
| scripts/install_impeccable.sh | 按需克隆 impeccable 精修 skill（上游无 LICENSE，不随包分发） |

## 技术栈默认组合

uv + FastAPI + SQLAlchemy 2.0 + Typer + Vue3/Vite + uni-app（小程序+App）+ pywebview（桌面，可切 Electron）+ SQLite→PostgreSQL
