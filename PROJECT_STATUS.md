# 项目状态

## 当前权威状态（2026-09-12）

- 项目：**PaperForge — Verified Academic Document Agent**；当前阶段：**READY FOR CONTROLLED PUBLIC BETA**。
- Production：前端 `https://aetherislab.xyz`；浏览器 API：`https://aetherislab.xyz/api`。ECS 已运行本轮 `v3.7.5`，runtime digest、migration/readiness 和部署事实已同步记录。
- Release candidate：`v3.7.5`；release commit：`4ca4bf29a1eee67f05bcdd6c7b5dfd8a0841a018`；frontend/backend 均从该同一 commit 构建。
- P0 源码状态：frontend Docker build 已保留 local loopback fallback，并要求生产 CI 显式传递三个 `NEXT_PUBLIC_*` build args；Next.js 已升级到 `15.5.24`，兼容传递依赖审计为 0 vulnerabilities。
- 本地验证：frontend production `npm run build` **PASS**；backend 从 `paper-ai/backend` 执行 `pytest -q` 为 **107 passed**；`.next/server` 与 `.next/static` 未发现 `http://localhost:8000` 或 `http://127.0.0.1:8000`，并发现生产 API URL。Docker image build 尚未在本机执行；这只代表 local build 环境状态，不代表 production Docker 故障。
- 发布状态：canonical ACR run `34678107681` 已从 release commit 成功构建并推送 immutable backend/frontend images；ECS 已按 digest 部署，Alembic 已验证为 `0013_beta_feedback (head)`，公开 `/api/health`、`/api/ready` 和首页均为 200。Feedback authenticated submit、unauthenticated 401、数据库写入、普通用户 admin 403、Local task、SSE、preview、合法 DOCX download 均 PASS。2026-09-12 已备份生产 `.env`，配置 `ADMIN_EMAILS` 并将其注入 ECS historical Compose backend；管理员登录、`/admin/stats`、`/admin/feedback`、`/admin`、`/admin/feedback` 页面均 PASS，未认证请求为 401，临时普通测试账号请求为 403。旧 `ops/acr-build-v3.6` workflow 已废弃。ECS 数据库、PostgreSQL volume 和现有数据 bind mounts 未被删除或替换。
- 受控 smoke 资源：A task `2c3eee5f-597f-4ebe-a6b9-23411b257424`；B task `e8831a6f-fd94-4a69-9f43-36676721cda3`。仅记录非敏感资源标识；账号密码、JWT、数据库和 provider 凭据未写入仓库。
- 运行时事实：ECS `/opt/paperforge` 沿用历史 Compose 数据挂载结构，仅替换 backend/frontend image；不得未经数据迁移审查直接切换到仓库新版 named-volume Compose。
- 当前 P1：localStorage bearer token 的 XSS 暴露面、单进程限流/缺少 WAF 与外部监控、单进程 worker 重启后 `interrupted`、复杂 DOCX/AI 内容审校深度仍需后续治理；不得把这些未完成项伪装成 P0 已完成。
- 当前 P2：checkpoint/resume、分布式队列/多副本调度、对象存储、企业 SSO/SCIM、计费与更深的内容 Agent 仍不在本次 P0 发布范围。
- Beta Feedback Entry：已部署 v3.7.5；`feedback` 表、认证提交和只读 admin console API/UI 已上线。生产 smoke 发现并修复 ORM `metadata_json` 未显式映射 migration `metadata` 列的问题；修复已通过专项回归并随 v3.7.5 发布。
- Beta Feedback 安全边界：API 必须 JWT 认证，user/tenant 由服务端 membership context 绑定；task_id 仅接受当前 tenant 任务；不保存 JWT、Authorization、cookie、上传文件或论文正文。速度反馈复用现有 task status/started_at/finished_at，后续 observability enhancement 留在 TODO。
- 事实冲突处理：先核实 source code、Git、ECS/Compose、health/readiness 和浏览器行为，再更新仓库文档；聊天仅为临时上下文。

下方 Day/版本段落是历史里程碑记录；如与上方当前状态或真实 ECS 检查冲突，以上方当前状态和生产 runbook 为准。

项目名称：**PaperForge**

正式定位：**Verified Academic Document Agent**

中文定位：**学术文档可信智能处理 Agent**

当前阶段：**P0 修复、immutable 镜像和 ECS production 发布已完成；Controlled Beta 最终登录后 E2E / tenant isolation 验收待受控账号**

