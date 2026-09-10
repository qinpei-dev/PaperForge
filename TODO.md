# TODO

## [DONE] PaperForge Day9-P2 — Tenant Context & Resource Isolation

目标：建立 Tenant → Membership → Tenant Context → Template Scope → Query Isolation → Task Provenance 的最小 SaaS 资源边界，不扩展完整 RBAC、tenant switcher 或管理后台。

已完成：

- 新增 Tenant / TenantMembership，用户可属于多个 tenant；注册、登录、startup 对 personal tenant 幂等兼容。
- 新增统一 Tenant Context；personal tenant 或 membership disabled 时明确拒绝，不静默切换。
- Template 支持 platform / tenant scope；平台模板共享，不为 tenant 复制。
- 数据库级保证 platform identity 唯一、同 tenant identity 唯一，同时允许不同 tenant 重名。
- Registry、Repository、templates API 和 task/agent 模板解析 tenant-aware，跨 tenant 精确 ID 解析返回 404。
- Task 显式保存 tenant_id、user_id 和 template provenance；Task detail、SSE、Artifact、预览和下载按 tenant 隔离。
- 新增 Alembic `0005_day9_tenant_isolation`，覆盖 existing users/templates/tasks backfill，支持从 0004 原地升级。
- legacy uploaded template 与不传 template_id 的默认流程保持兼容；匿名路径仅能接触平台资源。

验收：backend pytest 59 passed；Day9-P2 专项 7 passed；compileall、Alembic 0005、frontend production build、git diff check 全部 PASS。

下一步：等待 Day9-P2 用户验收；本轮不 commit、不 push、不创建 tag。

## [DONE] PaperForge Day9-P1 — Template Persistence

状态：**PASS（等待用户验收）**

完成：

- 新增正式 `Template` SQLAlchemy 模型，使用 `(template_id, version)` 数据库唯一约束、JSON metadata、状态和时间戳。
- 新增 Alembic `0004_day9_template_persistence` migration。
- 新增最小 `TemplateRepository`，支持 create、get、versions、list/filter、status 更新、exists 与 resolve candidates。
- 新增 Persistence Service：内置模板首次 bootstrap 写入，后续启动不重复插入且绝不覆盖已存在模板的 status。
- P0 Registry 保持 register/get/list/resolve 语义；startup 与 API 请求从 DB 刷新 Registry。
- `GET /templates`、`POST /tasks`、`POST /agent/run` 现由持久化 Registry 解析。
- 验证动态插入 `test-university-thesis / 2030.1` 后可 list/resolve，无需修改静态 Python 模板定义。
- legacy uploaded template 继续是 ephemeral compatibility path，不写入正式表。
- 新增 `test_template_persistence.py`；后端 pytest 52 passed，Python compileall、Alembic upgrade 到 `0004`、frontend build、git diff check PASS。

下一步：等待 Day9-P1 用户验收；本轮暂不 commit、不 push、不创建 tag。

## [DONE] PaperForge Day9-P0 — Multi-template Template Registry

状态：**PASS（等待用户验收）**

完成：

- 新增统一 `TemplateRegistry`，支持 register、get、list、resolve。
- 模板定义包含稳定 `template_id`、name、school、document_type、version、status、source、locator 和 metadata。
- 支持同一 template family 多版本、精确 ID/version 解析、metadata 匹配、默认模板兼容，以及不存在、歧义、disabled 明确失败。
- 内置通用默认规则和版本化 bundled DOCX；旧请求不传 `template_id` 与旧模板上传流程保持兼容。
- result、task state、Agent Trace、修改报告和 Task Detail 可追踪实际 template ID/version。
- 新增 `GET /templates`；`POST /tasks` 与 `POST /agent/run` 新增可选 `template_id`、`template_version`。
- 前端新增最小 Template Selector，并在同步结果与异步任务详情展示 template provenance。
- Registry 返回深拷贝定义，模板解析结果按调用生成，未发现跨模板共享可变状态。
- 未修改数据库结构、Executor 或 SSE 协议；未扩展到用户模板管理、多租户模板持久化或模板市场。
- 新增 `test_template_registry.py`；后端 pytest 47 passed，Python compileall、frontend build、git diff check PASS。

下一步：等待 Day9-P0 用户验收后，再决定是否 commit；本轮暂不 commit、不 push。

## [DONE] PaperForge Day8-P1 — Template Rule Extraction Enhancement

状态：**PASS**

完成：

- `TemplateAnalysis` 新增 `inherited_rules`、`override_rules`、`rule_priority` 和 `effective_rules`。
- 解析 Normal、Heading 和实际使用的段落样式的 `base_style` 继承链。
- abstract、references、appendix、cover 可生成高优先级区域覆盖规则；cover 默认追加保护规则。
- 按模板基础（10）→ 样式继承（20）→ 区域覆盖（30）确定性合并 `effective_rules`。
- AI Reasoning 优先消费匹配 scope 的 effective rule，旧调用保持兼容。
- 未修改 Executor、SSE 协议或数据库结构；新增 `test_template_rules.py`。
- 专项测试 13 passed，全量后端 pytest 40 passed，Python 编译和 diff 检查 PASS。

下一步：进入 Day9 Multi-template SaaS，设计模板知识的多模板存储、选择与隔离边界。

## [DONE] PaperForge Day8-P0 — Template Intelligence Layer

状态：**PASS**

完成：

- 新增 `backend/services/template_intelligence.py`，生成可序列化 `TemplateAnalysis`。
- 支持 cover、abstract、table_of_contents、body、references、appendix 区域识别。
- 提取 font、size、bold、alignment、spacing、margins 格式规则。
- 识别 cover fields、fixed headers、fixed tables 保护区域。
- 接入 Document Intelligence → Template Intelligence → AI Reasoning；pipeline 结果和 task state 新增 `template_analysis`。
- 未修改 Executor、SSE 协议或数据库结构；旧 reasoning 调用和旧 task state 保持兼容。
- 新增 `test_template_intelligence.py`；专项测试 10 passed，全量后端 pytest 37 passed，Python 编译 PASS。

下一步：进入 Day8-P1 Rule Extraction Enhancement，增强按区域/样式继承的规则提取。

## [DONE] PaperForge Day7-P2 Paper Quality Intelligence

状态：**PASS**

完成：

- 新增 `backend/services/paper_quality.py`，基于 document analysis、reasoning results 和 verification results 生成四维质量报告。
- 支持 format、structure、reference、visual 维度，并保留每个维度的 evidence。
- 接入 Verifier 后处理链路，结果和 task state 新增 `quality_report`。
- 不修改 Executor、SSE 协议或数据库；旧任务缺少 quality_report 时保持兼容。
- 新增 `test_paper_quality.py`；全量后端 pytest、编译和 diff 检查通过。

## [DONE] PaperForge AI Reasoning Layer

状态：**PASS**

完成：

- 新增 `backend/services/ai_reasoning.py`，对标题、正文段落、参考文献和图表格式问题输出结构化解释、建议、风险等级和 confidence。
- Planner 的 `PlanStep` 增加可选 `reasoning`，旧的 `build_execution_plan` 调用保持兼容。
- pipeline 结果和 task state 新增 `reasoning_results`；不修改 Executor、SSE 协议或数据库结构。
- 新增 `test_ai_reasoning.py`，覆盖 reasoning、confidence、Planner 接入和旧 state 初始化兼容。
- 全量后端 pytest 31 passed，Python 编译和 `git diff --check` PASS。

## [DONE] PaperForge Day 7 Document Intelligence Layer

