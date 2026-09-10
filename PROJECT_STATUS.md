# 项目状态

项目名称：**PaperForge**

正式定位：**Verified Academic Document Agent**

中文定位：**学术文档可信智能处理 Agent**

当前阶段：**Day9-P3 Tenant Template Management & Storage 完成，等待用户验收**

Day9-P3 最新增量：**Tenant Template Management & Storage 已完成**。新增 `LocalTemplateStorage`，托管模板数据库只保存稳定 `local://tenant-templates/...` locator，不保存本地绝对路径；文件按 tenant/resource/version 隔离，并具备安全 locator 解析、删除和本地处理边界。`Template` 新增 storage locator、原始文件名、文件大小、content type、SHA-256、uploaded_by 等正式字段，Alembic `0006` 从 `0005` 升级。登录用户可通过 `POST /templates` 上传合法 DOCX，系统完成空文件/扩展名/大小/ZIP DOCX 校验和 Template Intelligence 解析后才创建 tenant-scoped 资源；失败会回滚 DB 并清理已写文件。新增 tenant-aware detail、patch、原始文件下载和受 provenance 保护的 delete；已被 Task 使用的模板只能 disabled，不能物理删除。Registry 在创建、更新、删除后立即刷新，版本身份不可静默覆盖；Task trace 保留实际模板快照。首页新增最小“我的模板”上传与选择入口，legacy 临时模板上传仍保持 ephemeral。验收结果：后端 pytest 62 passed，Day9-P3 专项 3 passed，Python compileall、Alembic fresh/`0005→0006`、frontend build、git diff check PASS。

Day9-P2 最新增量：**Tenant Context & Resource Isolation 已完成**。新增 Tenant、TenantMembership、统一 personal Tenant Context，以及 Task 的 `tenant_id/user_id` provenance；Template 扩展为 platform/tenant scope，Registry、Repository、`GET /templates`、`POST /tasks`、`POST /agent/run` 全部按 tenant 可见集合解析。Task 列表、详情、SSE、Artifact、文件名下载/预览和确认版输出均按 tenant 隔离，越权统一隐藏为 404；匿名兼容仅可使用平台模板且不能读取持久化 tenant 产物。Alembic `0005` 可从 `0004` 原地 backfill 既有用户 personal tenant、membership、平台模板和历史 Task。数据库唯一性采用 tenant identity unique constraint + platform partial unique index，允许不同 tenant 使用相同 template_id/version。验收结果：后端 pytest 59 passed，Day9-P2 专项 7 passed，Python compileall、Alembic upgrade 至 0005、frontend build、git diff check PASS。

Day9-P1 最新增量：**Template Persistence 已完成**。新增 SQLAlchemy `Template` 模型与 `(template_id, version)` 数据库级唯一约束、Alembic `0004` migration、Template Repository 和 Persistence Service。内置模板以幂等 bootstrap 写入数据库且不覆盖已有 status；Registry 在 startup 和 API 解析前从持久化数据刷新。`GET /templates`、`POST /tasks`、`POST /agent/run` 已使用 DB Registry；运行时新增模板无需改 Python 静态定义即可解析，legacy upload 仍保持 ephemeral。未引入 tenant、RBAC、用户模板管理或对象存储。验收结果：后端 pytest 52 passed，Python compileall、Alembic upgrade 至 0004、frontend build、git diff check PASS。

Day9-P0 最新增量：**Multi-template Template Registry 已完成**。新增统一内存 Registry、稳定 template identity、版本/status/source/locator/metadata、精确与元数据解析、禁用与歧义保护；内置通用默认规则和版本化 bundled DOCX。`GET /templates`、`POST /tasks`、`POST /agent/run` 已最小接入，result、task state、Agent Trace、报告和任务详情可追踪实际模板 ID/version。旧请求不传 `template_id` 继续走兼容默认，旧模板上传继续可用；未修改数据库结构、Executor 或 SSE 协议。验收结果：后端 pytest 47 passed，Python compileall、frontend build、git diff check PASS。

Day8-P1 最新增量：**Template Rule Extraction Enhancement 已完成**。模板知识新增样式继承、区域覆盖、规则优先级和最终 effective rules；AI Reasoning 优先消费 effective rules 判断格式问题。未修改 Executor、SSE 协议或数据库结构；旧 reasoning 调用、无模板输入和旧 task state 保持兼容。

Day8-P0 最新增量：**Template Intelligence Layer 已完成**。新增模板区域识别、格式规则提取和保护区域识别；结果以 `template_analysis` 接入既有 Document Intelligence → AI Reasoning 链路，并保存到 task state。未修改 Executor、SSE 协议或数据库结构；无模板输入、旧 reasoning 调用和旧 task state 保持兼容。

最新增量：**AI Reasoning Layer 已完成窄范围接入**。Reasoning 只消费既有
document analysis、检测到的问题和模板规则，生成可序列化解释，不直接修改
DOCX；Planner 仅附带 reasoning，Executor、SSE 协议和旧任务字段保持兼容。

Day7-P2 最新增量：**Paper Quality Intelligence 已完成**。Quality Analyzer
基于 document_analysis、reasoning_results、verification_results 生成 format、
structure、reference、visual 四维质量报告，并写入 task state；不修改 Executor、
SSE 协议或数据库，旧任务缺少 quality_report 时保持兼容。

Day 3 已在不改变 Planner / Executor / Verifier 核心逻辑的前提下完成 Agent Trace 驱动的工作流状态展示、Task Detail/Dashboard 产品化、Storage 抽象、Compose 健康检查与部署文档整理。

验收日期：**2026-09-08**

验收基线：`c0bcc2f80dd46d15df1d1067ef1174cd05e36d4d`

正式结论：**READY**

PaperForge V2 核心开发已经完成；Day 1 SaaS 基础升级已在保持 Agent Pipeline 兼容的前提下完成。当前已具备 PostgreSQL/SQLAlchemy/Alembic 元数据层、JWT 认证、Workspace/Task 基础隔离和最小 SaaS 前端入口。

Day 1 SaaS 验收结果：后端 pytest 9 passed，前端 build PASS，SaaS 专项测试 4 passed，docker compose config PASS。Docker 镜像实际构建待 Docker Desktop daemon 启动后复验。

Day 2 Task 生命周期验收结果：新增认证 `POST /tasks` 编排入口，现有 Agent Pipeline 保持不变；Task 状态支持 pending → running → completed / failed，trace、score、输出 DOCX、JSON report 自动持久化为 Task/Artifact；Dashboard 已接入真实任务列表和详情页。SaaS 测试 6 passed，全量 pytest 11 passed，前端 build PASS。