品牌视觉增量：**PaperForge Brand Visual System 已完成**。已生成并导入 Canva 可编辑品牌板，包含字标优先 Logo / PF 图形方向、字体与色彩系统、Landing Page Hero 软件窗口概念及品牌定位边界；不修改 Agent 主链路。

Landing Page 增量：**真实用户首页已完成**。首页现以产品窗口为主视觉，包含 Hero、PaperForge App Preview、Workflow、Verification Result 与 CTA；移除品牌规范展示和虚假评分，统一使用 `Template parsed`、`Changes verified`、`Report generated`、`Preview available` 等真实状态文案。未修改后端 API 或 Agent 主链路。

Day17-P0 最新增量：**Security Hardening 已完成**。JWT 现携带并校验用户持久化 `token_version`；`POST /auth/revoke-sessions` 原子递增该版本，使当前用户的所有旧 bearer token 立即失效，后续登录签发新版本 token。公开 Nginx 示例补充严格 CSP、每 IP `60r/m` 边缘限流（burst 20、429）及 SSE 兼容代理设置。`docker-compose.yml` 现明确是 development-only stack（`paperforge-dev`）；生产仍只能使用 `docker-compose.prod.yml` 与受审查的 public edge。新增 Day17 专项测试；未修改 TaskWorker 或 Agent 业务逻辑。真实域名/TLS、immutable image、备份、migration、health/readiness 已在本轮目标环境完成；登录后业务链路和 tenant isolation 仍待受控账号验收。

Day12-P1 最新增量：**Observability Foundation 已完成**。每个 HTTP 请求现在生成 UUID request ID，并通过 `X-Request-ID` 返回；请求完成/失败日志采用 JSON 结构，含 timestamp、level、request_id、tenant/user/task（可用时）、event 与 duration，敏感字段（JWT、password、API key、论文/文件正文）会被排除或脱敏。既有 durable `task_events` 继续作为 task execution history authority，同时新增 task created/claimed/started/stage changed/completed/failed 的关联结构化诊断日志，可按 task_id 查询一次执行过程。`/health` 仅表示进程存活；新增 `/ready` 以轻量 `SELECT 1` 验证数据库可达。HTTP 错误现返回 `error.code`、`error.message`、`request_id`，分类为 AUTH_ERROR、VALIDATION_ERROR、TASK_ERROR、STORAGE_ERROR 或 INTERNAL_ERROR。未引入 Prometheus/Grafana/ELK/OpenTelemetry 或改变业务 Agent 行为。

Day12-P0 最新增量：**Security Hardening 已完成**。已审计认证、tenant authorization、上传、artifact、API、secrets、数据库边界、日志与前端。production 启动强制非占位且至少 32 字符的 `JWT_SECRET_KEY`、`AUTH_REQUIRED=true` 与显式 `CORS_ORIGINS`；生产 CORS 不再自动允许 localhost。任务、SSE、managed templates 与 artifact 均以 tenant-scoped SQL 查询授权；按 filename 的下载、预览和确认修改先解析 tenant-scoped artifact，再触及文件系统。DOCX 上传现校验安全名、扩展、MIME、原始大小、ZIP 容器、必需部件、条目数及解压总量，并继续 UUID 请求目录隔离。注册/登录按 client 与邮箱、上传/Agent 按 client 或用户实施轻量单进程限流；该措施不替代 reverse proxy/WAF 的分布式限流。前端 preview HTML 源自服务端 escape 的 DOCX renderer；access token 仍位于 localStorage，是后续 httpOnly cookie/session 迁移前的已知 XSS 影响面。未发现受跟踪 env 文件或相关 git history 中的明显真实凭证。

Day11 最新增量：**Durable Task Runtime 已完成**。现有 `tasks` 表已增量扩展为 PostgreSQL authoritative task lifecycle，保存 progress/stage、运行与完成时间、worker run identity、attempt/recovery/error/result/input metadata 与 state version；新增 tenant-scoped append-only `task_events`，SSE 通过 event sequence 与 `Last-Event-ID` 可重放数据库事件。`PENDING -> RUNNING` 使用数据库 conditional update claim，terminal task 不会被旧 worker 回写为 RUNNING。backend startup 会将遗留 RUNNING 任务明确标记为 `interrupted`，记录前 worker identity 和检测时间，不伪造 checkpoint resume。旧 JSON task-state 保留为 pipeline compatibility artifact，不再作为 SaaS task lifecycle authority。未引入外部队列或多节点调度；真实 checkpoint/resume、retry API、对象存储、生产监控和真实 production deployment 仍未实现。

