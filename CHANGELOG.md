# Changelog

## 1.5.1 (2026-11-06)

- 全量复检发现并修复 6 个问题（2 个会直接跑挂）：
  - **CI 必挂**：`pnpm install --frozen-lockfile` 在无 pnpm-lock.yaml 时报错——改为 `pnpm install` 并注释 lockfile 提交策略
  - **根目录命令跑不通**：root workspace 未声明 server/cli 依赖，`uv sync` 后 `uv run uvicorn/CLI` 找不到包——root dependencies 补齐两者 + pytest testpaths 固定收集范围；生成 README 的错误命令（`task add`→`add`、electron 启动提示、.env 提示）一并修正
  - **verify 随产物分发**：scaffold 把 verify_project.py 复制进 `<项目>/scripts/`，CI 新增架构约束校验步骤（此前 output-spec 声称 CI 拦截但模板无此能力）；manifest 检查同步加该文件
  - 清理：web 未使用的 @tanstack/vue-query 依赖；文件数口径 42→43（pywebview）/45（electron）三处文档统一
- 回归：demo-app 干净重建 43 文件 → verify --test PASS → 根目录 uv sync 后 server/health、POST API、CLI add/list 全通且 CLI 可见 server 数据（共享 dev.db）→ electron 模式 verify PASS → validate_skill PASS

## 1.5.0 (2026-11-06)


- 第二轮审查（3 严重 + 2 轻微）修复落地，经本会话独立回归确认：
  - **数据库配置统一**：server 适配器改为读 `DATABASE_URL` 环境变量（默认 sqlite:///./dev.db，生产配 postgresql+psycopg://…），补 `psycopg[binary]` 依赖，docker-compose/.env.example 口径一致（原 SQLite/Postgres 自相矛盾）
  - **Dockerfile 修复**：从 monorepo 根构建、正确 COPY core 包源码（原以 apps/server 为构建上下文，缺 packages/core 必然失败）
  - **server repo.py**：消除 Task 重复 import（DomainTask 别名），清理未用的 session_factory
  - verify_project.py docstring 与禁止集合口径对齐（vite 表述）
- 独立回归证据：electron 模式重新生成 → verify --test PASS → 生成产物中 DATABASE_URL/psycopg/docker-compose 三处均在、全 Python 编译通过、无 DomainTask 残留 → validate_skill PASS
- 清理：`_test_e`（46 文件纯模板产物，与脚手架输出逐文件 diff 确认后删除）；同目录另有 `_test_demo`（733 文件/11M 含 .venv）待确认

## 1.4.1 (2026-11-06)

- 外部审查报告 P0-P4 逐条核实与处置：
  - P0 文档口径：scaffold.md"pydantic 可留作数据校验"已改为与 output-spec/architecture 统一（core dependencies 必须为空，pydantic 禁止）；P0 代码部分与 P1/P4 系旧版产物残留（demo-app 因 rm 静默失败未更新），当前模板 core deps=[]、CLI 自带 stdlib sqlite3 适配器、HttpTaskRepository 已转换 Task
  - P2 不成立：verify_project.py 中无 CORE_DEP_DECL
  - P3 不成立：design/README.md 本就标注 Apache 2.0，ui-ux-pro-max 有 LICENSE
  - **新发现真 bug 并修复**：verify_project.py 依赖检查只处理多行数组，漏检单行 `dependencies = ["pydantic>=2"]`——已改用正则整体解析（兼容两种写法），并用最小用例证明拦截生效
- demo-app 用当前模板重新生成，全链路回归通过：verify --test PASS、server /health+POST、CLI local 模式 add/list

## 1.4.0 (2026-11-06)

- 对标 anthropics/skills 官方模式（实地核查 19 个 skill + spec + template + skill-creator），新增：
  - `scripts/validate_skill.py`：skill 自校验（官方 quick_validate 同规则：frontmatter 六键白名单、name kebab-case ≤64、description ≤1024 无尖括号；附加 12 必需文件与 evals 结构检查）
  - `evals/evals.json`：官方格式 5 条评测（prompt + expectations 断言）
  - `references/anthropic-patterns.md`：官方放置/调用（渐进式披露三层）/整合（官方互不引用，组合在代理层）/模板与产物核查（skill-creator evals + mcp-builder 评估 harness）拆解与对照
  - 补 LICENSE 文件（validate_skill 首跑即抓到 frontmatter 声明 MIT 却无 LICENSE 的真实缺口，含 design/ 第三方许可声明）
- 已知差距：官方 run_eval.py 定量跑分体系未实现（需多轮代理执行环境），evals 供人工/会话内抽查

## 1.3.0 (2026-11-06)

- 新增 `scripts/verify_project.py`：生成项目验证器——结构完整性（42 文件清单）、核心纯净性（core 禁止 import 框架，AST 级检查）、依赖方向性、核心测试，一条命令判定产出是否合格
- 新增 `references/output-spec.md`：产出规范——固定产物清单、四条硬约束（C1-C4）、运行时验收证据链、演进期防腐约束
- SKILL.md 阶段 2 增加"生成后必须立即验证"步骤
- 实测：demo-app 生成 → verify PASS（含 --test）→ 注入违规 import 被 FAIL 拦截 → 移除恢复 PASS → server/CLI 全链路跑通

## 1.2.2 (2026-11-06)

- 命名调整：架构名称由「一核五端」改为「一核多端」（One Core, Multi-Client），不再固定端数量；文档中所有"五端"表述改为"各端/多端/所有端"，端组合按项目裁剪

## 1.2.0 (2026-11-06)

- 新增设计能力包 references/design/（vendor，均 MIT）：frontend-design（审美定调）、theme-factory（主题 token）、ui-ux-pro-max（设计系统检索数据 80 风格/192 配色/74 字体对）、animation-vocabulary + improve-animations（动效，Emil Kowalski 贡献）
- design/README.md 定义五步加载顺序与防冲突硬约束（token 唯一来源 / theme-factory 不碰布局 / impeccable 只在最后 / 动效克制 / uni-app 降级）
- impeccable 因上游无 LICENSE 不随包分发，改为 scripts/install_impeccable.sh 按需克隆
- 脚手架 web 模板新增 tokens.css（设计 token 唯一来源）并接入 App.vue；验收清单新增"设计质量"组
- 回归实测：electron 模式生成 + PY/JS 语法 + core 单测 + bash -n 全通过

## 1.1.0 (2026-11-06)

- 新增桌面端 Electron 选项：`scaffold.py --desktop electron` 生成 Electron 主进程 + Python sidecar（stdout 端口握手、/health 轮询、before-quit 进程回收、sidecar 同源伺服 web 静态资源）
- 修复：`/health` 路由移入 `create_app()` 工厂（sidecar 与 uvicorn 入口共用）
- 已实测：Electron 模式生成 43 文件、main.js/sidecar_entry.py 语法校验、sidecar 启动握手 + API 增查全通、core 单测通过

## 1.0.0 (2026-11-06)

- 首版发布：一核多端统一应用架构（CLI/Web/桌面/小程序/App）
- 基于公开资料调研的选型结论（桌面 pywebview vs Tauri vs Electron；跨端 uni-app vs Taro）
- scripts/scaffold.py 一键生成 Monorepo 骨架，已实测：core pytest 通过、server /health+增查 API 通过、业务规则 422 拦截通过、CLI local 模式增查通过
