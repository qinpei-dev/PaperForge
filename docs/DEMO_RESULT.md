# Demo Result

版本：`v2.0-paperforge / PaperForge V2`

本文档记录本仓库当前内置的面试演示样本和一次真实 local 模式运行输出。样本内容为人工构造的脱敏模拟文本，不来自真实用户论文，不来自 CAJ 原文，也不用于论文代写。

当前公开运行基线为 tag `v2.0-paperforge`。`v1.0-showcase` 和 `v0.9.x` 仅作为历史展示阶段保留。本文档记录的 demo 输入为人工构造的脱敏样本；接口与页面能力应以当前 `main` / V2 代码为准。

## Demo 输入文件

- 待处理论文样本：`demo_inputs/messy_paper_sample.docx`
- 模板样本：`demo_inputs/template_sample.docx`

## Demo 输出文件

- 格式处理后 DOCX：`demo_outputs/formatted_result_sample.docx`
- 运行报告样例：`demo_outputs/report_sample.json`
- Agent Trace 样例：`demo_outputs/agent_trace_sample.json`
- Task State 样例：`demo_outputs/task_state_sample.json`

## 样本中故意设置的格式问题

- 标题层级格式不统一：部分标题使用 Heading 样式，部分标题保留为普通正文样式。
- 正文段落缩进不统一：包含无首行缩进、标准首行缩进和过大缩进。
- 行距不统一：包含 1.0、1.5 和 2.0 等不同段落行距。
- 图表编号存在可检查点：正文中故意引用 `图 3`，但样本只放置 `图 1`。
- 参考文献编号存在可检查点：参考文献包含 `[1]`、`[3]`、重复 `[3]`，用于观察报告提示。
- 样本包含封面、中文摘要、英文摘要、关键词、正文 5 节、表题、图题和参考文献。

## 运行方式

本次没有启动 `uvicorn --reload`、`npm run dev` 或其他常驻服务。处理流程通过现有后端函数直接调用：

```powershell
@'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "paper-ai" / "backend"))

from services.agent_pipeline import run_agent_pipeline

result = run_agent_pipeline(
    paper_path=root / "demo_inputs" / "messy_paper_sample.docx",
    template_path=root / "demo_inputs" / "template_sample.docx",
    output_dir=Path("<temporary-output-dir>"),
    allow_non_paper=True,
    mode="local",
)
'@ | python -
```

本次运行结果：

- `status`: `ok`
- `mode`: `local`
- `classification.document_type`: `academic_paper`
- `classification.confidence`: `0.95`
- `before_score`: `80`
- `after_score`: `86`
- `score_breakdown.ai_score`: `null`
- `score_breakdown.ai_used`: `false`

## v0.9.2 页面演示补充

v0.9.2 final demo check 使用真实前端页面完成了完整演示验收。由于 Windows + Chromium/Edge CDP 自动化在中文仓库路径下可能出现文件句柄读取异常，自动化演示建议临时复制同内容 demo 文件到 ASCII 路径，例如：

- `C:\Temp\paper-ai-demo\messy_paper_sample.docx`
- `C:\Temp\paper-ai-demo\template_sample.docx`

该临时路径只用于自动化上传，不改变仓库内固定 demo 文件来源。检查完成后应删除临时文件。

页面验收结果：

- 上传论文：PASS。
- 上传模板：PASS。
- 本地规则模式：PASS。
- `/document/classify`: 200。
- `/agent/run`: 200。
- `/preview/{filename}`: 200。
- 下载接口：PASS。
- 评分示例：`80 -> 86`。
- TracePanel：PASS，默认折叠，包含 9 个步骤。
- demo 后 `git status --short`：干净。

## 输出样例重点字段

`demo_outputs/report_sample.json` 重点观察：

- `classification`: 文档识别为标准论文。
- `before_score` / `after_score`: 展示格式处理前后评分变化。
- `score_breakdown`: local 模式下 `ai_score=null`、`ai_used=false`。
- `modification_report`: 包含自动处理数量、评分维度变化、人工复查建议。
- `reference_check`: 记录参考文献检查结果。
- `figure_table_check`: 记录图表编号检查结果。
- `repeat_risk`: 记录重复风险检测 / 相似度预检结果。