Production Infrastructure P0 最新增量：新增 immutable-image `docker-compose.prod.yml`，包含 PostgreSQL、backend、frontend、健康检查、内部网络，以及 PostgreSQL / uploads / outputs / managed templates / task states / bundled templates 的 named volumes；该仓库 Compose 是后续标准。真实 ECS 本轮保守沿用历史 Compose 的 PostgreSQL named volume 与 `/opt/paperforge-data/{uploads,outputs,template_storage}` bind mounts，完成 immutable image pull、Alembic、runtime update 和公开 health/readiness；不得在没有数据迁移方案时直接替换挂载结构。Docker Desktop 仅完成 local config/build validation，不是 production runtime。

Day10-P2 最新增量：**Ownership Lifecycle + Tenant Audit Log + Tenant Settings 已完成**。Owner 通过 24 小时、hash-only、显式接受的 transfer lifecycle 转让 ownership；接受时在事务/行锁内将旧 Owner 降为 Admin、新成员提升为 Owner。数据库对 active owner 与 pending transfer 均使用 tenant-scoped partial unique index；服务层进一步验证参与者 active 状态与唯一 Owner。新增 append-only tenant audit events，覆盖成员、邀请、ownership transfer 与设置变更，metadata 自动排除 token/hash/secret；Owner/Admin 可读，Member 不可读。新增 Owner-only Workspace display name 更新，首页治理区支持 settings、transfer、audit，另有明确确认的 `/ownership-transfer?token=...` 接受页。Alembic `0009_day10_ownership_audit_settings` 从 `0008` 升级。未扩展 SSO/SAML、SCIM、custom roles、企业目录、邮件或计费。

Day10-P1 最新增量：**Tenant Member Governance + Active Workspace Switching 已完成**。Owner 可通过集中 `services/rbac.py` 权限层添加已注册用户、在 `admin/member` 间切换及移除非 Owner 成员；普通成员 API 永不授予/降级/删除 Owner。新增轻量 `tenant_invitations`：仅保存安全随机 token 的 SHA-256 hash，支持 7 天过期、pending/accepted/revoked/expired、一次性接受、认证邮箱匹配与事务内 membership 创建；不接 SMTP。`GET /workspaces` 现返回用户全部 active membership 的 tenant 工作区，首页 Workspace Switcher 将选择仅保存在 localStorage，并让所有 tenant-scoped 请求携带 `X-Tenant-ID`；服务端仍逐次做 membership 校验，失效选择安全回退，切换时清除 tenant 专属 UI 数据。Owner 有最小成员/邀请界面；Admin/Member 不显示 mutation 入口，后端继续独立校验。Alembic `0008_day10_member_governance` 从 `0007` 增加 invitation 表。验收结果：full backend pytest 73 passed，Day10/Day9/SaaS targeted 21 passed，compileall、frontend build、PostgreSQL fresh + `0007→0008→0007→0008`、git diff check PASS。未实现 ownership transfer、custom roles、SSO/SAML、SCIM、企业目录、邮件投递或企业审计 dashboard。

Day10-P0 最新增量：**Tenant Membership + RBAC Foundation 已完成**。在既有 `TenantMembership` 上扩展固定 `owner/admin/member` 角色、`updated_at` 和 tenant+role 索引；新增集中 `services/rbac.py`，以代码级权限矩阵统一 tenant、template、task、member 授权，并预留最后 OWNER 保护、非 OWNER 不得变更角色/移除成员的服务约束。Tenant Context 现在可接收不可信 `X-Tenant-ID`，但只能解析当前用户的 active membership；非成员与跨 tenant 行为继续返回 404。新增当前 membership、指定 tenant 当前 membership、tenant members 只读 API；模板、任务、SSE、Artifact、下载、预览和确认版写入均接入相应权限。旧客户端未传 active tenant 时仍自动使用 personal tenant。Alembic `0007` 从 `0006` 扩展既有 membership 表，不移除 legacy owner/workspace 关系。首页轻量展示当前 Owner/Admin/Member，后端仍为唯一 authority。验收结果：backend pytest 69 passed，Day10/Day9/SaaS 专项 20 passed，Python compileall、Alembic `0006→0007→0006→0007`、frontend build、git diff check PASS。

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

## [DONE] PaperForge Day13-P0 — Usage & Quota System

目标：在既有多 tenant、durable task 与 PostgreSQL 架构上增加最小 SaaS 额度闭环，不扩展支付、会员或后台。

