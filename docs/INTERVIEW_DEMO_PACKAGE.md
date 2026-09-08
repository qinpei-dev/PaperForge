# Interview Demo Package

版本：`v1.0-showcase / 暑期实习展示版`

本文档用于面试和项目演示。当前推荐稳定演示基线是 tag `v1.0-showcase`，对应 commit `10904db`。`main` 分支包含 `v1.0-showcase` 之后的公开前文档和面试材料补充，不代表 `v1.0-showcase` tag 已移动。`v0.9.4-demo-screenshot-package` 是上一阶段截图包 tag。当前项目定位是论文格式 Agent，不是论文代写工具、正式查重系统或完整工业级 Agent。

## A. 项目一句话介绍

这是一个面向高校论文模板的 AI 论文格式审查与自动排版 Agent，支持上传论文和模板，输出格式化 DOCX、评分变化、修改报告、参考文献/图表检查、Agent Trace 和任务状态摘要。

## B. 30 秒介绍

这个项目用 FastAPI + Next.js 做了一个可运行的 DOCX 论文格式 Agent。用户上传论文和可选模板后，后端会完成文档分类、模板规则提取、格式修复、重复风险预检、参考文献检查、图表编号检查，并返回修改报告、评分变化、在线预览和下载链接。它的重点不是论文代写，而是把格式审查、模板对齐、报告生成和 Agent 执行过程可观测做成一条稳定工程链路。

## B1. 3 分钟项目讲解稿

大家好，这个项目是我做的 AI 论文格式修改 Agent，当前封版为 `v1.0-showcase` 暑期实习展示版。它解决的问题很具体：很多论文或课程报告不是内容写不出来，而是 DOCX 格式、标题层级、行距缩进、参考文献编号、图表编号和模板要求经常不一致。我的目标不是做论文代写，而是把“上传论文 -> 自动格式处理 -> 生成报告 -> 在线预览 -> 下载结果”做成一条稳定、可解释、可演示的工程链路。

技术上，前端用 Next.js 和 TypeScript，负责上传论文、上传模板、选择 local/ai 模式、展示结果 dashboard、TracePanel、在线预览和下载入口。后端用 FastAPI，核心处理依赖 python-docx。API 层在 `main.py`，真正的处理流程由 `agent_pipeline.py` 包一层统一调度，再调用 `paper_agent.py` 串联文档分类、模板解析、格式修复、评分分析、语言审校 fallback、重复风险检测、报告生成等模块。

这个项目里我比较重视三件事。第一是稳定主链路。即使用户不上传模板，也会走通用论文规则；即使 AI 调用失败，也会 fallback 到本地规则，不会因为 LLM 不可用导致用户拿不到结果。local 模式明确保持 `ai_score=null`、`ai_used=false`，避免夸大 AI 参与。第二是可解释性。接口会返回 `agent_trace`，前端会展示每一步做了什么、耗时多少、有没有 fallback；同时还有 `task_id` 和 `task_state_path`，用于解释任务生命周期。第三是可验证性。项目里有 smoke test、trace 测试、manifest 回归、generated_manifest 回归和 heavy_manifest 压力样本记录，核心目标是让演示不是“页面看起来能跑”，而是主要边界都有回归依据。

现场演示时，我会用内置的 demo 论文和模板。流程是上传 `messy_paper_sample.docx` 和 `template_sample.docx`，选择本地规则模式，点击启动 Agent。结果页会展示评分变化，比如固定样例是 `80 -> 86`，然后展示修改报告、参考文献检查、图表编号检查、重复风险检测、Agent Trace、在线预览和最终 DOCX 下载。这个 demo 的重点不是说 AI 已经深度改写论文，而是展示一个 DOCX 格式 Agent 如何把文档处理、报告、fallback 和可观测性做成完整产品链路。

我也会主动说明边界：当前不是正式查重，只做重复风险检测 / 相似度预检；不是论文代写，不生成观点、实验结果或参考文献正文；也不是完整工业级 Agent，没有用户系统、异步队列、断点续跑和云端多用户部署。v1.1 以后可以继续扩展深度内容修改、完整 task state 可视化、学校模板库、更完整的修改前后 Diff 和真实授权样本验证，但 v1.0-showcase 的重点是稳定、清楚、可展示。

