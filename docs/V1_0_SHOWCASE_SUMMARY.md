# v1.0-showcase 封版摘要（历史归档）

版本定位：`v1.0-showcase / 暑期实习展示版`（历史版本）

> 当前公开版本为 `v2.0-paperforge`。本文档保留用于说明上一阶段展示版，不是当前产品规格。

历史展示基线：tag `v1.0-showcase`，指向 commit `10904db`

说明：`v0.9.4-demo-screenshot-package` 是上一阶段截图包 tag；`v1.0-showcase` 是稳定展示版本，包含 v0.9.5 trace UI 相关增强。`main` 分支包含 `v1.0-showcase` 之后的公开前文档和面试材料补充，不代表 `v1.0-showcase` tag 已移动。

## 项目定位

这是一个基于 FastAPI + Next.js 的 DOCX 论文格式 Agent。它面向“上传论文和模板，自动做格式检查与修复，生成报告，在线预览并下载结果”的展示场景。

当前定位仍是格式 Agent，不是论文代写工具、不是正式查重系统、不是深度内容润色系统，也不是完整工业级 Agent。AI 模式只作为语言审校建议和参考评分增强；主链路稳定性来自本地 DOCX 解析、格式规则、fallback 和回归测试。

## 当前可展示功能

- DOCX 论文上传。
- 可选 DOCX 模板上传。
- 文档分类与非标准论文确认机制。
- 模板样式提取与 fallback。
- 标题、正文、段落、页边距、行距、缩进等基础格式修复。
- 标题正文混排处理。
- `C-51` 等异常模板编号清理。
- `modification_report` 修改报告。
- `format_diff_summary` 格式差异摘要。
- 在线 HTML 预览。
- 最终 DOCX 下载。
- `reference_check` 参考文献检查。
- `figure_table_check` 图表编号检查。
- 重复风险检测 / 相似度预检。
- local 模式：`ai_score=null`、`ai_used=false`。
- ai 模式：LLM 不可用时 fallback，不中断主流程。
- `agent_trace` 标准化执行轨迹。
- `agent_trace_detail` 旧解释型 trace 兼容保留。
- `task_id` / `task_state_path` / `running` / `succeeded` / `failed` 最小任务状态。
- `demo_inputs` 与 `demo_outputs` 示例材料。
- `docs/assets/screenshots/real-web-2026-06-27/` 真实网页截图资产。
- smoke / manifest / generated_manifest / heavy_manifest 等回归测试体系。

## 演示流程

1. 启动 FastAPI 后端和 Next.js 前端。
2. 打开前端页面。
3. 上传 `demo_inputs/messy_paper_sample.docx`。
4. 上传 `demo_inputs/template_sample.docx`。
5. 选择 local 模式，展示 `ai_score=null`、`ai_used=false` 的边界。
6. 点击启动 Agent。
7. 展示评分变化、`modification_report`、`format_diff_summary`、`reference_check` 和 `figure_table_check`。
8. 展开 TracePanel，讲解 `agent_trace` 的步骤、状态、耗时和 fallback。
9. 展示 `task_id` / `task_state_path` 摘要。
10. 打开在线预览。
11. 下载最终 DOCX。

## 技术架构摘要

- `paper-ai/backend/main.py`：FastAPI API 层，负责上传、分类、运行 Agent、预览和下载。
- `paper-ai/backend/services/agent_pipeline.py`：统一调度层，包装核心 Agent，标准化 `agent_trace`，写入 task state，并保持旧字段兼容。
- `paper-ai/backend/services/paper_agent.py`：核心处理流程。
- `paper-ai/backend/services/docx_formatter.py`：DOCX 格式修复。
- `paper-ai/backend/services/docx_analyzer.py`：评分、参考文献检查、图表编号检查。
- `paper-ai/backend/services/template_extractor.py`：模板样式提取与容错默认值。
- `paper-ai/backend/services/language_reviewer.py`：AI / 本地语言审校 fallback。
- `paper-ai/backend/services/plagiarism_checker.py`：重复风险检测 / 相似度预检。
- `paper-ai/backend/services/preview_service.py`：DOCX 到 HTML 预览。
- `paper-ai/backend/services/task_state.py`：最小任务状态落盘。
- `paper-ai/frontend/app/page.tsx`：前端上传、模式选择、运行、结果展示、TracePanel、预览和下载。