Day 3 验收结果：状态展示升级为 pending → analyzing → planning → executing → verifying → completed / failed；已补齐论文名、前后评分、Trace workflow、DOCX/report Artifact 下载、Dashboard 统计、LocalStorage/S3Storage 接口和生产配置说明。pytest 11 passed，前端 build PASS，compileall PASS，Alembic head PASS，Compose config PASS，diff check PASS。

Day 4 验收结果：新增可空 `Task.workflow_stage` 与 Alembic 0003 迁移；`run_agent_pipeline(progress_callback=...)` 保持旧调用兼容并提供 analyzing → planning → executing → verifying → completed / failed 回调；SaaS Task 实时持久化阶段，API 返回 workflow_stage/progress，Task Detail/Dashboard 展示当前阶段；生产模式缺失 JWT_SECRET_KEY 时禁止启动，本地模式保留兼容 fallback。Day 4 测试 5 项新增、全量 pytest 16 passed，frontend build PASS，compileall PASS，migration PASS，Compose config PASS，diff check PASS。

Day 5 验收结果：`POST /tasks` 创建任务后立即返回 `task_id` 和 pending 状态；新增进程内轻量 `TaskWorker`，使用独立 SQLAlchemy session 后台执行现有 Agent Pipeline，持续写入 status/workflow_stage，并保存 Artifact、捕获异常；Task Detail 以 2 秒轮询自动刷新，终态自动停止；`/agent/run` 保持同步旧语义。Day 5 测试新增 3 项、全量 pytest 19 passed，frontend build PASS，compileall PASS，git diff check PASS。

Day 6 验收结果：新增进程内 `TaskEventStore`，按 `task_id` 保存有界事件历史并支持并发订阅；`GET /tasks/{task_id}/events` 在完成用户归属校验后返回 SSE，回放事件并在 completed/failed 后自动关闭；TaskWorker 先持久化 DOCX/report Artifact、发布 artifact_created，再提交 completed 并发布 task_completed；失败 SSE 使用安全文案，完整异常仅保留在服务端日志和内部任务记录；Task Detail 优先使用认证 fetch-stream SSE，仅在连接失败或非终态断流时回退 2 秒轮询。终态事件历史有 TTL 和最大保留数量限制。测试为每个异步用例隔离 Worker 和 SQLite 文件数据库，并在 teardown 前等待任务结束；Day 6 全量 pytest 连续两次均为 24 passed，frontend build PASS，compileall PASS，docker compose config PASS（临时注入必需校验变量），git diff check PASS。

Day 7 Document Intelligence Layer 验收结果：新增 `document_intelligence.py`，在既有 DOCX parse/model 与 Planner 之间生成可序列化 `DocumentAnalysis`；支持中英文标题、摘要、关键词、引言、相关工作、方法、实验、结论、参考文献的保守识别，并输出段落语义类型与 confidence；结果同时返回 API pipeline 并保存到 task state。未修改 Executor、formatter、SSE 协议或数据库结构；新增测试 4 passed，全量后端 pytest 28 passed，Python 编译 PASS，git diff check PASS。

Day 7 下一步建议：**有条件进入 P1 AI reasoning 设计/窄范围实现**。先让 reasoning 只消费 `document_analysis` 并输出建议或解释，不直接改写 DOCX；保留本地规则 fallback、confidence 门槛和现有 Runtime/Planner/Executor 边界。

V2 第二次大升级正式验收结果：26 项核心能力 PASS；A～F 端到端场景 PASS；Safety Audit、Provenance / Verification、Score Credibility、Frontend build、Real DOCX Regression 10/10、AI failure fallback 和 Legacy compatibility 均 PASS；0 warning，0 blocking FAIL。

## 当前边界

深度语义润色仍有限；复杂目录、脚注、公式、复杂表格、交叉引用、异步恢复、checkpoint/resume 和审批后继续执行尚未完成。事件流仅保存在单进程内存，进程重启或跨实例不会保留历史；终态事件历史按 TTL / 上限清理；轮询仅作为 SSE fallback。

## 历史开发状态

`PaperOps Agent v2.0` 仅作为历史开发阶段代号保留。以下 P2/P1/P0 记录描述真实历史完成情况，不代表当前品牌或未来路线。

P2 收尾状态：统一格式/内容 evidence summary、内容 Before/After、单条 suggestion 确认采纳、stale conflict、确认版 DOCX 重读验证和 verified-change 内容评分均已完成。Runtime/API/report 暴露 `review_summary`、`change_evidence`、`pending_actions`；前端明确区分自动修改、未写入建议、已采纳验证和 HITL。保留旧字段与老任务安全降级。

P2 第一阶段状态：段落级内容审查与安全修改闭环已完成（safe content review loop）。新增 paragraph issue model、AUTO_FIX / SUGGEST_ONLY / HITL_REQUIRED policy、内容 provenance、输出重读验证，并接入既有 Decision/HITL、报告和前端结果区。AI 候选不得绕过本地 policy；local 与 AI fallback 均保留主流程兼容。

P1 Closure 状态：已完成 Analyze → Plan → Conflict Check → 稳定执行 → 输出 DOCX 重读 → target-level verification → evidence aggregation → Decision → HITL → Runtime / Frontend evidence。PlanStep 支持轻量规范化、重复去重、同 target 同 field 冲突阻断与稳定排序；target failed 优先进入人工复核，unsupported 保留原因并进入精确 HITL，验证摘要来自 provenance。

P0.3 Runtime UI / Task State 状态：已完成最小接入。保留 P0.2 真实闭环与 `/agent/run` 旧字段；task state 新增 runtime_state、current_phase、current_step、decision、replan_count、human_review_required 摘要。前端在既有结果与 Trace 区域旁展示 Runtime Workflow、Verification、Decision、HumanReviewRequest 与 Replan 摘要，并对旧任务字段缺失安全降级；不包含审批继续、checkpoint 恢复或自动 resume。

P1 Executor Expansion + Provenance Foundation：已将低风险正文格式动作拆分为字体/字号、对齐、行距、首行缩进、段前段后，并保留低风险页边距动作；PlanStep 使用段落/节 locator。Executor 记录逐实际修改的 before/after、rule、plan、step、target 与执行状态，Verifier 以 rule 或 document scope 回填验证结论。引用、图表编号与无定位步骤仍为 unsupported / HITL；未实现内容语义改写、引用重编号或复杂表格修改。

P1.1 Target-level Formatting Verification：已为 Word 标题样式和可解析编号的图题/表题建立保守 paragraph locator；标题、图题、表题仅对 locator 指定段落执行字体、字号、加粗、对齐、行距与段落间距等低风险格式动作。Verifier 会重新读取输出 DOCX 并记录 target-level expected/actual evidence；无 locator、低置信或越界目标不会伪造成功。前端 Runtime 区新增兼容降级的“实际修改”摘要。

