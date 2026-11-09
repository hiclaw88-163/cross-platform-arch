# Changelog

## legacy-rewrite 1.0.1 (2026-11-10)

- 产出路径对齐 project-docs specs 体系：`docs/legacy-assets.md` →
  `docs/specs/legacy/{层级字母}-{NN}-{主题}.md`（层级前缀以项目 `specs/README.md`
  映射为准，如 `A0-01-旧系统知识资产.md`）；migration.md 与 evals.json 同步

## project-docs 1.1.0 (2026-11-10)

- **init_docs.py 生成 specs 入口 README**（新增 `templates/specs/README.md`）：
  默认 TOGAF 层级映射表 + 换前缀避让提醒 + 文档清单表，新项目开箱即符合 specs 命名标准
- **修复 00-项目配置 自指替换缺陷**（ai-marina 审计时发现）：变量定义表里的
  `{project}`/`{projectName}` 是变量名字面量，曾被 AUTO_VARS 一并替换成项目名
  （生成 `| ai-marina | ai-marina |` 自指行）；新增 NO_AUTO_REPLACE 排除该文件，
  变量值留待人工在唯一变量入口填写

- **补 specs/guides 文件命名规范缺口**（ai-marina 落地时暴露：specs 下混出
  PROPOSAL/ARCHITECTURE/DESIGN/legacy-assets 四种类型前缀，编号各自为政）；
  guides/ 文件命名 `NN-主题.md`（目录内递增编号）；类型前缀禁止与编号规则见
  下条 specs 恢复条目及 structure.md
- **specs 命名恢复 keshumai 原生格式**（用户核对原文后纠正：规范权威源是 keshumai
  `specs/architecture/README.md` §1，字母序号在 NN 前）：`L{层级}-{NN}{分册字母}-{主题}.md`
  - `L{层级}`：TOGAF 对齐参考映射 L0 项目管理/L1 架构愿景/L2 应用架构/L3 技术架构/
    L4 详细设计/L5 实现规范/L6 部署运维；层级字母↔子目录映射由项目自定并写入 specs 入口 README；
    项目已有 `L{N}` 语义占用时（如产品能力分层）必须换前缀字母
  - `{NN}`：层级内两位递增；分册字母在 NN 后主题前——概述/实现配对共享数字加 `i`，
    兄弟子文档 `j/k/l`，同号并行文档须目录 README 标注
  - 初版收编时误将 L 前缀记为"有意省略"，本轮以 keshumai 原文为准恢复
- **补齐分册字母规则**（收编时只在 conventions/ 段保留，specs/guides 段遗漏）：
  conventions 分册仍为字母后缀 `02a-`（主册过载拆分，keshumai conventions 实例：
  `02-后端工程结构` + `02a-api契约` + `02b-srv分层` + `02c-framework`），
  拆分时同步更新 AGENTS.md 编号路由
- structure.md 同步更新；ai-marina docs 为首个按新规范重命名的项目

## 2.0.0 (2026-11-10) — breaking

单 skill 拆分为 4 个独立 skill（方案 A，按工作流阶段拆分）：

- `cross-platform-design`（架构设计与评审）— 收编原核心原则、阶段1 需求定位、
  关键决策速查表与 architecture/hexagonal-arch/clients/tech-stack/reuse 五份规约
- `monorepo-scaffold`（从零搭建）— 收编原阶段2 脚手架生成、阶段3 演示链路、
  阶段3.5 设计系统与 scaffold.py/playbook/design 能力包
- `arch-verify`（机器门禁验收）— 收编原 verify 七项检查、verify_project.py 与 output-spec.md
- `legacy-rewrite`（存量重写接入）— 收编原阶段2.5 定性反转与 migration.md

配套变更：

- evals 按 skill 拆分（eval 2→design，1/5→scaffold，4/7→verify，3/6→legacy）
- validate_skill.py 迁入 tools/ 并改造：批量模式（自动发现所有 skill）+ 引用闭合检查
  （SKILL.md 中引用的本地路径必须存在、../ 跨 skill 引用目标目录必须存在），evals.json 检查改为可选