状态：**PASS**

完成：

- 新增 `backend/services/document_intelligence.py`，生成可序列化 `DocumentAnalysis`。
- 在既有 parse/model 与 Planner 之间接入中英文论文结构识别和段落语义分类。
- 将 `document_analysis` 暴露在 pipeline 结果并保存到 task state；旧任务/旧结果缺少该字段时保持兼容。
- 不修改 Executor、DOCX formatter、SSE 协议或数据库结构。
- 新增 4 项测试；全量后端 pytest 28 passed，Python 编译和 `git diff --check` PASS。

下一步建议：进入 Day7-P1 AI reasoning 的窄范围设计，先只消费分析结果并输出可解释建议，不直接执行高风险内容改写。

## [DONE] PaperForge V2 Final Acceptance

状态：**READY**

完成：

- V2 capability matrix 26/26 PASS
- formatting verification closure
- content review closure
- provenance closure
- suggestion confirmation closure
- stale conflict
- confirmed DOCX verification
- verified score credibility
- frontend integration
- real DOCX regression 10/10 PASS

## [DONE] PaperForge Day 1 SaaS 基础升级

状态：**PASS**

完成：

- SQLAlchemy ORM 与 Alembic 初始迁移
- PostgreSQL Docker service
- User / Workspace / Project / Task / Artifact 数据模型
- scrypt 密码 hash 与 JWT Authentication
- 默认 Workspace 自动创建
- Workspace / Task / Artifact 用户隔离
- 登录页、注册页和 Dashboard
- SaaS 专项测试 4 passed，后端 pytest 9 passed，前端 build PASS

边界：

- 保留本地文件系统上传/输出逻辑
- `AUTH_REQUIRED=false` 保留单机兼容模式
- Docker 镜像构建需 Docker Desktop daemon 可用后复验

## [DONE] PaperForge Day 2 Task 生命周期接入

状态：**PASS**

完成：

- 新增认证的 `POST /tasks`，创建 pending 任务并同步接入现有 Agent Pipeline
- Task 生命周期持久化为 pending → running → completed / failed
- 自动保存 Agent trace、score、输出 DOCX Artifact 和 JSON report Artifact
- `GET /tasks` / `GET /tasks/{task_id}` 补充任务中心字段与 trace 详情
- 首页工作台切换为 Task API，Dashboard 展示最近任务并支持进入任务详情
- 新增 Task 成功执行、Artifact 持久化和跨用户访问隔离测试
- SaaS 测试 6 passed，全量 pytest 11 passed，前端 build PASS

边界：

- 当前仍为同步任务编排，不是异步队列或断点续跑
- 保留 `/agent/run` 旧接口和 `AUTH_REQUIRED=false` 本地兼容模式

## [DONE] PaperForge Day 3 SaaS 产品化增强

状态：**PASS**

完成：

- Task 增加兼容的论文名称、修改前评分和 Day 3 Alembic 迁移。
- 复用 Agent Trace 生成 analyzing → planning → executing → verifying → completed / failed 的详情页流程展示。
- Task Detail 展示论文名、创建时间、状态、评分变化、Trace、修改后 DOCX 和分析报告下载。
- Dashboard 展示 Workspace、总任务数、已完成、处理中和最近任务。
- 新增 StorageService、LocalStorage 默认实现和 S3Storage 预留接口，保持 `uploads/`、`outputs/` 原路径。
- Compose 补充服务健康检查、数据库/JWT/API 环境变量说明和根目录 `.env.example`。

验收结果：`git diff --check`、全量 `pytest`（11 passed）、前端 `npm run build`、`docker compose --env-file .env.example config --quiet`、`compileall`、Alembic head 和敏感/临时文件检查均 PASS。

## [DONE] PaperForge Day 4 Agent Runtime 增强

状态：**PASS**

完成：

- 新增兼容旧任务的 `Task.workflow_stage` 与 Alembic 0003 migration。
- `run_agent_pipeline` 新增可选 progress callback，阶段顺序稳定，callback 异常不影响主流程。
- SaaS Task 实时持久化 workflow stage，API 返回 `workflow_stage` / `progress`。
- Task Detail 与 Dashboard 展示当前 Agent 阶段。
- 生产模式缺失 `JWT_SECRET_KEY` 时禁止启动，本地开发保留兼容 fallback；Compose 显式使用 production。
- 新增 workflow、失败、旧任务兼容和用户隔离测试。

验收结果：Day 4 新增测试通过，全量 `pytest` 16 passed，frontend `npm run build` PASS，`compileall` PASS，Alembic migration PASS，Compose config PASS，`git diff --check` PASS。

## [DONE] PaperForge Day 5 轻量异步任务执行

状态：**PASS**

完成：

- `POST /tasks` 创建任务后立即返回 `task_id`、`pending` 状态，不再占用同步 HTTP 生命周期执行 Agent。
- 新增进程内 `TaskWorker`，无 Redis/Celery/Kubernetes；worker 使用独立数据库 session 执行现有 Agent Pipeline。
- 保留 Planner / Executor / Verifier 核心逻辑；阶段回调继续持久化 analyzing → planning → executing → verifying → completed / failed。
- 后台保存 Agent trace、评分、DOCX/report Artifact，并捕获异常写入 failed 状态。
- Task Detail 增加 2 秒轮询，展示 status、workflow_stage、progress，完成或失败后自动停止轮询。
- 首页工作台创建任务后跳转 Task Detail；`/agent/run` 继续保持同步兼容。
- 新增异步创建、后台执行、状态变化、失败处理和用户隔离测试。

验收结果：全量 `pytest` 19 passed，frontend `npm run build` PASS，`compileall` PASS，`git diff --check` PASS。

当前限制：worker 仅为单进程内存线程池；进程重启不会恢复运行中的任务，不提供跨实例调度、checkpoint/resume 或重试队列。生产多副本部署仍需后续引入持久化队列方案。

## [DONE] PaperForge Day 6 Agent Event Stream

状态：**PASS**

完成：

- 新增轻量进程内 `TaskEventStore`，按 `task_id` 隔离事件，支持多任务订阅、有限历史回放和并发等待。
- 新增 `GET /tasks/{task_id}/events` SSE 接口，复用现有用户归属查询，发送 workflow_update 数据并在 completed/failed 后关闭。
- TaskWorker 在创建、启动、阶段变化、产物生成、完成和失败节点发布事件，不改变 Planner / Executor / Verifier 和既有数据库持久化链路。
- Task Detail 优先使用带 JWT 的流式 SSE；仅在连接失败或非终态断流时自动回退到原 2 秒轮询，并展示当前阶段、进度和实时 Agent 日志。
- Artifact 创建和持久化完成后才提交 Task completed 并发布 task_completed；failed SSE 使用安全消息，完整异常只保留服务端日志和内部任务记录。
- 终态事件历史增加 TTL 与最大保留数量限制，保持单进程内存事件流定位。
- 新增自有任务订阅、跨用户隔离、Artifact-before-completed、失败脱敏、事件清理和前端 fallback 合约测试。

验收结果：异步测试为每个用例隔离 Worker 和 SQLite 文件数据库，并在 teardown 前等待后台任务完成；全量 `pytest -q` 连续两次均 24 passed，frontend `npm run build` PASS，`compileall` PASS，`docker compose config` PASS（使用临时环境变量满足 compose 必填校验），`git diff --check` PASS。

当前限制：事件不落库，进程重启会丢失事件历史；跨实例部署未提供共享事件总线；终态历史会按 TTL / 上限删除；前端仅在 SSE 不可用时使用轮询 fallback。

