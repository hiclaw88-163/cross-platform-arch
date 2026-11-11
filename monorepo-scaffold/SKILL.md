---
name: monorepo-scaffold
description: 从零搭建「一核多端」Monorepo 项目：脚手架生成、OpenAPI 契约打通各端 TS SDK、演示链路跑通、设计系统生成。TRIGGER when 新建一核多端项目、生成 Monorepo 骨架、打通 OpenAPI 契约到各端 SDK、页面太丑要升级设计系统；DO NOT TRIGGER when 只做架构设计或选型问答（用 cross-platform-design）、旧项目功能迁移（用 legacy-rewrite）、仅验收已有项目（用 arch-verify）。
license: MIT
metadata:
  version: "1.1.0"
  author: WorkBuddy Agent
---

# 从零搭建「一核多端」Monorepo 项目

## 脚手架生成

直接运行本 skill 自带脚本生成 Monorepo 骨架：

```bash
python scripts/scaffold.py --name my-app --dir /path/to/my-app
# 桌面端想用 Electron：--desktop electron（生成 Electron 主进程 + Python sidecar 模板）
```

生成内容：`apps/server`（FastAPI）、`apps/cli`（Typer）、`apps/web`（Vue3+Vite）、`apps/desktop`（pywebview 壳，或 `--desktop electron` 时生成 Electron 主进程 + sidecar 入口）、`apps/uniapp`（小程序+App 占位）、`packages/core`（六边形分层核心）、`packages/sdk`（OpenAPI 生成脚本）、docker-compose、CI 配置、**提交信息强制校验**（`.githooks/commit-msg` 钩子 + `pnpm install` 自动启用）。结构与关键文件说明见 `references/scaffold.md`。

## 生成后必须立即验证（把架构约束交给机器判定）

运行 **arch-verify** skill 自带的 verify_project.py（该 skill 独立安装，按其实际安装路径执行）：

```bash
python <arch-verify 安装目录>/scripts/verify_project.py --project /path/to/my-app --test
```

七项检查（结构完整性 / 核心纯净性 / 依赖方向 / Token 引用闭合 / 六边形桥闭合+契约新鲜度 / 无空包残留 / 核心测试）详见 arch-verify skill。任何一项 FAIL 必须先修复再进入下一步。

## 跑通演示链路

按 `references/playbook.md` 的演示脚本执行：实现一个最小用例（示例为"任务管理"），验证各端可见同一份数据：

1. CLI：`my-app task add "hello"` → SQLite 落库
2. Web：页面列表出现该任务
3. 桌面：pywebview/Electron 窗口内同一列表
4. 小程序/App：HBuilderX 运行到模拟器，同一列表
5. 修改核心包一处业务规则 → 所有端行为同时变化（证明"一核"）

## 设计系统生成（前端不止于"能用"——必执行,不许跳过）

内置设计能力包（`references/design/`，均为 MIT 许可的提示词知识库），**严格按加载顺序**执行：

1. `frontend-design/` 定审美方向与字体人格（反模板化）
2. `theme-factory/` 选/生成主题 → 覆写 `apps/web/src/styles/tokens.css`
3. `ui-ux-pro-max/` 按优先级查可访问性/交互/布局规则与反模式
4. `improve-animations/`（可选）关键交互动效，尊重 prefers-reduced-motion
5. impeccable 精修（**未内置**，仓库无 LICENSE；需要时运行 `scripts/install_impeccable.sh` 按需克隆后 `/audit` → `/polish`）

**必产物（缺一即 FAIL，verify 会查）**：

- `apps/web/src/styles/tokens.css` —— 颜色/字体/间距/字号 token 全量定义；组件与样式表引用的每个 `var(--x)` 必须在此（或本文件）有定义（verify 检查项 4）
- `docs/design-decisions.md` —— 设计决策记录（主题定位/配色出处/字体/布局/动效/可访问性），保证审美选择是"决策"而非"默认"

防冲突硬约束（token 唯一来源、theme-factory 不碰布局、impeccable 只在最后）见 `references/design/README.md`。uni-app 端仅同步颜色/字号变量。

## 参考文件

- `references/scaffold.md` — Monorepo 目录结构与关键文件逐个说明
- `references/playbook.md` — 分阶段实施计划、演示脚本、验收清单
- `references/design/` — 设计能力包（frontend-design / theme-factory / ui-ux-pro-max / 动效×2，均 MIT；README 含加载顺序与防冲突规则）
- `scripts/scaffold.py` — 一键生成 Monorepo 骨架（`--desktop electron` 切桌面壳）
- `scripts/install_impeccable.sh` — 按需克隆 impeccable 精修 skill（上游无 LICENSE，不随本 skill 分发）

## 同步警示

本 skill 的脚手架产出清单与 **arch-verify** skill 的检查项必须对齐。**单一事实来源是
arch-verify 的产出规范文件 output-spec**——改脚手架产出（新增/删除生成文件）
时必须同步该清单，否则机器门禁会误报或漏报。

## 配套 skill（语义配合，无文件依赖）

- **cross-platform-design** — 架构设计与选型问答
- **arch-verify** — 生成后验收（生成后必须立即运行其 verify_project.py）
- **legacy-rewrite** — 旧项目功能重写接入
