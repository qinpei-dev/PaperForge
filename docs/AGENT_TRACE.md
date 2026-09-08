# Agent Trace

`agent_trace` 是 PaperForge 的工程执行轨迹，用来解释 Agent 做了哪些任务、调用了哪些工具、为什么 fallback、是否需要人工复查，以及当前结果的规则置信度。

Agent Trace 不是 LLM 思维链。它不记录模型隐藏推理，也不尝试展示“内心过程”。它是可审计的工程日志，来自确定性的后端流程和规则判断。

## 字段说明

### task_plan

Agent 的任务计划和执行状态。

典型任务：

- `classify_document`
- `analyze_before`
- `extract_template`
- `format_document`
- `language_review`
- `analyze_after`
- `generate_report`

每个任务包含：

- `id`
- `label`
- `tool`
- `required`
- `status`
- `summary`

### tools_used

实际调用过的工具列表。

示例工具：

- `document_classifier.classify_document`
- `docx_analyzer.analyze_docx`
- `template_extractor.extract_template_profile`
- `docx_formatter.apply_paper_format`
- `language_reviewer.review_language_with_status`
- `report_generator/build_modification_report`

### agent_decision

Agent 的工程决策摘要。

包含：

- `mode`：`local` 或 `ai`
- `document_type`：文档分类结果
- `template_strategy`：模板策略
- `format_strategy`：格式处理策略
- `language_strategy`：语言审校策略
- `review_strategy`：人工复查策略

`review_strategy` 当前支持：

- `user_confirmation_required`
- `manual_review_recommended`
- `advisory_notice_only`
- `automatic_review_passed`

### fallback_reason

记录 fallback 原因。

当前支持：

- `no_template_uploaded`
- `template_parse_warning`
- `local_mode_skip_ai`
- `llm_unavailable_use_local_rules`
- `non_paper_requires_confirmation`

### manual_review_required

布尔值，表示是否需要人工复查。

v0.5.1 之后，只有 blocking 或 high_risk 风险会触发 `manual_review_required=true`。warning 和 info 只作为提示，不强制触发人工复查。

### confidence

规则置信度，不是 AI 自评。

它根据文档分类置信度、fallback 情况、人工复查风险和报告完整度计算，用于提示当前结果是否稳定可靠。

## 使用建议

- 面向用户时，可展示简化版 Agent Trace：执行了哪些步骤、哪些工具成功、是否 fallback。
- 面向开发者时，可用 Agent Trace 排查分类、模板、AI fallback、风险判断和报告生成问题。
- 不应把 Agent Trace 描述为 LLM 思维链。
