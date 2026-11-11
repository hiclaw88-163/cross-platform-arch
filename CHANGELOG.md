# Changelog

## repo 2.0.4 (2026-11-11)

- tools/validate_skill.py 版本校验修正三种边界场景（原 regex 把 version 限定为
  metadata: 后第一个缩进子键、只剥双引号）：version 不是第一个子键 → 漏检改
  为正确比对；单引号值 → 误报改为正确剥除比对；metadata 块缺 version → 静默
  跳过改为 FAIL。CHANGELOG.md 不存在（校验仓库外目录）时跳过比对，无该 skill
  条目时报"无条目"。验证（临时仓库副本）：基线 5 skill 全 PASS；9.9.9 非
  首子键 → FAIL 指认；'1.1.4' 单引号匹配 → PASS；删 version → FAIL"缺少
  metadata.version"

## monorepo-scaffold 1.1.7 (2026-11-11)

- 收紧 CORS 默认值：`allow_origins=["*"]` 改为 `_cors_origins()`——`CORS_ORIGINS`
  环境变量逗号分隔，未设置时默认放行 Vite 开发端口（vite.config.ts 未改端口，
  默认 5173）的 localhost/127.0.0.1 两个来源；桌面离线模式 API 与页面同源伺服、
  不经 CORS，无需额外配置。生成 README「后续接入」补 CORS 说明。验证：默认/
  覆盖/空串三种取值输出正确；web 开发流程走 Vite 代理（同源），不受影响；
  verify --test PASS

## monorepo-scaffold 1.1.6 (2026-11-11)

- 移除 JWT_SECRET 死配置（实测全仓库无读取，用户身份为写死的 DEMO_USER，
  compose 却强制 `JWT_SECRET:?` 会让使用者误以为已有鉴权）：从 .env.example 与
  docker-compose.yml 删除；生成 README 新增「后续接入」一节写明"鉴权尚未实现，
  DEMO_USER 为占位"

## monorepo-scaffold 1.1.5 (2026-11-11)

- 桌面外壳健壮性四项（无桌面环境，静态检查 + 最小脚本模拟验证）：
  - Electron 离线模式 sidecar 产物名按平台选择（`process.platform === "win32" ?
    "server-sidecar.exe" : "server-sidecar"`），sidecar_entry.py 打包注释与
    apps/desktop/README.md 同步注明各平台产物名（原写死 .exe，macOS/Linux 不可用）
  - Electron spawn 失败补 `sidecar.on("error")`：error 是异步事件、外层
    try/catch 抓不到，现转为 sidecarError 变量在等待循环抛出，保证走到
    `dialog.showErrorBox("启动失败")`；sidecar 中途退出且窗口仍开时
    `on("exit")` 明确提示并退出（before-quit 置 quitting 标志避免误报）。
    验证：node --check 通过；最小脚本 spawn 不存在路径 → error 事件异步触发
    → 错误信息送达对话框路径
  - 打包后数据库不可写：Electron 离线启动 sidecar 时经环境变量传
    `DATABASE_URL=sqlite:///<userData>/app.db`（路径转正斜杠）；pywebview
    外壳离线模式用标准库方案（Windows APPDATA / macOS Library/Application
    Support / Linux XDG_DATA_HOME 回退 ~/.local/share）setdefault 数据库
    URL，开发模式默认值不变。验证：生成代码跑 `_default_db_url()` 得
    `sqlite:///C:/Users/…/AppData/Roaming/my-app/app.db` 且 create_engine
    connect 成功
  - pywebview 内嵌 server 等待循环加 15 秒超时（原 `while not server.servers`
    无超时会永久挂起），与 sidecar_entry.py 口径一致；线程存活检查兜底，
    超时/线程退出打印明确错误并 sys.exit(1)。验证：最小脚本复刻等待循环，
    线程启动失败 → 主线程报错 exit 1（不挂起）

## monorepo-scaffold 1.1.4 (2026-11-11)