完成：新增 tenant-scoped `quotas` 配额表与 append-only `usage_records` 使用流水表，Alembic `0011_day13_usage_quota` 从 Day11 migration 升级；额度按自然月、单一 `agent_run` 指标统计，默认每 tenant 每月 100 次，可通过 `DEFAULT_AGENT_RUN_QUOTA` 配置。`POST /agent/run` 在创建 Task 前执行额度检查，Task 与 usage 在同一事务中提交；额度耗尽返回 429/`QUOTA_EXCEEDED`，不会创建新 Task。新增只读 `GET /usage`，按当前已验证 tenant 返回周期、额度、已用量和剩余额度。

验收：新增 `test_day13_quota.py` 4 passed；全量后端 pytest 90 passed；Python compileall、`git diff --check`、frontend `npm run build`、Alembic `head→0010→head` roundtrip 均 PASS。

明确不包含：支付、会员等级、后台额度配置、充值、退款、计费、异步计量和跨服务计费对账。

## [DONE] PaperForge Day13-P1 — Quota UX

目标：把 Day13-P0 的 tenant-scoped quota 能力接入首页前端，不扩展支付、套餐或充值逻辑。

完成：首页沿用现有认证 token 与 `X-Tenant-ID` 请求头接入 `GET /usage`；新增 Usage/Quota 展示组件，显示 Monthly limit、Used、Remaining、使用进度和统计周期。Workspace 切换或退出登录时清理旧 usage 状态，随后按当前 tenant 重新加载。前端错误解析兼容后端 `QUOTA_EXCEEDED` 包装，并在额度耗尽时展示已用/总额度和周期提示；同时保留前端剩余额度为 0 的即时阻断提示。

验收：frontend `npm run build` PASS；backend full pytest 90 passed；Python compileall、`git diff --check` PASS。认证、tenant isolation、现有上传/任务流程未改变。

明确不包含：支付、套餐、会员、充值、退款、后台额度配置和计费逻辑。

## [DONE] PaperForge Day14-P0 — Admin Dashboard

目标：在现有多 tenant、认证、durable task 与 usage/quota 架构上增加最小运营后台。

完成：新增平台管理员邮箱 allowlist 配置 `ADMIN_EMAILS` 与 admin-only `GET /admin/stats`；接口要求有效 JWT 和平台管理员身份，只返回租户、用户、任务、任务状态及 Agent-run usage 的聚合统计，不返回跨租户明细。新增前端 `/admin` Admin Dashboard，支持核心指标、Task status summary、Usage summary 和非管理员拒绝态；登录用户响应增加只读 `is_admin` 标识，首页仅对管理员显示入口。未新增支付、用户管理、复杂权限或数据库迁移。

验收：Day14 专项 2 passed；后端全量 pytest 92 passed；`py_compile`、frontend `npm run build`、`git diff --check` PASS。

配置说明：在部署环境通过 `ADMIN_EMAILS=ops@example.com`（多个邮箱以逗号分隔）授予平台运营后台访问权；tenant `admin` 角色不会自动获得平台管理员权限。

## [DONE] PaperForge Day15-P0 — Production Hardening

目标：将 PaperForge 从可运行 SaaS 提升为可测试生产版本，在保持 JWT、tenant isolation、quota 和 admin dashboard 的前提下补齐基础运行保护。

完成：

- 全 API 增加进程内基础限流，健康/就绪探针豁免；继续明确需要生产 reverse proxy/WAF 提供分布式限流和 DDoS 防护。
- 新增按 user 和 tenant 的活跃任务并发限制，`pending` 与 `running` 均计入；默认上限分别为 2 和 4，超限返回 `429/TASK_CONCURRENCY_LIMIT`，不创建新任务。
- 上传保护增强为分块哈希、请求体上限、DOCX ZIP 重复条目/危险路径/符号链接/压缩比/展开大小/条目数校验和文件名长度校验；数据库或模板解析失败时清理临时上传并回滚事务。
- PostgreSQL 连接池增加 pre-ping、pool timeout/recycle、size/overflow 参数；请求级数据库依赖在异常时显式 rollback；生产启动强制 `AUTO_CREATE_DB=false`，由 Alembic 管理 schema。
- 新增 `verify_postgres_backup.ps1`、`backup_files.ps1`、`restore_files.ps1`，并在备份 runbook 中规定 dump 完整性检查、五类文件卷、隔离恢复和二次确认。
- 新增黑盒 `scripts/production_smoke_test.py`，覆盖 health/readiness、登录、分类、local Agent、usage、预览、下载及 local AI 字段契约。
- 未新增支付、会员、复杂权限或 AI 功能；未改动前端主流程和 Agent 核心算法。