## [CURRENT] PaperForge Release Freeze

当前公开版本：`v2.0-paperforge`。本轮仅进行公开包装、文档治理和低风险展示文案调整，不改变主链路。

仅允许：

- 品牌统一
- README / PROJECT_STATUS / release notes
- 部署可靠性小改
- blocking regression 修复
- 对外项目包装

禁止：

- P3 功能开发
- 大规模重构
- 异步队列扩展
- checkpoint/resume
- 新 Agent 架构重写

---

### [DONE] PaperOps Agent v2.0 P2 收尾 — 统一证据与确认采纳闭环

已完成：

- 新增轻量 evidence aggregation 层，统一格式/内容的 issue_id、locator、before/proposed/actual_after、reason、evidence、risk、action、status、verification 与确认要求。
- 内容 AUTO_FIX 严格按段落原文写入并重读验证；suggestion/HITL 默认保持正文不变，suggestion 带稳定 issue_id/locator 并明确“尚未写入文档”。
- 新增单条 `/agent/apply-suggestion` 确认接口：仅允许指定 issue_id/段落 locator，重新校验原文，stale 时返回 conflict，生成确认版 DOCX 并记录 accepted_by_user/provenance/verification。
- 新增 deterministic content score summary，评分改善只来自 verified auto fix 或 verified user acceptance，未采纳建议、HITL 和失败验证不产生虚假改善。
- API、修改报告、Runtime 结果和前端接入 `review_summary`、`change_evidence`、`pending_actions`；保留旧字段兼容。
- 新增 P2 closure tests，现有 P0/P1/P2、smoke、score consistency、真实 DOCX 10/10 回归和前端 build 通过。

状态：已完成。高风险数字、实验结果、结论、引用、方法、定义、公式等仍由本地 policy 阻断自动采纳。

---

### [DONE] PaperOps Agent v2.0 P2 第一阶段 — 段落级内容审查与安全修改闭环

目标：建立 Paragraph Content Analysis → Issue Classification → Risk Level → Auto Fix / Suggestion / HITL → Content Provenance → Verification → Decision → Frontend / Report 的完整闭环。

已完成：
- 新增 paragraph-level 内容 issue model，绑定 `paragraph_index` / `body_paragraph` locator，并区分 local / ai source、confidence、risk、status。
- 建立 `AUTO_FIX`、`SUGGEST_ONLY`、`HITL_REQUIRED` 三档策略；确定性连续空格、重复标点和模板编号残留可限定段落自动修正；语言润色和大范围/高风险内容不自动写回。
- AI/fallback 候选统一经过本地 policy；旧 `apply_language_suggestions` wrapper 也不能绕过 policy。
- AUTO_FIX 记录 before/after/reason/confidence/source，并重新读取输出 DOCX 验证；建议记录 original/suggested/reason 且确认原文未被修改；高风险证据进入最终 Decision/HITL。
- 内容统计与明细接入 `modification_report`、API 结果和前端结果区；保持旧字段、local AI 字段、预览和下载兼容。
- 新增 `test_p2_content_review_closure.py`。

状态：已完成。下一阶段应作为新的 P2 收尾大包规划，不拆成本轮小点任务。

---

## 当前路线图 / Roadmap

### [DONE] PaperOps Agent v2.0 P1.2-body-target-verification

目标：为既有可靠正文 paragraph locator 建立真实输出 DOCX 重读、expected/actual 比较与 paragraph target-level provenance。

已完成：
- 正文段落 provenance 新增 `target_type=body_paragraph` 与 `expected`，保持既有字段兼容。
- 字体、字号、对齐、行距、首行/左右缩进、段前段后均按指定 paragraph target 重读验证。
- 无 locator 或无有效目标时记录 unsupported provenance 与原因，不伪造 verified。
- 新增 `test_p1_2_body_target_verification.py`，覆盖 target-only 修改、输出重读、expected/actual 不一致与 unsupported。
- P1.1、P1、P0.1、P0.2、smoke、Python 编译与前端 build 全部通过。

状态：已完成。引用、图表编号、交叉引用、目录域、复杂表格、无 locator 目标及内容语义改写仍维持 HITL / unsupported。

---

### [DONE] PaperOps Agent v2.0 P1.1-target-level-formatting-verification

目标：在既有 P1 Rule → PlanStep → Locator → Executor → Provenance 链路上，为可靠标题、图题和表题提供局部格式执行与真实 target-level verification。

已完成：
- Word 标题样式匹配且置信度足够时生成标题 paragraph locator。
- 使用既有确定性编号解析识别 figure/table caption paragraph locator。
- 标题、图题和表题只修改 PlanStep 指定段落的低风险格式属性，不修改文本、编号或交叉引用。
- Verifier 重新读取输出 DOCX，以 target-level expected/actual evidence 回填 provenance；缺 locator、低置信或越界不伪造成功。
- 前端 Runtime 区增加“实际修改”轻量摘要，并对旧 API 数据安全降级。
- `test_p1_1_target_verification.py`、P0.1/P0.2/P1、smoke、Python 编译与前端 build 均通过。

状态：已完成。引用/参考文献重编号、图表编号重排、交叉引用、复杂表格与内容语义改写仍保持 HITL / unsupported。

---

### [DONE] v0.6.3-real-demo-files

目标：补充人工构造的脱敏模拟 demo DOCX 和一次真实 local 模式运行输出，让面试演示从“路径和案例说明”升级为“可直接复现的固定样本”。

已完成：
- 已放入人工构造的脱敏模拟论文样本和模板样本。
- 已使用固定命名：`demo_inputs/messy_paper_sample.docx`、`demo_inputs/template_sample.docx`。
- 已通过现有 `run_agent_pipeline(...)` local 模式运行一次主流程，并保留 `demo_outputs/formatted_result_sample.docx`、`demo_outputs/report_sample.json`、`demo_outputs/agent_trace_sample.json`。
- 已在 `docs/DEMO_RESULT.md` 记录样本来源、故意设置的格式问题、运行方式、重点字段、限制和验收情况。

状态：已完成。样本不是真实用户论文，输出来自一次真实 local 模式处理流程。

---

### [DONE] v0.7.0-task-state-minimal

目标：为长流程 Agent 增加最小任务状态持久化 `task_state.json`，方便后续展示任务生命周期和异常恢复。

已完成：
- 新增 `paper-ai/backend/services/task_state.py`。
- task state 默认写入 `paper-ai/backend/task_states/{task_id}.json`。
- 已记录 `running`、`succeeded`、`failed` 生命周期状态。
- 已明确 `task_state.json` 与现有 `agent_trace` 的边界：前者描述任务生命周期，后者描述处理步骤。
- `/agent/run` 保持同步执行语义，旧字段兼容；仅额外透出 `task_id` 和 `task_state_path`。

状态：已完成。当前还不是断点续跑或异步队列。

---

### [DONE] v0.7.1-docs-sync-task-state

目标：同步 task state 文档说明，明确当前真实能力、字段、架构位置、演示方式和边界。

已完成：
- README 已补充 task state 能力说明。
- `docs/ARCHITECTURE.md` 已补充 `task_state.py` 和 `task_states/{task_id}.json`。
- `docs/archive/INTERVIEW_QA.md` 已补充 task state 相关问答。
- `docs/DEMO_SCRIPT.md` 已补充 task state 演示步骤。
- `docs/DEMO_RESULT.md` 已在 v0.7.1 记录当时缺少固定 `task_state_sample.json` 的缺口；该缺口已在 v0.7.2 补齐。