## B2. 简历项目描述

可放在简历中的 3 条版本：

- 基于 FastAPI、Next.js 和 python-docx 实现 DOCX 论文格式 Agent，支持论文/模板上传、文档分类、格式修复、参考文献与图表编号检查、修改报告、在线预览和 DOCX 下载。
- 设计 `agent_pipeline` 统一调度层，标准化输出 `agent_trace`、`agent_trace_detail`、`task_id` 和 `task_state_path`，提升长流程文档处理的可观测性与前后端字段兼容性。
- 建立 smoke、trace、manifest、generated_manifest 和 heavy_manifest 回归体系，覆盖 local 模式、模板 fallback、AI fallback、预览下载、`ai_score=null` / `ai_used=false` 等关键边界。

更短的 1 条版本：

- 独立实现 AI 论文格式修改 Agent，完成 DOCX 上传、模板解析、格式修复、检查报告、Agent Trace、在线预览和下载闭环，并通过 smoke/manifest/heavy 回归保障展示版稳定性。

面试口头版：

> 这是一个偏工程化的 AI 应用，不是单纯调 LLM。我把 DOCX 论文格式处理拆成分类、模板解析、格式修复、评分检查、报告生成和 trace 展示几个模块，并通过 fallback 和回归测试保证主链路稳定。

## C. 2 分钟演示流程