- 修复 db 未就绪时 server 在导入阶段崩溃（实测：DATABASE_URL 指向不可达 Postgres，
  `import server.main` 抛 OperationalError）：仓储实例化与建表从模块导入期挪到
  应用启动期（FastAPI lifespan 里 init_db + 存 app.state，路由经 Depends 注入，
  不再导入 adapters；create_engine 本身惰性）。选择方案：**导入不连库，第一次
  真正请求数据时才报错**。docker-compose.yml 补 db healthcheck（pg_isready）、
  server `depends_on: condition: service_healthy` 与 `restart: on-failure`
  （compose 竞态为推断项，无 Docker 环境未实测）。验证：不可达 DB 下
  `import server.main` OK、pytest 通过、SQLite 基线全链路可用（创建/422 中文
  提示/列表）、verify --test PASS（契约探针导入不再需要数据库）

## monorepo-scaffold 1.1.3 (2026-11-11)

- 修复生成项目 `apps/server/Dockerfile` 构建必失败：原 COPY 只含根 pyproject 与
  core/server 源码、缺 `apps/server/pyproject.toml`，`uv pip install .` 触发
  "Workspace member is missing"。改为复制全部 workspace 成员的包定义（含
  apps/cli/pyproject.toml，仅定义不需源码），直接安装 `./packages/core
  ./apps/server`。uv 镜像 `latest` 固定为 0.13.7（注释说明可升级）；加非 root
  用户（useradd + USER，/app 归属应用用户）。验证：按 COPY 清单模拟复制后
  `uv pip install ./packages/core ./apps/server` 成功，`import server.main,
  my_app_core` OK

## arch-verify 1.1.4 (2026-11-11)

- 修复验收漏洞：显式传 `--test` 而核心测试因缺 uv 被跳过时，此前整体仍 PASS、
  exit 0——CI 会把"测试没跑"当成"测试通过"。改为 FAIL（exit 1），信息明确
  写出"--test 已指定但核心测试未能执行：未检测到 uv"；由 main() 统一升级，
  check_tests 不特殊处理。不带 --test 时行为不变：契约新鲜度缺 uv 仍 SKIP、
  无 engine 的六边形桥仍 SKIP。验证：有 uv --test PASS exit 0 / 无 uv --test
  FAIL exit 1 / 无 uv 不带 --test PASS exit 0
- 同步 monorepo-scaffold 同源副本（字节一致）

## arch-verify 1.1.3 (2026-11-11)

- 修复 Token 闭合检查误报：注释里的 var 引用（CSS 块注释 / TS 行首注释 /
  HTML 注释）被当成真实引用误 FAIL——注释掉的旧样式行是高频操作。新增
  _strip_comments（剥 `/* */`、`<!-- -->`、行首 `//` 整行），引用与定义
  统计均在剥注释后进行（tokens.css 里注释掉的变量定义同样不算数）。回归
  10 场景：3 类注释引用 0 违规、真实未定义引用仍拦截、注释内定义+引用
  拦截、嵌套兜底/行内定义/跨文件引用行为不变。同批次回归复核契约新鲜度
  5 场景（一致/漂移/占位/缺文件/恢复）全部正确，无需改动；同步
  monorepo-scaffold 同源副本（字节一致）

## arch-verify 1.1.2 (2026-11-11)

- 修复六边形桥检查误报：规约允许的规范导入形式 `from <engine>.bridge import X`
  与 `import <engine>.bridge`（含 `as` 别名）被 ast 判定误判违规（报错文案还与
  放行规则自相矛盾）。check_hexagonal 改为精确匹配规范形式——`<engine>.bridge`
  本体与 `from <engine>.bridge import`（仅 bridge 名）放行；`import <engine>`
  本体、`import <engine>.store` 等子模块、`from <engine>.bridge.sub import`
  （桥下更深模块）仍判违规。回归 7 场景：规范 3 形式 0 违规、违规 4 形式各
  拦 1 违规；同步 monorepo-scaffold 同源副本（字节一致）