- 新增 tools/sync.sh：整组同步所有 skill 到 ~/.claude/skills/（自动发现，新增 skill 零改动）
- anthropic-patterns.md 移入 docs/（元知识，非业务 skill 内容）
- 各 skill **完全独立、互不依赖**（anthropics/skills 形态）：禁止 `../` 跨 skill 文件引用，
  validate_skill.py 强制校验；skill 间只有语义配合（scaffold 产出清单与 verify 检查项的
  单一事实来源定为 arch-verify/references/output-spec.md）
- 各 skill 版本自 1.0.0 独立起步；本 CHANGELOG 继续记录整个仓库

## 1.8.0 (2026-11-10)

- **migration.md 由「存量项目移植规范」改名为「存量项目重写接入规范」**:
  "移植"一词实测会诱导 AI 把旧代码整体搬进新仓库（本次真实发生: ai-marina
  项目初期文档按"移植"叙事产出映射表, 用户及时叫停）。核心定性反转:
  **旧项目 = 协议字典 + 行为验收 oracle, 不是代码来源**。
  - 新增「核心裁定」: 搬旧文件（含改名式复制）= 把旧架构弊端原样带进来,
    等于白换架构; 旧项目只扮演协议字典/验收 oracle/教训清单三个角色;
  - **第 4 步从"技术能力保持原样搬入适配器"改为"按协议重写"**——原文与
    "搬运 ≠ 移植"自相矛盾, 是诱导全量抄的根源; 协议知识提炼为版本化
    PROTOCOL.md, 实现按新端口契约重写;
  - 第 1 步新增「表 B · 旧弊端 → 新解法对照」: 没有它, "为什么换架构"
    会在实现过程中被遗忘, 弊端随"照着旧代码写"悄悄复活;
  - 第 5 步验收新增两条: grep 不得出现旧仓库复制来的实现; 行为一致性
    对照（新旧系统同输入同结果）;
  - 新增判断口诀 2: "这段代码是从旧仓库复制来的吗?" 是 → 打回。
  - SKILL.md 阶段 2.5 同步改写; output-spec C6 措辞同步。
  - 落地范本: ai-marina `docs/legacy-assets.md`（协议字典/验收基准/带与不带清单）。

## 1.7.2 (2026-11-07)

- **verify 新增"无空包残留"门禁(check_empty_packages)**: `packages/*/src` 下任何
  全空目录一律 FAIL。背景是真实事故——重构把 `owk_engine/store` 改名 `ledger`
  但旧目录留着,Python 3 把空目录当命名空间包,`from owk_engine import store`
  **导入成功却什么都没有**,`AttributeError` 落进 best-effort 的 `except` 被吞,
  台账静默丢失一整天而 CLI 输出完全正常。
  该检查上线后立刻在同项目抓出另外 5 个改名残留空目录
  (`apps/qoder`、`apps/doubao_cn`、`apps/workbuddy_cn`、`kit`、`domainsignin`、
  `scheduledomain`),均已清除。
- **migration.md 新增「改名/重构后的清场规程」**: 搜旧名残留 → 删目录本身 →
  verify 复检 → best-effort 路径必须留痕 → 副作用要有"真的写进去了"的测试。

## 1.7.1 (2026-11-07)

- **verify 新增契约新鲜度门禁(check_sdk_freshness)**: generate.mjs 生成时写入
  openapi.json 的 sha256 指纹(src/gen/openapi.sha256),verify 重算比对——"改了后端
  没重新生成 SDK"当场 FAIL。已用注入测试验证: 给 response_model 加一字段即触发
  "契约漂移"。manifest 同步要求 schema.d.ts 与 openapi.sha256 入库。
  背景: generate.mjs 曾躺平数周未被任何检查发现——文件存在 ≠ 流程生效。

## 1.7.0 (2026-11-07)

open-work-kit 包结构审计（旧项目平移 vs 框架原生）暴露的规范缺口补齐：

