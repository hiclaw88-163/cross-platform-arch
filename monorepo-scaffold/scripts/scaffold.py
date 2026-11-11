#!/usr/bin/env python3
"""一核多端 Monorepo 脚手架生成器。

用法:
    python scaffold.py --name my-app --dir /path/to/my-app
    python scaffold.py --name my-app --dir . --force

生成内容: apps/{server,cli,web,desktop,uniapp} + packages/{core,sdk}
+ docker-compose + pnpm/uv workspace + CI 配置 + README。
仅用标准库；已存在文件默认跳过（--force 覆盖）。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

def F(files: dict[str, str], pkg: str, name: str) -> dict[str, str]:
    out = {}
    for path, content in files.items():
        key = path.replace("{pkg}", pkg).replace("{name}", name)
        out[key] = content.replace("{pkg}", pkg).replace("{name}", name)
    return out

def build(name: str, desktop: str = "pywebview") -> dict[str, str]:
    pkg = name.replace("-", "_")
    files: dict[str, str] = {}

    # ---------- workspace 配置 ----------
    files |= F({
        "pyproject.toml": f'''[project]
name = "{name}-workspace"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["{pkg}-core", "{pkg}-server", "{pkg}-cli"]

[dependency-groups]
dev = ["pytest>=8"]

[tool.pytest.ini_options]
testpaths = ["packages/core/tests"]

[tool.uv.workspace]
members = ["packages/core", "apps/server", "apps/cli"]

[tool.uv.sources]
{pkg}-core = {{ workspace = true }}
{pkg}-server = {{ workspace = true }}
{pkg}-cli = {{ workspace = true }}
''',
        "pnpm-workspace.yaml": "packages:\n  - apps/web\n  - apps/uniapp\n  - packages/sdk\n",
        "package.json": f'''{{
  "name": "{name}-frontend",
  "private": true,
  "scripts": {{
    "postinstall": "node scripts/setup_hooks.cjs",
    "dev:web": "pnpm --filter web dev",
    "build:web": "pnpm --filter web build",
    "gen:sdk": "pnpm --filter @{name}/sdk generate"
  }}
}}
''',
        # ---------- 提交信息强制校验（commit 钩子，pnpm install 自动启用) ----------
        ".githooks/commit-msg": '''#!/bin/sh
# commit-msg 钩子：强制校验提交信息（权威说明见 README「提交与协作」/docs 规范 08-提交信息规范）
# 启用：pnpm install 自动执行 git config core.hooksPath .githooks；手动：python scripts/install_hooks.py
#
# 合法形式（单号必填，无关联需求占位 [0]）：
#   <type>:[<需求单号>]: <主题>             例：feat:[OMS--958]: 任务采集
#   <type>(<scope>):[<需求单号>]: <主题>    scope 可选，例：fix(bridge):[OMS--777]: 修复推送丢失
#   （] 后冒号可省，但必须有空格接主题）
# 强制项：type 白名单 / 单号必填 / 主题 ≤30 字（按字符计数）/ 不以句号（。或 .）结尾

msg_file="$1"
first=$(head -n 1 "$msg_file")

# merge/revert 系统生成的提交放行
case "$first" in
  "Merge "*|"Revert "*) exit 0;;
esac

fail() {
  echo "" >&2
  echo "✗ 提交信息不符合规范" >&2
  echo "  要求格式：<type>:[<需求单号>]: <中文主题>，单行、动词开头、≤30 字、不加句号" >&2
  echo "  type 取值：feat / fix / refactor / docs / chore / build / test" >&2
  echo "  需求单号：必填，无关联用 [0]，关联需求用 [OMS--958] 形式" >&2
  echo "  示例：feat:[OMS--958]: 任务采集批量上报" >&2
  echo "  当前首行：$first" >&2
  echo "" >&2
  exit 1
}

# 第一步：type[(scope)]: 前缀
if ! printf '%s' "$first" | grep -Eq '^(feat|fix|refactor|docs|chore|build|test)(\\([a-zA-Z0-9_-]+\\))?:'; then
  fail
fi

rest=$(printf '%s' "$first" | sed -E 's/^(feat|fix|refactor|docs|chore|build|test)(\\([a-zA-Z0-9_-]+\\))?://')

# 第二步：[需求单号] 必填（] 后冒号可省，之后必须有空格 + 主题）
if printf '%s' "$rest" | grep -Eq '^\\[[^][]+\\]:? .+'; then
  subject=$(printf '%s' "$rest" | sed -E 's/^\\[[^][]+\\]:? //')
else
  fail
fi

# 第三步：不加句号——拒绝末尾的中文句号与英文句点
if printf '%s' "$subject" | grep -Eq '[。.]$'; then
  fail
fi

# 主题 ≤30 字，强制拒绝。优先 python3 按字符计数（C locale 下 wc -m 按字节计，
# 中文会被误判超长）；无 python3 时退回 awk（gawk 在 UTF-8 locale 下按字符计数）
if command -v python3 >/dev/null 2>&1; then
  len=$(printf '%s' "$subject" | python3 -c "import sys; print(len(sys.stdin.read()))")
else
  len=$(printf '%s' "$subject" | awk '{print length($0)}')
fi
if [ "$len" -gt 30 ]; then
  echo "" >&2
  echo "✗ 主题超长：$len 字符（上限 30）——$subject" >&2
  exit 1
fi
exit 0
''',
        "scripts/install_hooks.py": '''#!/usr/bin/env python3
"""启用提交信息强制校验钩子（幂等，可重复执行）。