状态：已完成。仅同步文档，未修改核心业务逻辑。

---

### [DONE] v0.7.2-task-state-sample

目标：为 `demo_outputs/` 补充一次固定 task state 输出样例，方便面试演示时直接查看。

已完成：
- 已保存固定样例 `demo_outputs/task_state_sample.json`。
- 样例字段与当前 `report_sample.json`、`agent_trace_sample.json` 的关键字段保持一致。
- 已更新 `docs/DEMO_CASE.md`，明确 demo 样本是人工构造 / 脱敏模拟，不来自真实用户论文，不来自 CAJ 原文，不用于论文代写。
- 已更新 `docs/DEMO_RESULT.md`、`docs/DEMO_SCRIPT.md`、README、PROJECT_STATUS 和开发记录。
- 没有把前端描述为已有 task state 可视化，也没有把系统描述为异步队列或完整断点续跑。

状态：已完成。

---

### [DONE] v0.7.3-task-state-cleanup

目标：为 `paper-ai/backend/task_states/` 增加轻量清理策略，避免运行产物长期膨胀。

已完成：
- 已在 `.gitignore` 中新增 `paper-ai/backend/task_states/`。
- 已明确 `paper-ai/backend/task_states/{task_id}.json` 是运行产物，不应提交。
- 已明确 `demo_outputs/task_state_sample.json` 是固定 demo 样例，应继续保留在 Git 中。
- 已补充 README、架构、演示脚本、demo 结果和项目状态说明。
- 未修改 `task_state.py`，未改变 `/agent/run` 同步语义。

状态：已完成。当前只做运行产物治理，尚未实现自动清理函数。

---

### v0.7.4-task-state-cleanup-function

目标：为 `paper-ai/backend/task_states/` 增加轻量清理函数或维护命令。

计划：
- 可选新增 `cleanup_task_states(task_states_dir, keep_latest=20)`。
- 只用标准库。
- 默认保留最近 20 个 task state JSON。
- 只删除 `task_states/` 目录内的 `.json` 文件。
- 不自动接入 pipeline，不改变当前 `/agent/run` 行为。

状态：规划中。

---

### [DONE] v0.8.1-trace-ui-minimal

目标：在前端结果页增加最小 Agent 执行过程展示，同时保持上传、预览、下载主流程不变。

已完成：
- 已在结果页增加默认折叠的 `agent_trace` 展示区域。
- 已展示 `step`、`status`、`duration_ms`、`fallback_used`、`message`。
- 已展示 `task_id` 和 `task_state_path` 摘要。
- 未读取 `task_state_path` 对应文件内容。
- 未展示 `agent_trace_detail`。
- 未修改后端核心 pipeline、`/agent/run` 同步语义或测试断言。

状态：已完成。当前只是最小前端展示，不是异步队列、完整 task state 可视化或完整断点续跑。

---

### [DONE] v0.8.2-trace-ui-polish

目标：优化 trace 展示文案、空状态和异常态，让 fallback 与失败状态更容易区分。

已完成：
- TracePanel 标题和说明已优化为“Agent 执行过程”，强调它是步骤级执行记录。
- `fallback_used=true` 已显示为“已使用 fallback / 本地规则兜底”，不表述为严重失败。
- `task_id` / `task_state_path` 摘要说明已补充“前端不会读取文件内容、不代表异步队列或任务恢复能力”。
- 已增加缺失 `message`、`duration_ms`、`status` 时的温和默认展示。
- 保持上传、预览、下载交互不变。

状态：已完成。当前只是展示体验打磨，不是完整 task state 可视化、异步队列或完整断点续跑。

---

### v0.8.3-demo-ui-check

目标：对 demo 输入输出和前端 TracePanel 做人工演示检查或截图检查，确认面试展示路径清晰。

计划：
- 使用 `demo_inputs/messy_paper_sample.docx` 和 `demo_inputs/template_sample.docx` 做一次人工演示检查。
- 确认结果页评分、报告、下载、预览和 TracePanel 展示不互相遮挡。
- 检查 fallback 文案、task state 摘要和缺字段状态是否容易解释。
- 如需截图验收，优先只记录检查结果，不修改核心流程。

状态：规划中。

---

### [DONE] v0.8.4-ui-polish-layout

目标：优化前端页面整体层次和演示观感，让页面更像正式工具产品，而不是功能堆叠页。

已完成：
- 上传论文、上传模板、模式选择和运行按钮已整理为更清晰的“开始处理”区域。
- 结果页已按结果总览、评分变化、修改报告、评分模块、检查结果、重复风险、Agent 执行过程、预览与下载组织。
- before_score / after_score 更醒目，并展示提升值、模式、AI 参考参与状态和任务 ID。
- TracePanel 仍默认折叠，只展示 `agent_trace` 和 `task_id` / `task_state_path` 摘要。
- 未读取 task state 文件内容，未展示 `agent_trace_detail`。
- 未修改后端核心 pipeline、`/agent/run` 同步语义、上传/预览/下载主流程或测试断言。

状态：已完成前端布局打磨。当前仍不是异步队列、完整 task state 可视化、完整断点续跑或完整工业级 Agent。

---

### [DONE] v0.8.5-ui-polish-details

目标：继续优化展示文案、空状态、小标签和细节样式。

已完成：
- 修复 390px 左右窄屏下的轻微横向溢出。
- 为页面根容器、主要卡片、按钮、TracePanel 和报告区域补充 `min-width: 0`、`max-width: 100%`、换行和小屏内边距规则。
- 窄屏下上传区、模式区、结果区、检查区和操作按钮会自然收敛，避免撑破 viewport。
- 长任务 ID、`task_state_path`、文件名和说明文字可自然换行。
- 未修改后端接口、核心 pipeline、上传/预览/下载主流程或测试断言。

状态：已完成。当前仍不是异步队列、完整 task state 可视化、完整断点续跑或完整工业级 Agent。

---

### [DONE] v0.8.6-template-runtime-cleanup

目标：治理 demo 上传模板后产生的后端模板运行副本，避免 `paper-ai/backend/templates/template_sample.docx` 这类未跟踪文件污染 Git 工作区。

已完成：
- 已删除当前未跟踪运行产物 `paper-ai/backend/templates/template_sample.docx`。
- 已在 `.gitignore` 中新增 `paper-ai/backend/templates/*.docx`。
- 已明确 `demo_inputs/template_sample.docx` 是固定 demo 输入样本，应继续被 Git 跟踪。
- 未修改后端核心逻辑、前端 UI、上传/预览/下载主流程或测试断言。

状态：已完成。当前只是运行产物治理，不是业务功能增强。

---

### v0.8.7-demo-ui-final-check

目标：重新使用 demo 输入文件做人工演示检查或截图检查，确认模板运行产物被忽略后，demo 后 Git 工作区仍保持干净。

计划：
- 使用 `demo_inputs/messy_paper_sample.docx` 和 `demo_inputs/template_sample.docx` 做人工演示。
- 检查上传、运行、评分、报告、TracePanel、预览、下载是否适合现场展示。
- 检查运行后 `git status --short` 不再出现 `paper-ai/backend/templates/template_sample.docx`。
- 只记录检查结果，除非发现明确展示问题或新的运行产物污染。

状态：规划中。

---

### [DONE] v0.9.0-ui-landing-redesign

目标：把前端首页从普通后台工具页升级为更适合演示的 AI SaaS 产品页 + 工具工作台 + 结果仪表盘风格。

