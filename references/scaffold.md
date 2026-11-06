# Monorepo 目录结构与关键文件

## 1. 顶层布局（pnpm workspace + uv workspace）

```
my-app/
├── apps/
│   ├── server/          # FastAPI 服务（入站适配器层）
│   ├── cli/             # Typer 命令行
│   ├── web/             # Vue3 + Vite 管理端/用户端
│   ├── desktop/         # pywebview 桌面壳（复用 web 构建产物）
│   └── uniapp/          # uni-app（微信小程序 + App，HBuilderX 打开）
├── packages/
│   ├── core/            # 纯 Python 业务核心（六边形）
│   └── sdk/             # OpenAPI → TS SDK 生成脚本与产物
├── docker-compose.yml   # server + postgres + redis（生产形态）
├── pnpm-workspace.yaml  # 前端 workspace
├── pyproject.toml       # uv workspace 成员声明
├── .github/workflows/ci.yml
└── README.md
```

## 2. Python 侧（uv workspace）

根 `pyproject.toml`：
```toml
[tool.uv.workspace]
members = ["packages/core", "apps/server", "apps/cli"]
```

`packages/core/pyproject.toml`：`dependencies = []`，必须为空——核心只依赖标准库（含 dataclasses/sqlite3 等内置模块）。**pydantic 也在禁止之列**（数据校验用 dataclass + 手写规则，见 output-spec.md C1 与 verify_project.py 的 FORBIDDEN_IN_CORE 清单）；禁止 fastapi/sqlalchemy/httpx。

`apps/server/pyproject.toml`：`dependencies = ["fastapi", "uvicorn", "sqlalchemy", "pydantic-settings", "my-app-core"]`（本地路径依赖）。

### server 关键文件

```
apps/server/src/server/
├── main.py          # app 工厂：挂路由、CORS、/health、异常映射
├── deps.py          # get_current_user、get_uow 等 FastAPI 依赖
├── routes/tasks.py  # 路由 = 解析请求 → 调用用例 → 映射响应
└── adapters/        # 出站适配器：SqliteTaskRepository（实现 core 的 Port）
```

路由示例（体现"只做协议转换"）：
```python
@router.post("/tasks", response_model=TaskOut)
def create_task(body: TaskCreate, user=Depends(get_current_user)):
    try:
        task = get_create_task_usecase(session_factory).execute(user.id, body.title)
    except TaskTitleEmpty as e:
        raise HTTPException(422, str(e))
    return TaskOut.model_validate(task)
```

### CLI 关键文件

```python
# apps/cli/src/cli/main.py
app = typer.Typer()

@app.command()
def add(title: str, remote: bool = False):
    repo = HttpTaskRepository(BASE_URL) if remote else SqliteTaskRepository(DB_PATH)
    uc = bootstrap.create_task(repo)
    uc.execute(user_id, title)
```

## 3. 前端侧（pnpm workspace）

```
apps/web/
├── src/
│   ├── api/          # 引用 packages/sdk 生成的 client，禁止手写 fetch URL
│   ├── stores/       # Pinia：auth、ui 状态；服务端数据一律走 Vue Query
│   └── pages/
└── vite.config.ts    # dev 期 proxy /api → http://127.0.0.1:8000

packages/sdk/
├── generate.mjs      # 拉 openapi.json → openapi-typescript + 生成 fetch client
└── src/gen/          # 生成产物（提交进 git，diff 可评审）
```

生成命令：
```bash
npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/gen/schema.d.ts
npx openapi-typescript-codegen --input openapi.json --output src/gen --client fetch
```

## 4. 桌面壳（apps/desktop，二选一）

### 4a. pywebview（默认）

```python
# apps/desktop/main.py —— 在线/离线双模式
def start_offline_server():
    cfg = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning")
    server = uvicorn.Server(cfg)
    threading.Thread(target=server.run, daemon=True).start()
    return server  # server.servers[0].sockets[0].getsockname()[1] 取实际端口

webview.create_window("MyApp", web_base_url, js_api=BridgeApi())
webview.start()
```

打包：`pyinstaller --windowed --add-data "../web/dist:web"`（产物含前端静态文件与 Python 运行时）。

### 4b. Electron（`--desktop electron` 生成）

```
apps/desktop/
├── main.js          # Electron 主进程：在线模式 WEB_URL 直载；离线拉起 sidecar
├── package.json     # electron + electron-builder（extraResources: sidecar/）
└── README.md        # 打包步骤
apps/server/
└── sidecar_entry.py # sidecar 入口：create_app() + 静态资源同源伺服 + 空闲端口 + stdout 握手
```

关键机制（已实测）：
- sidecar 预绑定空闲端口，启动完成后向 stdout 打印 `SIDECAR_PORT=<port>`；main.js 解析该行并轮询 `/health` 后才 `loadURL`。
- `sidecar_entry.py` 把 web 构建产物挂到 FastAPI 根路径（StaticFiles html=True）——**API 与页面同源**，天然规避 CORS 与 file:// 限制；`/health` 必须在 `create_app()` 工厂内部注册（sidecar 与 uvicorn 入口共用工厂）。
- `app.on("before-quit")` 回收 sidecar 进程；sidecar 异常时 `dialog.showErrorBox` 提示。
- 打包链：`pnpm build:web` → 拷 dist 到 `apps/server/web_dist` → `pyinstaller --onefile --add-data "web_dist:web_dist" sidecar_entry.py` → exe 放 `apps/desktop/sidecar/` → `npm run dist`。
- 开发期在线模式：`WEB_URL=http://localhost:5173 npm start`（走 vite proxy）。

## 5. uni-app（apps/uniapp）

- HBuilderX 打开；`manifest.json` 配置小程序 AppID。
- 请求层统一 `src/api/request.ts`：读 `import.meta.env.VITE_API_BASE`，小程序后台需配置该域名。
- 页面结构与 web 同构（列表/详情/表单），样式用 uni-ui 或原子 CSS 方案。

## 6. CI（.github/workflows/ci.yml 关键步骤）

1. `uv sync && uv run pytest`（core 单测 + server 集成测试）
2. `pnpm i && pnpm -r generate:sdk`（契约生成，diff 检查破坏性变更）
3. `pnpm -r build`（web 构建，供桌面壳与静态部署）
4. （可选 matrix）pyinstaller 桌面包 + HBuilderX 云打包由人工/本地触发