## Agent Trace 的意义

`agent_trace` 让 Agent 从黑盒变成可解释流程。它记录每一步的 `step`、`status`、`duration_ms`、`fallback_used` 和 `message`，适合解释“这次处理经历了什么”。`agent_trace_detail` 保留旧解释型 trace，降低兼容风险。

`task_state` 记录任务生命周期，适合解释“这次任务是否 running/succeeded/failed、输入输出和总耗时是什么”。当前前端只展示 `task_id` 和 `task_state_path` 摘要，不读取 task state 文件内容。

## 测试与回归说明

当前仓库已有以下回归材料：

- `test_smoke_agent_flow.py`：覆盖分类、local、模板、AI fallback、预览、下载和 trace 结构。
- `test_agent_orchestrator_trace.py`：覆盖 trace 结构。
- `test_reference_checker.py`：覆盖参考文献检查。
- `test_figure_table_checker.py`：覆盖图表编号检查。
- `test_formatter_mixed_heading.py`：覆盖标题正文混排。
- `test_score_consistency.py`：覆盖评分语义。
- `run_real_doc_regression.py`：读取 `manifest.csv` / `generated_manifest.csv` / `heavy_manifest.csv` 做批量回归。
- `test_documents/manifest.csv`：固定 10 个测试样本。
- `test_documents/generated_manifest.csv`：生成样本回归清单。
- `test_documents/heavy_manifest.csv`：74.79MB heavy DOCX 压力样本清单。

`v1.0-showcase` tag 已创建并指向 `10904db`；公开前不得移动、删除或重建该 tag。

本轮封版整理最小回归：

- `python -m py_compile`：PASS。
- `python test_agent_orchestrator_trace.py`：PASS。
- `python test_smoke_agent_flow.py`：PASS。
- `python run_real_doc_regression.py --manifest test_documents/manifest.csv --mode local --limit 1 --run-id v1_0_showcase_manifest_smoke`：PASS，1/1。
- `python run_real_doc_regression.py --manifest test_documents/generated_manifest.csv --mode local --limit 1 --run-id v1_0_showcase_generated_smoke`：PASS，1/1。
- `npm run build`：PASS。
- heavy_manifest 全量回归：本轮未执行，保留为本地脱敏样本可选长测；历史记录已有 heavy 1/1 PASS。

公开 clone 后的默认可复现测试建议优先运行 `test_agent_orchestrator_trace.py` 和 `test_smoke_agent_flow.py`。`manifest.csv`、`generated_manifest.csv`、`heavy_manifest.csv` 对应的完整 DOCX 回归样本属于本地脱敏样本和压力测试资产，不全部随公开仓库发布；完整 manifest / heavy 回归不是公开 clone 后的默认必跑流程。

## 已知限制

- 当前不是论文代写，不生成实验结果、观点或参考文献正文。
- 当前不是正式查重，只做重复风险检测 / 相似度预检。
- 当前不是完整工业级 Agent，没有用户系统、任务队列、多租户或云部署。
- `/agent/run` 仍是同步执行。
- task state 只是状态持久化雏形，不是完整断点续跑。
- 前端不读取 task state 文件内容。
- AI 内容修改能力仍有限，主要是语言审校建议和参考评分。
- 复杂模板、目录、脚注、公式、页眉页脚和复杂图文排版仍可能需要人工复核。
- 在线预览是结构化 HTML 预览，不是 Word 像素级还原。

## v1.1 后续计划

- 深度内容级修改能力。
- 完整 task state 可视化。
- 异步队列 / 断点续跑。
- 学校模板库。
- 更强的模板规则摘要。
- 更完整的修改前后 Diff。
- 真实授权用户样本扩展。
- AI 评分与真实修改量强绑定。
- 云端部署与多用户系统。

## 面试讲解要点

- 先强调工程闭环：上传、处理、报告、预览、下载。
- 再强调稳定性：local 模式、AI fallback、模板 fallback、相似度预检 fallback。
- 再讲可解释性：`agent_trace`、`agent_trace_detail`、`task_id`、`task_state_path`。
- 再讲测试：smoke、manifest、generated_manifest、heavy_manifest。
- 最后主动讲边界：不是论文代写、不是正式查重、不是完整工业级 Agent。