- **新增 references/hexagonal-arch.md（六边形架构规约）**：R1-R9 带编号规则清单，
  每条标注验证方式与豁免流程（design-decisions 留痕）；分层拓扑与阿里 COLA
  （adapter/app+domain/infrastructure/client/start）逐层对照，模型分层 DO/DTO/VO
  对照《阿里巴巴 Java 开发手册》§分层领域模型。engine 出站适配器按**能力词汇**命名
  （signin/ledger/scheduling/adapters/declarative/extensions），禁止旧业务目录名平移
  （真实案例：kit/domainsignin/scheduledomain 平移改名后仍读不出架构语义，二次重排）。
- **新增 references/clients.md（apps/ 多端规约）**：端=三件事（协议转换/呈现/端能力桥接）
  的薄壳纪律；端间关系矩阵（唯一豁免：desktop 内嵌 server 启动装配）；共享代码
  "三处同构必须下沉"分流表（语义→core / 契约→sdk / 能力→engine）；各端目录模板与
  附加纪律；多端一致性验收门禁（幂等/dry_run 语义全端一致）。
- **verify_project.py 新增检查：六边形桥闭合（check_hexagonal）**——①引擎必须有
  bridge.py 唯一出桥；②各端只许 `from <engine>.bridge import`，直接触达引擎内部
  子包即 FAIL；③端间禁止互相 import（desktop→server 白名单）。理由：此类违规不崩
  构建，数月后才以语义漂移形式爆发。
- SKILL.md 参考文件挂载两份新规约。
- 经验教训沉淀：文件存在 ≠ 流程生效（generate.mjs 躺平未被 verify 发现 →
  manifest 增加 schema.d.ts 生成物检查）；设计决策文档必须随主题变更同步升版。

## 1.6.0 (2026-11-06)

真实落地项目（open-work-kit）运行调试暴露的 skill 缺口集中修复：

- **新增 references/migration.md（存量项目移植规范）**：真实事故复盘——旧引擎 8k 行整体搬进适配器层、core 只剩 195 行薄壳，业务规则散落外圈，导致"dry_run 试运行静默降级成真实执行"缺陷。规范给出搬运 vs 移植对照、五步流程（功能清单分析→领域词汇提取→编排语义上移→技术能力留适配器→端零映射验收）、机器可查红线。SKILL.md 新增阶段 2.5 挂载。
- **verify_project.py 新增检查项 4：Token 引用闭合**——web 端引用的每个 `var(--x)` 必须在 tokens.css（或引用所在文件）定义。真实事故：tokens.css 缺 `--space-5/--font-size-*/--color-accent` 等被引用的 token，样式残缺但零报错，页面"安静地变丑"。manifest 同步加 `docs/design-decisions.md`（阶段 3.5 必产物）。
- **阶段 3.5 设计包流程升级为"必执行，不许跳过"**：tokens.css 全量 token + design-decisions.md 列为必产物（缺一 verify FAIL）——此前只在注释里"建议"，真实项目生成时被跳过。
- **evals.json 5→7**：新增"移植类任务必须产出映射表且防薄壳"（id 6）与"样式不完整→token 闭合诊断"（id 7）两条评测。
- SKILL.md 版本 1.6.0；output-spec.md 产出清单补 design-decisions.md、新增 C5（Token 闭合）/C6（语义决策只在一处）硬约束。

## 1.5.2 (2026-11-06)

- **修复 web 模板缺 tsconfig.json**(真实项目首次 pnpm build:web 即挂,CI 同样会挂): 模板新增标准 tsconfig;build 脚本 `vue-tsc -b`(需 project references)改为 `vue-tsc --noEmit`
- **修复 verify_project.py manifest 硬编码演示文件名** `test_task.py`: 改为"tests 目录至少一个 test_*.py"(真实项目重命名领域模块后误报缺文件)
- 首个真实落地项目验证: open-work-kit(auto-signin-kit 功能移植)——生成→engine 扩展包→verify PASS→web build PASS→CLI/Server/看板全链路实测

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
