# 设计备忘：六边形门禁与脚手架拓扑的对齐（待评审）

日期：2026-11-10 ｜ 状态：draft，评审后落地
关联：cross-platform-design 1.0.0 / monorepo-scaffold 1.0.1 / arch-verify 1.0.1

## 1. 问题发现（2026-11-10 审计）

`verify_project.py` 的六边形桥检查**写死了 `packages/engine/`**：

```python
def check_hexagonal(root: Path) -> list[str]:
    eng_src = root / "packages/engine/src"     # ← 写死
    if not eng_src.is_dir() or not ends_root.is_dir():
        return []                              # ← 无 engine 时整项静默跳过
```

而 `monorepo-scaffold` 生成的项目只有 `packages/core`（无 engine、无 bridge.py），
出站适配器分布在两处：

- `apps/server/src/server/adapters/`（SQLAlchemy 仓储）
- `apps/cli/src/cli/repo.py`（stdlib sqlite3 本地仓储 + httpx 远程仓储）

对照 `cross-platform-design/references/hexagonal-arch.md` 的分层契约：

| 规约（COLA 对照）                     | 脚手架实际              | 是否相符 |
|---|---|---|
| app+domain → packages/core            | packages/core           | ✅ |
| **infrastructure → packages/engine**  | **apps/server/adapters + apps/cli/repo.py** | ❌ 分散在三个端里 |
| start 装配 → server 组合根            | routes 里的 `_repo = SqlTaskRepository()` | ⚠️ 装配发生在路由模块顶层 |
| 端只许 `from <engine>.bridge import`  | 端经 bootstrap.py 组装根 | 协议不同（bootstrap 是 core 出口的装配，不是 engine 桥） |

后果：**scaffold 交付的全部项目，"六边形桥闭合"检查实际永不执行**——门禁宣称的
七项退化成六项有效；规约文档与门禁能力承诺不一致。这不是运行时 bug（端间隔离
检查仍会跑），而是基建覆盖缺失，且极易在"engine 该不该出现在模板项目"这个
问题上反复横跳。

## 2. 两个候选方向

### 方案 A · 脚手架生成 engine + bridge（规约优先）

脚手架模板新增 `packages/engine`：

```
packages/engine/src/<pkg>_engine/
  ├── __init__.py
  ├── bridge.py          # 唯一出桥：装配端口↔适配器，端只见此文件
  └── adapters/          # 同起：SQLAlchemy 仓储（数据库 url 走环境变量）
```

- 端侧改动：server/cli import 从 `{pkg}_core.bootstrap` 换成
  `{pkg}_engine.bridge`；bootstrap 保留在 core（装配根），适配器实现迁到
  engine 桥内注册。
- CLI 本地 sqlite3 仓储同样收进 engine（`adapters/local_repo.py`），本地/远程
  双模式由 bridge 的同一装配点切换，cli/repo.py 删除。
- verify 不改（写死路径开始生效）；monorepo-scaffold 与 arch-verify 的
  "单一事实来源"清单同步迁移。
- playbook 的 P0/P1 步骤调整。

优点：一处模板，项目长期符合 R1–R9；新增端零心智负担。
缺点：模板复杂度上升（bridge 装配 + 组合根模式），小 demo 的"30 分钟可跑"
承诺变重；与"1 核多端精简模板"的定位冲突的风险。

### 方案 B · 规约收录 core-only 变体（现实优先）

hexagonal-arch.md 增设**变体条款**：当项目没有 `packages/engine/` 时，允许
"core + 端内适配器"形态，但必须满足三条硬化约束（否则门禁 FAIL）：

1. 适配器必须实现 core 的 Port（`TaskRepository` 等 Protocol），不许私下
   另立接口——已有：SqlTaskRepository/Sqlite 都实现了 Port ✓
2. 装配收敛单一注册点：server 用 bootstrap/create_app 组装根，CLI 同样经
   bootstrap（现 routes 顶层 `_repo = SqlTaskRepository()` 违规，迁入
   FastAPI Depends 或 create_app 内）；
3. verify 的 check_hexagonal 改为能识别两形态：engine 存在 → bridge 门禁；
   不存在 → 改为检查"端内适配器不越过 Port 边界 + 装配点唯一"（AST 扫描
   `x_task_repository(` 的实例化点收敛性）。

优点：模板保持精简；规约覆盖既有真实项目形态；门禁从 6.5 项补齐到 7 项。
缺点：R4 的"唯一出桥"语义弱化——端不再都走一个 bridge，端间
`infrastructure 逻辑泄漏` 的拦截靠装配点唯一性近似，不如 bridge 是硬边界；
"端零映射（legacy-rewrite）"表格里的 engine 归属列需要一列备注变体。

## 3. 推荐

**推荐 B（先收录变体、硬化三条约束），把 A 留给第二次评审**。理由：

1. 变体已是全部存量脚手架项目的现实形态，规约先承认现实才能谈硬化；
2. 三条硬化约束与现有 verify 的 token 闭合 / 空包检查风格一致（AST/文本
   机器判定，不新增依赖）；
3. A 的模板改造成本与 demo 定位不匹配；当出现第二个 engine 级业务
   （legacy-rewrite 接入端）时再升级模板不迟。

## 4. 落地清单（评审通过后）

- [ ] cross-platform-design/references/hexagonal-arch.md 增补变体条款（v1.0.1）
- [ ] verify_project.py.check_hexagonal 双形态改写 + 用例
- [ ] scaffold 模板收敛装配点（`_repo` 迁出 routes 顶层）
- [ ] output-spec.md 硬约束 C2 补变体条目
- [ ] legacy-rewrite migration.md 归属表备注
- [ ] evals：给 scaffold/verify 各补一条"装配点唯一性"评估
- [ ] CHANGELOG 全链路同步