P1.2 Body Paragraph Target-level Verification：正文低风险格式修改现在将每个 paragraph index 记录为 `body_paragraph` target，并保留 before、expected、after 与 locator。Verifier 会重新读取输出 DOCX 并对字体、字号、对齐、行距、首行/左右缩进、段前段后逐 target 比较 actual；无法定位的正文 PlanStep 会写入 unsupported provenance 和原因，不再以 rule-level 分数伪装段落验证。

当前公开发布基线：tag `v2.0-paperforge`，指向当前 HEAD `966dc02`

版本口径：

- `v2.0-paperforge` 是当前公开发布与 Release Freeze 基线。

- `v0.9.4-demo-screenshot-package` 是上一阶段截图包 tag。
- `v1.0-showcase` 是稳定展示版本，指向 `10904db`。
- `v1.0-showcase` 和 `v0.9.4-demo-screenshot-package` 仅作为历史展示 tag 保留。
- 不移动、删除或重建 `v1.0-showcase` 和 `v0.9.4-demo-screenshot-package` tag。

# 已完成功能

- 文档分类：支持识别标准论文、课程作业、实验报告、简历、未知文档。
- 格式修复：支持标题、正文样式、字体、行距、缩进、页边距等基础格式修复。
- AI审校：支持 DeepSeek/OpenAI API；API 不可用时可降级到本地规则。
- 重复风险预检：支持相似段落、重复句子和重复风险等级检测。
- 在线预览：支持将最终 docx 转成 HTML 预览，并增强标题层级、参考文献区域和表格基础样式展示。
- 修改报告：支持输出修复项、评分对比、修改次数、未修复项、人工复查建议和格式差异摘要。
- 参考文献检查：支持识别参考文献章节、文末编号、正文引用、编号跳号、重复编号、正文引用缺失和文末未引用条目。
- 图表编号检查：支持识别图题、表题、Figure/Table 编号、编号跳号、重复编号和正文引用不存在的图表编号。
- 真实论文测试库：v0.3.5 第一步已建立 `test_documents/` 测试资产目录、`manifest.csv` 占位清单、`regression_results/` 结果目录和 `real_paper_test_plan.md` 测试计划；第二步已生成 10 个脱敏 DOCX 测试样本并更新 manifest。
- 批量真实样本回归脚本：v0.5.0 已新增 `run_real_doc_regression.py`，支持读取 `manifest.csv` / `generated_manifest.csv` 批量运行分类、local/ai Agent、报告、预览、下载和 local AI 字段校验，并输出 `summary.csv`、`summary.json` 与单 case JSON。
- CNKI / GB/T 7714 来源规范：v0.5.0 已新增 `test_documents/CNKI_GBT7714_SOURCE_NOTES.md`，明确只使用公开或已授权文件，不纳入登录/付费/验证码/受限全文；真实论文必须脱敏后才能进入测试库。
- Agent Orchestrator Layer：v0.3.7 已新增可解释智能体调度记录 `agent_trace`，记录 task_plan、tools_used、agent_decision、fallback_reason、manual_review_required 和 confidence，不改变原有处理结果。
- 评分语义：v0.4.1 已新增 `score_breakdown.format_score`、`risk_score`、`ai_language_score`、`final_score`、`score_confidence` 和 `score_explanation`，AI 语言评分仅作参考，不会拉低最终评分。
- 重复风险检测性能保护：v0.4.6 已为 `check_repeat_risk` 增加段落采样、比较次数硬上限和异常 fallback，极端 DOCX 不再因相似段落两两比较导致完整 Agent 超时。
- 资源压力测试：v0.4.7.1 已完成 74.79MB 重型 DOCX 全链路验证，覆盖上传、分类、local Agent、格式修复、评分、预览、下载和 AI fallback。
- 重复风险检测性能优化：v0.4.9 已优化 `plagiarism_checker`，在 `SequenceMatcher` 前加入段落长度差过滤、字符集合重叠率过滤、中文关键词重叠率过滤，并增加 `MAX_SEQUENCE_MATCHER_PAIRS=3000` 与 `REPEAT_RISK_TIME_BUDGET_SECONDS=25`，保持 `truncated/sampled_paragraphs/total_paragraphs/max_comparisons` 返回字段兼容。
- Beta 文档：v0.4.0-beta-docs 已整理 README 和 docs 文档，补充架构、Agent Trace、Risk Level、真实回归结果和部署规划说明。
- local模式：只执行本地格式修复和基础预检，返回 `ai_score=null`、`ai_used=false`。
- ai模式：在 local 格式修复基础上执行 AI/语言审校，返回 AI 语言参考评分和建议；主展示评分仍以格式规则分为准。
- Demo 文件：v0.6.3 已新增人工构造的脱敏模拟论文样本、模板样本和一次 local 模式输出样例，路径见 `docs/DEMO_RESULT.md`。
- Task State：v0.7.0 已新增最小任务状态落盘记录，默认写入 `paper-ai/backend/task_states/{task_id}.json`，用于记录每次 Agent 运行的生命周期状态。
- Task State 文档同步：v0.7.1 已同步 README、架构说明、面试问答、演示脚本和 demo 结果说明，明确 task state 与 agent_trace 的边界。
- Task State Demo 样例：v0.7.2 已新增 `demo_outputs/task_state_sample.json`，用于固定展示 task state 字段结构和 demo 生命周期状态。
- Task State 运行产物治理：v0.7.3 已将 `paper-ai/backend/task_states/` 纳入 `.gitignore`，避免运行 JSON 污染 Git 工作区。
- Agent Trace 前端展示：v0.8.1 已在结果页增加默认折叠的 `agent_trace` 步骤列表，并展示 `task_id` / `task_state_path` 摘要；未读取 task state 文件内容，未改变后端同步接口或核心 pipeline。
- Agent Trace 展示打磨：v0.8.2 已小范围优化 TracePanel 文案、fallback 兜底提示、task state 摘要说明和缺字段保护；未改变上传、预览、下载主流程。
- 前端演示布局打磨：v0.8.4 已优化上传操作区、结果总览、评分变化、修改报告、检查结果、TracePanel、预览与下载的页面层次；未改变后端同步接口、核心 pipeline 或上传/预览/下载主流程。
- 前端窄屏细节修复：v0.8.5 已修复 390px 左右窄屏横向溢出，优化小屏卡片、模式按钮、主按钮和长文本换行；未改变后端核心逻辑或上传/预览/下载主流程。
- 模板运行产物治理：v0.8.6 已忽略 `paper-ai/backend/templates/*.docx` 上传模板副本，避免 demo 后未跟踪运行产物污染 Git 工作区；未改变后端核心逻辑、前端 UI 或上传/预览/下载主流程。
- 前端产品化视觉升级：v0.9.0 已将首页升级为 AI SaaS 产品页 + 工具工作台 + 结果仪表盘风格，增强第一屏吸引力和演示效果；未改变后端核心逻辑、`/agent/run`、上传/预览/下载主流程或依赖文件。
- 前端运行链路修复：v0.9.1 已修复页面点击运行 Agent 时错误提示过于笼统、分类失败后继续运行未透传确认状态的问题；浏览器页面上传 demo 文件、点击运行、生成报告、TracePanel、预览和下载链路已验收通过。
- 前端 fetch 兼容修复：v0.9.2 已统一前端后端请求 base URL，支持 `NEXT_PUBLIC_API_BASE_URL` 覆盖，默认 `http://127.0.0.1:8000`；网络错误会显示实际请求地址，便于定位本地浏览器到 FastAPI 的连接问题。
- 面试演示包：v0.9.3 已新增 `docs/INTERVIEW_DEMO_PACKAGE.md`，并同步 README、DEMO_SCRIPT、INTERVIEW_QA、DEMO_RESULT 和 DEMO_CASE，用于说明 v0.9.2 稳定演示基线、演示流程、架构讲法、项目亮点、边界和面试追问。
- 截图/录屏素材指南：v0.9.4 已新增 `docs/DEMO_SCREENSHOT_GUIDE.md`，整理首页、上传、结果 dashboard、TracePanel、预览、下载和 390px 窄屏等素材清单，用于面试、简历、作品集和演示准备。
- 真实网页截图归档：已将 2026-06-27 的 10 张真实运行截图整理到 `docs/assets/screenshots/real-web-2026-06-27/`，覆盖首页、上传、运行中、结果 dashboard、检查模块、TracePanel、在线预览和下载入口。
- v1.0-showcase 稳定展示版：tag `v1.0-showcase` 已创建并指向 `10904db`；`main` 分支仅在其后继续补充公开前文档和面试材料。

