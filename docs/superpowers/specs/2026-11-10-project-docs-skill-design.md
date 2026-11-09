# 设计文档：project-docs skill（项目文档体系标准 + 脚手架）

日期：2026-11-10
状态：已确认（方案 A：独立 skill，规约 + init_docs.py 脚手架）
素材来源：`/Users/jason.zhuo/codes/zuoyou/keshumai-repos/backend/keshumai-docs`（唯一 grounding，零杜撰）

## 硬规则（用户指定，全 skill 适用）

1. **禁止杜撰**：所有结构/格式/纪律只从 keshumai-docs 实际存在的文件与写法提炼，不添加该体系中没有的内容。
2. **无时间信息**：SKILL.md 不含 date 元数据与"20xx 调研"类时间串；模板中日期一律 `{date}` 占位符。
3. **无写死路径**：任何项目特定值（项目名/包名/磁盘路径/机器名）一律 `{占位符}`，唯一入口是 `00-项目配置.md`。

## skill 结构

```
project-docs/
├── SKILL.md              # 触发词 + 目录标准总览 + init_docs.py 用法 + 纪律索引（短）
├── references/
│   ├── structure.md      # 目录标准：每类目录放什么/不放什么
│   ├── templates.md      # 各类文件写法纪律（含格式规范）
│   └── governance.md     # 治理规则：唯一事实来源、冲突优先级、升版、链接有效性
├── templates/            # 可直接拷贝的模板，全部 {占位符}，零写死内容
│   ├── AGENTS.md / README.md / TODO.md
│   ├── conventions/（00-项目配置.md、规范索引.md、规范模板.md）
│   └── adr/ADR-模板.md
├── scripts/init_docs.py  # --name --dir [--force]：生成骨架 + 替换 {project}/{projectName}
└── evals/evals.json
```

## 目录标准（收编自 keshumai-docs）

conventions/（编号强制规范，00-项目配置=唯一变量入口）、specs/（设计规格，按架构层级分子目录）、adr/（ADR-编号-标题）、guides/（操作指南）、plans/（交付计划）、scripts/（文档配套脚本）、AGENTS.md（AI 任务路由）、README.md（导航）、TODO.md（执行待办）。

## 写法纪律（全部来自 keshumai 实例共性）

- 变量唯一入口 00-项目配置.md；规范 frontmatter name/description(TRIGGER)/version/level(must)
- 冲突优先级声明"本文 > 上级摘要 > 通用默认"（keshumai 01-命名空间原文模式）
- 规范索引三段式：关系声明 + 使用前必读 + 快速路由表
- AGENTS.md 编号任务路由（"起模块→读01"模式）
- ADR 格式：frontmatter + 状态/{date}/决策者/关联 + 背景/决策/后果(正面/负面)
- TODO 双轨：TODO.md 管"要做"、缺口清单管"缺不缺"
- 反引号路径引用需可校验（keshumai check-backtick-paths 实践）

## 触发词（互斥）

TRIGGER：新建项目文档体系、整改散乱文档、写 AGENTS.md/规范索引/ADR/项目配置
DO NOT TRIGGER：代码工程脚手架（monorepo-scaffold）、架构设计问答（cross-platform-design）、单篇业务文档正文

## 实施清单

1. 建 project-docs/ 结构，写 SKILL.md + 3 份 references
2. 写 6 份模板（全占位符）
3. 写 init_docs.py（stdlib，占位符替换，剩余占位符打印提醒）
4. evals 2 条
5. README 总览表加一行
6. 验证：validate_skill.py PASS；init_docs.py 生成到临时目录、{project}/{projectName} 已替换、无写死路径/时间串；提交推送
