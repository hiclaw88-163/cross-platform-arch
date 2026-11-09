# 设计能力包（design pack）

本目录是「一核多端」架构 skill 内置的**提示词知识库**（非代码依赖），让脚手架产出的项目不仅"能用"而且"好看、不撞脸"。全部为文本驱动的 SKILL.md + 数据文件，随本 skill 一起被 agent 按需加载。

## 来源与许可

| 子能力 | 来源仓库 | 许可 | 版本基线 |
|---|---|---|---|
| `frontend-design/` | anthropics/skills | Apache 2.0（见包内 LICENSE.txt） | 2026-11 main |
| `theme-factory/` | anthropics/skills | Apache 2.0（见包内 LICENSE.txt） | 2026-11 main |
| `ui-ux-pro-max/` | nextlevelbuilder/ui-ux-pro-max-skill | MIT（仓库 skill.json） | v2.15.0 |
| `animation-vocabulary/`、`improve-animations/` | anthropics/skills（Emil Kowalski 贡献） | Apache 2.0 | 2026-11 main |
| impeccable（**未 vendor**） | pbakaus/impeccable | **仓库无 LICENSE**，不可复制分发 | 按需用 `scripts/install_impeccable.sh` 克隆 |

## 加载顺序（生成/精修前端时严格按此执行）

```
1. frontend-design   定调：审美方向、字体人格、反模板化（最先加载，输出"设计决策"）
2. theme-factory     落色：从 10 个预设主题选一或生成新主题 → 输出颜色/字体 token
3. ui-ux-pro-max     查规：按 Priority 1→10 查可访问性/交互/布局规则与反模式，
                     用 --domain <Domain> 检索数据（80 风格/192 配色/74 字体对）
4. improve-animations / animation-vocabulary（可选）动效：仅对关键交互加动效，克制
5. impeccable（可选，未内置）精修：/audit 体检 → /polish 精修（最后执行）
```

## 防冲突规则（给 agent 的硬约束）

1. **token 唯一来源**：颜色/字体/间距 token 由 theme-factory 产出并写入 `apps/web/src/styles/tokens.css`；ui-ux-pro-max 检索到的配色只做参考校验，**不得**绕过 tokens.css 直接写硬编码色值。
2. **theme-factory 只管 token，不管布局**：不得让它覆盖 frontend-design 的结构/排版判断；frontend-design 先行定调，theme-factory 在其框架内选色。
3. **impeccable 命令词显式化**：它有自己的 `/audit`、`/polish` 命令，只能在本 skill 流程的"第 5 步"调用，不得在生成阶段调用，也不得与 ui-ux-pro-max 的规则检查交叉执行（先查规后精修）。
4. **动效克制**：仅 `improve-animations` 允许引入动效；列表/表单等常规页面零动效；所有动效尊重 `prefers-reduced-motion`。
5. **uni-app 端降级**：小程序/App 端只应用 tokens.css 的颜色与字号变量（通过条件编译），GSAP 等 Web 动效方案不进小程序。

## 在本架构流程中的挂载点

- **P2（Web 端）**：生成页面结构前先走 1→2→3，产出 tokens.css + 一段"设计决策记录"（写入 `docs/design-decisions.md`），再写组件。
- **P4（uni-app）**：只同步 tokens.css 变量。
- **P5 / 验收**：跑 ui-ux-pro-max 的规则检查（对比度/触达尺寸/焦点态）；需要更高品质时按需安装 impeccable 跑 `/audit`。

## impeccable 按需安装（不随本 skill 分发）

```bash
bash <本skill>/scripts/install_impeccable.sh ~/.claude/skills
```
脚本仅做 `git clone --depth 1` 并提示来源；是否使用由使用者决定。