# 最近回归测试结果

最近一次完整回归结果：PASS。

v1.0-showcase 封版整理最小回归结果：PASS。

- `python -m py_compile`：PASS。
- `python test_agent_orchestrator_trace.py`：PASS。
- `python test_smoke_agent_flow.py`：PASS。
- `python run_real_doc_regression.py --manifest test_documents/manifest.csv --mode local --limit 1 --run-id v1_0_showcase_manifest_smoke`：PASS，1/1。
- `python run_real_doc_regression.py --manifest test_documents/generated_manifest.csv --mode local --limit 1 --run-id v1_0_showcase_generated_smoke`：PASS，1/1。
- `npm run build`：PASS。
- heavy_manifest 全量回归：本轮未执行，保留为本地脱敏样本可选长测；历史记录已有 heavy 1/1 PASS。

PASS：

- Agent 能正常运行。
- 本地模式 local 正常：返回 `local_score`，`ai_score=null`，`ai_used=false`。
- AI模式 ai 正常：可运行完整流程；LLM 成功或 fallback 时不应中断主流程。
- local / template / ai fallback smoke test 全部 PASS。
- 标准论文弱结构样例不再被识别为 `unknown`。
- 标题正文混排已能拆分，例如 `4.结语：正文内容...`。
- 真实样本暴露的段落中间标题混排已修复，例如 `...办法。4. 结语：正文内容...` 会拆成前文、标题、正文三段。
- 上传模板后未再出现 `unsupported operand type(s) for *` 阻断错误。
- `C-51` 等异常模板残留已在 smoke test 中验证清理。
- 上传论文正常。
- 上传模板正常，模板缺失字段不会导致 Agent 直接崩溃。
- 不上传模板也可以启动 Agent。
- 在线预览正常：`/preview/{filename}` 返回 HTML。
- v0.3.2 在线预览优化已完成：增强标题层级、正文行距缩进、参考文献分区、表格样式和前端预览失败提示。
- 文件下载正常：`/download/{filename}` 返回 docx。
- 修改报告正常：包含 summary、before_after、change_counts、manual_review_items。
- v0.3.1 格式差异报告增强已完成：新增 format_diff_summary、changed_dimensions、score_delta_by_dimension、auto_fix_count、needs_manual_review_count。
- v0.3.3 参考文献检查已完成：新增 reference_check 字段，并将参考文献风险合并进人工复查项。
- v0.3.4 图表编号检查已完成：新增 figure_table_check 字段，并将图表编号风险合并进人工复查项。
- v0.3.5 Test Corpus 第一步已完成：新增真实论文测试库目录、脱敏说明、manifest 占位清单、回归结果目录和测试计划；未修改业务代码。
- v0.3.5 Test Corpus 第二步已完成：生成 clean、messy、references、figures_tables、template_mismatch 共 10 个脱敏 DOCX 测试样本，并更新 manifest；未修改业务代码。
- v0.3.7 Agent Orchestrator Layer 已完成：新增 agent_trace 顶层字段，用于解释 Agent 计划、工具调用、fallback 和人工复查判断；旧字段保持兼容。
- v0.4.1 Scoring Semantics Refinement 已完成：新增 score_breakdown 评分语义字段，保留 local_score/ai_score/ai_used 等旧字段，避免 AI 语言参考分造成“修完更低分”的误解。
- v0.4.6 Repeat Risk Performance Guard 已完成：提交 `af81c08`（tag: `v0.4.6-repeat-risk-performance-guard`）只修改 `paper-ai/backend/services/plagiarism_checker.py`，为重复风险检测增加最多 300 段参与比较、最多 30000 次相似度比较、`truncated/sampled_paragraphs/total_paragraphs/max_comparisons` 元数据和检测失败 fallback。
- v0.4.6 极端 DOCX 回归 PASS：`extreme_stress_test_thesis.docx` 完整 local Agent 返回 200，约 50.67s 完成，`status=ok`，评分 `78 -> 84`，预览和下载均 PASS，local 模式保持 `ai_score=null`、`ai_used=false`。
- v0.4.6 普通 smoke 回归 PASS：`test_smoke_agent_flow.py` 全部 PASS，覆盖分类、local、模板、AI fallback、预览和下载。
- v0.4.6 fallback 注入测试 PASS：重复风险检测异常时返回低风险占位结构，主流程不因相似度预检失败而中断。
- v0.4.7.1 Resource Stress Test 已完成：`realistic_heavy_thesis.docx` 大小 74.79MB，267 页，2489 段，80 张表，100 张唯一图片，300 条参考文献；分类为 `academic_paper`，置信度 0.90。
- v0.4.7.1 大文档 local Agent 回归 PASS：完整 local Agent 返回 200，`status=ok`，耗时 510.88s，评分 `81 -> 84`，local 模式保持 `ai_score=null`、`ai_used=false`。
- v0.4.7.1 接口与保真审计 PASS：预览接口返回 200，下载接口返回 200；输出文档保持 2489 段、80 张表、100 张图片和 300 条参考文献；图片数量、唯一性和可打开性均通过审计。
- v0.4.7.1 AI fallback 回归 PASS：模拟 AI 故障后主流程不中断，`language_review.mode=local`，耗时 479.86s。
- v0.4.9 Repeat Risk Performance Optimization PASS：`plagiarism_checker` before `196.741s -> 17.724s`，after `181.200s -> 17.928s`，合计 `377.941s -> 35.652s`；74.79MB heavy DOCX 完整 local Agent `510.88s -> 51.209s`；py_compile PASS，smoke PASS，local `ai_score=null` / `ai_used=false` PASS，预览 PASS，下载 PASS。
- v0.4.0-beta-docs 已完成：新增根目录 README 和 docs/ 文档，项目可展示、可运行、可说明。
- v0.5.0 批量真实样本回归入口已完成：新增 `run_real_doc_regression.py`，支持 small/medium/large 文件大小分桶、case/category/limit 过滤、非标准论文自动确认参数和 `regression_results/<run_id>/` 结果输出。
- v0.5.0 CNKI / GB/T 7714 来源规范已完成：新增公开/授权来源入库边界说明，禁止将登录、付费、验证码或授权受限的 CNKI 正文全文作为自动下载测试集。
- v0.5.0 批量回归脚本验证 PASS：`generated_manifest.csv --limit 2` 为 2/2 PASS；`manifest.csv` 完整 10 个样本为 10/10 PASS；`test_smoke_agent_flow.py` PASS。
- v0.5.1 / real-doc-regression-boundary-pass 已完成：`run_real_doc_regression.py` 支持区分 `BOUNDARY_WARNING` 与 blocking `FAIL`；`generated_manifest.csv` 中 3 个 `reports_*` hybrid 样本标记为 `classification_boundary`，不再计入阻断级 FAIL；generated 回归为 21 PASS + 3 boundary warnings + 0 blocking FAIL。
- v0.5.1 Heavy DOCX Stress Regression 已接入：`D:\新下载\realistic_heavy_thesis.docx` 已复制到 `test_documents/real/realistic_heavy_thesis.docx`，新增 `test_documents/heavy_manifest.csv`；74.79MB 样本 local 回归 PASS，耗时 57.558s，分类 `academic_paper`，输出 DOCX / 修改报告 / 预览 / 下载均通过，local `ai_score=null`、`ai_used=false`。
- 历史版本总结和受控试用文档已归档到 `docs/archive/`；包括 v0.5.1-v0.5.4 总结、beta readiness、controlled beta 用户指南和反馈表。
- `before_score` 和 `after_score` 正常返回。
- 首页 `http://127.0.0.1:3000` 返回 200。
- 核心接口无 404：`/health`、`/document/classify`、`/agent/run`、`/preview/{filename}`、`/download/{filename}`。
- 前端按钮不会因为 templateFile 为空、preview 为空、result 为空、document_type=unknown 而永久 disabled。