pnpm install 时由 scripts/setup_hooks.cjs 自动调用（node/npm 环境无需手动）；
纯 Python / 未跑 install 的环境手动执行一次：python scripts/install_hooks.py
目标仓库 = 当前工作目录所在的 git 仓库（git rev-parse --show-toplevel）——
把 .githooks/ 拷到其他仓库后，在该仓库里执行本脚本同样生效。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HOOKS_DIR = ".githooks"


def main() -> int:
    # 与 verify_project.py 同样的控制台防护：不可编码字符降级，不在启用入口崩溃
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, OSError, ValueError):
            pass
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL: 未找到 git 仓库（请在目标仓库内执行本脚本）: {r.stderr.strip()}")
        return 1
    root = Path(r.stdout.strip())
    hook = root / HOOKS_DIR / "commit-msg"
    if not hook.is_file():
        print(f"FAIL: 找不到 {HOOKS_DIR}/commit-msg（请在仓库根执行，或先拷入 .githooks/）")
        return 1
    # 补可执行位（幂等）：从 zip / Windows 拷贝会丢权限位，git 会静默忽略非可执行钩子
    try:
        hook.chmod(hook.stat().st_mode | 0o111)
    except OSError:
        pass
    r = subprocess.run(["git", "config", "--local", "core.hooksPath", HOOKS_DIR],
                       capture_output=True, text=True, cwd=root)
    if r.returncode != 0:
        print(f"FAIL: git config 失败: {r.stderr.strip()}")
        return 1
    print(f"已启用提交信息强制校验: {root} → core.hooksPath = .githooks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
        "scripts/setup_hooks.cjs": '''// pnpm install 收尾自动启用提交信息钩子（任何失败都不阻断安装）
const { execSync } = require("child_process");

try {
  execSync("git config --local core.hooksPath .githooks", { stdio: "pipe" });
  console.log("已启用提交信息钩子（.githooks/commit-msg）");
} catch (e) {
  console.warn("跳过提交钩子启用（手动可跑 python scripts/install_hooks.py）: "
    + String(e.message).split("\\n")[0]);
}
''',
        "docker-compose.yml": '''services:
  server:
    build:
      context: .
      dockerfile: apps/server/Dockerfile
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql+psycopg://app:app@db:5432/app
      - JWT_SECRET=${JWT_SECRET:?set_jwt_secret}
    depends_on: [db]
  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=app
      - POSTGRES_PASSWORD=app
      - POSTGRES_DB=app
    volumes: [pgdata:/var/lib/postgresql/data]
volumes:
  pgdata:
''',
        ".env.example": "JWT_SECRET=change-me\nDATABASE_URL=sqlite:///./dev.db\n",
        "docs/design-decisions.md": f'''# {name} 设计决策记录（ADR）

> 阶段 3.5 设计包流程必产物：技术/设计决策可追溯。决策变更时升版并在对应小节补记。

## D-1 一核多端架构

- 背景：{name} 需要覆盖 Web/桌面/CLI（及小程序）端
- 决策：业务规则只写在 packages/core（domain/application），各端为薄壳适配器
- 理由：规则单源，各端行为自动一致；新增端只写协议转换，不复制业务逻辑
- 后果：core 禁止框架 import（verify 核心纯净性门禁强制）

## D-2 设计 token

- 决策：颜色/字号/间距唯一来源为 apps/web/src/styles/tokens.css
- 约束：组件内禁止硬编码色值；token 引用必须闭合（verify 检查项强制）

## D-3 契约流水线

- 决策：server OpenAPI 变更后必须重跑 `pnpm gen:sdk`（生成 schema.d.ts 并写入契约指纹 openapi.sha256）
- 约束：verify_project.py 的契约新鲜度门禁重算指纹比对，漂移即 FAIL
''',
        ".gitignore": "__pycache__/\n.venv/\nnode_modules/\ndist/\n*.db\n.env\n",
        "README.md": f'''# {name}（一核多端架构）

```bash
cp .env.example .env                            # JWT_SECRET 等环境变量（docker compose 自动读取）
uv sync && pnpm install
pnpm gen:sdk                                    # 生成 SDK 类型与契约指纹（verify 契约新鲜度门禁依赖）
uv run uvicorn server.main:app --reload         # server（根目录即可，workspace 已装 server/cli）
uv run {name}-cli add "hello"                   # CLI
pnpm dev:web                                    # Web
python apps/desktop/main.py                     # 桌面 pywebview（需先 pnpm build:web）
# electron 桌面: cd apps/desktop && npm i && WEB_URL=http://localhost:5173 npm start
# apps/uniapp 用 HBuilderX 打开运行到微信开发者工具
```
分层规则见 SKILL/references/architecture.md：core 禁止框架 import。
架构自检: python scripts/verify_project.py --project . --test

## 提交与协作（强制）

提交信息强制校验随 `pnpm install` 自动启用（`scripts/setup_hooks.cjs` 执行
`git config core.hooksPath .githooks`）；不跑 install 的环境手动执行一次
`python scripts/install_hooks.py`。不符合格式的提交会被 `commit-msg` 钩子
**拒绝**（merge/revert 系统提交放行）：type 白名单、单号必填、主题超 30 字、
以句号（。或 .）结尾——命中任一条即拦截。

格式 `<type>:[<需求单号>]: <中文主题>`：

- type：feat / fix / refactor / docs / chore / build / test
- 需求单号：**必填**，无关联需求占位 `[0]`；关联需求用 `[前缀--编号]`（如 `[OMS--958]`）
- 主题：单行、动词开头、≤30 字（按字符计数）、不加句号；scope 可选（`fix(bridge):[OMS--777]: 修复推送丢失`）
- **一次提交一个意图**：禁止把无关改动混入同一提交；提交前 `git status` + `git diff` 核对
- 提交规范正文（项目建了 docs 仓库时）：`docs/conventions/08-提交信息规范.md`
''',
        ".github/workflows/ci.yml": '''name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      # 顺序关键：先生成 SDK 与契约指纹，verify 的契约新鲜度门禁才有比对基准——首次 push 即绿
      - run: uv sync
      # 首次本地 pnpm install 后提交 pnpm-lock.yaml，之后可改回 --frozen-lockfile
      - run: pnpm install        # postinstall 顺带启用提交信息钩子
      - run: pnpm gen:sdk        # 离线探针生成 schema.d.ts + openapi.sha256
      - name: 架构约束校验（结构/核心纯净/依赖方向/Token 闭合/契约新鲜度）
        run: python scripts/verify_project.py --project .
      - run: uv run pytest
      - run: pnpm build:web
''',
    }, pkg, name)

    # ---------- packages/core ----------
    files |= F({
        "packages/core/pyproject.toml": f'''[project]
name = "{pkg}-core"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
''',
        f"packages/core/src/{pkg}_core/__init__.py": f'__version__ = "0.1.0"\n',
        f"packages/core/src/{pkg}_core/domain/__init__.py": "",
        f"packages/core/src/{pkg}_core/application/__init__.py": "",
        f"packages/core/src/{pkg}_core/domain/task.py": '''from dataclasses import dataclass, field
from datetime import datetime, timezone


class DomainError(Exception):
    pass


class TitleTooShort(DomainError):
    pass


@dataclass
class Task:
    id: str
    user_id: str
    title: str
    done: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if len(self.title.strip()) < 2:
            raise TitleTooShort("标题至少 2 个字符")

    def complete(self) -> None:
        if self.done:
            raise DomainError("任务已完成")
        self.done = True
''',
        f"packages/core/src/{pkg}_core/application/ports.py": '''from abc import ABC, abstractmethod
from uuid import uuid4

from {pkg}_core.domain.task import Task


class TaskRepository(ABC):
    @abstractmethod
    def save(self, task: Task) -> None: ...

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[Task]: ...


def new_id() -> str:
    return uuid4().hex
''',
        f"packages/core/src/{pkg}_core/application/usecases.py": '''from dataclasses import dataclass

from {pkg}_core.application.ports import TaskRepository, new_id
from {pkg}_core.domain.task import Task


@dataclass
class CreateTask:
    repo: TaskRepository

    def execute(self, user_id: str, title: str) -> Task:
        task = Task(id=new_id(), user_id=user_id, title=title)
        self.repo.save(task)
        return task


@dataclass
class ListTasks:
    repo: TaskRepository

    def execute(self, user_id: str) -> list[Task]:
        return self.repo.list_by_user(user_id)
''',
        f"packages/core/src/{pkg}_core/bootstrap.py": '''"""组装根：CLI / server 统一从这里取用例对象（传入各自适配器）。"""

from {pkg}_core.application.ports import TaskRepository
from {pkg}_core.application.usecases import CreateTask, ListTasks


def create_task(repo: TaskRepository) -> CreateTask:
    return CreateTask(repo)


def list_tasks(repo: TaskRepository) -> ListTasks:
    return ListTasks(repo)
''',
        "packages/core/tests/test_task.py": '''import pytest

from {pkg}_core.application.ports import new_id
from {pkg}_core.application.usecases import CreateTask
from {pkg}_core.domain.task import Task, TitleTooShort


class MemRepo:
    def __init__(self):
        self.items: dict[str, Task] = {}

    def save(self, task: Task):
        self.items[task.id] = task

    def list_by_user(self, user_id: str):
        return [t for t in self.items.values() if t.user_id == user_id]


def test_create_and_rule():
    repo = MemRepo()
    CreateTask(repo).execute("u1", "写周报")
    assert len(repo.list_by_user("u1")) == 1

    with pytest.raises(TitleTooShort):
        Task(id=new_id(), user_id="u1", title="a")
''',
    }, pkg, name)

    # ---------- apps/server ----------
    files |= F({
        "apps/server/pyproject.toml": f'''[project]
name = "{name}-server"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]",
    "sqlalchemy>=2",
    "psycopg[binary]",
    "pydantic-settings",
    "{pkg}-core",
]

[tool.uv.sources]
{pkg}-core = {{ workspace = true }}

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/server"]
''',
        "apps/server/Dockerfile": '''# 构建上下文必须是 monorepo 根目录（server 依赖 workspace 里的 core 包）
FROM python:3.12-slim
WORKDIR /app

# uv 固定版本保证构建可复现（升级时改这一行即可）
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

# workspace 上下文必须完整：根 pyproject.toml 声明了 core/server/cli 三个成员，
# 少任一成员的包定义 uv 都会拒绝解析（"Workspace member is missing"）
COPY pyproject.toml ./
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/core/src packages/core/src
COPY apps/server/pyproject.toml apps/server/pyproject.toml
COPY apps/server/src apps/server/src
COPY apps/cli/pyproject.toml apps/cli/pyproject.toml
RUN uv pip install --system --no-cache ./packages/core ./apps/server

# 非 root 运行；应用目录归属应用用户（可读可写，SQLite 数据库落在 /app 下也能建）
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
        "apps/server/src/server/__init__.py": "",
        "apps/server/src/server/main.py": '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes.tasks import router as tasks_router


def create_app() -> FastAPI:
    app = FastAPI(title="{name}", version="0.1.0")
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    app.include_router(tasks_router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
''',
        "apps/server/src/server/adapters/__init__.py": "",
        "apps/server/src/server/adapters/repo.py": '''import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from {pkg}_core.application.ports import TaskRepository
from {pkg}_core.domain.task import Task

from .orm import Base, TaskRow


class SqlTaskRepository(TaskRepository):
    """出站适配器：实现 core 的 TaskRepository Port（SQLite/PostgreSQL 通用）。"""

    def __init__(self, url: str | None = None) -> None:
        url = url or os.environ.get("DATABASE_URL", "sqlite:///./dev.db")
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, connect_args=connect_args)
        Base.metadata.create_all(self.engine)

    def save(self, task: Task) -> None:
        with Session(self.engine) as s:
            s.merge(TaskRow(id=task.id, user_id=task.user_id, title=task.title,
                            done=task.done, created_at=task.created_at))
            s.commit()

    def list_by_user(self, user_id: str) -> list[Task]:
        with Session(self.engine) as s:
            rows = s.query(TaskRow).filter_by(user_id=user_id).all()
            return [Task(id=r.id, user_id=r.user_id, title=r.title,
                         done=r.done, created_at=r.created_at) for r in rows]
''',
        "apps/server/src/server/adapters/orm.py": '''from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TaskRow(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
''',
        "apps/server/src/server/routes/__init__.py": "",
        "apps/server/src/server/routes/tasks.py": '''from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from {pkg}_core.bootstrap import create_task, list_tasks
from {pkg}_core.domain.task import TitleTooShort

from server.adapters.repo import SqlTaskRepository

router = APIRouter(tags=["tasks"])

_repo = SqlTaskRepository()  # 默认读 DATABASE_URL 环境变量；生产环境可改从 deps 注入

DEMO_USER = "u1"  # 鉴权落地后替换为 Depends(get_current_user)


class TaskIn(BaseModel):
    title: str


class TaskOut(BaseModel):
    id: str
    title: str
    done: bool


@router.post("/tasks", response_model=TaskOut)
def create_task_ep(body: TaskIn):
    try:
        task = create_task(_repo).execute(DEMO_USER, body.title)
    except TitleTooShort as e:
        raise HTTPException(422, str(e))
    return TaskOut(id=task.id, title=task.title, done=task.done)


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks_ep():
    return [TaskOut(id=t.id, title=t.title, done=t.done)
            for t in list_tasks(_repo).execute(DEMO_USER)]
''',
    }, pkg, name)

    # ---------- apps/cli ----------
    files |= F({
        "apps/cli/pyproject.toml": f'''[project]
name = "{name}-cli"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["typer", "rich", "httpx", "{pkg}-core"]

[project.scripts]
{name}-cli = "cli.main:app"

[tool.uv.sources]
{pkg}-core = {{ workspace = true }}

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cli"]
''',
        "apps/cli/src/cli/__init__.py": "",
        "apps/cli/src/cli/main.py": f'''import typer
from rich.console import Console
from rich.table import Table

from {{pkg}}_core.bootstrap import create_task, list_tasks

from cli.repo import make_repo

app = typer.Typer(help="{{name}} CLI（local=SQLite 直调核心 / remote=走 API）")
console = Console()
USER = "u1"


@app.command()
def add(title: str, remote: bool = typer.Option(False, help="走远端 API")):
    task = create_task(make_repo(remote)).execute(USER, title)
    console.print(f"[green]已创建[/green] {{task.id[:8]}} {{task.title}}")


@app.command("list")
def list_(remote: bool = typer.Option(False)):
    """列出任务。函数名加下划线避免遮蔽内建 list（命令名保持 list 不变）。"""
    table = Table("id", "title", "done")
    for t in list_tasks(make_repo(remote)).execute(USER):
        table.add_row(t.id[:8], t.title, "✓" if t.done else "")
    console.print(table)
''',
        "apps/cli/src/cli/repo.py": '''"""CLI 双模式数据源：local 自带轻量 SQLite 适配器，remote 走 HTTP（核心无感）。"""
import sqlite3
from datetime import datetime

from {pkg}_core.application.ports import TaskRepository
from {pkg}_core.domain.task import Task


class SqliteTaskRepository(TaskRepository):
    """轻量 SQLite 适配器，不依赖 server 框架。"""

    def __init__(self, url: str = "sqlite:///./dev.db") -> None:
        path = url.replace("sqlite:///", "") if url.startswith("sqlite:///") else url
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id TEXT PRIMARY KEY, user_id TEXT, title TEXT, done INTEGER, created_at TEXT)"
        )
        self.conn.commit()

    def save(self, task: Task) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO tasks (id, user_id, title, done, created_at) VALUES (?,?,?,?,?)",
            (task.id, task.user_id, task.title, int(task.done), task.created_at.isoformat()),
        )
        self.conn.commit()

    def list_by_user(self, user_id: str) -> list[Task]:
        rows = self.conn.execute(
            "SELECT id, user_id, title, done, created_at FROM tasks WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return [
            Task(
                id=r[0],
                user_id=r[1],
                title=r[2],
                done=bool(r[3]),
                created_at=datetime.fromisoformat(r[4]),
            )
            for r in rows
        ]


class HttpTaskRepository(TaskRepository):
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/v1") -> None:
        self.base_url = base_url

    def save(self, task: Task) -> None:
        import httpx

        resp = httpx.post(
            f"{self.base_url}/tasks",
            json={"title": task.title},
            timeout=10,
        )
        resp.raise_for_status()

    def list_by_user(self, user_id: str) -> list[Task]:
        import httpx

        resp = httpx.get(f"{self.base_url}/tasks", timeout=10)
        resp.raise_for_status()
        return [
            Task(id=t["id"], user_id="u1", title=t["title"], done=t["done"])
            for t in resp.json()
        ]


def make_repo(remote: bool) -> TaskRepository:
    return HttpTaskRepository() if remote else SqliteTaskRepository()
''',
    }, pkg, name)

    # ---------- apps/web ----------
    files |= F({
        "apps/web/package.json": f'''{{
  "name": "web",
  "private": true,
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build"
  }},
  "dependencies": {{
    "vue": "^3.5.0"
  }},
  "devDependencies": {{
    "@vitejs/plugin-vue": "^5.2.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "vue-tsc": "^2.1.0"
  }}
}}
''',
        "apps/web/tsconfig.json": '''{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true,
    "jsx": "preserve",
    "types": ["vite/client"]
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.vue"]
}
''',
        "apps/web/vite.config.ts": '''import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true } },
  },
  build: { outDir: "dist" },
});
''',
        "apps/web/src/main.ts": '''import { createApp } from "vue";
import "./styles/tokens.css";
import App from "./App.vue";

createApp(App).mount("#app");
''',
        "apps/web/src/styles/tokens.css": '''/* 设计 token（唯一颜色/字体来源，硬编码色值禁止出现在组件里）
   生成期由设计能力包覆盖：references/design/theme-factory 定色 → frontend-design 定调
   规则见 references/design/README.md */
:root {
  --color-primary: #0f6e56;
  --color-primary-weak: #e1f5ee;
  --color-bg: #fafaf7;
  --color-surface: #ffffff;
  --color-text: #1c1c1a;
  --color-text-muted: #6b6a64;
  --color-border: #e4e2da;
  --color-danger: #a32d2d;
  --font-body: "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  --font-display: var(--font-body);
  --radius-md: 8px;
  --radius-lg: 12px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
}

body {
  margin: 0;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-body);
  line-height: 1.6;
}
''',
        "apps/web/src/App.vue": '''<script setup lang="ts">
// 生产环境: import { client } from "./api/gen";  ← packages/sdk 生成
import { onMounted, ref } from "vue";

const apiBase = "/api/v1";
const title = ref("");
const tasks = ref<{ id: string; title: string; done: boolean }[]>([]);

async function load() {
  tasks.value = await (await fetch(`${apiBase}/tasks`)).json();
}
async function add() {
  await fetch(`${apiBase}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title.value }),
  });
  title.value = "";
  await load();
}
onMounted(load);
</script>

<template>
  <main style="max-width: 560px; margin: 40px auto; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-6)">
    <h2 style="font-family: var(--font-display)">任务列表</h2>
    <form @submit.prevent="add">
      <input v-model="title" placeholder="新任务标题（≥2 字）" />
      <button>添加</button>
    </form>
    <ul><li v-for="t in tasks" :key="t.id">{{ t.title }}</li></ul>
  </main>
</template>
''',
        "apps/web/index.html": f'''<!doctype html>
<html lang="zh-CN">
  <head><meta charset="utf-8" /><title>{name}</title></head>
  <body><div id="app"></div><script type="module" src="/src/main.ts"></script></body>
</html>
''',
    }, pkg, name)

    # ---------- apps/desktop（--desktop pywebview | electron） ----------
    if desktop == "electron":
        files |= F({
            "apps/desktop/package.json": f'''{{
  "name": "{name}-desktop",
  "private": true,
  "version": "0.1.0",
  "main": "main.js",
  "scripts": {{
    "start": "electron .",
    "start:online": "cross-env WEB_URL=http://localhost:5173 electron .",
    "dist": "electron-builder"
  }},
  "devDependencies": {{
    "electron": "^33.0.0",
    "electron-builder": "^25.0.0"
  }},
  "build": {{
    "appId": "com.example.{name}",
    "files": ["main.js", "package.json"],
    "extraResources": [
      {{ "from": "sidecar/", "to": "sidecar/" }}
    ]
  }}
}}
''',
            "apps/desktop/main.js": '''// Electron 桌面壳：在线模式（WEB_URL）直接加载；离线模式拉起 Python sidecar
const { app, BrowserWindow } = require("electron");
const { spawn } = require("node:child_process");
const http = require("node:http");
const path = require("node:path");

let win = null;
let sidecar = null;

async function waitForHealth(port, timeoutMs = 15000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const ping = () => {
      const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
        res.resume();
        resolve();
      });
      req.on("error", () => {
        if (Date.now() - started > timeoutMs) {
          reject(new Error("sidecar 启动超时"));
          return;
        }
        setTimeout(ping, 200);
      });
    };
    ping();
  });
}

async function resolveBaseUrl() {
  if (process.env.WEB_URL) return process.env.WEB_URL; // 在线/开发模式
  // 离线模式：启动 PyInstaller 打包的 sidecar，监听 stdout 里的 SIDECAR_PORT
  const exe =
    process.env.SIDECAR_EXE ||
    path.join(process.resourcesPath, "sidecar", "server-sidecar.exe");
  sidecar = spawn(exe, [], { windowsHide: true });
  sidecar.stdout.on("data", (chunk) => {
    const m = String(chunk).match(/SIDECAR_PORT=(\\d+)/);
    if (m) sidecar.port = m[1];
  });
  const deadline = Date.now() + 15000;
  while (!sidecar.port) {
    if (Date.now() > deadline || sidecar.exitCode !== null) {
      throw new Error("sidecar 启动失败（SIDECAR_EXE 路径或打包有误）");
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  await waitForHealth(sidecar.port);
  return `http://127.0.0.1:${sidecar.port}`;
}

app.whenReady().then(async () => {
  try {
    const base = await resolveBaseUrl();
    win = new BrowserWindow({
      width: 1100,
      height: 760,
      webPreferences: { contextIsolation: true, nodeIntegration: false },
    });
    await win.loadURL(base);
  } catch (err) {
    const { dialog } = require("electron");
    dialog.showErrorBox("启动失败", String(err));
    app.quit();
  }
});

app.on("before-quit", () => {
  if (sidecar) sidecar.kill();
});
app.on("window-all-closed", () => app.quit());
''',
            "apps/server/sidecar_entry.py": '''# Electron 离线模式的 sidecar 入口：API + web 静态资源同源伺服
# 打包: pyinstaller --onefile --name server-sidecar \\
#   --add-data "../web/dist:web_dist" sidecar_entry.py
import os
import socket
import sys
import threading
import time

import uvicorn
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from server.main import create_app  # noqa: E402


def resolve_web_dist() -> str | None:
    candidates = [
        os.path.join(os.path.dirname(sys.executable), "web_dist"),  # PyInstaller onefile
        os.path.join(os.path.dirname(__file__), "web_dist"),  # 源码运行
    ]
    return next((p for p in candidates if os.path.isdir(p)), None)


def pick_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def main() -> None:
    app = create_app()
    web_dist = resolve_web_dist()
    if web_dist:
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")

    port = int(os.environ.get("SIDECAR_PORT", "0")) or pick_free_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    threading.Thread(target=server.run, daemon=True).start()

    deadline = time.time() + 15
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    if not server.started:
        print("SIDECAR_ERROR=failed to start", flush=True)
        sys.exit(1)
    print(f"SIDECAR_PORT={port}", flush=True)

    try:  # 保持进程存活，Ctrl+C 优雅退出
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.should_exit = True


if __name__ == "__main__":
    main()
''',
            "apps/desktop/README.md": '''# Electron 桌面壳（Python sidecar 模式）

## 双模式

- **在线/开发**：`WEB_URL=http://localhost:5173 npm start`（或指向线上站点）。
- **离线**：Electron 拉起 PyInstaller 打包的 `server-sidecar.exe`（API + web 静态资源同源伺服），stdout 读取 `SIDECAR_PORT` 后加载页面。

## 打包步骤

```bash
# 1. 构建前端并复制给 sidecar
pnpm build:web && cp -r ../web/dist ../server/web_dist
# 2. 打包 sidecar（在 apps/server 下）
uv run pyinstaller --onefile --name server-sidecar --add-data "web_dist:web_dist" sidecar_entry.py
# 3. 放置产物并打包桌面壳
mkdir -p sidecar && cp dist/server-sidecar.exe sidecar/
npm run dist   # electron-builder，extraResources 已配置
```

> 注：以上为 bash 语法，Windows 换用等价命令（`Copy-Item`/`mkdir`）；pyinstaller 的 `--add-data` 在 Windows 上分隔符是 `;`（如 `"web_dist;web_dist"`）。

## 何时选 Electron（对比 pywebview）

需要 electron-updater 自动更新、系统托盘、跨 OS 一致的 Chromium 渲染、成熟崩溃上报时选它；
代价是安装包 100-200MB、内存 ~150-300MB、Node+Python 双工具链。纯 Python 团队/轻量工具用 pywebview。
''',
        }, pkg, name)
    else:
        files |= F({
            "apps/desktop/requirements.txt": "pywebview>=5.2\nuvicorn\n\n# 打包: pip install pyinstaller && pyinstaller --windowed --add-data \"../web/dist:web\" main.py\n# (Windows 上 --add-data 的路径分隔符是 \";\"，即 --add-data \"../web/dist;web\")\n",
            "apps/desktop/main.py": f'''"""桌面壳：在线模式加载云端/本地 web 构建；离线模式内嵌 FastAPI + SQLite。"""

import os
import sys
import threading

import uvicorn
import webview

WEB_DIST = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
API_BASE = os.environ.get("API_BASE")  # 设置则走在线模式


def start_embedded_server() -> str:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server", "src"))
    from server.main import app  # noqa: E402

    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    import time

    while not server.servers:
        time.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    return f"http://127.0.0.1:{{port}}"


def main() -> None:
    base = API_BASE or start_embedded_server()
    webview.create_window("{name}", base, width=1100, height=760)
    webview.start()


if __name__ == "__main__":
    main()
''',
        }, pkg, name)

    # ---------- apps/uniapp + sdk ----------
    files |= F({
        "apps/uniapp/README.md": '''# uniapp 端（微信小程序 + App 一码双投）

1. HBuilderX 打开本目录，manifest.json 填小程序 AppID。
2. src/api/request.ts 里配置 API_BASE（线上需 ICP 备案 + 微信后台 request 合法域名）。
3. 运行 → 运行到小程序模拟器；发行 → 原生 App 云打包。
4. 页面骨架与 apps/web 同构：列表 + 新增表单，统一走 SDK 请求层。
''',
        "apps/uniapp/src/api/request.ts": '''// 统一请求层：超时/错误码/鉴权头集中在此，页面禁止手写 URL
export const API_BASE = "http://127.0.0.1:8000/api/v1"; // 上线前替换为备案域名

export async function api<T>(path: string, options: UniApp.RequestOptions = {}): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${path}`,
      timeout: 10000,
      ...options,
      success: (res) => (res.statusCode < 400 ? resolve(res.data as T) : reject(res)),
      fail: reject,
    });
  });
}
''',
        "packages/sdk/package.json": f'''{{
  "name": "@{name}/sdk",
  "private": true,
  "type": "module",
  "scripts": {{
    "generate": "node generate.mjs"
  }},
  "devDependencies": {{
    "openapi-typescript": "^7.4.0"
  }}
}}
''',
        "packages/sdk/generate.mjs": '''// 契约流水线第一步：离线生成 SDK——不依赖运行中的 server
// 流程: ①探针(uv run python -c "…app.openapi()")导出 OpenAPI JSON → 临时文件
//       ②openapi-typescript 生成 src/gen/schema.d.ts
//       ③sha256(探针 stdout，规范化 CRLF→LF) 写入 src/gen/openapi.sha256
// 指纹必须与 arch-verify verify_project.py::check_sdk_freshness 重算口径一致：
// 同一条探针命令 + 同样的换行规范化，否则 Windows 上永远"契约漂移"。
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url)); // packages/sdk
const repoRoot = dirname(dirname(here)); // monorepo 根（uv workspace 根）

// 与 verify_project.py 的 OPENAPI_PROBE_CMD 保持逐字一致
const probeArgs = [
  "run",
  "python",
  "-c",
  "import json; from server.main import app; print(json.dumps(app.openapi()))",
];

const stdout = execFileSync("uv", probeArgs, {
  cwd: repoRoot,
  encoding: "utf8",
  stdio: ["ignore", "pipe", "inherit"],
});
// Windows 下 stdout 可能是 CRLF；verify 端 text=True 已统一为 LF，这里同步规范化
const normalized = stdout.replace(/\\r\\n/g, "\\n");
const sha = createHash("sha256").update(normalized, "utf8").digest("hex");

// 直接以 node 执行 openapi-typescript 的 bin 入口：Windows 下 spawnSync("npx",…)
// 会因 .cmd 垫片 ENOENT，这里从本包 devDependencies 解析入口，跨平台稳定
const require_ = createRequire(import.meta.url);
const tsPkgJson = require_.resolve("openapi-typescript/package.json");
const tsPkgDir = dirname(tsPkgJson);
const tsBin = join(
  tsPkgDir,
  JSON.parse(readFileSync(tsPkgJson, "utf8")).bin["openapi-typescript"],
);

const tmp = mkdtempSync(join(tmpdir(), "openapi-"));
try {
  const jsonFile = join(tmp, "openapi.json");
  writeFileSync(jsonFile, normalized, "utf8");
  execFileSync(process.execPath, [tsBin, jsonFile, "-o", "src/gen/schema.d.ts"], {
    cwd: here,
    stdio: "inherit",
  });
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

writeFileSync(join(here, "src/gen/openapi.sha256"), sha + "\\n", "utf8");
console.log("SDK 生成完成 → packages/sdk/src/gen/{schema.d.ts, openapi.sha256}");
''',
        "packages/sdk/src/gen/schema.d.ts": '''// 占位产物：真实类型由 `pnpm gen:sdk`（openapi-typescript）生成，脚本为 packages/sdk/generate.mjs
export {};
''',
        "packages/sdk/src/gen/openapi.sha256": "placeholder-run-pnpm-gen-sdk\n",
    }, pkg, name)

    return files


