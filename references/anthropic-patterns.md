# anthropics/skills 官方模式拆解（2026-11-06 调研）

> 来源：github.com/anthropics/skills 仓库实地核查（README、spec/、template/、skill-creator、mcp-builder 等 19 个 skill）。
> 结论用于对照改进本 skill，官方规范全文在 agentskills.io/specification。

## 1. Skill 如何放置（placement）

官方仓库三层结构：

```
anthropics/skills/
├── skills/          # 19 个 skill，每个独立文件夹
│   └── <name>/      # 文件夹名 = skill 名（kebab-case）
│       ├── SKILL.md # 唯一必需文件（入口）
│       ├── references/  # 按需加载的深度文档
│       ├── scripts/     # 可执行工具（校验/评测/生成）
│       ├── examples/    # 可运行示例（webapp-testing）
│       ├── agents/      # 子代理定义（skill-creator 的 grader/analyzer）
│       └── LICENSE.txt  # 每个 skill 独立许可
├── spec/            # 只有一行：指向 agentskills.io/specification
└── template/        # 官方 skill 模板（SKILL.md 骨架，仅 6 行）
```

**放置原则**：自包含、零跨文件夹依赖；每个 skill 可独立拷走使用。发布渠道三种：Claude Code 插件市场（`/plugin marketplace add anthropics/skills`）、Claude.ai 上传 zip、API 传文件夹。

## 2. Skill 如何被调用（invocation）——渐进式披露

三层加载，上下文成本递增：

| 层 | 内容 | 何时进入上下文 |
|---|---|---|
| L1 | frontmatter 的 `description` | **常驻**——系统启动时所有 skill 的描述都在，用于触发匹配 |
| L2 | SKILL.md 正文 | 被触发后整篇载入 |
| L3 | references/、scripts/ | 正文里"按需引用"，用到才读 |

因此官方对 frontmatter 有硬规则（skill-creator/scripts/quick_validate.py 逐条校验）：
- 允许键仅 6 个：`name, description, license, allowed-tools, metadata, compatibility`
- `name`：kebab-case，≤64 字符，不得有非法连字符
- `description`：≤1024 字符、**不得含尖括号**——它是唯一的触发依据，必须写清"何时使用 + 何时不用"

## 3. Skill 如何整合（composition）

官方 skill 之间**互相不引用**——grep 全仓库，没有任何 SKILL.md 引用另一个 skill。组合发生在**代理层**：多个 skill 同时安装，代理按任务各自触发。官方模板也只有 6 行骨架，没有"依赖声明"机制。

这与我们不同：我们的 `references/design/` vendor 了 5 个外部 skill 并写了**显式加载顺序 + 防冲突硬约束**（design/README.md）。这是有意为之的偏离——设计子能力有严格的先后语义（先定调再落色再查规），不能靠代理自由裁量。代价是耦合，收益是确定性。

## 4. 模板 + 产物核查（evaluation）——官方有两套

### 4a. skill 本身的质量：skill-creator 的 evals 体系
- `evals/evals.json`：测试 prompt + expected_output + **expectations（可核验断言列表）**
- `run_eval.py` 跑测试 → `grader` 子代理按断言打分 → `aggregate_benchmark.py` 出通过率 → 版本对比（history.json，won/lost 迭代）
- 描述触发不准时用 `improve_description.py` 优化 description

### 4b. skill 生成产物的质量：mcp-builder 的 evaluation harness
mcp-builder（生成 MCP server 的 skill）自带 `scripts/evaluation.py` + `reference/evaluation.md`：
- 生成 10 个只读、可验证答案的测试问题
- 让无上下文的 LLM 仅用生成的 server 回答
- **产物质量 = LLM 不看文档也能用它的程度**，而不是代码写得多全

### 本 skill 的对应实现（已对齐）

| 官方机制 | 本 skill 对应 | 状态 |
|---|---|---|
| template/SKILL.md | scaffold.py（项目模板，比官方深一层：是可运行项目而非文档骨架） | ✅ 更强 |
| quick_validate.py | scripts/validate_skill.py（同规则 + 12 文件清单 + evals 结构检查） | ✅ 已落地 |
| evals.json | evals/evals.json（5 条中文评测，覆盖生成/选型/复用/核查/设计场景） | ✅ 已落地 |
| 产物评估 harness | scripts/verify_project.py（结构/纯净性/依赖方向/测试）+ output-spec.md 运行时验收链 | ✅ 对应 4b |
| run_eval.py 定量跑分 | 未实现（需多轮代理执行环境，WorkBuddy 场景下手动按 evals 抽查即可） | ⚪ 记为已知差距 |

## 5. 对照后的改进记录（v1.4.0）

1. 新增 `scripts/validate_skill.py` —— 首次运行即抓到真实问题：frontmatter 声明 MIT 但**没有 LICENSE 文件**，已补（含第三方声明：design/ 内 Apache 2.0 / MIT 各归其主）
2. 新增 `evals/evals.json` —— 官方格式的 5 条评测
3. 本文档 —— 官方模式与本 skill 的逐项对照