FAIL：

- 当前最新回归没有阻断级 FAIL。

Current Bottleneck：

- 当前功能层面没有阻断级 FAIL，适合进入 v1.0-showcase 封版整理。
- 主要瓶颈已从功能修复转为版本口径、演示材料和回归记录统一。
- `v1.0-showcase` tag 是推荐稳定展示基线；`main` 分支保留 tag 之后的公开前文档补充；`v0.9.4-demo-screenshot-package` 保留为上一阶段截图包 tag。
- 本阶段不做核心格式化算法重构，不改上传、预览、下载主流程，不破坏 local/ai 模式兼容。
- 本阶段不能改动 tag，不能移动、删除或重建 `v0.9.4-demo-screenshot-package` tag。

回归后仍需关注：

- AI模式实际内容修改量偏低。
- 修改报告对 AI 增强的表达可能强于实际改写效果。
- 参考文献识别仍可能偏弱。

# 当前已知Bug

## P0

- 当前没有阻断级 P0。
- Known High Risk：无阻断级风险。
- v0.4.9 已修复 74.79MB heavy DOCX 重复风险检测性能瓶颈，`plagiarism_checker` 合计耗时 `377.941s -> 35.652s`，完整 local Agent `510.88s -> 51.209s`；当前无阻断级性能风险。
- 已修复极端 DOCX 在重复风险检测阶段超时的问题：`check_repeat_risk` 已加入性能上限和 fallback，避免 1000+ 段文档触发不可控的两两 `SequenceMatcher` 比较。
- 已修复 standard paper 被识别为 `unknown` 的弱结构样例问题。
- 已修复标题正文混排：例如 `4.结语：正文内容...` 可拆成独立标题和正文。
- 已修复段落中间标题正文混排：例如 `...办法。4. 结语：正文内容...` 可拆成独立标题和正文。
- 已修复模板解析 `unsupported operand type(s) for *` 类阻断风险，模板异常时可 fallback。
- 已修复 `C-51` 等异常模板残留的基础清理规则。
- local / template / ai fallback smoke test 全部 PASS。

## P1

- AI内容评分可信度仍需提升：`ai_language_score` 已改为参考分，不参与主评分，但内容修改量与语言建议质量仍需继续增强。
- AI审校偏浅：当前主要是词语级替换，不能稳定完成段落级学术润色。
- 关键词规范不足：能修正“关键字/关键词”标签，但不能稳定规范关键词内容。
- 文档分类仍有边界问题：结构较弱、摘要/关键词/参考文献缺失的论文可能识别不稳定。
- 模板提取仍有限：复杂模板、目录、页眉页脚、脚注、图片题注、公式编号未完整处理。
- 修改报告可信度需增强：需要更明确区分格式修改、内容修改和 AI 实际改写。

## P2

- UI仍需优化：当前优先保证可用性，视觉和交互精细度还有提升空间。
- 前端中文文案和编码需要持续检查：PowerShell 中曾出现乱码显示，需保证文件按 UTF-8 保存。
- 仓库清理不足：uploads、outputs、日志、构建产物等容易污染长期上下文。
- 在线预览只保留基础结构，不追求 Word 完全还原。

# 当前风险

## 技术风险

- Word 文档格式复杂：python-docx 对目录、页眉页脚、批注、脚注、公式、图片题注等支持有限。
- AI输出不可控：LLM 可能返回非 JSON、空建议或过度改写，需要继续强化解析和保护策略。
- 评分系统解释风险已缓解：v0.4.1 已明确格式规则分、风险稳定分、AI语言参考分和最终评分；后续仍需继续绑定真实内容修改量。
- 文档分类存在误判风险：非标准论文、课程作业、实验报告和弱结构论文之间边界不稳定。
- 文件编码风险：中文文案在不同终端下可能显示乱码，后续修改需注意 UTF-8。
- 运行产物膨胀风险：uploads、outputs、`.next`、`node_modules`、日志文件会增加仓库体积和 AI 上下文成本。

## 产品风险

