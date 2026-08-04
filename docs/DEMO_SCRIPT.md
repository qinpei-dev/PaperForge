# 面试演示脚本

版本：`v1.0-showcase / 暑期实习展示版`

本文档用于暑期实习面试时演示 AI论文格式修改Agent。演示重点是“一个可运行、可解释、有 fallback、有测试覆盖的 DOCX 格式处理 Agent”。不要把它讲成论文代写、正式查重或深度内容生成系统。

当前推荐演示基线：tag `v1.0-showcase`，对应 commit `10904db`。`v0.9.4-demo-screenshot-package` 是上一阶段截图包 tag；`main` 分支包含 `v1.0-showcase` 之后的公开前文档和面试材料补充，不代表 `v1.0-showcase` tag 已移动。

## 0. 演示准备

内置输入样本路径：

- `demo_inputs/messy_paper_sample.docx`
- `demo_inputs/template_sample.docx`

已生成输出样例路径：

- `demo_outputs/formatted_result_sample.docx`
- `demo_outputs/report_sample.json`
- `demo_outputs/agent_trace_sample.json`
- `demo_outputs/task_state_sample.json`

注意：

- 这些文件从 `v0.6.3-real-demo-files` 开始已经存在。
- 样本是人工构造的脱敏模拟文本，不来自真实用户论文，也不来自 CAJ 原文。
- 输出样例由现有 local 模式处理流程生成，详见 `docs/DEMO_RESULT.md`。
- v0.7.0 后每次重新运行 Agent Pipeline 还会生成 task state 文件。
- v0.7.2 已固定保存 `demo_outputs/task_state_sample.json`，用于展示 task state 字段结构。
- 自动化演示建议把 demo 文件临时复制到 ASCII 路径，例如 `C:\Temp\paper-ai-demo\`，避免 Windows + CDP 在中文路径下出现文件句柄读取异常。

## 1. 开场介绍，约 30 秒

可以这样说：

> 这个项目是一个基于 FastAPI 和 Next.js 的 AI论文格式修改Agent。用户上传 DOCX 后，系统会做文档分类、格式修复、重复风险检测、参考文献检查、图表编号检查、生成修改报告，并提供在线预览和下载。当前版本定位是格式 Agent，AI 只作为语言审校和参考评分，不承诺深度内容改写。

强调三点：

- 主链路完整：上传、处理、预览、下载。
- 流程可解释：每一步都有 `agent_trace`。
- 稳定性优先：AI 失败、模板缺失等情况都有 fallback。

## 2. 展示 README，约 1 分钟

打开 `README.md`，讲：

- 当前版本：`v1.0-showcase / 暑期实习展示版`。
- 技术栈：FastAPI、python-docx、Next.js、TypeScript。
- 核心模块：`agent_pipeline.py`、`paper_agent.py`、`docx_formatter.py`、`docx_analyzer.py`、`language_reviewer.py`。
- Demo 样本：`demo_inputs/` 已放入模拟论文和模板，`demo_outputs/` 已保存一次 local 模式运行输出。
- Task State：v0.7.0 已支持每次运行生成 `task_id` 和 `task_state_path`，记录任务生命周期。
- 演示素材：v0.9.4 已新增 `docs/DEMO_SCREENSHOT_GUIDE.md`，整理截图清单、录屏脚本和自动化演示注意事项；v1.0-showcase 继续沿用这组素材，并以 tag `v1.0-showcase` 作为稳定演示基线。
- 项目边界：不是 RAG，不是 LangGraph，不是 Milvus，不是数据库系统，不是论文代写。

可说：

> 我没有为了包装概念引入复杂框架，而是先把 DOCX 处理主链路做稳定，把流程、fallback、测试和演示路径补齐。

## 3. 展示架构图，约 2 分钟

打开 `docs/ARCHITECTURE.md`，展示 mermaid 图。

讲解顺序：

1. 前端只负责上传、展示结果、预览和下载。
2. `main.py` 是 API 层。
3. `agent_pipeline.py` 是统一调度层，负责包装核心 Agent 和标准化 trace。
4. `paper_agent.py` 串联真正的业务工具。
5. `docx_formatter.py` 修改 Word 格式。
6. `docx_analyzer.py` 做评分、参考文献、图表编号检查。
7. `language_reviewer.py` 处理 AI/本地语言审校 fallback。
8. `task_state.py` 记录任务生命周期，默认写入 `paper-ai/backend/task_states/{task_id}.json`。

可说：

> 我把“调度”和“核心处理”拆开，是为了让接口输出稳定，并且不把格式修复逻辑和展示层 trace 混在一起。

## 4. 演示固定案例，约 3 分钟

参考 `docs/DEMO_CASE.md`。

内置样本特征：

- 标题格式不统一。
- 正文缩进或行距不规范。
- 参考文献编号存在可检查点。
- 图表编号和正文图号引用存在可检查点。

演示步骤：

1. 打开前端页面。
2. 上传论文 DOCX。推荐路径：`demo_inputs/messy_paper_sample.docx`。
3. 可选上传模板 DOCX。推荐路径：`demo_inputs/template_sample.docx`。
4. 选择本地规则模式，便于展示 local 模式下 `ai_score=null`、`ai_used=false` 的真实边界。
5. 启动 Agent。
6. 展示评分变化：`80 -> 86`。
7. 展示修改报告、参考文献检查和图表编号检查。
8. 展开 TracePanel，展示 9 个步骤、耗时和 fallback 状态。
9. 展示 `task_id` / `task_state_path` 摘要。
10. 展示在线预览。
11. 下载最终 DOCX。

讲解重点：

- 未上传模板时走通用论文规则 fallback。
- local 模式必须返回 `ai_score=null`、`ai_used=false`。
- 修改报告说明改了什么、还有哪些人工复查建议。
- v0.9.2 之后前端统一使用 `NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"`，避免本地演示时混用 host 或协议。