## cross-platform-design 1.0.1 (2026-11-11)

- references/hexagonal-arch.md 快速自检：具名 CLI `open-work-kit-cli` 改为
  `<server-cli>` 占位（违反"项目特定值一律占位符"约定）；"五道门禁"改为
  "七项门禁（--test 含测试）"与 verify 实现一致
- references/tech-stack.md 去除时间性表述（README 约定：skill 正文无时间性表述）

## cross-platform-design 1.0.0 (2026-11-06)

- 初始版本：一核多端架构设计 skill（分层模型/端选型/六边形规约/契约流水线；
  SKILL.md + references + evals）——补记：此前 CHANGELOG 漏登初始条目

## legacy-rewrite 1.0.3 (2026-11-11)

- references/migration.md 清场规程：具名 `owk_engine` 改为 `<engine>` 占位；
  标题去除具体日期（时间性表述约定）

## arch-verify 1.1.1 (2026-11-11)

- 文件头检查清单与实现统一为 7 项 + --test 第 8 项（此前只列 5 项），并写明
  SKIP 语义
- check_empty_packages 文档字符串去具名项目（open-work-kit/owk_engine →
  `<engine>` 占位）、去具体日期
- output-spec.md 去时间性表述（"已实测记录（demo-app）"）

## project-docs 1.2.2 (2026-11-11)

- 修复规范编号冲突：生成的 `conventions/01-规范模板.md` 占用了 01 号，而
  规范索引把 01 路由给 `01-命名空间.md`；模板改用 `99-规范模板.md`（01-08
  留给项目真实规范），索引补路由行。验证：init_docs.py 重新生成，conventions/
  下编号无冲突

## project-docs 1.2.1 (2026-11-11)

- 「08-提交信息规范」模板同步提交钩子强制规则（详见 repo 2.0.3 条目）：
  单号必填、示例带单号、规则重排

## monorepo-scaffold 1.1.2 (2026-11-11)

- 同步 arch-verify 1.1.4 自检器同源副本（字节一致）：--test 被指定而核心测试
  因缺 uv 被跳过时判 FAIL，不再让 CI 把"测试没跑"当"测试通过"

## monorepo-scaffold 1.1.1 (2026-11-11)

- 自检器 vendoring 去跨 skill 运行时依赖：scaffold 自带同源副本
  scripts/verify_project.py（与 arch-verify 权威版本字节一致），运行时不再
  探测同侧 arch-verify skill 目录（独立性与版本漂移双保险）
- tools/validate_skill.py 增强生效：scripts/ 内脚本禁止引用兄弟 skill 目录
  （生成项目内部相对路径 ../web/dist 放行）；monorepo-scaffold 副本与
  arch-verify 权威版本字节一致性强制校验。验证：篡改副本 → 校验 FAIL，
  还原 → PASS
- 生成 README/SKILL 验证指引更新（项目内副本为首选路径）
- 生成 CLI 避免遮蔽内建 list：apps/cli 的 `def list(...)` 改为 `def list_(...)`
  并以 `@app.command("list")` 保持命令名不变。验证：重新生成后
  `uv run <name>-cli add/list` 正常
- install_impeccable.sh 移除写死的 `http.schannelCheckRevoke=false`（它会关闭
  Windows 证书吊销检查）；脚本/SKILL.md 保留"上游无 LICENSE"的显式说明
- references/design/README.md 补体积说明：ui-ux-pro-max 约 3.4MB 的来源
  （phosphor 图标索引/Google Fonts 元数据/许可证清单三份数据）与保留理由
  （离线自足），只评估未删数据

## repo 2.0.3 (2026-11-11)

- 修复「脚手架产物过不了自家门禁」：scaffold 补齐 `docs/design-decisions.md` 与
  `packages/sdk/src/gen/{schema.d.ts, openapi.sha256}`（脚手架放占位）；产出清单
  口径更新为 pywebview 50 / electron 52（含 vendoring 自检器）