1. 打开前端页面：`http://127.0.0.1:3000`。
2. 上传 demo 论文：`demo_inputs/messy_paper_sample.docx`。
3. 上传 demo 模板：`demo_inputs/template_sample.docx`。
4. 自动化演示时可先复制到 ASCII 临时路径，例如 `C:\Temp\paper-ai-demo\`，避免中文路径下浏览器自动化文件句柄异常。
5. 选择本地规则模式。
6. 点击启动 Agent。
7. 展示评分变化：`80 -> 86`。
8. 展示 `Agent修改报告`：自动处理、变化维度、人工复查项。
9. 展示 `reference_check`：参考文献重复编号、跳号、未引用条目。
10. 展示 `figure_table_check`：正文引用图号不存在等检查点。
11. 展开 TracePanel，说明 9 个步骤、耗时、fallback 和 message。
12. 展示 `task_id` / `task_state_path` 摘要，强调前端不读取 task state 文件内容。
13. 展示在线预览。
14. 点击下载最终 DOCX。

当前推荐演示基线是 `v2.0-paperforge`。`v1.0-showcase` 仅作为历史展示版本保留；当前演示应以 V2 的验证、证据、人工复核和确认版 DOCX 闭环为重点。

## C1. 演示流程 Checklist

演示前：

- 确认当前代码位于 `v1.0-showcase` tag，或位于包含 `10904db` 之后文档补充的 `main` 分支。
- 确认后端使用 `http://127.0.0.1:8000`。
- 确认前端 `NEXT_PUBLIC_API_BASE_URL` 未配置或指向 `http://127.0.0.1:8000`。
- 准备 `demo_inputs/messy_paper_sample.docx`。
- 准备 `demo_inputs/template_sample.docx`。
- 如做浏览器自动化录屏，先复制 demo 文件到 `C:\Temp\paper-ai-demo\`。

演示中：

- 打开首页，先说明这是“格式 Agent”，不是论文代写。
- 上传论文 DOCX。
- 上传模板 DOCX。
- 选择 local 模式。
- 点击启动 Agent。
- 展示评分变化、修改报告、参考文献检查、图表编号检查和重复风险检测。
- 展开 TracePanel，说明步骤、耗时和 fallback。
- 展示 `task_id` / `task_state_path`，强调不是异步队列或断点续跑。
- 打开在线预览。
- 点击下载最终 DOCX。

演示后：

- 如现场允许，可展示 `python test_smoke_agent_flow.py` 的历史/当前 PASS 结果。
- 如被问到查重，统一说“重复风险检测 / 相似度预检”，不要说正式查重。
- 如被问到 AI 内容改写，明确当前只是语言审校建议和参考评分，不承诺深度润色。

## D. 技术架构讲法

- 前端：Next.js + React + TypeScript，负责上传、模式选择、结果 dashboard、TracePanel、预览和下载。
- 后端：FastAPI，提供 `/document/classify`、`/agent/run`、`/preview/{filename}` 和 `/download/{filename}`。
- DOCX 解析与格式化：基于 `python-docx`，围绕段落、标题、行距、缩进、页边距和样式规则做处理。
- `template_extractor`：从上传模板中提取可用格式规则，缺失或不完整时 fallback 到通用论文规则。
- `docx_formatter`：执行标题、正文、段落和页面基础格式修复。
- `docx_analyzer`：生成 before/after 评分，包含 reference_check 和 figure_table_check。
- `reference_check`：检查参考文献章节、编号、跳号、重复编号、正文引用和未引用条目。
- `figure_table_check`：检查图题/表题编号、跳号、重复编号和正文引用不存在的图表编号。
- `agent_pipeline`：作为 API 和核心 Agent 之间的薄调度层，标准化返回字段和 trace，不重构核心逻辑。
- `agent_trace`：步骤级执行记录，解释处理链路、耗时、fallback 和每步 message。
- `task_state`：任务生命周期记录，默认写入 `paper-ai/backend/task_states/{task_id}.json`。
- local/ai fallback：local 模式不启用 AI 评分；ai 模式失败时 fallback，不让 AI 故障中断主流程。
- demo_outputs 四件套：`formatted_result_sample.docx`、`report_sample.json`、`agent_trace_sample.json`、`task_state_sample.json`。

## E. 项目亮点

- 不只是调模型，而是结构化 DOCX 文档处理 + Agent 调度 + 可解释报告。
- 支持模板规则提取，模板不完整时可以 fallback。
- 支持 before/after score，用 `80 -> 86` 展示格式处理效果。
- 支持结构化修改报告，说明改了什么、哪些还要人工复查。
- 支持 reference_check 和 figure_table_check，能解释参考文献和图表编号风险。
- 支持 agent_trace 可观测，前端 TracePanel 默认折叠展示。
- 支持 task_state 最小状态持久化，用于记录任务生命周期。
- 有真实可运行 demo 文件和固定 demo_outputs。
- 有 smoke、构建和 final demo check 记录。
- 有 manifest / generated_manifest / heavy_manifest 回归体系。
- 前端已有产品化展示页，更适合现场讲解。
- `v1.0-showcase` 已包含 v0.9.5 trace UI 相关增强；v0.9.4 已整理截图/录屏清单，让面试展示材料更容易复用到 README、简历附件、作品集和 PPT。

## F. 截图/录屏素材建议

详细清单见 `docs/DEMO_SCREENSHOT_GUIDE.md`。

真实网页截图已归档到 `docs/assets/screenshots/real-web-2026-06-27/`，共 10 张，覆盖首页、上传、运行中、结果 dashboard、检查模块、TracePanel、在线预览和下载入口。建议作品集主图使用 `01_home_overview_real.png`，面试流程展示按 `03_upload_waiting_real.png`、`04_running_agent_real.png`、`06_result_dashboard_real.png`、`08_trace_expanded_real.png`、`10_preview_download_real.png` 顺序展开。

建议至少准备 13 张截图：首页 Hero、上传工作台、文件已选择、运行中状态、结果 dashboard、评分 `80 -> 86`、修改报告、参考文献/图表检查、TracePanel 默认折叠、TracePanel 展开 9 步、在线预览、下载入口和 390px 窄屏适配。

录屏建议控制在 60-90 秒：先展示页面定位，再上传 demo 论文和模板，选择本地规则模式，点击启动 Agent，展示评分、报告、检查结果、TracePanel、预览和下载。讲 TracePanel 时强调“Agent 可观测”，不要说成完整工业级调度平台。

注意：本次真实截图中的结果评分为 `81 -> 87`，历史固定 demo 输出样例为 `80 -> 86`。现场讲解时以当前展示截图为准，避免把两个样例混成同一次运行。

自动化录屏建议使用 ASCII 临时路径，例如 `C:\Temp\paper-ai-demo\`，并在结束后确认 `git status --short` 干净、临时服务已停止。

## G. 当前边界

- 不是论文代写，不生成实验结果、观点或参考文献正文。
- 不是正式查重，只做重复风险检测 / 相似度预检。
- 不是完整工业级 Agent，没有用户系统、任务队列、多租户或云部署。
- 不是异步队列，`/agent/run` 仍是同步执行。
- 不是完整断点续跑，task_state 只是状态持久化雏形。
- 前端不读取 task_state 文件内容，只展示 `task_id` 和 `task_state_path` 摘要。
- AI 内容修改能力仍有限，当前主要是语言审校建议和参考评分。
- 复杂模板、目录、脚注、公式、页眉页脚和复杂图文排版仍可能需要人工复核。
- demo 样本是人工构造的脱敏模拟文本，不来自真实用户论文，也不来自 CAJ 原文。

## H. 面试追问回答

### 0. 这个项目最核心的技术难点是什么？

核心难点不是“调用大模型”，而是把 DOCX 这种结构复杂的文件处理成稳定工程链路。Word 文档里的标题、正文、行距、缩进、页边距、参考文献、图表编号不是普通纯文本，必须用确定性规则处理；同时还要保证 AI 不可用、模板缺失、文档分类边界等情况不会中断主流程。

### 1. 为什么不用大模型直接改 Word？

Word 格式问题不是单纯文本生成问题。标题层级、行距、缩进、页边距、参考文献编号和图表引用都需要结构化 DOCX 解析和确定性规则。大模型可以做语言建议，但直接让它改 Word 容易不可控、不可测试，也难以保证下载文件格式稳定。

### 2. `agent_pipeline` 有什么作用？

它是 API 层和核心处理流程之间的薄包装层。它不重写 `paper_agent` 的核心逻辑，主要负责统一调用、补充 `agent_trace`、透出 `reference_check` / `figure_table_check`、写入 task_state，并保持旧字段兼容。

### 3. `agent_trace` 和 `task_state` 有什么区别？

`agent_trace` 记录步骤，回答“这次处理经历了什么”。`task_state` 记录生命周期，回答“这次任务是否 running/succeeded/failed，输入输出和总耗时是什么”。前者适合步骤解释，后者适合任务状态追踪；两者不互相替代。

### 3.1 为什么要保留 `agent_trace_detail`？

`agent_trace` 是展示友好的步骤列表，适合前端 TracePanel；`agent_trace_detail` 保留旧解释型 trace，用于兼容原有字段和调试信息。这样做可以让前端展示变清楚，同时不破坏已有测试和旧字段消费者。

### 4. AI 失败怎么办？

AI 是增强项，不是主流程唯一依赖。ai 模式下 LLM 调用失败会 fallback 到本地规则，主流程仍应返回结果、预览和下载。local 模式完全不依赖 AI。

### 5. 为什么 local 模式 `ai_score=null`、`ai_used=false`？

这是为了保证评分语义真实。local 模式没有调用 AI，就不应该展示 AI 分数或假装 AI 参与。这样面试时也能说明系统没有夸大能力。

### 6. 怎么证明修改有效？

可以从四层证明：before/after score 从 `80 -> 86`，`modification_report` 说明具体改动，reference_check / figure_table_check 展示可检查风险，最终 DOCX 可以预览和下载。

### 6.1 怎么证明它不是只做了一个前端 demo？

后端有真实 DOCX 处理链路，demo_outputs 中有真实 local 模式输出；公开 clone 后默认建议优先跑 smoke 和 trace 测试。manifest、generated_manifest 和 heavy_manifest 是本地脱敏样本/压力测试回归体系，不全部随公开仓库发布，不应被包装成外部用户 clone 后的默认必跑流程。v1.0-showcase 最小回归曾覆盖 py_compile、前端 build、trace、smoke、manifest limit 1 和 generated_manifest limit 1。

### 7. 如何避免运行产物污染 Git？

`.gitignore` 已忽略 `paper-ai/backend/task_states/` 和 `paper-ai/backend/templates/*.docx`。v0.9.2 final demo check 后 `git status --short` 仍干净，说明模板上传副本和 task_state 运行产物不会进入版本控制。

### 8. 当前项目最大不足是什么？

内容级修改仍弱。AI 模式主要做语言审校建议和参考评分，不是深度段落级润色，也不会补写事实或实验结论。复杂 Word 对象也需要继续增强。

### 9. 下一步怎么做？

不会在 v1.0-showcase 上继续加功能。后续如果进入 v1.1，才考虑深度内容级修改、完整 task state 可视化、异步队列/断点续跑、学校模板库、更强模板规则摘要、更完整修改前后 Diff、真实授权用户样本扩展和云端部署。

### 10. 如果要上线，还缺什么？

至少还需要用户系统、文件隔离、任务队列、任务清理策略、安全读取 task_state 的接口、权限控制、云部署、日志审计、异常告警、真实用户样本评估和隐私合规流程。

### 11. 前端产品化首页有什么意义？

它让面试官第一眼能看懂项目不是零散脚本，而是一个完整工具：首屏说明能力，工作台承接上传，结果区像 dashboard，TracePanel 解释 Agent 执行过程。

### 12. 为什么默认使用 `http://127.0.0.1:8000`？

本地 FastAPI 默认监听 HTTP 8000，统一使用 `127.0.0.1` 可以避免 `localhost` / `127.0.0.1` 或 `http` / `https` 混用。v0.9.2 也支持 `NEXT_PUBLIC_API_BASE_URL` 覆盖。

### 13. v1.0-showcase 和旧 tag 是什么关系？

`v0.9.4-demo-screenshot-package` 是上一阶段截图素材包 tag；`v1.0-showcase` 是当前暑期实习展示版稳定 tag，对应 commit `10904db`。`main` 分支包含后续公开前文档和面试材料补充，但不代表 `v1.0-showcase` tag 已移动。面试展示优先使用 `v1.0-showcase` 或包含该 tag 的 main 最新提交。

### 14. v1.1 准备做什么？

v1.1 主要承接展示版之后的能力增强：深度内容级修改、完整 task state 可视化、异步队列/断点续跑、学校模板库、更强模板规则摘要、更完整修改前后 Diff、真实授权用户样本扩展、AI 评分与真实修改量强绑定，以及云端部署和多用户系统。

### 14.1 本轮有没有进入 v1.1 开发？

没有。本轮只整理面试展示材料，不新增功能、不改后端核心代码、不改前端主流程、不改 API。v1.1 只作为后续规划写在文档里。

### 15. 为什么自动化上传建议使用 ASCII 临时路径？

在当前 Windows + CDP 自动化环境中，中文仓库路径下的文件句柄曾触发 `NotFoundError`，并在 Network 中表现为上传请求失败。把同内容文件复制到 ASCII 临时路径后，真实页面流程稳定通过。这是自动化环境兼容问题，不是 demo 文件来源变化。

### 16. `ERR_ALPN_NEGOTIATION_FAILED` 是怎么定位的？

先确认 Python 直调 `/agent/run` 返回 200，排除后端字段和业务错误；再用浏览器 Network 捕获到 `/document/classify` 和 `/agent/run` 的 loadingFailed；最后对比小请求、ASCII 临时路径和真实页面流程，定位为本地浏览器自动化上传路径兼容问题，并通过统一 API base URL 和更清晰错误提示降低排查成本。

## I. 项目边界：已完成与后续计划

已完成，可在 v1.0-showcase 中展示：

- DOCX 论文上传和可选模板上传。
- 文档分类与非标准论文确认机制。
- 模板样式提取与 fallback。
- 标题、正文、段落、页边距、行距、缩进等基础格式修复。
- 标题正文混排处理。
- `C-51` 等异常模板编号清理。
- `modification_report` 和 `format_diff_summary`。
- 在线 HTML 预览和最终 DOCX 下载。
- `reference_check` 参考文献检查。
- `figure_table_check` 图表编号检查。
- 重复风险检测 / 相似度预检。
- local 模式 `ai_score=null`、`ai_used=false`。
- ai 模式 LLM 不可用时 fallback，不中断主流程。
- `agent_trace`、`agent_trace_detail`、`task_id`、`task_state_path`。
- demo 输入输出、真实网页截图资产和回归测试体系。

当前只是边界或后续计划，不能在面试中说成已完成：

- 深度内容级修改能力。
- 完整 task state 可视化。
- 异步队列 / 断点续跑。
- 学校模板库。
- 更强的模板规则摘要。
- 更完整的修改前后 Diff。
- 真实授权用户样本扩展。
- AI 评分与真实修改量强绑定。
- 云端部署与多用户系统。