已完成：
- 首屏已组织为 Hero、能力卡片、静态仪表盘预览和上传工作台。
- 上传论文、上传模板、模式选择和启动 Agent 的主流程语义保持不变。
- 结果区继续以 dashboard 形式展示评分变化、修改报告、参考文献检查、图表检查、TracePanel、预览和下载。
- TracePanel 仍默认折叠，只展示 `agent_trace` 步骤和 `task_id` / `task_state_path` 摘要。
- 未修改后端核心逻辑、`/agent/run`、测试断言、依赖文件或 demo 样本。

状态：已完成。当前仍不是异步队列、完整 task state 可视化、完整断点续跑或完整工业级 Agent。

---

### [DONE] v0.9.1-ui-run-flow-fix

目标：修复 v0.9.0 后完整 demo 检查中发现的页面点击运行 Agent 失败/错误提示过于笼统问题。

已完成：
- 已确认前端字段名与后端 `/agent/run` 字段一致：`paper`、`template`、`mode`、`allow_non_paper`。
- 已补充前端响应读取保护，支持读取 JSON、空响应和非 JSON 错误文本，避免真实错误被吞成笼统提示。
- 已补充分类型失败后的继续运行语义：当分类请求失败但用户继续运行时，向后端透传 `allow_non_paper=true`。
- 已通过浏览器真实点击 demo 流程验收：上传论文、上传模板、选择本地规则模式、点击运行、报告、TracePanel、预览和下载均可用。
- 未修改后端核心逻辑、UI 视觉布局、上传/预览/下载主流程语义或依赖文件。

状态：已完成。当前仍不是异步队列、完整断点续跑或完整工业级 Agent。

---

### [DONE] v0.9.2-ui-fetch-compat-fix

目标：修复真实浏览器页面请求本地 FastAPI 后端时出现 `ERR_ALPN_NEGOTIATION_FAILED` / `Failed to fetch` 的兼容排查问题。

已完成：
- 已确认后端 `/agent/run`、`/preview/{filename}`、`/download/{filename}` 直调可用，问题不属于后端字段不匹配或 4xx/5xx。
- 已统一前端 API base URL，默认 `http://127.0.0.1:8000`，并支持 `NEXT_PUBLIC_API_BASE_URL` 覆盖。
- 已将 `/document/classify`、`/agent/run`、`/preview/{filename}` 和下载链接统一通过 `apiUrl(...)` 拼接。
- 已增强网络错误提示，失败时展示实际请求地址，方便定位本地服务地址、端口或浏览器上传兼容问题。
- 未修改后端核心逻辑、UI 视觉布局、上传/预览/下载主流程语义或依赖文件。

状态：已完成。当前仍不是异步队列、完整断点续跑或完整工业级 Agent。

---

### [DONE] v0.9.3-interview-demo-package

目标：整理面试/演示材料，让项目从“能跑”升级为“能讲、能展示、能回答追问”。

已完成：
- 新增 `docs/INTERVIEW_DEMO_PACKAGE.md`。
- 已整理项目一句话介绍、30 秒介绍、2 分钟演示流程、技术架构讲法、项目亮点、当前边界和面试追问。
- 已同步 README、DEMO_SCRIPT、INTERVIEW_QA、DEMO_RESULT、DEMO_CASE 和 DEVELOPMENT_LOG。
- 当时推荐演示代码基线为 `v0.9.2-ui-fetch-compat-fix`；当前推荐稳定展示基线已切换为 tag `v1.0-showcase`。
- 本轮未修改后端核心逻辑、前端 UI、接口语义、依赖文件或 demo 输入输出文件。

状态：已完成。当前仍不是论文代写、正式查重、异步队列、完整断点续跑或完整工业级 Agent。

---

### [DONE] v0.9.4-demo-screenshot-package

目标：整理截图/录屏清单，为面试现场准备可视化展示材料。

已完成：
- 新增 `docs/DEMO_SCREENSHOT_GUIDE.md`。
- 已整理 13 张推荐截图：Hero、上传工作台、文件已选择、运行中、结果 dashboard、评分 `80 -> 86`、修改报告、参考文献/图表检查、TracePanel 折叠/展开、在线预览、下载入口和 390px 窄屏。
- 已归档 2026-06-27 真实网页运行截图：`docs/assets/screenshots/real-web-2026-06-27/`，共 10 张，覆盖首页、上传、运行中、结果 dashboard、检查模块、TracePanel、在线预览和下载入口。
- 已整理 60-90 秒录屏脚本。
- 已补充 ASCII 临时路径、API base URL、demo 后 Git 干净和临时服务停止等自动化演示注意事项。
- 已同步 README、PROJECT_STATUS、DEMO_SCRIPT、INTERVIEW_DEMO_PACKAGE 和 DEVELOPMENT_LOG。
- 本轮未修改后端核心逻辑、前端 UI、接口、依赖文件或 demo 输入输出文件。

状态：已完成。当前只是展示素材整理，不是业务功能增强；仍不是论文代写、正式查重、异步队列、完整断点续跑或完整工业级 Agent。

---

### [DONE] v0.9.5-demo-trace-ui

目标：在 `v0.9.4-demo-screenshot-package` 已完成、真实网页截图已归档的基础上，增强结果页演示解释能力，让 Agent Trace、模板规则和修改前后差异更容易被用户和面试官理解。

已完成/当前状态：
- 增强 Agent Trace 可视化，展示更清晰的处理步骤、耗时、fallback 和任务状态摘要。
- `v1.0-showcase` tag 已包含 trace UI 相关增强，并指向 `10904db`；`main` 分支包含 tag 之后的公开前文档和面试材料补充。
- 模板规则摘要和更完整修改前后 Diff 仍作为 v1.1 延期项，不在 v1.0-showcase 封版整理中继续扩展。
- 保持现有上传、预览、下载功能不变。
- 保持 local/ai 模式兼容，local 模式仍必须 `ai_score=null`、`ai_used=false`。
- 不大规模重构，不重写核心格式化算法，不改变 `/agent/run` 同步语义。
- 不改动 tag，不移动、删除或重建 `v0.9.4-demo-screenshot-package` tag。

状态：已作为 `v1.0-showcase` 稳定展示版能力发布；公开前清理阶段只同步文档、配置和展示文案，不新增功能。

---

### v0.9.5-resume-project-description（后续非当前优先级）

目标：整理简历项目描述、作品集摘要和面试口径，方便把当前项目压缩成 3-5 条高质量简历 bullet。

计划：
- 输出一版中文简历项目描述。
- 输出一版面试口头介绍。
- 输出一版作品集 README 摘要。
- 明确项目边界，不包装为论文代写、正式查重或完整工业级 Agent。

状态：后续规划中；当前优先级已让位给 `v0.9.5-demo-trace-ui`，避免与下一阶段路线冲突。

---

### v1.0-showcase-public-readiness

目标：维护 `v1.0-showcase` 暑期实习展示版公开口径，冻结稳定展示能力、边界说明、演示材料和回归检查清单。

任务：
- 统一 README、PROJECT_STATUS、TODO、DEMO_SCRIPT、INTERVIEW_DEMO_PACKAGE、DEMO_SCREENSHOT_GUIDE 和 DEVELOPMENT_LOG 的版本口径。
- 明确当前推荐稳定展示基线为 tag `v1.0-showcase`，而不是旧的 `v0.9.2` 或 `v0.9.4`。
- 明确 `v0.9.4-demo-screenshot-package` 是上一阶段截图包 tag。
- 明确 `v1.0-showcase` 指向 `10904db`，`main` 分支包含 tag 之后的公开前文档和面试材料补充。
- 补充封版摘要文档 `docs/V1_0_SHOWCASE_SUMMARY.md`。
- 不移动、删除或重建 `v1.0-showcase` tag。

