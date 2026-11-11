# 产出规范：生成的项目长什么样、如何验收

> 回答两个问题：**脚手架最终产出什么？怎么判定它合格？**
> 机器判定入口：`scripts/verify_project.py --project <项目目录> --test`

## 1. 产出清单（模板 49 个文件；`--desktop electron` 为 51 个，机器可查）

> 另有 vendoring 的 `scripts/verify_project.py`（+1，复制自 arch-verify skill 的
> `scripts/verify_project.py`，最佳努力：该 skill 未安装时输出手动安置指引），总计
> pywebview 50 个 / electron 52 个。

脚手架以 `--name my-app` 为例的固定产物（verify_project.py 已内置此清单检查）：

| 分区 | 文件 | 说明 |
|---|---|---|
| 工作区 | `pyproject.toml` / `pnpm-workspace.yaml` / `package.json` | uv + pnpm 双工作区定义 |
| 工程化 | `.github/workflows/ci.yml` / `docker-compose.yml` / `.env.example` / `.gitignore` / `README.md` | CI、本地编排、环境变量样例 |
| 提交门禁 | `.githooks/commit-msg` / `scripts/install_hooks.py` / `scripts/setup_hooks.cjs` | 提交信息强制校验钩子 + 启用器（pnpm install 自动 / 纯 Python 手动） |
| **核心** | `packages/core/src/<pkg>_core/domain/task.py` | 领域实体 + 业务规则（唯一规则源） |
| | `.../application/ports.py` | 仓储接口（Protocol，依赖倒置的关键） |
| | `.../application/usecases.py` | 用例编排（create/list） |
| | `.../bootstrap.py` | 组装入口（按环境注入适配器） |
| | `packages/core/tests/test_task.py` | 核心单测（纯 Python，无框架） |
| 后端 | `apps/server/src/server/main.py` / `routes/tasks.py` | FastAPI 路由（薄壳，只做协议转换） |
| | `.../adapters/repo.py` / `orm.py` | SQLAlchemy 适配器实现 ports |
| | `apps/server/Dockerfile` | 镜像构建 |
| CLI | `apps/cli/src/cli/main.py` / `repo.py` | Typer 命令；local 模式用自带 stdlib sqlite3 适配器（零框架） |
| 自检 | `scripts/verify_project.py` | 随产物分发的架构自检器（CI verify 步骤依赖；vendoring 自本 skill，本 skill 升级后需对已生成项目重新复制） |
| 设计 | `docs/design-decisions.md` | 设计决策记录（阶段 3.5 设计包流程必产物；verify 清单含此项） |
| Web | `apps/web/src/App.vue` / `main.ts` / `styles/tokens.css` / `vite.config.ts` | Vue3 页面 + 设计 token（唯一颜色来源） |
| 桌面 | `apps/desktop/main.py`（pywebview）或 `main.js` + `apps/server/sidecar_entry.py`（Electron） | 壳，加载 web 构建产物 |
| 小程序/App | `apps/uniapp/src/api/request.ts` + README | uni-app 请求封装与运行说明 |
| 契约 | `packages/sdk/generate.mjs` / `package.json` | 离线探针生成脚本（uv probe → openapi-typescript，不依赖运行中的 server） |
| | `packages/sdk/src/gen/schema.d.ts` / `openapi.sha256` | 契约产物与指纹（脚手架放占位，`pnpm gen:sdk` 生成真实值；verify 契约新鲜度门禁比对） |

**可变部分**：应用名/包名（`--name` 注入）、桌面壳类型（`--desktop`）、以及你随后填充的业务内容。骨架本身是固定的，这是"多项目一致"的保证。

## 2. 硬约束（verify_project.py 逐条机器判定）

### C1 核心纯净性（铁律）
`packages/core/src/**` 内禁止 import：fastapi、sqlalchemy、typer、uvicorn、httpx、requests、pydantic、flask、django、starlette、rich、click、aiohttp。
核心只依赖标准库。业务规则只写在这里 → 各端行为自动一致。

### C2 依赖方向
- 允许：任意端 → 核心；端 → 端的适配器实现（CLI remote 模式连 server API）。
- 禁止：核心 → 任何端、核心 → 任何框架。

### C3 结构完整性
上表文件必须齐全（electron 模式另含 main.js/desktop package.json/sidecar_entry.py/desktop README）（缺 CI 配置、缺 tokens.css 都算 FAIL）。

### C4 测试通过
`uv run pytest packages/core/tests` 必须绿。业务规则（如"标题≥2字"）要有核心层单测覆盖。

### C5 Token 引用闭合（样式残缺是隐性破损）
web 端（App.vue / styles/*.css）引用的每个 `var(--x)` 必须在 `tokens.css` 或引用所在文件中有定义。该类破损不报错、不崩构建，页面只是"安静地变丑"——人工 review 极易漏检，由 verify 检查项 4 机器判定。

### C6 语义决策只在一处（重写接入类项目重点）
结果词汇枚举+分类谓词、硬承诺规则（如 dry_run 只报告不领取）、空集语义、目标校验——只写在 core（domain/application）；bridge/路由/端零映射表、零语义决策。适配器只做形状转换与能力申报。对照检查见 `references/migration.md` 的"薄壳反模式"表。

## 3. 运行时验收（生成的项目开箱即用的证据链）

```bash
# 1. 结构 + 约束 + 单测（一条命令）
python verify_project.py --project . --test
# 期望: PASS — 结构完整、核心纯净、依赖方向正确、Token 闭合、契约新鲜、测试通过

# 2. 契约流水线（不依赖运行中的 server；verify 的契约新鲜度门禁依赖此步）
uv sync && pnpm install && pnpm gen:sdk
# 无 node 环境: 生成后补跑一次指纹步骤即可 PASS——
#   sha256( uv run python -c "import json; from server.main import app; print(json.dumps(app.openapi()))" 的 stdout )
#   （CRLF 统一按 LF 规范化后求哈希，写入 packages/sdk/src/gen/openapi.sha256）

# 3. server 全链路（根目录直接跑，workspace 已装 server/cli）
uv run uvicorn server.main:app --port 8000
curl localhost:8000/health                     # {"status":"ok"}
curl -X POST localhost:8000/api/v1/tasks -H "Content-Type: application/json" -d '{"title":"写周报"}'
curl -X POST localhost:8000/api/v1/tasks -H "Content-Type: application/json" -d '{"title":"a"}'
# 期望: 422 + 中文错误提示（核心业务规则经 API 生效）

# 4. CLI 全链路（根目录）
uv run my-app-cli add "hello" && uv run my-app-cli list
```

> 已实测记录（demo-app）：三项全过，CLI 与 server 通过同一份 SQLite 看到彼此的数据。

## 4. 演进期约束（防止项目长歪）

- 新增业务实体：先在 core 写实体+规则+单测 → ports 加接口 → server/cli 加适配器与路由 → 重新生成 SDK。**永远自内向外**。
- 业务规则出现第二份拷贝（某端自己写了 if 判断）即视为架构腐化，CI 里跑 verify_project.py 拦截。
- 颜色/字号只写在 `tokens.css`，组件内禁止硬编码（见 `references/design/README.md`）。
- 破坏性 API 变更：改版本号 + 重新生成 SDK，前端编译期报错兜底。