def main() -> None:
    ap = argparse.ArgumentParser(description="一核多端 monorepo 脚手架")
    ap.add_argument("--name", required=True, help="应用名（kebab-case，如 my-app）")
    ap.add_argument("--dir", required=True, help="目标目录")
    ap.add_argument(
        "--desktop",
        choices=["pywebview", "electron"],
        default="pywebview",
        help="桌面端壳技术（默认 pywebview；electron 走 Python sidecar 模式）",
    )
    ap.add_argument("--force", action="store_true", help="覆盖已存在文件")
    args = ap.parse_args()

    root = Path(args.dir).resolve()
    if not args.force and root.exists() and any(root.iterdir()):
        sys.exit(f"目录非空: {root}（确认覆盖请加 --force）")

    created = 0
    for rel, content in build(args.name, desktop=args.desktop).items():
        path = root / rel
        if path.exists() and not args.force:
            print(f"跳过（已存在）: {rel}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        # 二进制写入：内容含 \n 的 sh 脚本/yaml 保持 LF，避免 Windows 文本模式翻成 CRLF
        path.write_bytes(content.encode("utf-8"))
        # 可执行位：#! 开头的脚本与提交钩子必须可执行——否则 Linux/macOS 上 git
        # 静默忽略钩子（"hook was ignored because it's not set as executable"）。
        # Windows 的 os.chmod 无权限位概念，调用无害，保留以保持行为同源。
        rel_norm = rel.replace("\\", "/")
        is_hook = rel_norm.startswith(".githooks/")
        if content.startswith("#!") or is_hook:
            try:
                path.chmod(path.stat().st_mode | 0o111)
            except OSError:
                pass
        created += 1
        print(f"生成: {rel}")

    # 随产物分发架构自检器（CI 的 verify 步骤依赖它；单文件、纯标准库）。
    # 来源是本 skill 自带的同源副本 scripts/verify_project.py（与 arch-verify 的
    # 权威版本字节一致，由 tools/validate_skill.py 强制校验）——运行时不再探测
    # 同侧安装的 arch-verify skill（跨 skill 运行时依赖违反独立性约定）。
    verify_src = Path(__file__).resolve().parent / "verify_project.py"
    verify_dst = root / "scripts" / "verify_project.py"
    if verify_src.exists() and (args.force or not verify_dst.exists()):
        verify_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(verify_src, verify_dst)
        created += 1
        print(f"生成: scripts/verify_project.py（vendoring 自 {verify_src.name}）")
    elif not verify_src.exists():
        print("提示: 本 skill 缺少 scripts/verify_project.py 副本（安装不完整？）")
        print("      请从 arch-verify skill 的 scripts/verify_project.py 复制到")
        print("      <项目>/scripts/verify_project.py 后再跑 verify/CI。")

    print(f"\n完成：{created} 个文件 → {root}")
    print("下一步：")
    print("  uv sync && pnpm install")
    print("  pnpm gen:sdk                 # 生成 SDK 类型与契约指纹（verify 契约新鲜度门禁依赖）")
    print("  uv run pytest packages/core/tests")
    print("  uv run uvicorn server.main:app --reload  （根目录即可，workspace 已装 server/cli）")


if __name__ == "__main__":
    main()
