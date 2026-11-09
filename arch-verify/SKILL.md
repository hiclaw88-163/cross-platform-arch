---
name: arch-verify
description: 一核多端项目的机器门禁验收：verify_project.py 七项检查 + 产出规范与质量门禁清单。TRIGGER when 验收或检查项目是否符合一核多端架构要求、把架构约束交给机器判定、诊断"页面样式不完整/间距颜色没生效"这类 token 未定义问题；DO NOT TRIGGER when 从零生成新项目（用 monorepo-scaffold）、修改架构规范本身（用 cross-platform-design）。
license: MIT
metadata:
  version: "1.0.0"
  date: "2026-11-10"
  author: WorkBuddy Agent
---

# 一核多端项目机器门禁验收

## 用法

```bash
python scripts/verify_project.py --project /path/to/my-app --test
```

## 七项检查

1. **结构完整性**——含设计决策记录 `docs/design-decisions.md`。
2. **核心纯净性**——`packages/core` 禁止 import 任何框架（"一核多端"铁律）。
3. **依赖方向性**——核心不得反向依赖任何端。
4. **Token 引用闭合**——web 引用的 `var(--x)` 必须在 tokens.css 定义。样式残缺不报错不崩构建、页面安静变丑，必须机器判定。
5. **六边形桥闭合 + 契约新鲜度**——各端只许 `from <engine>.bridge import`；后端改了没重新生成 SDK → FAIL。
6. **无空包残留**——改名后留下的空目录会被 Python 当成命名空间包，让 `from X import Y` 假成功、内部 `AttributeError` 被吞——台账/日志类副作用会静默丢失。
7. **核心测试通过**。

任何一项 FAIL 必须先修复再继续后续流程。

## 产出规范

文件清单、硬约束、运行时验收证据链见 `references/output-spec.md`。

本文件清单是**单一事实来源**：`../monorepo-scaffold/` 的脚手架产出必须与本清单对齐，
脚手架变更时同步更新本清单。

## 与其他 skill 的关系

- 从零搭新项目：`../monorepo-scaffold/`（其脚手架生成后必须立即运行本 skill 的 verify_project.py）
- 架构设计规约来源：`../cross-platform-design/`
- 存量项目重写接入的项目：验收时额外执行 `../legacy-rewrite/` 的"端零映射 + 行为一致性"检查