## 4.1 截图和录屏顺序

详细素材清单见 `docs/DEMO_SCREENSHOT_GUIDE.md`。建议录屏控制在 60-90 秒，按下面顺序推进：

真实网页截图已归档到 `docs/assets/screenshots/real-web-2026-06-27/`。如果不现场录屏，也可以直接按以下顺序展示静态截图：

1. `01_home_overview_real.png`
2. `03_upload_waiting_real.png`
3. `04_running_agent_real.png`
4. `06_result_dashboard_real.png`
5. `07_checks_reference_figures_real.png`
6. `08_trace_expanded_real.png`
7. `10_preview_download_real.png`

本次真实截图评分为 `81 -> 87`；如果讲固定 demo 输出样例，再使用 `80 -> 86`。

1. 首页 Hero 区：停顿 3-5 秒，说明这是格式审查、模板对齐和 Agent 可观测工具。
2. 上传工作台：停顿 5 秒，展示论文上传、模板上传、本地规则模式和启动按钮。
3. 文件已选择状态：停顿 3 秒，说明 demo 使用人工构造的脱敏模拟样本。
4. 运行中状态：短暂停顿，说明当前 `/agent/run` 是同步执行，不是异步队列。
5. 结果 dashboard：停顿 6-8 秒，展示评分 `80 -> 86` 和结果总览。
6. 修改报告与检查结果：停顿 8-10 秒，展示 `modification_report`、`reference_check`、`figure_table_check`。
7. TracePanel 默认折叠：停顿 3 秒，说明主结果区不会被日志打乱。
8. TracePanel 展开：停顿 8-10 秒，强调这是步骤级 `agent_trace`，用于展示 Agent 可观测，不要讲成完整工业级调度平台。
9. 在线预览和下载入口：停顿 5 秒，展示最终 DOCX 可预览、可下载。
10. 390px 窄屏适配：如做作品集素材，可补一张移动端截图，说明页面没有横向溢出。
11. 封版口径：说明当前推荐演示基线是 tag `v1.0-showcase`，旧 tag `v0.9.4-demo-screenshot-package` 只是上一阶段截图包。
12. 公开复现口径：默认建议运行 smoke test 和 agent trace test；完整 manifest / heavy DOCX 回归依赖本地脱敏样本，不是公开 clone 后默认必跑流程。

## 5. 演示 agent_trace，约 2 分钟

在浏览器 Network 面板或后端返回 JSON 中展示 `agent_trace`。

说明每一项：

- `step`：当前处理步骤。
- `status`：步骤状态。
- `duration_ms`：耗时。
- `fallback_used`：是否使用 fallback。
- `message`：给用户或开发者看的简短说明。

当前已保存输出样例：

- `demo_outputs/agent_trace_sample.json`

可说：

> 这个 trace 不是为了炫技，而是为了让 Agent 不像黑盒。出了问题时，我能知道卡在分类、模板、格式修复、AI 审校还是报告生成。

## 6. 演示 task_state，约 1 分钟

