---
name: arch-verify
description: 一核多端项目的机器门禁验收：verify_project.py 七项检查 + 产出规范与质量门禁清单。TRIGGER when 验收或检查项目是否符合一核多端架构要求、把架构约束交给机器判定、诊断"页面样式不完整/间距颜色没生效"这类 token 未定义问题；DO NOT TRIGGER when 从零生成新项目（用 monorepo-scaffold）、修改架构规范本身（用 cross-platform-design）。
license: MIT
metadata:
  version: "1.1.4"
---

# 一核多端项目机器门禁验收

## 用法

```bash
python scripts/verify_project.py --project /path/to/my-app --test
```

## 七项检查（--test 时加跑第 8 项核心测试）

1. **结构完整性**——含设计决策记录 `docs/design-decisions.md`。
2. **核心纯净性**——`packages/core` 只允许标准库 + 本包自身（白名单制，含动态导入检测）。
3. **依赖方向性**——core 源码不得 import 任何端（ast 扫描 import）。
4. **Token 引用闭合**——web 引用的 `var(--x)` 必须有定义（扫描 `.css/.scss/.vue/.html/.ts/.tsx`，定义可出现在任意位置）；带兜底值的引用未定义仅 WARN。样式残缺不报错不崩构建、页面安静变丑，必须机器判定。
5. **六边形桥闭合**——各端只许 `from <engine>.bridge import` 触达引擎；项目没有 `packages/engine` 时该项显式 SKIP（PASS 行只列真正执行过的检查，不谎报"桥闭合"）。
6. **契约新鲜度**——后端改了没重新生成 SDK（openapi.sha256 指纹漂移）→ FAIL。
7. **无空包残留**——改名后留下的空目录会被 Python 当成命名空间包，让 `from X import Y` 假成功、内部 `AttributeError` 被吞——台账/日志类副作用会静默丢失。
8. **核心测试通过**（仅 `--test`）——因缺 uv 等原因未能执行时判 **FAIL**（"测试没跑"不能被当成"测试通过"）；其余 SKIP 项（无 engine 的六边形桥、缺 uv 的契约新鲜度）保持 SKIP 不算失败。

任何一项 FAIL 必须先修复再继续后续流程。

## 产出规范

文件清单、硬约束、运行时验收证据链见 `references/output-spec.md`。

本文件清单是**单一事实来源**：monorepo-scaffold skill 的脚手架产出必须与本清单对齐，
脚手架变更时同步更新本清单。

## 配套 skill（语义配合，无文件依赖）

- **monorepo-scaffold** — 其脚手架生成后必须立即运行本 skill 的 verify_project.py
- **cross-platform-design** — 架构设计规约来源
- **legacy-rewrite** — 存量项目重写接入的项目，验收时额外执行其"端零映射 + 行为一致性"检查