状态：已完成封版整理。`v1.0-showcase` tag 已创建并指向 `10904db`；当前公开前清理只做文档、轻量配置和展示文案整理，未新增核心功能，未重构核心代码，未改变 API 字段结构。

---

### v1.1-showcase-follow-up

目标：承接 v1.0-showcase 之后的能力增强，但不在封版整理中实现。

延期项：
- 深度内容级修改能力。
- 完整 task state 可视化。
- 异步队列 / 断点续跑。
- 学校模板库。
- 更强的模板规则摘要。
- 更完整的修改前后 Diff。
- 真实授权用户样本扩展。
- AI 评分与真实修改量强绑定。
- 云端部署与多用户系统。

状态：规划中。

---

### v1.2-real-user-case

目标：在合法授权和脱敏前提下，整理真实用户样本试用案例，用于验证格式 Agent 在更真实文档上的稳定性。

状态：规划中。

---

## 后续补充说明

- 如需完整 task state 可视化，需要后续新增安全读取接口，而不是让前端直接读取本地 `task_state_path`。
- v1.0-showcase 封版整理只统一文档和展示口径，不改动后端核心 pipeline，不改动上传、预览、下载主流程。
- 不得改动或移动 `v0.9.4-demo-screenshot-package` tag；`v1.0-showcase` 已创建并指向 `10904db`，公开前不得移动、删除或重建。

---

### v0.9-resume-draft

目标：设计断点续跑能力，但暂不默认实现完整异步队列。

计划：
- 梳理哪些步骤可重试、哪些步骤必须重新执行。
- 明确 `task_state`、`agent_trace`、输出文件之间的恢复关系。
- 先写设计文档，再决定是否实现。

状态：规划中。

---

## 下一阶段

### 在线预览优化

目标：提升最终 docx 在线预览的结构还原度和阅读体验。

状态：已完成（v0.3.2）

---

### 格式差异报告增强

目标：更清晰展示格式修改前后差异、实际修改段落数和处理项。

状态：已完成（v0.3.1）

---

### 参考文献检查

目标：增强参考文献标题、编号条目、尾部文献区和引用格式检查。

状态：已完成（v0.3.3）

---

### 图表编号检查

目标：检查图题、表题、编号连续性、单位和题注格式。

状态：已完成（v0.3.4）

---

### 真实论文测试库 / Real Paper Stress Test

目标：建立真实 DOCX 测试库和回归记录机制，验证 Agent 面对真实论文、报告、模板不匹配和复杂参考文献/图表编号场景时的稳定性。

状态：v0.5.1 稳定测试版已完成并冻结（v0.3.5 第一步已完成：已建立测试目录、manifest 占位清单、回归结果目录和测试计划；第二步已完成：已生成 10 个脱敏 DOCX 测试样本并更新 manifest；v0.4.6 已完成极端 DOCX 重复风险检测性能保护；v0.4.7.1 已完成 74.79MB 资源压力测试；v0.5.0 已新增批量回归脚本；v0.5.1 已完成 classification boundary warning 与 heavy_manifest.csv 压力回归接入；后续仅继续扩充样本库）

---

### [DONE] Resource Stress Test v0.4.7.1

目标：验证 30MB+ 大文档在上传、分类、格式修复、评分、预览、下载和 AI fallback 全链路中的稳定性。

状态：已完成（v0.4.7.1，`realistic_heavy_thesis.docx`：74.79MB、267 页、2489 段、80 张表、100 张唯一图片、300 条参考文献；完整 local Agent PASS，耗时 510.88s；预览、下载、AI fallback 和格式保真审计均 PASS）

---

### [DONE] 重复风险检测性能保护

目标：修复极端 DOCX 在重复风险检测阶段因段落两两相似度比较导致完整 Agent 超时的问题。

状态：已完成（v0.4.6，commit `af81c08`，tag `v0.4.6-repeat-risk-performance-guard`；`check_repeat_risk` 已增加最多 300 段采样、最多 30000 次比较硬上限、截断元数据和异常 fallback；普通 smoke、极端 DOCX 完整 local Agent、local `ai_score=null` / `ai_used=false` 均 PASS）

---

### [DONE] v0.4.9 repeat risk optimization

目标：优化 `plagiarism_checker` 性能，降低 74.79MB heavy DOCX 在重复风险检测阶段的耗时。

状态：已完成。`plagiarism_checker` before `196.741s -> 17.724s`，after `181.200s -> 17.928s`，合计 `377.941s -> 35.652s`；heavy local Agent `510.88s -> 51.209s`；py_compile、smoke、heavy DOCX、local `ai_score=null` / `ai_used=false`、预览和下载均 PASS。

---

### 标题正文混排

目标：识别并拆分段落开头或段落中间出现的编号标题与正文混排。

状态：已修复（已覆盖 `4.结语：正文` 和 `...办法。4. 结语：正文` 两类场景）

---

### Agent Orchestrator Layer

目标：把现有格式处理工具链包装为可解释智能体流程，记录计划、工具调用、决策、fallback、人工复查和规则置信度。

状态：已完成（v0.3.7，新增 `agent_trace` 顶层字段，旧前端兼容）

---

### Scoring Semantics Refinement

目标：统一格式规则分、风险稳定分、AI语言参考分和最终评分的展示语义，避免 AI 语言评分被误解为主评分。

状态：已完成（v0.4.1，新增 `score_breakdown` 语义字段，AI 分数仅作参考，不参与主评分）

---

### Beta 项目文档整理

目标：将项目整理为可展示、可运行、可说明的 beta 项目，包含 README、架构说明、Agent Trace、Risk Level、真实回归结果和部署规划。

状态：已完成（v0.4.0-beta-docs，仅新增/修改文档，未改业务代码）

---

### 学校模板库

目标：沉淀可复用的学校模板规则，减少每次上传模板的不确定性。

状态：待处理

---

### 批量真实样本回归脚本

目标：为 `test_documents/manifest.csv` 中的样本建立批量回归入口，统一记录分类、local/ai fallback、预览、下载、评分语义和性能耗时。

状态：已完成（v0.5.0）。新增 `paper-ai/backend/run_real_doc_regression.py`，支持读取 `manifest.csv` / `generated_manifest.csv`，按 case/category/limit 过滤运行，记录分类、Agent 状态、报告、预览、下载、local AI 字段、耗时和 small/medium/large 文件大小分桶；输出到 `regression_results/<run_id>/summary.csv`、`summary.json` 和 `cases/<case_id>.json`。不改变业务主链路。

---

### CNKI / GB/T 7714 真实来源入库规范

目标：明确 CNKI 期刊投稿库、公开投稿模板和 GB/T 7714 参考文献材料作为测试来源时的合法边界与入库流程。

状态：已完成（v0.5.0）。新增 `test_documents/CNKI_GBT7714_SOURCE_NOTES.md`，明确只使用公开或已授权文件，不纳入登录/付费/验证码/受限全文；真实论文必须脱敏；查重相关产品表述仍使用“重复风险检测”和“相似度预检”。

---

### 分类边界测试规则

目标：区分真实功能失败和可解释分类边界，避免 `lab_report` / `academic_paper` 混合结构样本误报为阻断级回归失败。