- 用户可能误以为 AI 已经深度修改论文内容，但当前主要能力仍是格式修复。
- 如果最终评分较高但内容改动很少，会损害用户信任。
- 修改报告如果没有展示真实改动量，会显得像“包装过度”。
- 非论文文档如果被强制套用论文格式，可能造成用户误解。
- 仅提供最终结果而缺少修改前后对照，会让用户难以判断 Agent 是否真的有效。

# 下一阶段目标

## v1.0-showcase 稳定展示版

- 统一 README、PROJECT_STATUS、TODO 和 docs 演示材料中的版本口径。
- 明确当前推荐稳定展示基线为 `v1.0-showcase` tag，而不是旧的 `v0.9.2` 或 `v0.9.4`。
- 明确 `v0.9.4-demo-screenshot-package` 是上一阶段截图包 tag。
- 明确 `v1.0-showcase` tag 指向 `10904db`，`main` 分支包含该 tag 之后的公开前文档和面试材料补充。
- 冻结当前可展示能力、边界说明、demo 输入输出、截图资产和回归检查清单。
- 本阶段只做封版整理，不新增核心功能，不改后端 pipeline / formatter / analyzer / classifier / preview / download 主逻辑。

## v1.1 延期项

- 深度内容级修改能力。
- 完整 task state 可视化。
- 异步队列 / 断点续跑。
- 学校模板库。
- 更强的模板规则摘要。
- 更完整的修改前后 Diff。
- 真实授权用户样本扩展。
- AI 评分与真实修改量强绑定。
- 云端部署与多用户系统。

## v0.9.5 Demo Trace UI（已纳入 v1.0-showcase）

- 增强 Agent Trace 可视化，让用户更清楚看到每一步处理、耗时、fallback 和任务状态摘要。
- 增加模板规则摘要展示，让上传模板解析出的关键格式规则可以被解释和演示。
- 增加修改前后 Diff 展示，让用户能判断 Agent 实际改了什么，而不是只看到最终文件。
- 保持现有上传、预览、下载功能不变。
- 保持 local/ai 模式兼容，local 模式仍必须 `ai_score=null`、`ai_used=false`。
- 不大规模重构，不重写核心格式化算法，不改动 tag，不移动 `v0.9.4-demo-screenshot-package` tag。

## 未来1周

- 在线预览优化（v0.3.2 已完成）。
- 格式差异报告增强（v0.3.1 已完成）。
- 参考文献检查（v0.3.3 已完成）。
- 图表编号检查（v0.3.4 已完成）。
- 学校模板库。

## 未来1个月

- 从格式Agent升级到内容Agent：
  - 系统识别口语化表达。
  - 系统识别主观化表达。
  - 系统识别情绪化表达。
  - 识别逻辑不通顺、观点跳跃、因果不清。
  - 识别关键词内容不规范。
  - 输出段落级问题清单。
- 从内容Agent升级到真正论文修改Agent：
  - 将修改分为安全自动修改、建议型修改、需要人工确认的修改。
  - AI评分绑定真实修改量和未解决问题数量。
  - 在线预览支持修改前后对照。
  - 修改报告明确展示“改了什么、没改什么、为什么没改”。
- 长期维护优化：
  - 清理运行产物。
  - 完善 `.gitignore`。
  - 保持 `AI_CONTEXT.md` 和 `PROJECT_STATUS.md` 随版本更新。
  - 每次功能变更后执行固定回归清单。

## v0.5.4 Summer Internship Showcase

- 新增 `paper-ai/backend/services/agent_pipeline.py` 作为统一调度层，`/agent/run` 已切换到该层调用。
- 新 `agent_trace` 为逐步列表，每项包含 `step`、`status`、`duration_ms`、`fallback_used`、`message`。
- 旧解释型 trace 保留为 `agent_trace_detail`，旧字段 `modification_report`、`reference_check`、`figure_table_check` 保持兼容。
- 新增/更新 `docs/ARCHITECTURE.md` 和 `docs/DEVELOPMENT_LOG.md`，用于说明架构、处理流程和 fallback 策略。
- 本轮回归：`py_compile` PASS；现有后端测试 PASS；`npm run build` PASS。

## v0.6.1 Demo Polish

- 本轮只做展示文档增强，不修改核心业务逻辑、`agent_pipeline` 执行逻辑、`/agent/run` 接口行为、前端交互、测试断言或依赖文件。
- README 已补充项目定位、技术栈、核心功能、处理流程、启动方式、测试命令、当前版本和展示亮点。
- `docs/ARCHITECTURE.md` 已补充架构图、`agent_pipeline`、`agent_trace`、local/ai fallback 和旧字段兼容说明。
- 新增 `docs/DEMO_SCRIPT.md` 和 `docs/archive/INTERVIEW_QA.md`，用于暑期实习面试演示历史记录。
- 当前仍定位为格式 Agent；不宣传为论文代写、正式查重或深度内容改写系统。
## v0.6.2 Demo Samples

- 本轮只新增/更新演示样本目录说明和固定演示案例文档，不修改核心业务逻辑。
- 新增 `demo_inputs/README.md`，说明推荐输入样本路径：`messy_paper_sample.docx` 和 `template_sample.docx`。
- 新增 `demo_outputs/README.md`，说明推荐输出样例路径：`formatted_result_sample.docx`、`report_sample.json`、`agent_trace_sample.json`。
- 新增 `docs/DEMO_CASE.md`，说明固定面试演示案例、推荐样本特征、处理流程、重点观察字段和 1 分钟讲解话术。
- 更新 README 和 `docs/DEMO_SCRIPT.md`，把固定演示样本目录纳入展示流程。
- 当前仍未新增真实脱敏 DOCX 样本，也未新增真实运行输出；后续需要补充脱敏真实论文、模板和一次真实输出样例。

## v0.6.3 Real Demo Files

- 本轮新增人工构造的脱敏模拟 DOCX 输入样本和模板样本，不使用真实用户论文原文。
- 新增 `demo_inputs/messy_paper_sample.docx`，包含封面、中文摘要、英文摘要、关键词、正文 5 节、图表标题和参考文献，并故意设置标题、缩进、行距、图表编号引用和参考文献编号检查点。
- 新增 `demo_inputs/template_sample.docx`，包含一级标题、二级标题、正文、摘要、参考文献、图题和表题样式示例。
- 使用现有 `run_agent_pipeline(...)` local 模式生成一次真实输出样例：
  - `demo_outputs/formatted_result_sample.docx`
  - `demo_outputs/report_sample.json`
  - `demo_outputs/agent_trace_sample.json`
- 本次运行结果：`status=ok`，`mode=local`，`classification.document_type=academic_paper`，`confidence=0.95`，`before_score=80`，`after_score=86`，local 模式保持 `ai_score=null`、`ai_used=false`。
- 新增 `docs/DEMO_RESULT.md`，记录输入/输出路径、运行方式、重点字段、限制和验收情况。
- 本轮未修改核心业务逻辑、前端交互、测试断言或依赖文件；DOCX 渲染视觉 QA 因当前环境缺少 LibreOffice/`soffice` 跳过。