在浏览器 Network 面板或后端返回 JSON 中查看：

- `task_id`
- `task_state_path`

固定 demo 样例可以直接打开：

- `demo_outputs/task_state_sample.json`

如果是在本地后端运行，也可以打开 `task_state_path` 指向的 JSON 文件。重点观察：

- `status`：任务生命周期状态，例如 `running`、`succeeded`、`failed`。
- `duration_ms`：本次任务总耗时。
- `input_files`：论文和模板输入路径。
- `output_files`：最终 DOCX 输出路径。
- `fallback_used`：本次任务是否出现 fallback。
- `agent_trace_steps_count`：对应 agent trace 的步骤数量。
- `error`：失败时的错误信息。

讲解边界：

- `task_state` 用于解释任务生命周期。
- `agent_trace` 用于解释处理步骤。
- 当前前端还没有 task_state 可视化界面；演示时通过返回 JSON 和本地 JSON 文件查看。
- 当前不是异步队列，也不是断点续跑。
- `task_state_sample.json` 是固定 demo 样例，不代表真实用户论文任务。

## 7. 演示报告和输出，约 2 分钟

重点观察：

- `modification_report`
- `reference_check`
- `figure_table_check`
- `before_score`
- `after_score`
- `download_url`

当前已保存样例：

- `demo_outputs/formatted_result_sample.docx`
- `demo_outputs/report_sample.json`

注意：这些文件由 `v0.6.3` 的 local 模式真实运行生成；不要把它讲成 AI 深度内容改写结果。

## 8. 演示 ai fallback，约 1 分钟

不一定现场调用真实 LLM，可以讲 smoke test 里已经覆盖：

- 模拟 AI 调用失败。
- `/agent/run` 仍返回 `status=ok`。
- `score_breakdown.ai_used=false`。
- 下载文件仍生成。

可说：

> 我把 AI 当成增强项，不当成主流程唯一依赖。所以 AI 不可用时，用户仍然能拿到本地格式修复结果。

## 9. 展示测试，约 2 分钟

展示命令，不建议现场全部跑很久；如果面试允许，可以跑 smoke 或说明已经验收。

推荐说明：

```powershell
# 在 Git 仓库根目录执行
cd .\paper-ai\backend
python test_smoke_agent_flow.py
```

测试覆盖点：

- 文档分类。
- local 主流程。
- 模板上传。
- AI fallback。
- 预览接口。
- 下载接口。
- `agent_trace` 结构。
- `task_state` 成功/失败状态落盘。
- `reference_check`、`figure_table_check` 兼容字段。

## 10. 项目边界说明，约 30 秒

主动说明限制会更可信：

- 当前不是正式查重，只做重复风险检测 / 相似度预检。
- 当前不是论文代写，不生成实验结果或参考文献。
- 内置 demo 样本不来自真实用户论文，也不来自 CAJ 原文。
- 复杂 Word 对象支持有限，例如目录、脚注、公式、页眉页脚。
- AI 评分只是参考，不参与主评分，不会拉低格式规则分。
- 当前已内置人工构造的脱敏模拟 DOCX 样本、一次 local 模式输出样例和真实网页截图资产；不要把它们说成真实用户论文。
- 当前 task_state 只是最小状态持久化能力，不是异步队列、断点续跑或前端可视化任务中心。
- `paper-ai/backend/task_states/` 是运行产物目录，`demo_outputs/task_state_sample.json` 是固定演示样例，两者不要混淆。

## 11. 收尾，约 30 秒

可以这样总结：

> 这个项目的重点不是堆 AI 名词，而是把一个 DOCX 格式处理需求做成稳定的 Agent 工程：有清晰模块、有 fallback、有兼容字段、有 trace、有测试。当前 `v1.0-showcase` 已经适合展示完整上传、处理、报告、Trace、预览和下载闭环；后续再把深度内容修改、完整 task state 可视化、异步队列和真实用户样本扩展放到 v1.1。

## 12. 常见演示风险

- 不要上传隐私敏感或正式提交论文。
- 不要承诺任何正式检测结果。
- 不要承诺“AI 深度润色整篇论文”。
- 如果 AI API 没配置，直接解释 fallback 设计。
- 不要把内置模拟样本说成真实用户论文。
- 不要声称前端已经有 task_state 可视化界面。
- 不要声称已经支持异步队列或断点续跑。
- 如果预览样式与 Word 不完全一致，说明预览是结构化 HTML，不是像素级还原。