状态：已完成（v0.5.1 / real-doc-regression-boundary-pass）。`run_real_doc_regression.py` 已支持 `BOUNDARY_WARNING`，`generated_manifest.csv` 中 `reports_001/002/003` 已通过 `known_risks=classification_boundary` 标记；处理崩溃、输出缺失、报告缺失、预览/下载失败、local AI 字段异常仍计入 blocking FAIL。

---

### Heavy DOCX 压力回归接入

目标：将 30MB-100MB 大体积 DOCX 纳入真实文档回归体系，验证分类、local Agent、输出文件、修改报告、在线预览、下载和 local AI 字段稳定性。

状态：已完成（v0.5.1）。`realistic_heavy_thesis.docx` 已复制到 `test_documents/real/`，新增 `test_documents/heavy_manifest.csv`；本轮 local 回归 1/1 PASS，耗时 57.558s，输出 DOCX / 修改报告 / 预览 / 下载均通过，local `ai_score=null`、`ai_used=false`。

---

### [DONE] Performance Profiling v0.4.8

目标：拆分 74.79MB 重型 DOCX 完整 local Agent 的 510.88s 耗时分布，并将大文档处理时间优化到 120~150s。

状态：已完成。v0.4.8 已定位 Top1 瓶颈为 `plagiarism_checker`，before 196.741s，after 181.200s，合计 377.941s，占 heavy profiling 有效总耗时 92%+；v0.4.9 已完成对应优化。

---

### v0.5.0 Beta Readiness

目标：进入真实用户试用准备阶段，确认格式 Agent 在试用前的主流程、交付物和兼容性风险。

任务：
- 真实用户试用准备
- UI 流程检查
- 上传流程检查
- 下载流程检查
- 报告质量检查
- 文档兼容性检查

状态：已完成（v0.5.2 / beta-readiness-audit）。历史审计文档已归档到 `docs/archive/VERSION_0_5_2_BETA_READINESS_AUDIT.md`；本轮验收结果为 manifest 10/10 PASS、generated 21 PASS + 3 boundary warnings + 0 blocking FAIL、heavy 1/1 PASS、smoke PASS、frontend `npm run build` PASS。结论：可进入 controlled beta，但产品表述仍应定位为格式 Agent，不应包装为深度内容改写 Agent。

---

### 内容 Agent 段落级问题清单

目标：从当前词语级 AI 审校升级到段落级问题识别，输出口语化、主观化、逻辑跳跃、因果不清、关键词不规范和重复表达问题清单。

状态：待处理（在格式 Agent 稳定后推进）

---

### Controlled Beta 用户试用准备

目标：为第一轮 controlled beta 试用准备用户筛选、文档准入、试用任务、阻断标准、反馈表和退出条件。

状态：已完成（v0.5.3 / controlled-beta-trial-prep）。历史准备文档已归档到 `docs/archive/VERSION_0_5_3_CONTROLLED_BETA_TRIAL_PREP.md`；当前建议先收集 3-5 名可信用户的真实 DOCX 试用反馈，再决定 v0.5.4 优先做 UI polish、报告措辞修正或内容 Agent 窄能力。

---

### 准备试用用户说明和反馈表

目标：为 controlled beta 试用用户准备简单说明文档和反馈表，明确测试版边界、上传建议、支持能力、非承诺事项和问题反馈字段。

状态：已完成。受控试用用户说明和反馈表已归档到 `docs/archive/BETA_TRIAL_USER_GUIDE.md`、`docs/archive/BETA_TRIAL_FEEDBACK_FORM.md`；归档资料仅作为历史记录，当前展示入口以 README 和 v1.0-showcase 文档为准。
---

### [DONE] 暑期实习展示版整理

目标：在不大规模重构、不改变前端上传/预览/下载功能的前提下，增加统一调度层、标准化 Agent Trace、补充架构文档和开发记录。

状态：已完成。新增 `paper-ai/backend/services/agent_pipeline.py`，`/agent/run` 已通过统一调度层调用现有 `paper_agent`；`agent_trace` 已标准化为逐步列表，并保留旧解释型 trace 到 `agent_trace_detail`；顶层兼容 `modification_report`、`reference_check`、`figure_table_check`。本轮 `py_compile`、现有后端测试和 `npm run build` 均 PASS。
---

### [DONE] v0.6.3 demo 文件整理

目标：准备适合面试演示的脱敏模拟 DOCX 样本，覆盖标准论文、模板上传、参考文献提示、图表编号提示和 local 输出说明。

已完成：

- 已准备一个小型模拟标准论文样本，适合现场演示。
- 已准备一个模板样本，展示模板解析输入。
- 已准备包含参考文献编号和图表编号引用检查点的样本，展示 `modification_report`、`reference_check`、`figure_table_check`。
- 已保存一次 local 模式输出样例，并记录预期展示点和不应承诺的边界。

状态：已完成（v0.6.3-real-demo-files）。仅整理样本和说明，未修改核心业务逻辑。

---

### [DONE] v0.7 task_state

目标：为 Agent 长流程增加任务状态记录，方便后续支持更清晰的运行状态、错误恢复和前端进度展示。

状态：已完成最小落盘版本（v0.7.0-task-state-minimal）、v0.7.1 文档同步、v0.7.2 固定 task state 样例和 v0.7.3 运行产物治理。后续清理函数见 `v0.7.4-task-state-cleanup-function`，断点续跑设计见 `v0.9-resume-draft`。

---

### [DONE] v0.8 trace UI

目标：将后端 `agent_trace` 展示到前端 UI，让用户能看到每一步处理、耗时和 fallback 状态。

已完成：

- 在结果页增加执行轨迹区域。
- 展示 `step`、`status`、`duration_ms`、`fallback_used`、`message`。
- 对 fallback 步骤做温和提示，不把 fallback 显示为严重失败。
- 展示 `task_id` 和 `task_state_path` 摘要，但不读取 task state 文件内容。
- 保持原有上传、预览、下载交互不变。
- 如后续需要完整 task state 可视化，应新增安全读取接口，而不是让前端直接读本地路径。

状态：已完成最小展示版本（v0.8.1-trace-ui-minimal）和展示打磨版本（v0.8.2-trace-ui-polish）。后续可进入 `v0.8.3-demo-ui-check` 或 `v0.9-resume-draft`。

---

### [DONE] PaperOps Agent v2.0 P0.1 — Document / Rule / Plan Foundation

目标：在不改变现有 DOCX formatter 和 `/agent/run` 兼容字段的前提下，建立真实的 `DOCX → DocumentModel → Rule[] → ExecutionPlan` 数据链。

状态：已完成。新增 `document_model.py`、`rule_engine.py`、`planner.py` 与 `test_p0_1_planning_foundation.py`；真实 Agent 调用会返回 planning artifacts。P0.1 仍不执行 Plan，也没有 Verifier/Replan/HITL workflow；这些属于 P0.2。

---

### [DONE] PaperOps Agent v2.0 P0.2 — Plan / Execute / Verify / Govern Runtime

目标：让 P0.1 的 ExecutionPlan 真实驱动已稳定的格式修改，并建立独立验证、结构保护、重规划与人工复核闭环。

状态：已完成最小真实运行时。新增 `agent_runtime.py`、`executor_adapter.py`、`verifier.py`、`governance.py` 和 `test_p0_2_agent_runtime.py`。安全 PlanStep 通过既有 formatter 执行；Verifier 会重新读取输出 DOCX；结构保护会比较段落、标题、表格、图片、参考文献与 fingerprint。Decision Engine 统一输出 COMPLETE / REPLAN / HUMAN_REVIEW / FAIL，默认最多一次 Replan。高风险引用/图表/不支持步骤不伪造执行，形成 HumanReviewRequest。API 保持兼容并新增 runtime 工件和内部回归指标。P0.2 仍不包含复杂审批 UI、段落级完美 provenance、内容语义自动重写或异步恢复。