验收：Day15 专项 6 passed；后端全量 pytest 98 passed；Alembic `0001→0011` 临时数据库升级 PASS；独立 smoke PASS；Python compile PASS；PowerShell 脚本解析 PASS；生产 Compose `config --quiet` PASS；frontend `npm run build` PASS；`git diff --check` PASS。未执行真实公网部署、真实生产数据库恢复或 WAF/DDoS 实测。

已知边界：应用内限流是单进程保护，不替代边缘分布式限流；任务仍由轻量进程内 worker 执行，重启恢复语义保持 Day11 的 interrupted；项目内旧 `paperforge.db` 若未执行 Alembic 会缺少新 schema，生产必须先迁移再启动。

## [DONE] PaperForge Day16-P0 — Controlled Beta Release Closure

完成：版本一致性核对；Compose 三服务 release label、固定 PostgreSQL 镜像入口与 retention 配置；生产 migration head 统一为 `0011_day13_usage_quota`；可复现 Nginx HTTPS/SSE 配置；Task Detail verification summary、Bearer 下载、DOCX 在线预览、失败/中断说明与 retry API/button；分类临时上传自动清理；正式 Artifact 保护型 orphan cleanup command；production smoke 扩展到 task detail、SSE task event 和 artifact download。

验收：Day16 专项 4 passed；后端全量 pytest 102 passed；frontend `npm run build` PASS；Python compile PASS；Compose config PASS；`git diff --check` PASS；smoke/cleanup 脚本 `--help` PASS。真实公网 TLS、registry image pull、真实 PostgreSQL restore 和 WAF 仍未在目标环境执行。

当时状态：**Controlled Beta Ready（受控测试就绪，待 commit/release tag 与目标环境 smoke）**；该里程碑已被上方当前 P0 production 发布状态 supersede。

## PaperForge Auth Experience Release Candidate

已完成：Login / Register 统一升级为 PaperForge SaaS Auth Layout。桌面端采用左侧品牌与真实能力说明、右侧认证表单；移动端收拢为单列表单并保留可滚动输入体验。未修改 Login/Register API、JWT、Preview Auto Login、redirect、workspace 或 auth guard。

验收：`/login`、`/register` 桌面端实际渲染检查通过；移动端 390/360 响应式断点与溢出规则检查通过；frontend `npm run build` PASS；`git diff --check` PASS。

## PaperForge Frontend Final Release Sweep

已完成：覆盖 Landing、Auth、Dashboard、New Task、模板选择、Task Detail、结果、预览、下载、Sidebar、Topbar、Workspace、Empty/Loading/Error 状态与 1920/1440/1280/1024/768/390/360 响应式检查。最小修复网络错误文案、模板/设置入口、任务中心 Loading/Retry、产物下载异常保护和移动端 Preview 徽标裁切；未修改后端 API、数据库或 Agent 主链路。

验收：Frontend P0=0、P1=0；`npm run build` PASS；`git diff --check` PASS；隔离 SQLite 真实 local 任务 smoke PASS（running → completed、验证 112/112、DOCX/报告产物、在线预览与下载）；主要页面 Console error/warn=0。正式 commit/push 后，Frontend Productization 阶段结束。
# PaperForge V4 前端产品化第一阶段

状态：已完成。新增 SaaS 前端基础目录 `components/`、`lib/`、`types/` 和 `styles/tokens.css`；提供 Button、Card、Badge、Input、EmptyState、Loading 基础组件，并抽离公共 API URL、认证请求头/会话读写和任务状态标签。既有页面、后端 API 与上传、模板、local/ai、Agent、预览、下载业务流均保持兼容。前端 `npm run build` 已通过。

## PaperForge V4-P1.2 — SaaS App Shell

状态：已完成。新增 `(workspace)` 路由组与统一 AppShell，提供 Sidebar、Topbar、真实 Workspace Switcher 和 User Menu；`/dashboard` 与 `/tasks/[taskId]` 保持原 URL 且接入壳层，新增 `/tasks`、`/templates`、`/settings` 工作区入口。根论文处理工作台、认证/Admin 页面及后端 API 均未改动；模板和设置入口继续复用工作台中的既有业务界面。前端 `npm run build` PASS。

## PaperForge V4-P1.3 — Dashboard 产品化