- 提交钩子真正强制（详见 arch-verify 1.1.0 与 monorepo-scaffold 1.1.0 条目）：
  拒绝句号/超长（按字符计数）/缺单号；project-docs「08-提交信息规范」模板同步
  （单号必填、示例带单号、规则重排），project-docs 1.2.1
- 5 个 SKILL.md 移除 `author: WorkBuddy Agent`（README 格式约定无该字段）
- tools/sync.sh 与 sync.py 排除项对齐（__pycache__/.venv/node_modules/缓存与
  IDE 目录）
- generate.mjs 重写为离线探针（uv probe → 临时文件 → openapi-typescript），不再
  依赖运行中的 server；sha256(规范化 stdout) 写入 openapi.sha256，与 verify 的
  check_sdk_freshness 逐字同一条探针命令 + 同一换行规范化（CRLF→LF），Windows
  不再永远"契约漂移"
- 生成的 ci.yml 调整为 `uv sync → pnpm install → pnpm gen:sdk → verify → pytest
  → build:web`：先生成 SDK 与指纹再验收，首次 push 即绿
- 提交钩子可执行位修复：scaffold 写盘后对 `#!` 脚本与 `.githooks/*` 补 chmod +x，
  install_hooks.py 启用时幂等补 +x（zip/Windows 拷贝丢权限位曾让 Linux/macOS
  上钩子被 git 静默忽略）；仓库自身 `.githooks/commit-msg` 与
  `install_impeccable.sh` 的 git 索引模式 100644→100755
- package.sh 补可执行位（git 索引 100644→100755，`./package.sh` 不再
  Permission denied）；核对仓库全部 `#!` 脚本：`.sh` 与钩子均 100755，
  `.py` 均为 `python xxx.py` 调用、文档无 `./` 直执行写法，保持 644
- install_hooks.py 改为以 `git rev-parse --show-toplevel` 从 cwd 定位目标仓库：
  把 `.githooks/` 拷到其他仓库后，在该仓库里执行同样生效（原实现锁定脚本自身
  所在项目，拷贝场景必失效）
- Windows 实测：生成 → uv sync → pnpm gen:sdk → verify --test PASS；改 server
  路由不重生成 → 契约漂移 FAIL；electron 模式同样 PASS；生成的钩子在真实 git
  中拒绝非法提交信息（exit 1）、放行规范提交

## monorepo-scaffold 1.1.0 (2026-11-11)

- 新增产物：`docs/design-decisions.md`（ADR 最小模板）、`packages/sdk/src/gen/
  schema.d.ts`（占位）与 `openapi.sha256`（占位，verify 对占位值给出明确提示）
- generate.mjs 离线化：探针命令与 arch-verify 的 OPENAPI_PROBE_CMD 逐字一致；
  openapi-typescript 改经 createRequire 解析 bin 入口以 node 直接执行（Windows
  spawnSync("npx") 对 .cmd 垫片 ENOENT）
- 可执行位：写盘后对 `#!` 开头脚本与 `.githooks/*` chmod +x；install_hooks.py
  启用时幂等补 +x，并改为 cwd 的 git toplevel 定位目标仓库（拷贝场景生效）
- 生成 README/下一步提示补 `pnpm gen:sdk`（契约指纹步骤）

## arch-verify 1.1.0 (2026-11-11)