---

### [DONE] PaperOps Agent v2.0 P0.3 — Runtime UI / Task State

目标：以最小改动将 P0.2 workflow、verification、decision、replan 与 HumanReviewRequest 接入现有结果页和 task state。

状态：已完成。task state 保留旧字段并新增 runtime_state、current_phase、current_step、decision、replan_count、human_review_required；结果页新增中文 Runtime Workflow、验证摘要、Decision 解释、独立人工复核卡片和可展开 Replan 历史。旧结果缺少 runtime 字段时不渲染新面板，保持上传、预览、下载和 Agent Trace 兼容。未实现审批继续、checkpoint 恢复或自动 resume。

---

### [DONE] PaperOps Agent v2.0 P1 — Executor Expansion + Provenance Foundation

目标：扩展真实低风险格式执行，并建立 Rule → PlanStep → Executor → Verification provenance 链路。

状态：已完成最小实现。正文格式 PlanStep 现在带 paragraph index locator，支持字体/字号、对齐、行距、首行缩进及段前段后；页边距使用 section locator。每个实际修改会记录 change_id、document/rule/plan/step、target、before/after、executor、状态、时间和验证范围；Verifier 重读输出后以 rule 或 document scope 补充验证证据。C-51 模板残留和可靠标题正文混排保留为显式 hygiene PlanStep。引用关系、参考文献重编号、图表编号、复杂表格和无可靠 locator 的动作仍不自动执行并交由 HITL。新增 `test_p1_executor_provenance.py`。

### [DONE] PaperOps Agent v2.0 P1 — Verified Execution Closure

目标：完成 P1 阶段级执行可信闭环，不再拆分单点 P1.x 任务。

状态：已完成。新增轻量 Plan normalization、稳定 execution ordering、重复 PlanStep 去重、同 target 同 field 冲突审计；Executor 在冲突字段上阻断自动执行并记录 provenance。Verifier 输出真实 target verification summary，Decision 优先消费 target failed / unsupported / conflict evidence；HITL 记录具体 target、字段、原因、expected/actual 或候选值。Runtime、task state 和前端补充 execution / conflict / verification summary 与最多 5 条 HITL evidence。新增 `test_p1_execution_closure.py`，真实 DOCX manifest 回归 10/10 PASS。P1 可正式结束，下一阶段仅进入 P2 方向规划。
## [DONE] PaperForge Day10-P0 — Tenant Membership + RBAC Foundation

目标：在保持 Day9 tenant isolation 与个人 tenant 默认兼容的前提下，建立多用户/多 tenant membership、固定 RBAC 和最小成员只读 API。

完成：`TenantMembership` 扩展为 `owner/admin/member`、`updated_at` 与 `(tenant_id, role)` 索引；新增集中 `rbac.py` 权限矩阵和安全的未来成员变更 service。`X-Tenant-ID` 仅作为未可信选择输入，经 active membership 校验后生成 tenant context；非成员/跨 tenant 返回 404。模板、任务、SSE、artifact、下载、预览和确认写入已通过集中权限校验；新增 `/tenants/membership/me`、`/tenants/{tenant_id}/membership/me`、`/tenants/{tenant_id}/members`。首页只轻量显示当前角色，未引入团队管理 UI。Alembic `0007_day10_membership_rbac` 从 `0006` 升级，并保留既有 owner/workspace 字段与个人 tenant backfill。

验收：Day10 + Day9 + SaaS targeted pytest 20 passed；backend full pytest 69 passed；compileall、Alembic `0006→0007→0006→0007`、frontend production build、git diff check PASS。

下一步：Day10-P1 可实现受 OWNER 约束的成员邀请/增删/角色变更 API 与 workspace 切换 UX；本轮不创建 tag、不部署 production。

## [DONE] PaperForge Day10-P1 — Tenant Member Governance + Active Workspace Switching

目标：让 Owner 可安全管理 `admin/member`，让多 Workspace 用户可切换 active tenant，同时不弱化 Day9/Day10-P0 isolation。

完成：新增 Owner-only 成员添加、角色更新、删除 API；Owner 不能经普通 API 被授予、降级或移除。新增持久化轻量 invitation，token 仅保存 hash，具备 7 天 expiry、一次性接受、撤销、邮箱匹配和原子 membership 创建。`GET /workspaces` 返回 active tenant memberships；首页提供 Workspace selector，localStorage 仅存 UI preference，切换时清空旧 tenant 的 templates/results/members/invitations，并由后端继续校验每个 `X-Tenant-ID`。Owner 可见最小成员与邀请管理 UI；非 Owner 不显示 mutation controls。

验收：成员、邀请、隔离、SaaS targeted pytest 21 passed；backend full pytest 73 passed；compileall、frontend build、PostgreSQL fresh upgrade 与 `0007→0008→0007→0008` roundtrip、git diff check PASS。

暂未实现：ownership transfer、custom roles/fine-grained editor、SSO/SAML、SCIM、enterprise directory、email delivery、audit-log enterprise dashboard。

下一步建议：Day10-P2 仅在真实团队工作流需求明确后，增加 ownership transfer 的双确认流程、审计事件与 invitation acceptance UX；不在 P2 前扩展企业 IAM。

## [DONE] PaperForge Day10-P2 — Ownership Lifecycle + Audit + Tenant Settings

完成：新增唯一 pending 的安全 ownership transfer，token 仅存 hash、24 小时过期、目标成员明确接受；服务事务锁定 transfer/membership 并原子执行旧 Owner → Admin、新 Owner → Owner。数据库 partial unique index 限制每 tenant 至多一个 active owner 与一个 pending transfer。新增 append-only audit event、Owner-only Workspace rename、最小 settings/transfer/audit UI 与显式 ownership accept 页面。

验收：P2 targeted、Day10/Day9/SaaS 回归及 full backend pytest 76 passed；compileall、frontend build、git diff check PASS。仍未实现 SSO/SAML、SCIM、custom/fine-grained roles、enterprise directory、email delivery、audit export/SIEM、billing 或 organization hierarchy。

## [DONE] PaperForge Day9-P3 — Tenant Template Management & Storage

目标：登录用户可上传、持久化、管理并安全使用 tenant-scoped DOCX Template Resource，同时保持 legacy task upload 为临时语义。

完成：新增 `LocalTemplateStorage` 与稳定 storage locator；模板文件按 tenant/resource/version 隔离。新增 `0006_day9_tenant_template_management`，持久化 locator、原始文件名、大小、content type、checksum、uploaded_by。新增 `POST /templates`、`GET /templates/{id}`、`PATCH /templates/{id}`、`GET /templates/{id}/file`、`DELETE /templates/{id}`；上传会做 DOCX/大小/安全名/SHA-256/Template Intelligence 验证，并对 storage/DB 失败清理补偿。跨 tenant 资源访问隐藏为 404；平台模板不可被普通 tenant 修改或删除；历史 Task 使用过的 tenant template 不允许物理删除。前端首页已补最小“我的模板”上传与选择。Registry 创建/更新/删除即时刷新，任务 trace 保存模板 provenance。

验收：backend pytest 62 passed；Day9-P3 专项 3 passed；compileall、Alembic fresh upgrade、Alembic `0005→0006`、frontend production build、git diff check 全部 PASS。

下一步：等待 Day9-P3 用户验收；本轮不 commit、不 push、不创建 tag。