状态：已完成。Dashboard 保留既有 `GET /tasks` 任务获取逻辑，并复用现有 `GET /usage` 展示当前 Workspace 的月度额度；新增产品欢迎区、Workspace 信息、Quick Start、Recent Tasks、状态 Badge、Metrics 和无任务引导。页面使用 V4 `Card/Badge/Button/EmptyState/Loading` 组件，Dashboard 专用布局样式放入 CSS Module，未继续扩展 `globals.css`；未修改后端、API contract 或论文处理业务流。Workspace 切换时同步本地 Workspace 名称，避免 Dashboard 显示旧名称。前端 `npm run build` PASS，`git diff --check` PASS。

## PaperForge V4-P1.4 — Task Detail 产品化

状态：已完成。任务详情页已升级为 SaaS 核心工作流页面，按“任务头部 → 结果概览 → Workflow Timeline → Agent Execution → Artifacts”展示；使用 V4 `Card/Badge/Button/Loading`，开发级 Trace 默认折叠。保留 SSE、`Last-Event-ID` 重连、轮询 fallback、Artifact 下载、DOCX 预览、失败重试和现有 Trace 数据；修改数量通过既有报告 Artifact 下载接口读取并在失败时降级显示。仅新增任务详情 CSS Module，未改后端、API contract 或 `globals.css`。

验收：frontend `npm run build` PASS；`git diff --check` PASS。

## PaperForge V4-P1.5 — New Task 页面产品化

目标：在不修改后端 API、不删除旧入口的前提下，将论文任务创建流程升级为正式 SaaS 四步工作流。

完成：新增 `/tasks/new` 新建任务页，保留 DOCX 论文上传、文档分类确认、已有模板选择、临时模板上传、Local/AI 模式、额度提示、`POST /tasks` 创建和 `/tasks/[taskId]` 跳转。页面使用 V4 Card/Button/Input/Badge 与 CSS Module；AI fallback 和 Local 模式边界说明收敛到用户流程与高级信息区域。Dashboard、任务中心和 AppShell 的正式新建入口已切换到 `/tasks/new`，根路径旧工作台仍保留。

验收：frontend `npm run build` PASS；`git diff --check` PASS；后端目录无本轮变更，API contract 未修改，`globals.css` 未新增内容。

## PaperForge V4-P1.6 — Local Preview 自动登录

已完成：增加 `PAPERFORGE_PREVIEW_AUTO_LOGIN` 与 `NEXT_PUBLIC_PAPERFORGE_PREVIEW_AUTO_LOGIN` 双开关，并要求非生产 `APP_ENV`；后端 Preview 路由只创建/加载保留的 `.local` 用户，密码为服务端随机值且不返回，JWT 仍使用现有正式 token/version 校验。前端 Preview 成功后自动保存标准 session，并从根路径/登录页进入 `/dashboard`。生产环境始终拒绝 Preview 路由，不改变正式认证和 RBAC。

验收：Preview 专项 2 passed；backend compile、frontend `npm run build`、Compose config、`git diff --check` PASS。

## PaperForge V4-P1.7 — Preview Experience Polish

已完成：Dashboard 空状态补充产品价值说明、三步示例流程和创建第一个任务按钮；AppShell 仅在 development/local/preview 环境显示 `Preview Environment`。登录跳转、未登录保护、refresh 后 session 保留和 logout 行为保持可用，并避免 Preview logout 后立即自动重新登录。未修改生产认证、数据模型或 Agent 核心流程。

验收：frontend `npm run build`、backend pytest、`git diff --check` PASS；旧 V4 路由路径断言的陈旧测试保持单独记录。

## PaperForge Single-Admin Beta Feedback Console

已完成：复用既有 `ADMIN_EMAILS` 平台管理员 allowlist、JWT 认证和 `require_platform_admin`，新增只读跨 tenant `GET /admin/feedback`，支持分页、分类、用户/email、task id 和版本筛选；仅返回反馈字段及白名单速度 metadata，不返回 token、密码、论文正文或上传文件。新增 `/admin/feedback` 页面，支持列表、详情、筛选、分页、空态、错误态和非管理员拒绝态；现有 `/admin` 统计 Dashboard 保持不变并增加入口。

未新增用户权限字段或数据库 migration；唯一管理员原则仍由部署环境 `ADMIN_EMAILS` 显式指定，管理员继续使用正常登录流程。验收：专项后端 7 passed；后端全量 112 passed；frontend production build PASS；`git diff --check` PASS。