- check_dep_direction 重写：ast 扫描 packages/core/src/**/*.py 的 import（原来
  只搜 pyproject 文本，core 里写 `from server.main import app` 可漏过）；端包名
  从 apps/*/src/<包名> 与 apps/<端目录名> 动态推断，不写死；违规信息给出文件、
  行号与被引用的端。验证：core 注入 leak.py（from server.main import app /
  import cli）→ FAIL 且精确指认；删除后恢复 PASS
- check_core_purity 改白名单制：core 源码仅允许标准库+本包自身+相对导入
  （3.10+ 用 sys.stdlib_module_names，3.9 回退内置名单），黑名单仅用于违规
  归类提示；新增 importlib.import_module/__import__ 字符串字面量动态导入检测
- pyproject 依赖解析：tomllib（3.11+）优先、3.9/3.10 手写括号深度回退；包名
  规范化（PEP 503），正确处理 extras（pydantic[email]、~=、==、环境标记）。
  验证：四种绕过写法（extras/~= 动态导入/黑名单外框架）均 FAIL，原样 PASS
- check_hexagonal 重写：ast 解析端源码 import（原正则对 `from engine import
  (a, b)`/`from engine import bridge, store` 漏报），多名导入与 engine.store
  子路径都被拦下；多引擎包显式报错（不再依赖 iterdir 不确定顺序）；扫描
  apps/* 排除 .venv/node_modules/__pycache__
- 六边形桥检查显式 SKIP：无 packages/engine 的项目（如本仓库脚手架生成的
  core-only 拓扑）此前静默空跑却谎报"六边形桥闭合"；现在 main() 按检查项
  收集 (是否执行, 违规) 结构，PASS 行只列真正执行过的检查，无 engine 时输出
  "SKIP: 未发现 packages/engine，六边形桥检查未执行"。SKILL.md 检查清单同步
  修正。验证：无 engine 项目输出 SKIP 且不含"桥闭合"；fixture
  `from engine import bridge, store` → FAIL 指认 store
- check_sdk_freshness：探针改为参数列表常量 OPENAPI_PROBE_CMD（与 generate.mjs
  逐字一致，消除 shell 引号差异）；stdout 统一 CRLF→LF 后求哈希；对占位指纹给
  出独立提示（区别于真实契约漂移）；捕获 TimeoutExpired/FileNotFoundError 转
  明确 FAIL，不再让整个验收器崩溃
- 无 uv 优雅降级落地：shutil.which("uv") 缺失时契约新鲜度与核心测试输出 SKIP
  （带原因），不再误报 FAIL（此前报"无法导出 openapi"，与 CHANGELOG 1.0.1 的
  降级声明不符）。验证：受限 PATH 下 --test 输出三项 SKIP、其余 PASS
- check_token_closure 修正三处误报/漏报：定义匹配不要求行首（`:root{--a:1}` 行内
  定义曾被误判"未定义"）；先剥除 var(...) 调用再扫定义（防把 var 内部的 `--x,`
  当定义），兜底值引用 `var(--x, #fff)` 降级为 WARN 不 FAIL（含嵌套兜底）；扫描
  范围扩展到 .scss/.html/.ts/.tsx。验证：行内定义识别、兜底引用仅 WARN、ts
  未定义引用 FAIL、清理后恢复 PASS
- 提交钩子真正强制（与 README 既有声明对齐）：拒绝末尾句号（。/.）、主题超
  30 字由"仅提示"改为拒绝（UTF-8 按字符计数：优先 python3，回退 awk，替代
  C locale 下按字节误判的 wc -m）、单号必填（`feat: 主题` 被拒，无关联用
  [0]）。仓库 `.githooks/commit-msg` 与 scaffold 内嵌生成版本两处同源同步，
  README/生成 README/project-docs 08 模板措辞一致。验证：11 行输入矩阵
  （句号/句点/超长/缺单号/非法 type/bang/标准/关联单号/省冒号/边界）真实 git
  全部符合预期，merge/revert 放行
- output-spec.md：产出清单 46/48→49/51（+vendoring 50/52），补契约产物行与
  「无 node 环境补指纹步骤」说明

## repo 2.0.2 (2026-11-10)

- 接入提交信息规范（收编自 rfid-collector-app §13.1，泛化为通用约束）：
  `<type>:[<需求单号>]: <中文主题>`——单行、动词开头、≤30 字、不加句号；
  type 取 feat/fix/refactor/docs/chore/build/test；无关联需求的单号占位 `[0]`
- 本仓库内置 `.githooks/commit-msg` 强制校验并启用（README「格式约定」补记）；
  全部历史提交重写为规范格式

## project-docs 1.2.0 (2026-11-10)

- init_docs 新增生成 `conventions/08-提交信息规范.md`（与规范索引路由、
  AGENTS.md 编号路由同步）；生成 init_docs 改回退为字节写入（LF 保持）
- 文档骨架自此默认携带提交格式约束——AI 生成提交前先读 08

## monorepo-scaffold 1.0.2 (2026-11-10)

- 脚手架新增提交信息强制校验三件套：
  `.githooks/commit-msg`（commit-msg 钩子）+ `scripts/install_hooks.py`
  （纯 Python 启用器，修正 cwd 指向目标项目根）+ `scripts/setup_hooks.cjs`
  （pnpm postinstall 自动启用，失败不阻断安装）
- 生成器改字书写入保留 LF——Windows 生成的 sh 脚本不再被翻成 CRLF
- 生成项目 README 新增「提交与协作（强制）」节；evals 补提交格式期望；
  产出清单口径更新（模板 46/48 个，含 vendoring 自检器总计 47/49 个）

## arch-verify 1.0.2 (2026-11-10)

- verify_project.py 门禁清单纳入提交钩子三件套（缺任一即 FAIL），
  与 output-spec 产出清单同步

## repo 2.0.1 (2026-11-10)

- 新增 `tools/sync.py`：`sync.sh` 的纯标准库等价实现（Windows/无 rsync 环境可用），
  镜像语义（多余文件删除、缓存目录排除）与 `sync.sh` 一致，README 安装说明同步
- README 环境要求修正：Python 3.8+ → 3.9+（verify_project.py 用了 `str.removesuffix`）
- 删除工作区残留 `_test_demo/`（曾用于脚手架实测，gitignored 但不应长在仓库根）
- 新增 `docs/superpowers/specs/2026-11-10-hexagonal-gate-alignment-design.md`：
  六边形门禁对脚手架项目失效的方案对比（待评审后实施）

## arch-verify 1.0.1 (2026-11-10)

- verify_project.py 双修复：
  - Windows GBK 控制台防护——`✗/✓` 等符号编码失败曾让验收器在最需要输出 FAIL
    清单的时刻崩溃（UnicodeEncodeError）；现在不可编码字符降级为 `?`，中文照常
  - `--test` 在无 uv 的机器上优雅降级为明确 FAIL 提示，不再抛
    `FileNotFoundError` 崩溃
- output-spec.md 产出清单补充 vendoring 说明（43/45 模板 + 1 自检器）

## monorepo-scaffold 1.0.1 (2026-11-10)

- 修复 scaffold.py 的自检器 vendoring 路径（拆分提交 22338c7 把
  verify_project.py 移入 arch-verify 后遗留的回归）：现在按"本 skill 目录 →
  同侧 arch-verify skill"顺序探测复制，生成项目终含
  `scripts/verify_project.py`（此前每次生成都打警告、交付页 CI verify 必挂）
- 生成的 pywebview/Electron 打包注释补 Windows `--add-data` 分隔符说明
- playbook demo 命令漂移修正：
  `my-app task add` → `my-app-cli add`；`uvicorn server:app` → `uvicorn server.main:app`

## legacy-rewrite 1.0.2 (2026-11-10)

- migration.md 的 specs 产物命名对齐 project-docs 1.1.0 恢复后的权威格式：
  `{层级字母}-{NN}-{主题}.md`（例 `A0-01-旧系统知识资产.md`）→
  `L{层级}-{NN}{分册字母}-{主题}.md`（例 `L0-01-旧系统知识资产.md`，
  概述/实现配对 `L0-01i`，兄弟子文档 `L0-01j/k`）

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