`demo_outputs/agent_trace_sample.json` 重点观察：

- `识别文档类型`
- `读取论文`
- `分析本地格式`
- `识别模板格式`
- `修复标题与正文格式`
- `AI增强审校`
- `重复风险预检`
- `最终复查`
- `生成最终报告`

其中 `AI增强审校` 在 local 模式下会标记为本地规则路径，不启用 AI 评分。

## Task State 样例

从 `v0.7.0-task-state-minimal` 开始，每次重新运行 demo 或 `/agent/run` 时，系统会额外生成 task state 文件：

- 返回结果中会包含 `task_id`。
- 返回结果中会包含 `task_state_path`。
- task state 默认写入 `paper-ai/backend/task_states/{task_id}.json`。

从 `v0.7.2-task-state-sample` 开始，仓库固定保存一份 demo task state 样例：

- `demo_outputs/task_state_sample.json`

该文件展示任务生命周期状态结构，重点字段包括：

- `task_id`
- `status`
- `mode`
- `duration_ms`
- `input_files`
- `output_files`
- `fallback_used`
- `error`
- `before_score` / `after_score`
- `ai_used` / `ai_score`
- `agent_trace_steps_count`
- `sample_note`

它和 `agent_trace_sample.json` 的区别：

- `agent_trace_sample.json`：步骤级执行记录，用于查看分类、模板识别、格式修复、AI 审校、重复风险预检、最终复查和报告生成等步骤。
- `task_state_sample.json`：任务生命周期状态，用于查看任务是否成功、输入输出路径、总耗时、fallback 概览、错误字段和 trace 步数。

边界说明：

- `task_state_sample.json` 是固定 demo 样例，用于展示字段结构，不代表真实用户论文任务。
- `demo_outputs/task_state_sample.json` 是固定演示样例；`paper-ai/backend/task_states/{task_id}.json` 是运行时产物，两者用途不同。
- 文件中的时间字段是固定 demo 时间字符串，不是新的真实运行时间。
- `duration_ms` 使用固定演示样例值，用于配合当前 `agent_trace_sample.json` 展示结构。
- task state 是任务生命周期记录，不替代 `agent_trace`、`modification_report`、`reference_check` 或 `figure_table_check`。
- 当前仍不支持异步队列、完整断点续跑或前端 task state 可视化。

## 验收说明

- DOCX 结构检查：PASS，三个 DOCX 均可通过 `python-docx` 打开并读取段落和表格。
- 现有 local Agent 处理流程：PASS，已生成 `formatted_result_sample.docx`、`report_sample.json`、`agent_trace_sample.json`。
- Task State 固定样例：PASS，已补充 `demo_outputs/task_state_sample.json`，并与 `report_sample.json`、`agent_trace_sample.json` 的关键字段保持一致。
- DOCX 渲染视觉 QA：SKIPPED，当前环境缺少 LibreOffice/`soffice`，`render_docx.py` 无法完成 PNG 渲染。
- 完整后端测试与前端构建：SKIPPED，本轮未修改核心业务逻辑、前端交互、测试断言或依赖文件。

## 当前限制和下一步

- 当前样本是人工构造的脱敏模拟文本，不代表真实用户论文。
- 当前样本不来自 CAJ 原文。
- 当前输出来自 local 模式，适合展示格式处理、报告和 trace；不展示深度内容改写能力。
- 重复风险检测 / 相似度预检不等同于正式查重。
- 公开 clone 后默认可复现测试以 smoke test 和 agent trace test 为主；manifest / generated_manifest / heavy_manifest 对应的完整 DOCX 回归样本属于本地脱敏样本和压力测试资产，不全部随公开仓库发布。
- 后续可进入 `v0.7.3-task-state-cleanup`，为运行生成的 `paper-ai/backend/task_states/` 增加清理策略；也可在有 LibreOffice 的环境补做 DOCX 渲染截图验收。