## v0.7.0 Task State Minimal

- 新增 `paper-ai/backend/services/task_state.py`，提供 `task_id` 生成、task state 路径定位、UTF-8 JSON 原子写入、初始化和更新能力。
- `run_agent_pipeline(...)` 已在任务开始时写入 `running`，成功时写入 `succeeded`，异常或内部错误时写入 `failed`。
- `/agent/run` 仍保持同步执行语义；返回结果只额外增加 `task_id` 和 `task_state_path`，旧字段继续兼容。
- task state 记录任务生命周期；`agent_trace` 仍记录处理步骤，两者职责不互相替代。
- 当前边界：这还不是完整断点续跑，也不是异步队列；暂未实现 task state 清理策略和前端可视化。

## v0.7.1 Docs Sync Task State

- 本轮只同步文档，不修改核心业务逻辑、`task_state.py`、`agent_pipeline.py`、`main.py`、前端交互或测试断言。
- README 已补充 task state 能力、字段、写入路径和边界。
- `docs/ARCHITECTURE.md` 已补充 `task_state.py` 在架构中的位置，以及 `paper-ai/backend/task_states/{task_id}.json` 写入说明。
- `docs/archive/INTERVIEW_QA.md` 已补充 task state 与 agent_trace 的区别、为什么不直接做异步队列、当前解决的问题和限制。
- `docs/DEMO_SCRIPT.md` 已补充 task state 演示步骤。
- `docs/DEMO_RESULT.md` 在 v0.7.1 时记录了缺少固定 `demo_outputs/task_state_sample.json` 的缺口；该缺口已在 v0.7.2 补齐。
- 当前仍不是完整断点续跑或异步队列，也没有前端 task state 可视化界面。

## v0.7.2 Task State Sample

- 本轮只新增固定 demo JSON 样例和同步文档，不修改核心业务逻辑、前端交互或测试断言。
- 新增 `demo_outputs/task_state_sample.json`，字段与当前 `report_sample.json` 和 `agent_trace_sample.json` 保持一致。
- `docs/DEMO_CASE.md` 已补充样本来源边界：人工构造、脱敏模拟、不来自真实用户论文、不来自 CAJ 原文、不用于论文代写。
- `docs/DEMO_RESULT.md` 和 `docs/DEMO_SCRIPT.md` 已补充 task state 样例展示说明。
- 当前仍不是完整断点续跑或异步队列，也没有前端 task state 可视化界面。

## v0.7.3 Task State Cleanup

- 本轮只做运行产物治理和文档同步，不修改核心业务逻辑、`agent_pipeline.py`、`main.py`、前端交互或测试断言。
- `.gitignore` 已新增 `paper-ai/backend/task_states/`，运行生成的 task state JSON 不应进入 Git。
- `demo_outputs/task_state_sample.json` 仍是固定 demo 样例，应继续保留在 Git 中。
- README 已补充当前不是完整工业级 Agent。
- `docs/DEMO_SCRIPT.md` 和 `docs/DEMO_RESULT.md` 已补充 demo 样本不来自 CAJ 原文。
- 本轮未修改 `task_state.py`，后续如需自动清理可单独做轻量清理函数或维护命令。

## v0.8.1 Trace UI Minimal

- 本轮只在前端结果页增加最小 Agent Trace 展示，不修改后端核心业务逻辑、`agent_pipeline.py`、`main.py` 或 `/agent/run` 同步语义。
- `paper-ai/frontend/app/page.tsx` 已新增默认折叠的 Trace 面板，展示 `agent_trace` 的 `step`、`status`、`message`、`duration_ms`、`fallback_used`。
- Trace 面板同时展示 `task_id` 和 `task_state_path` 摘要，明确 `task_state_path` 是后端本地运行产物路径，仅用于开发/演示排查。
- 前端不读取 task state 文件内容，不展示 `agent_trace_detail`，不把 `fallback_used=true` 表述为严重失败。
- 当前仍不是异步队列，也不是完整断点续跑或完整工业级 Agent。

## v0.8.2 Trace UI Polish

- TracePanel 标题和说明已调整为“Agent 执行过程”，强调 `agent_trace` 是步骤级执行记录，用于展示处理链路、耗时和 fallback 情况。
- `fallback_used=true` 显示为“已使用 fallback / 本地规则兜底”，不作为严重失败展示。
- `task_id` 显示为“任务 ID”，`task_state_path` 显示为“后端任务状态文件路径”，并说明前端当前不会读取该文件内容，也不代表异步队列或任务恢复能力。
- 对缺失 `message`、`duration_ms`、`status` 的 trace 项增加温和默认展示，避免出现 `undefined` 或 `NaN`。
- 本轮未修改后端接口、核心 pipeline、上传/预览/下载主流程或测试断言。

## v0.8.4 UI Polish Layout

- 本轮主要优化前端页面层次和演示观感，不修改后端业务逻辑。
- 上传区已整理为“开始处理”工作区，论文上传、模板上传、模式选择和运行按钮层次更清楚。
- 结果页已按总览、评分变化、修改报告、评分模块、检查结果、重复风险、Agent 执行过程、预览与下载组织。
- before_score / after_score 在结果总览中更醒目，并展示提升值、模式、AI 参考参与状态和任务 ID。
- TracePanel 仍默认折叠，继续只展示 `agent_trace` 列表和 `task_id` / `task_state_path` 摘要，不读取 task state 文件内容，不展示 `agent_trace_detail`。
- 本轮未修改 `/agent/run` 同步语义、核心 pipeline、上传/预览/下载主流程或测试断言。

## v0.8.5 UI Polish Details

- 本轮只修前端 UI 细节，重点解决 390px 左右窄屏下页面轻微横向溢出问题。
- 已为页面根容器、工作区、主要卡片、按钮、TracePanel 和报告卡片补充 `max-width`、`min-width: 0`、自然换行和小屏内边距规则。
- 窄屏下上传卡片、模式卡片、操作按钮、结果区和检查区会收敛为单列，避免撑破 viewport。
- `task_state_path`、任务 ID、文件名、说明文字等长文本继续允许换行，不撑破页面。
- 本轮未修改后端核心逻辑、`/agent/run` 同步语义、上传/预览/下载主流程或测试断言。

## v0.8.6 Template Runtime Cleanup

