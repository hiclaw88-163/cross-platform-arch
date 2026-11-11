---
name: legacy-rewrite
description: 存量项目重写接入「一核多端」架构的规约：旧项目是协议字典+行为验收 oracle，不是代码来源。TRIGGER when 把已有项目/旧系统的功能用一核多端架构重新实现、评估旧代码怎么迁移、需要产出功能归属映射表或旧弊端对照表；DO NOT TRIGGER when 从零新项目（用 monorepo-scaffold）、纯架构设计问答（用 cross-platform-design）、常规项目验收（用 arch-verify）。
license: MIT
metadata:
  version: "1.0.3"
---

# 存量项目重写接入

旧项目**不是代码来源，是协议字典 + 行为验收 oracle**——任何把旧文件搬进新仓库的动作（含改名式复制）都会把旧架构的弊端原样带进来，等于白换架构。必须先产出功能归属映射表 + 旧弊端对照表，把协议知识提炼为 PROTOCOL.md，然后按新端口的契约重写实现；旧系统只用来做行为一致性对照。

## 五步流程与薄壳反模式

五步流程、功能→归属映射表、"薄壳反模式"对照与真实事故复盘见 `references/migration.md`。

此类项目在验收时，除常规机器门禁（arch-verify skill 的 verify_project.py）外，额外执行"端零映射 + 行为一致性"检查（grep 不得出现旧仓库复制来的实现；新旧系统同输入同结果）。

## 配套 skill（语义配合，无文件依赖）

- **monorepo-scaffold** — 从零搭新项目（无存量时用）
- **arch-verify** — 机器门禁验收（本项目额外叠加端零映射+行为一致性检查）
- **cross-platform-design** — 架构设计规约来源