- 本轮只做运行产物治理，修复 demo 上传模板后生成 `paper-ai/backend/templates/template_sample.docx` 未跟踪文件的问题。
- 已删除当前未跟踪运行产物 `paper-ai/backend/templates/template_sample.docx`。
- 已在 `.gitignore` 中新增 `paper-ai/backend/templates/*.docx`，未来上传模板副本不应进入 Git 工作区。
- `demo_inputs/template_sample.docx` 仍是固定 demo 输入样本，应继续被 Git 跟踪。
- 本轮未修改后端核心逻辑、前端 UI、接口语义、上传/预览/下载主流程或测试断言。

## v0.9.0 UI Landing Redesign

- 本轮只做前端视觉和布局升级，将首页从普通工具页提升为更适合演示的 AI SaaS 产品页风格。
- 首屏已组织为 Hero、能力卡片、静态仪表盘预览和上传工作台。
- 上传论文、上传模板、模式选择和启动 Agent 仍沿用原有 state、input 和 fetch 语义。
- 结果区继续按 dashboard 风格展示评分变化、修改报告、检查结果、TracePanel、预览和下载。
- TracePanel 仍默认折叠，只展示 `agent_trace` 步骤列表和 `task_id` / `task_state_path` 摘要；不读取 task state 文件内容，不展示 `agent_trace_detail`。
- 本轮未修改后端核心逻辑、`/agent/run` 同步接口、上传/预览/下载主流程、测试断言或依赖文件。
- 当前仍不是异步队列，也不是完整断点续跑或完整工业级 Agent。

## v0.9.1 UI Run Flow Fix

- 本轮只做前端运行链路小范围修复，不改后端核心逻辑、不改 UI 视觉布局、不改 `/agent/run` 同步语义。
- 修复点包括：统一读取 JSON/非 JSON 响应，避免 `response.json()` 异常被吞成笼统“后端服务未运行”；分类失败但用户继续运行时，向后端透传 `allow_non_paper=true`。
- 浏览器真实点击 demo 流程已通过：上传论文、上传模板、选择本地规则模式、点击运行、生成报告、展示 TracePanel、在线预览和下载均可用。
- 当前仍不是异步队列，也不是完整断点续跑或完整工业级 Agent。

## v0.9.2 UI Fetch Compat Fix

- 本轮只做前端 fetch 兼容性修复，不改后端核心逻辑、不改 UI 视觉布局、不改 `/agent/run` 同步语义。
- 前端所有后端请求统一通过 `apiUrl(...)` 拼接，默认 base URL 为 `http://127.0.0.1:8000`，可用 `NEXT_PUBLIC_API_BASE_URL` 覆盖。
- `document/classify`、`agent/run`、`preview` 和下载链接不再分散拼接 host，避免本地调试时混用 `localhost` / `127.0.0.1` 或 `http` / `https`。
- 网络错误提示会包含实际请求 URL，便于定位后端未启动、端口不一致或浏览器本地文件上传兼容问题。
- 当前仍不是异步队列，也不是完整断点续跑或完整工业级 Agent。

## v0.9.3 Interview Demo Package

- 当时 v0.9.2 是面试/演示稳定代码基线，已通过 final demo check；当前稳定展示基线已切换为 `v1.0-showcase` tag。
- 本轮主要整理展示材料，新增 `docs/INTERVIEW_DEMO_PACKAGE.md`。
- README、DEMO_SCRIPT、INTERVIEW_QA、DEMO_RESULT、DEMO_CASE 和 DEVELOPMENT_LOG 已同步 v0.9.3 演示口径。
- 本轮未修改后端核心逻辑、前端 UI、接口语义、依赖文件或 demo 输入输出文件。
- 当前仍不是论文代写、正式查重、异步队列、完整断点续跑或完整工业级 Agent。

## v0.9.4 Demo Screenshot Package

- 本轮主要整理截图/录屏素材指南，新增 `docs/DEMO_SCREENSHOT_GUIDE.md`。
- 截图清单覆盖首页 Hero、上传工作台、文件已选择、运行中状态、结果 dashboard、评分 `80 -> 86`、修改报告、参考文献/图表检查、TracePanel 折叠/展开、在线预览、下载入口和 390px 窄屏。
- 已补充真实网页截图素材目录 `docs/assets/screenshots/real-web-2026-06-27/`，本次真实截图评分为 `81 -> 87`，可作为 README、作品集和面试静态展示素材。
- `docs/DEMO_SCRIPT.md` 已补充 60-90 秒录屏顺序和重点停顿画面。
- `docs/INTERVIEW_DEMO_PACKAGE.md` 已增加截图/录屏素材建议，并指向 `docs/DEMO_SCREENSHOT_GUIDE.md`。
- 本轮未修改后端核心逻辑、前端 UI、接口语义、依赖文件或 demo 输入输出文件。
- 当前仍不是论文代写、正式查重、异步队列、完整断点续跑或完整工业级 Agent。

## v0.9.5 Demo Trace UI

- v0.9.5 trace UI 相关增强已纳入 `v1.0-showcase` 稳定展示版，并在 `main` 后续文档补充中继续保持一致口径。
- 目标一：增强 Agent Trace 可视化，提升执行链路、耗时、fallback 和任务状态解释能力。
- 目标二：增加模板规则摘要展示，让模板解析结果能以用户可理解的方式出现在结果页。
- 目标三：增加修改前后 Diff 展示，让报告和预览更贴近真实修改量。
- 范围限制：这是 UI 展示增强阶段，不是核心格式化算法重构，不修改后端核心 pipeline，不改变 `/agent/run` 同步语义。
- 兼容要求：保持现有上传、预览、下载功能不变，保持 local/ai 模式兼容。
- 版本治理：不得改动 tag，不得移动、删除或重建 `v0.9.4-demo-screenshot-package` tag。

## PaperOps Agent v2.0 P0.1 Planning Foundation

- 已新增 `DocumentModel`：从真实 DOCX 与现有分类/分析逻辑构建段落、章节、表格、图片、标题、摘要、关键词、参考文献、样式摘要和结构指纹；不确定信息保留 warning 与 confidence。
- 已新增 Rule normalization：在不改写 `template_extractor` 的前提下，将 template profile 或默认 profile 规范化为带 source、evidence、confidence、risk 和 auto-fix 标记的规则；模板 extraction fallback 不会伪装为模板证据。
- 已新增 Planner：根据 DocumentModel、规则和现有 analyzer breakdown 生成 ExecutionPlan；已满足规则不生成修改步骤，引用/图表风险和低置信标题只进入人工复核步骤。
- `/agent/run` 主链路已真实构建并返回 `document_model`、`rules`、`execution_plan`，但本阶段不让 ExecutionPlan 驱动 formatter。
- 新增 `test_p0_1_planning_foundation.py`；静态检查、既有后端测试、smoke、单例 manifest 回归和前端 build 均 PASS。
- 未改动 formatter 核心行为、前端、既有 Trace、`/agent/run` 旧字段、依赖或 v1.0-showcase tag。下一步为 P0.2：状态机与 Verifier 接入。
