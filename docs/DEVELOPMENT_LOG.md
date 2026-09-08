# Development Log (Historical)

> This is a chronological development record. Version labels and “current baseline” statements below describe their historical moment; the current public release is `v2.0-paperforge`. Use the README, architecture reference, and current code as the product specification.

## 2026-07-01 v1.0-showcase docs sync

### 修改目标

在 v0.9.5 trace UI 增强基础上做 v1.0-showcase 暑期实习展示版封版整理。当前功能层面未发现阻断级 FAIL；本轮重点是统一 README、PROJECT_STATUS、TODO 和 docs 演示材料中的版本口径，而不是继续开发新功能。

### 版本口径

- 当前稳定展示基线：tag `v1.0-showcase`，指向 commit `10904db`。
- `v0.9.4-demo-screenshot-package` 是上一阶段截图包 tag。
- `main` 分支包含 `v1.0-showcase` 之后的公开前文档和面试材料补充，不代表 `v1.0-showcase` tag 已移动。
- v0.9.5 trace UI 相关增强已纳入 `v1.0-showcase` 稳定展示版。

### 修改范围

- 更新 `README.md`
  - 标记当前版本为 `v1.0-showcase / 暑期实习展示版`。
  - 明确当前稳定展示基线为 tag `v1.0-showcase`。
  - 补充 v1.0-showcase 可展示能力和 v1.1 延期项。
- 更新 `PROJECT_STATUS.md`
  - 将当前阶段切换为 v1.0-showcase 封版整理。
  - 记录稳定展示 tag、main 后续文档补充和上一阶段 tag。
  - 将深度内容修改、完整 task state 可视化、异步队列/断点续跑等放入 v1.1。
- 更新 `TODO.md`
  - 将 v0.9.5 trace UI 相关增强纳入 `v1.0-showcase` 稳定展示版。
  - 将 v1.0-showcase 标记为稳定展示版本。
  - 整理 v1.1 延期项。
- 更新 `docs/DEMO_SCRIPT.md`、`docs/INTERVIEW_DEMO_PACKAGE.md`、`docs/DEMO_SCREENSHOT_GUIDE.md`
  - 统一演示基线、旧 tag 含义和封版 tag 建议。
- 新增 `docs/V1_0_SHOWCASE_SUMMARY.md`
  - 汇总项目定位、推荐基线、可展示功能、演示流程、架构摘要、Agent trace、回归说明、限制和 v1.1 计划。

### 未修改范围

- 没有修改 `paper-ai/backend/**` 核心业务代码。
- 没有修改 `paper-ai/frontend/app/page.tsx` 或上传、运行、预览、下载主流程。
- 没有修改 API 字段结构。
- 没有新增依赖。
- 没有移动、删除或重建任何 tag。

### v1.0-showcase 最小回归

- `python -m py_compile`：PASS。
- `python test_agent_orchestrator_trace.py`：PASS。
- `python test_smoke_agent_flow.py`：PASS。
- `python run_real_doc_regression.py --manifest test_documents/manifest.csv --mode local --limit 1 --run-id v1_0_showcase_manifest_smoke`：PASS，1/1。
- `python run_real_doc_regression.py --manifest test_documents/generated_manifest.csv --mode local --limit 1 --run-id v1_0_showcase_generated_smoke`：PASS，1/1。
- `npm run build`：PASS。
- heavy_manifest 全量回归：本轮未执行，保留为打 tag 前可选长测；历史记录已有 heavy 1/1 PASS。

## 2026-06-27 v0.9.5-demo-trace-ui roadmap sync

### 修改目标

在 `v0.9.4-demo-screenshot-package` 已完成、真实网页截图已归档、远端 `main` 已同步到 `e169bfb` 的基础上，先做一次阶段切换文档同步。下一阶段统一调整为 `v0.9.5-demo-trace-ui`，目标是增强 Agent Trace 可视化、模板规则摘要展示和修改前后 Diff 展示。

### 修改范围

- 更新 `PROJECT_STATUS.md`
  - 明确 v0.9.4 demo screenshot package 已完成。
  - 明确当前下一阶段为 `v0.9.5-demo-trace-ui`。
  - 写清 v0.9.5 是 UI 展示增强阶段，不是核心格式化算法重构。
  - 写清保持上传、预览、下载功能不变，保持 local/ai 模式兼容。
- 更新 `TODO.md`
  - 将当前 v0.9.5 路线调整为 `v0.9.5-demo-trace-ui`。
  - 将旧的 `v0.9.5-resume-project-description` 降级为后续非当前优先级，避免与新阶段冲突。
  - 补充不得移动、删除或重建 `v0.9.4-demo-screenshot-package` tag 的版本治理约束。
- 更新 `docs/DEVELOPMENT_LOG.md`
  - 增加本次阶段切换记录。
  - 修正 v0.9.4 日志中的后续路线指向。

### 未修改范围

- 没有修改 `paper-ai/backend/**`。
- 没有修改 `paper-ai/frontend/**`。
- 没有修改 `services/**`。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改任何业务代码。
- 没有修改任何截图文件。
- 没有改动 tag，未移动 `v0.9.4-demo-screenshot-package` tag。

### v0.9.5 路线边界

- 本阶段计划增强 Agent Trace 可视化。
- 本阶段计划增加模板规则摘要展示。
- 本阶段计划增加修改前后 Diff 展示。
- 本阶段必须保持现有上传、预览、下载功能不变。
- 本阶段必须保持 local/ai 模式兼容。
- 本阶段不做大规模重构，不重写核心格式化算法，不改变 `/agent/run` 同步语义。

## 2026-06-27 v0.9.4-demo-screenshot-package

### 修改目标

在 `v0.9.3-interview-demo-package` 稳定节点基础上，整理 demo 截图/录屏清单和展示素材说明，让项目更方便用于面试、简历、作品集和演示。本轮只改文档，不修改后端核心逻辑、前端 UI、接口、依赖或 demo 输入输出文件。

### 修改范围

- 新增 `docs/DEMO_SCREENSHOT_GUIDE.md`
  - 整理 13 张推荐截图：首页 Hero、上传工作台、文件已选择、运行中状态、结果 dashboard、评分 `80 -> 86`、修改报告、参考文献/图表检查、TracePanel 折叠/展开、在线预览、下载入口和 390px 窄屏。
  - 说明每张截图适合用于 README、简历附件、面试演示、作品集、社媒展示或答辩 PPT。
  - 补充 60-90 秒录屏脚本。
  - 补充 ASCII 临时路径、`http://127.0.0.1:8000` API base、`NEXT_PUBLIC_API_BASE_URL`、demo 后 `git status` 干净和临时服务停止等自动化演示注意事项。
  - 补充截图命名建议和能力边界提醒。
- 更新 `docs/DEMO_SCRIPT.md`
  - 版本同步到 `v0.9.4-demo-screenshot-package`。
  - 补充截图和录屏顺序、重点停顿画面和 TracePanel 讲解边界。
- 更新 `docs/INTERVIEW_DEMO_PACKAGE.md`
  - 新增“截图/录屏素材建议”小节，并指向 `docs/DEMO_SCREENSHOT_GUIDE.md`。
- 更新 README、PROJECT_STATUS、TODO 和 DEVELOPMENT_LOG
  - 标记当前版本为 `v0.9.4-demo-screenshot-package`。
  - 后续路线指向 `v0.9.5-demo-trace-ui` 和 `v1.0-demo-release-candidate`；`v0.9.5-resume-project-description` 保留为后续非当前优先级。

### 未修改范围

- 没有修改 `paper-ai/backend/**`。
- 没有修改 `paper-ai/frontend/app/page.tsx` 或 `paper-ai/frontend/app/globals.css`。
- 没有修改 `/agent/run`、上传、预览或下载接口语义。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 `demo_inputs/*` 或 `demo_outputs/*`。
- 没有新增异步队列、完整断点续跑、前端 task state 文件读取或完整工业级能力。

### v0.9.4 验收说明

- `git status --short`：PASS，仅包含本轮允许的文档改动和新增 `docs/DEMO_SCREENSHOT_GUIDE.md`。
- `git diff --name-only`：PASS，仅包含 README、PROJECT_STATUS、TODO、DEVELOPMENT_LOG、DEMO_SCRIPT、INTERVIEW_DEMO_PACKAGE 等文档文件；未出现代码、接口、依赖或 demo 样本改动。
- `npm run build`：SKIPPED，本轮只改文档，不修改前端代码、依赖或构建配置。
- 后端 smoke：SKIPPED，本轮只改文档，不修改后端逻辑、接口或测试断言。
- 能力边界检查：PASS，文档继续明确不是论文代写、正式查重、异步队列、完整断点续跑或完整工业级 Agent。

### 远端同步与素材目录状态

- 本地提交 `c1741ae` 已打 tag：`v0.9.4-demo-screenshot-package`。
- 远端同步前检查：PASS，`git status --short` 为空，当前分支为 `main`，HEAD 包含 `v0.9.4-demo-screenshot-package`，`origin` 指向 `https://github.com/AKl2781/ai-paper-format-agent.git`。
- 远端同步结果：PASS，`git push origin main` 和 `git push origin v0.9.4-demo-screenshot-package` 均成功。
- demo 截图素材目录已准备：`docs/assets/screenshots/`。
- 2026-06-27 已补充真实网页运行截图：`docs/assets/screenshots/real-web-2026-06-27/`，共 10 张，覆盖首页、上传、运行中、结果 dashboard、检查模块、TracePanel、在线预览和下载入口。
- 本次真实截图评分为 `81 -> 87`；历史固定 demo 输出样例仍为 `80 -> 86`，文档中已提醒展示时区分来源。

## 2026-06-27 v0.9.3-interview-demo-package

### 修改目标

在 `v0.9.2-ui-fetch-compat-fix` 稳定节点基础上，整理面试/演示材料，让项目从“能跑”进一步变成“能讲、能展示、能回答追问”。本轮基于 v0.9.2 final demo check 的真实结果整理材料，不修改核心代码。

### 修改范围

- 新增 `docs/INTERVIEW_DEMO_PACKAGE.md`
  - 整理项目一句话介绍、30 秒介绍、2 分钟演示流程、技术架构讲法、项目亮点、当前边界和面试追问。
  - 明确推荐演示代码基线为 `v0.9.2-ui-fetch-compat-fix`。
  - 记录 ASCII 临时路径上传建议、评分 `80 -> 86`、TracePanel 9 步、preview/download PASS 和 demo 后 Git 干净。
- 更新 `docs/DEMO_SCRIPT.md`
  - 同步到 v0.9.3 演示口径。
  - 补充 v0.9.2 final demo check 结果和 ASCII 临时路径说明。
- 更新 `docs/archive/INTERVIEW_QA.md`
  - 补充 v0.9.0-v0.9.2 后的新追问，包括产品化首页、API base URL、ASCII 临时路径、`ERR_ALPN_NEGOTIATION_FAILED` 定位和 Git 运行产物治理。
- 更新 `docs/DEMO_RESULT.md` 和 `docs/DEMO_CASE.md`
  - 补充当前推荐演示基线和真实页面 demo 验收结果。
- 更新 README、PROJECT_STATUS、TODO 和 DEVELOPMENT_LOG
  - 标记当前版本为 `v0.9.3-interview-demo-package`。
  - 后续路线指向 `v0.9.4-demo-screenshot-package`、`v1.0-demo-release-candidate`、`v1.1-resume-draft-design` 和 `v1.2-real-user-case`。

### 未修改范围

- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改 `task_state.py`。
- 没有修改 formatter/analyzer/language reviewer 核心业务逻辑。
- 没有修改前端 UI。
- 没有修改接口语义。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 demo 输入/输出样本文件。
- 没有新增异步队列、完整断点续跑、前端 task state 文件读取或完整工业级能力。

### v0.9.3 验收说明

- `git status --short`：PASS，仅包含本轮允许的文档改动和新增 `docs/INTERVIEW_DEMO_PACKAGE.md`。
- `git diff --name-only`：PASS，仅包含 README、PROJECT_STATUS、TODO、DEVELOPMENT_LOG、DEMO_SCRIPT、INTERVIEW_QA、DEMO_RESULT、DEMO_CASE 等文档文件；未出现代码、接口、依赖或 demo 样本改动。
- `npm run build`：SKIPPED，本轮只改文档，不修改前端代码、依赖或构建配置。
- 后端 smoke：SKIPPED，本轮只改文档，不修改后端逻辑、接口或测试断言。
- 能力边界检查：PASS，文档继续明确不是论文代写、正式查重、异步队列、完整断点续跑或完整工业级 Agent。

## 2026-06-26 v0.9.2-ui-fetch-compat-fix

### 修改目标

在 `v0.9.1-ui-run-flow-fix` 稳定节点基础上，只排查并修复前端浏览器请求本地 FastAPI 后端时出现 `Failed to fetch` / `ERR_ALPN_NEGOTIATION_FAILED` 的兼容问题。

### 问题定位

- 后端 `/agent/run` 使用同一组 demo 文件 Python 直调返回 200，说明不是后端字段不匹配，也不是后端 4xx/5xx。
- 后端本地服务为 HTTP，默认端口 8000；CORS 已允许 `http://localhost:3000` 和 `http://127.0.0.1:3000`。
- 前端原先硬编码 `http://127.0.0.1:8000`，所有请求虽然基本一致，但缺少集中配置和错误 URL 展示，不利于定位本地浏览器、代理、host 或协议问题。
- 自动化复现中，Chromium/Edge CDP 对当前中文仓库路径下的文件句柄存在读取异常；同内容 demo 文件复制到 ASCII 临时路径后，浏览器真实点击流程可通过。该现象会在 Network 中表现为上传请求 `ERR_ALPN_NEGOTIATION_FAILED`。

### 修改范围

- 更新 `paper-ai/frontend/app/page.tsx`
  - 新增 `DEFAULT_API_BASE_URL` 和 `API_BASE`，默认使用 `http://127.0.0.1:8000`。
  - 支持 `NEXT_PUBLIC_API_BASE_URL` 覆盖本地后端地址。
  - 新增 `apiUrl(...)`，统一拼接 `/document/classify`、`/agent/run`、`/preview/{filename}` 和下载链接。
  - 网络错误提示会包含实际请求 URL，便于定位后端地址、端口、协议或浏览器本地上传兼容问题。
- 更新 README、PROJECT_STATUS、TODO 和 DEVELOPMENT_LOG
  - 标记当前版本为 `v0.9.2-ui-fetch-compat-fix`。
  - 记录本轮只修前端 fetch 兼容层，不改后端核心逻辑或 UI 视觉布局。

### 未修改范围

- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改 `task_state.py`。
- 没有修改 formatter/analyzer/language reviewer 核心业务逻辑。
- 没有修改 UI 视觉布局。
- 没有修改上传、预览、下载主流程语义。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 demo 输入/输出样本文件。
- 没有新增依赖、异步队列、完整断点续跑或 task state 文件内容读取能力。

### v0.9.2 验收说明

- `npm run build`：PASS，无 warning。
- 浏览器请求：PASS；同内容 demo 文件从 ASCII 临时路径上传时，`/document/classify`、`/agent/run` 和 `/preview/{filename}` 均返回 200，未再出现 `ERR_ALPN_NEGOTIATION_FAILED`。
- 页面结果：PASS；评分、修改报告、参考文献检查、图表检查、默认折叠 TracePanel、`task_id` / `task_state_path` 摘要、在线预览和下载均可观察。
- 下载接口：PASS；下载链接返回 200，content-type 为 Word docx。
- 响应式检查：PASS；1440px 和 390px 视口下未发现横向溢出。
- 运行产物治理：PASS；后端模板上传副本和 `task_states/` 运行产物继续命中 `.gitignore`。

## 2026-06-26 v0.9.1-ui-run-flow-fix

### 修改目标

在 `v0.9.0-ui-landing-redesign` 稳定节点基础上，只排查并修复前端页面点击运行 Agent 失败/错误提示过于笼统的问题。后端 `/agent/run` 直接调用已成功，本轮重点确认浏览器页面上传、点击运行、报告、TracePanel、预览和下载链路。

### 问题定位

- 前端 `runAgent()` 的字段名与后端一致：`paper`、`template`、`mode`、`allow_non_paper`。
- 后端 `/agent/run` 接收字段也一致，接口直调 demo 文件返回 `status=ok`。
- 原前端在 `fetch` 后直接 `response.json()`，一旦遇到空响应、非 JSON 错误或网络异常，只会进入笼统 catch，显示“Agent 启动失败，请确认后端服务正在运行”，不利于定位真实原因。
- 原前端在文档分类请求失败但用户继续运行时，仍传 `allow_non_paper=false`，与页面“仍可启动 Agent”的提示不完全一致。

### 修改范围

- 更新 `paper-ai/frontend/app/page.tsx`
  - 新增轻量响应读取函数，支持 JSON、空响应和非 JSON 文本。
  - 新增统一错误信息提取函数，优先展示后端 `detail.failed_step`、`detail.error`、`detail.message` 或文本错误。
  - `runAgent()` 在分类失败但用户继续运行时透传 `allow_non_paper=true`。
  - 保持原有上传、预览、下载、TracePanel 和 `/agent/run` 同步调用语义不变。
- 更新 README、PROJECT_STATUS、TODO 和 DEVELOPMENT_LOG
  - 标记当前版本为 `v0.9.1-ui-run-flow-fix`。
  - 记录本轮只修前端运行链路，不改后端核心逻辑或 UI 视觉布局。

### 未修改范围

- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改 `task_state.py`。
- 没有修改 formatter/analyzer/language reviewer 核心业务逻辑。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 demo 输入/输出样本文件。
- 没有新增依赖、异步队列、完整断点续跑或 task state 文件内容读取能力。

### v0.9.1 验收说明

- `git status --short`：PASS，仅包含 `paper-ai/frontend/app/page.tsx` 与 README、PROJECT_STATUS、TODO、DEVELOPMENT_LOG 文档改动。
- `git diff --name-only`：PASS，仅包含本轮允许修改的 5 个文件，未出现后端核心代码、依赖文件或 demo 样本改动。
- `npm run build`：PASS，无 warning。
- 浏览器真实点击 demo 流程：PASS；上传 `messy_paper_sample.docx` 和 `template_sample.docx`，选择本地规则模式，点击运行后 `/agent/run` 返回 200，`/preview` 返回 200，页面存在下载链接。
- 页面结果：PASS；评分变化、修改报告、参考文献检查、图表检查、TracePanel、`task_id` / `task_state_path` 摘要、在线预览和下载均可观察。
- 运行产物治理：PASS；`paper-ai/backend/templates/template_sample.docx` 与 `paper-ai/backend/task_states/example.json` 均命中 `.gitignore` 规则，运行产物不会污染 Git 工作区。

## 2026-06-25 v0.9.0-ui-landing-redesign

### 修改目标

在 `v0.8.6-template-runtime-cleanup` 稳定节点基础上，只做前端视觉和布局升级，让首页更接近 AI SaaS 产品页 + 工具工作台 + 结果仪表盘风格，提升演示吸引力。

### 修改范围

- 更新 `paper-ai/frontend/app/page.tsx`
  - 首屏改为 Hero、能力卡片、静态仪表盘预览和上传工作台组合。
  - 上传论文、上传模板、模式选择和启动 Agent 仍保留原有 input、state 和 fetch 语义。
  - 结果区继续展示评分、修改报告、检查结果、TracePanel、预览和下载。
- 更新 `paper-ai/frontend/app/globals.css`
  - 升级页面背景、Hero、能力卡片、上传卡片、模式选择、主按钮和结果 dashboard 视觉层次。
  - 保留 390px 窄屏下的单列收敛、长文本换行和横向溢出保护。
  - TracePanel 继续默认折叠，展开后更像 Agent 执行时间线。
- 更新 README、PROJECT_STATUS、TODO 和 DEVELOPMENT_LOG
  - 标记当前版本为 `v0.9.0-ui-landing-redesign`。
  - 说明本轮只做前端视觉升级，不改变后端接口或核心流程。
  - 后续路线指向 `v0.9.1-ui-final-demo-check`、`v0.9.2-interview-demo-package` 和 `v1.0-demo-release-candidate`。

### 未修改范围

- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改 `task_state.py`。
- 没有修改后端 smoke 测试断言。
- 没有修改 formatter/analyzer/language reviewer 核心业务逻辑。
- 没有修改 `/agent/run` 接口调用逻辑或同步语义。
- 没有修改上传、预览、下载主流程语义。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 demo 输入/输出样本文件。
- 没有新增 UI 库、异步队列、完整断点续跑或 task state 文件内容读取能力。

### v0.9.0 验收说明

- `git status --short`：PASS，仅显示本轮允许修改的 6 个文件。
- `git diff --name-only`：PASS，仅包含 `paper-ai/frontend/app/page.tsx`、`paper-ai/frontend/app/globals.css`、`README.md`、`PROJECT_STATUS.md`、`TODO.md`、`docs/DEVELOPMENT_LOG.md`。
- `npm run build`：PASS，无 warning。
- 桌面 / 390px 窄屏页面观察：PASS；1440px 和 390px 视口下 `scrollWidth == innerWidth`，未发现横向溢出。
- `python paper-ai/backend/test_smoke_agent_flow.py`：SKIPPED；本轮未修改后端逻辑、接口语义或测试断言。

## 2026-06-25 v0.8.6-template-runtime-cleanup

### 修改目标

在 `v0.8.5-ui-polish-details` 稳定节点基础上，只做运行产物治理，修复 demo 上传模板后产生 `paper-ai/backend/templates/template_sample.docx` 未跟踪文件的问题。

### 修改范围

- 删除未跟踪运行产物 `paper-ai/backend/templates/template_sample.docx`。
- 更新 `.gitignore`
  - 新增 `paper-ai/backend/templates/*.docx`。
  - 用于忽略后端上传模板运行副本，避免 demo 后污染 Git 工作区。
  - 不影响 `demo_inputs/template_sample.docx`，该文件仍是固定 demo 输入样本。
- 更新 README、PROJECT_STATUS、TODO 和 DEVELOPMENT_LOG
  - 标记当前版本为 `v0.8.6-template-runtime-cleanup`。
  - 说明本轮是运行产物治理，不是业务功能增强。
  - 后续路线指向 `v0.8.7-demo-ui-final-check` 和 `v0.9-resume-draft`。

### 未修改范围

- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改 `task_state.py`。
- 没有修改后端 smoke 测试断言。
- 没有修改 formatter/analyzer/language reviewer 核心业务逻辑。
- 没有修改前端 UI。
- 没有修改 `/agent/run` 同步语义。
- 没有修改上传、预览、下载主流程语义。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 demo 输入/输出样本文件。
- 没有新增异步队列、完整断点续跑或 task state 文件内容读取能力。

### v0.8.6 验收说明

- `git status --short`：PASS，仅包含 `.gitignore` 和状态文档改动，未出现未跟踪模板副本。
- `git diff --name-only`：PASS，仅包含 `.gitignore`、README、PROJECT_STATUS、TODO 和 DEVELOPMENT_LOG。
- `git check-ignore -v paper-ai/backend/templates/template_sample.docx`：PASS，命中 `.gitignore:18:paper-ai/backend/templates/*.docx`。
- `npm run build`：SKIPPED；本轮未修改前端代码、前端依赖或页面样式。
- `python paper-ai/backend/test_smoke_agent_flow.py`：SKIPPED；本轮未修改后端逻辑、接口语义或测试断言。

## 2026-06-25 v0.8.5-ui-polish-details

### 修改目标

在 `v0.8.4-ui-polish-layout` 稳定节点基础上，只修前端 UI 细节，重点解决 390px 左右窄屏下页面轻微横向溢出问题，并优化小屏展示观感。

### 修改范围

- 更新 `paper-ai/frontend/app/globals.css`
  - 为 `html/body`、`.page`、`.workspace` 和主要页面区块增加横向溢出保护。
  - 为上传卡片、模式按钮、主按钮、结果区、TracePanel、报告卡片等补充 `min-width: 0`、`max-width: 100%`、自然换行和小屏内边距规则。
  - 窄屏下将 `mode-switch`、上传区、结果区、检查区和操作区收敛为单列。
  - 优化 `task_state_path`、任务 ID、文件名和说明文字的换行，避免长文本撑破页面。
- 更新 README、PROJECT_STATUS、TODO 和 DEVELOPMENT_LOG
  - 标记当前版本为 `v0.8.5-ui-polish-details`。
  - 说明本轮只修前端响应式细节，不改变后端接口或核心流程。
  - 后续路线指向 `v0.8.6-demo-ui-check` 和 `v0.9-resume-draft`。

### 未修改范围

- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改 `task_state.py`。
- 没有修改后端 smoke 测试断言。
- 没有修改 formatter/analyzer/language reviewer 核心业务逻辑。
- 没有修改 `/agent/run` 同步语义。
- 没有修改上传、预览、下载主流程语义。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 demo 输入/输出样本文件。
- 没有新增异步队列、完整断点续跑或 task state 文件内容读取能力。

### v0.8.5 验收说明

- `git status --short`：PASS，仅包含本轮允许的前端样式与文档文件改动。
- `git diff --name-only`：PASS，未出现后端核心代码、接口、测试断言、依赖文件或 demo 样本改动。
- `npm run build`：PASS，无 warning。
- 桌面 / 390px 窄屏截图检查：PASS；桌面布局保持正常，390px 视口下 `scrollWidth == innerWidth`，未发现横向溢出。
- `python paper-ai/backend/test_smoke_agent_flow.py`：SKIPPED；本轮未修改后端，且该脚本会覆盖 Git 跟踪的 smoke 模板文件。

## 2026-06-24 v0.8.4-ui-polish-layout

### 修改目标

在 `v0.8.2-trace-ui-polish` 稳定节点基础上，只做前端页面布局与展示层次打磨，让项目更适合演示和实习展示。

### 修改范围

- 更新 `paper-ai/frontend/app/page.tsx`
  - 顶部增加能力标签，让页面开头更像正式工具产品。
  - 上传论文、上传模板、模式选择和运行按钮整理到“开始处理”区域。
  - 结果区按总览、评分变化、修改报告、评分模块、检查结果、重复风险、Agent 执行过程、预览与下载重新组织。
  - before_score / after_score 在总览区更醒目，并展示提升值、模式、AI 参考参与状态和任务 ID。
  - TracePanel 保持默认折叠，继续只展示 `agent_trace` 列表和 `task_id` / `task_state_path` 摘要。
  - 不展示 `agent_trace_detail`，不读取 task state 文件内容。
- 更新 `paper-ai/frontend/app/globals.css`
  - 增加 `setup-panel`、`result-heading`、`score-pair`、`checks-grid`、结果元信息标签等局部样式。
  - 优化上传卡片、运行按钮、结果总览、报告卡片、TracePanel 和移动端布局。
  - 未引入新 UI 库，未改上传、预览、下载按钮功能。
- 更新 README、PROJECT_STATUS 和 TODO
  - 标记当前版本为 `v0.8.4-ui-polish-layout`。
  - 说明本轮是前端展示层次和演示观感优化。
  - 后续路线指向 `v0.8.5-ui-polish-details`、`v0.8.6-demo-ui-check` 和 `v0.9-resume-draft`。

### 未修改范围

- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改 `task_state.py`。
- 没有修改后端 smoke 测试断言。
- 没有修改 formatter/analyzer/language reviewer 核心业务逻辑。
- 没有修改 `/agent/run` 同步语义。
- 没有修改上传、预览、下载主流程语义。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 demo 输入/输出样本文件。
- 没有新增异步队列、完整断点续跑或 task state 文件内容读取能力。

### v0.8.4 验收说明

- `git status --short`：待最终检查。
- `git diff --name-only`：待最终检查。
- `npm run build`：待最终检查。
- `python paper-ai/backend/test_smoke_agent_flow.py`：计划跳过；本轮未修改后端，且该脚本会覆盖 Git 跟踪的 smoke 模板文件。

## 2026-06-18 v0.8.2-trace-ui-polish

### 修改目标

在 `v0.8.1-trace-ui-minimal` 稳定节点基础上，只对前端 TracePanel 做小范围展示打磨：优化步骤列表文案、fallback 兜底提示、task state 摘要说明和缺字段保护。

### 修改范围

- 更新 `paper-ai/frontend/app/page.tsx`
  - TracePanel 标题调整为“Agent 执行过程”。
  - 说明 `agent_trace` 是步骤级执行记录，用于展示处理链路、耗时和 fallback 情况。
  - `fallback_used=true` 显示为“已使用 fallback / 本地规则兜底”，不表述为严重失败。
  - `task_id` 显示为“任务 ID”，`task_state_path` 显示为“后端任务状态文件路径”。
  - 补充说明前端不会读取 task state 文件内容，也不代表异步队列或任务恢复能力。
  - 缺失 `message`、`duration_ms`、`status` 时使用温和默认展示。
- 更新 `paper-ai/frontend/app/globals.css`
  - 小范围补充 TracePanel、状态标签、fallback 标签和空状态样式。
  - 未改上传、预览、下载按钮样式或页面主布局。
- 更新 README、PROJECT_STATUS 和 TODO
  - 标记当前版本为 `v0.8.2-trace-ui-polish`。
  - 说明当前只是 TracePanel 展示体验打磨。
  - 后续路线指向 `v0.8.3-demo-ui-check` 和 `v0.9-resume-draft`。

### 未修改范围

- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改 `task_state.py`。
- 没有修改后端 smoke 测试断言。
- 没有修改 formatter/analyzer/language reviewer 核心业务逻辑。
- 没有修改上传、预览、下载主流程语义。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 demo 输入/输出样本文件。
- 没有新增异步队列、完整断点续跑或 task state 文件内容读取能力。
- 没有展示 `agent_trace_detail`。

### v0.8.2 验收说明

- `git status --short`：PASS，改动范围仅包含允许的前端文件和文档文件。
- `git diff --name-only`：PASS，未出现后端核心代码、依赖文件、demo 样本文件或测试断言改动。
- `npm run build`：PASS。
- `python paper-ai/backend/test_smoke_agent_flow.py`：SKIPPED；本轮未修改后端，且该脚本会生成运行产物，本轮重点验证前端构建。

## 2026-06-18 v0.8.1-trace-ui-minimal

### 修改目标

在 `v0.7.3-task-state-cleanup` 稳定节点基础上，给前端结果页增加最小 Agent 执行过程展示：默认折叠展示 `agent_trace` 步骤列表，并展示 `task_id` / `task_state_path` 任务状态摘要。

### 修改范围

- 更新 `paper-ai/frontend/app/page.tsx`
  - 新增 `AgentTraceItem` 类型。
  - 在 `AgentResult` 中新增可选字段：`agent_trace`、`agent_trace_detail`、`task_id`、`task_state_path`。
  - 新增默认折叠的 `TracePanel`。
  - 展示 `agent_trace` 的 `step`、`status`、`message`、`duration_ms`、`fallback_used`。
  - 展示 `task_id` 和 `task_state_path` 摘要。
  - 不展示 `agent_trace_detail`。
  - 不读取 `task_state_path` 对应文件内容。
- 更新 `paper-ai/frontend/app/globals.css`
  - 新增 `trace-panel`、`trace-list`、`trace-state`、`trace-meta` 等局部样式。
  - 未改上传、预览、下载按钮样式。
- 更新 README、PROJECT_STATUS 和 TODO
  - 标记当前版本为 `v0.8.1-trace-ui-minimal`。
  - 说明当前只是最小前端 trace 展示和 task state 摘要展示。
  - 说明当前仍不是异步队列、完整 task state 可视化、完整断点续跑或完整工业级 Agent。

### 未修改范围

- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改 `task_state.py`。
- 没有修改后端 smoke 测试断言。
- 没有修改 formatter/analyzer/language reviewer 核心业务逻辑。
- 没有修改上传、预览、下载主流程语义。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 demo 输入/输出样本文件。

### v0.8.1 验收说明

- `git status --short`：PASS，改动范围仅包含允许的前端文件和文档文件。
- `git diff --name-only`：PASS，未出现后端核心代码、依赖文件、demo 样本文件或测试断言改动。
- `npm run build`：PASS。
- `python paper-ai/backend/test_smoke_agent_flow.py`：PASS，local 模式仍保持 `ai_score=null`、`ai_used=false`，`agent_trace` 和 `task_state` 契约仍通过 smoke 校验。

## 2026-06-18 v0.7.3-task-state-cleanup

### 修改目标

在 `v0.7.2-task-state-sample` 稳定节点基础上，补充 task state 运行产物治理，避免 `paper-ai/backend/task_states/` 下的运行 JSON 污染 Git 工作区；同时补齐上轮只读检查发现的文档边界说明。

### 修改范围

- 更新 `.gitignore`
  - 新增 `paper-ai/backend/task_states/`。
  - 只忽略运行时 task state 目录。
  - 不影响 `demo_outputs/task_state_sample.json`，该文件仍作为固定 demo 样例保留在 Git 中。
- 更新 README
  - 标记当前版本为 `v0.7.3-task-state-cleanup`。
  - 补充当前不是完整工业级 Agent。
  - 说明 `task_states/` 是运行产物目录，`demo_outputs/task_state_sample.json` 是固定演示样例，两者不能混淆。
- 更新 `docs/ARCHITECTURE.md`
  - 补充 task state 运行产物与固定 demo 样例的区别。
- 更新 `docs/DEMO_SCRIPT.md` 和 `docs/DEMO_RESULT.md`
  - 补充 demo 样本不来自 CAJ 原文。
  - 保持“不来自真实用户论文、不用于论文代写”的边界说明。
- 更新 `PROJECT_STATUS.md` 和 `TODO.md`
  - 标记 v0.7.3 完成。
  - 将轻量清理函数或维护命令规划到 `v0.7.4-task-state-cleanup-function`。

### 未修改范围

- 没有修改 `task_state.py`。
- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改前端页面交互。
- 没有修改测试断言。
- 没有修改 demo 输入/输出样本文件。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。

### v0.7.3 验收说明

- 本轮只修改 `.gitignore` 和 Markdown 文档。
- 未运行完整后端测试、smoke test 或 `npm run build`，原因是未修改 Python/前端业务代码、测试断言或依赖文件。
- 未运行 `py_compile`，原因是本轮未修改 Python 文件。
- 验收命令：`git status --short`、`git diff --name-only`、`git check-ignore paper-ai/backend/task_states/example.json`。

## 2026-06-18 v0.7.2-task-state-sample

### 修改目标

在 `v0.7.1-docs-sync-task-state` 稳定节点基础上，补充固定 `demo_outputs/task_state_sample.json`，并修复 `docs/DEMO_CASE.md` 中样本来源边界说明不够明确的问题。

### 修改范围

- 新增 `demo_outputs/task_state_sample.json`
  - 使用固定 `task_id=demo-task-state-sample`。
  - `status=succeeded`，`mode=local`。
  - `before_score=80`，`after_score=86`，与 `report_sample.json` 一致。
  - `ai_used=false`，`ai_score=null`，保持 local 模式语义。
  - `agent_trace_steps_count=9`，与 `agent_trace_sample.json` 一致。
  - `fallback_used=true`，来自当前 trace 样例中的 local AI 审校 fallback 标记。
  - 增加 `sample_note`，明确这是固定 demo 样例，不代表真实用户论文任务。
- 更新 `docs/DEMO_CASE.md`
  - 明确 demo 输入是人工构造 / 脱敏模拟样本。
  - 明确不来自真实用户论文，不来自 CAJ 原文，不用于论文代写。
  - 补充 `task_state_sample.json` 作为固定输出样例。
- 更新 `docs/DEMO_RESULT.md`、`docs/DEMO_SCRIPT.md`、README、PROJECT_STATUS 和 TODO
  - 同步 v0.7.2 状态。
  - 说明 `task_state_sample.json` 与 `agent_trace_sample.json` 的区别。
  - 保持当前仍不是异步队列、完整断点续跑或前端 task state 可视化的边界。

### 未修改范围

- 没有修改核心业务逻辑。
- 没有修改 `task_state.py`。
- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改前端页面交互。
- 没有修改测试断言。
- 没有修改 demo 输入 DOCX、格式化输出 DOCX、report 样例或 agent trace 样例。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。

### v0.7.2 验收说明

- 本轮只新增固定 demo JSON 样例和 Markdown 文档。
- 未运行完整后端测试、smoke test 或 `npm run build`，原因是未修改 Python/前端业务代码、测试断言或依赖文件。
- 验收命令：`git status --short`、`git diff --name-only`、Python JSON 合法性和字段一致性检查。

## 2026-06-18 v0.7.1-docs-sync-task-state

### 修改目标

在 `v0.7.0-task-state-minimal` 稳定节点基础上，只同步文档，把 task state 最小任务状态持久化能力、边界和演示方式写清楚。

### 修改范围

- 更新 `README.md`
  - 补充 task state 是任务状态持久化雏形。
  - 说明每次 Agent Pipeline 运行会生成 `task_id`。
  - 说明 task state 记录 `status`、`input_files`、`output_files`、`duration_ms`、`fallback_used`、`error` 等信息。
  - 说明 `agent_trace` 记录处理步骤，`task_state` 记录任务生命周期。
- 更新 `docs/ARCHITECTURE.md`
  - 在架构图中加入 `task_state.py` 和 `task_states/{task_id}.json`。
  - 说明 `agent_pipeline.py` 调用 `task_state.py` 进行状态落盘。
  - 说明 `/agent/run` 同步返回仍保持兼容，只额外透出 `task_id` 和 `task_state_path`。
  - 说明 task state 不替代 `modification_report`、`reference_check`、`figure_table_check` 或 `agent_trace`。
- 更新 `docs/archive/INTERVIEW_QA.md`
  - 新增 task state 与 agent_trace 区别、为什么不直接做异步队列、当前解决的问题和后续限制等问答。
- 更新 `docs/DEMO_SCRIPT.md`
  - 增加 task state 展示步骤。
  - 明确当前前端还没有 task state 可视化界面。
- 更新 `docs/DEMO_RESULT.md`
  - 说明 v0.7.0 后重新运行 demo 会生成 task state。
  - v0.7.1 当时明确记录了缺少固定 `demo_outputs/task_state_sample.json` 的缺口。
- 更新 `PROJECT_STATUS.md` 和 `TODO.md`
  - 标记当前版本和后续任务。

### 未修改范围

- 没有修改核心业务逻辑。
- 没有修改 `task_state.py`。
- 没有修改 `agent_pipeline.py`。
- 没有修改 `main.py`。
- 没有修改前端页面交互。
- 没有修改测试断言。
- 没有修改 demo 输入/输出样本文件。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。

### v0.7.1 验收说明

- 本轮只修改 Markdown 文档。
- 未运行完整后端测试、smoke test 或 `npm run build`，原因是未修改 Python/前端业务代码、测试断言或依赖文件。
- 验收命令：`git status --short`、`git diff --name-only`。

## 2026-06-17 v0.7.0-task-state-minimal

### 修改目标

在 `v0.6.3-real-demo-files` 稳定节点基础上，新增最小任务状态持久化能力。目标是记录每次 Agent 运行的生命周期状态，而不是把 `/agent/run` 改成异步队列，也不替代已有 `agent_trace`。

### 修改范围

- 新增 `paper-ai/backend/services/task_state.py`
  - 使用标准库生成 `task_id`。
  - 默认写入 `paper-ai/backend/task_states/{task_id}.json`。
  - 使用 UTF-8 JSON。
  - 使用临时文件加 `os.replace(...)` 写入，降低半写文件风险。
  - 记录 `running`、`succeeded`、`failed` 生命周期状态。
- 更新 `paper-ai/backend/services/agent_pipeline.py`
  - 在 pipeline 开始时创建 task state 并写入 `running`。
  - 成功返回前写入 `succeeded`。
  - 异常或内部 `status=error` 时写入 `failed`。
  - 结果中额外返回 `task_id` 和 `task_state_path`。
  - 保留原有返回字段语义和同步执行语义。
- 更新 `paper-ai/backend/test_smoke_agent_flow.py`
  - 校验 `/agent/run` 成功后存在 `task_id` 和 `task_state_path`。
  - 校验 task state 文件存在且 `status=succeeded`。
  - 校验 task state 包含 `input_files`、`output_files`、`duration_ms`。
  - 校验 local 模式仍保持 `ai_score=null`、`ai_used=false`。
  - 校验 `agent_trace` 仍为 list，下载字段仍可用。
  - 增加一个 direct pipeline 失败路径校验：不存在的 paper path 会写入 `status=failed` 和 `error`。
- 更新 `PROJECT_STATUS.md`、`TODO.md`、`README.md`
  - 记录当前版本、能力边界和后续任务。

### task_state 与 agent_trace 边界

- `task_state`：记录任务生命周期，例如 running、succeeded、failed、输入文件、输出文件、耗时、错误和评分摘要。
- `agent_trace`：记录处理步骤，例如识别文档类型、分析本地格式、模板解析、格式修复、AI 审校、重复风险预检、最终复查和报告生成。
- 本轮不做断点续跑，不做异步任务队列，不做前端进度条。

### 未修改范围

- 没有修改 formatter、analyzer、language reviewer 核心业务逻辑。
- 没有修改前端页面交互。
- 没有修改 `/agent/run` 的同步返回语义。
- 没有修改下载/预览逻辑。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。
- 没有修改 v0.6.3 demo 输入/输出样本文件。

### v0.7.0 测试结果

- `python -m py_compile paper-ai/backend/services/task_state.py paper-ai/backend/services/agent_pipeline.py paper-ai/backend/main.py`：PASS。
- `python test_reference_checker.py`：PASS。
- `python test_figure_table_checker.py`：PASS。
- `python test_risk_level_system.py`：PASS。
- `python test_composite_numbering.py`：PASS。
- `python test_formatter_mixed_heading.py`：PASS。
- `python test_score_consistency.py`：PASS。
- `python test_agent_orchestrator_trace.py`：PASS。
- `python test_smoke_agent_flow.py`：PASS，覆盖 task state 成功落盘和失败路径落盘。
- `npm run build`：SKIPPED。本轮未修改前端交互、前端依赖或前端页面代码。

## 2026-06-17 v0.6.3-real-demo-files

### 修改目标

在 `v0.6.2-demo-samples` 稳定节点基础上，补充一组可用于面试演示的人工构造脱敏模拟 DOCX 输入样本、模板样本，以及一次 local 模式真实运行输出，让项目从“有 demo 样本目录说明”升级为“有可演示输入/输出样例”。

### 修改范围

- 新增 `demo_inputs/messy_paper_sample.docx`
  - 标题为“基于传感器数据分析的健康风险快速检测方法研究”。
  - 包含封面、中文摘要、英文摘要、关键词、正文 5 节、图表标题和参考文献。
  - 故意保留标题层级、正文缩进、行距、图表编号引用和参考文献编号检查点。
  - 内容为人工构造的脱敏模拟文本，不来自真实用户论文。
- 新增 `demo_inputs/template_sample.docx`
  - 包含一级标题、二级标题、正文、摘要、参考文献、图题和表题样式示例。
- 新增 `demo_outputs/formatted_result_sample.docx`
  - 由当前现有 `run_agent_pipeline(...)` local 模式处理生成。
- 新增 `demo_outputs/report_sample.json`
  - 保存本次运行的分类、评分、`score_breakdown`、`modification_report`、`reference_check`、`figure_table_check`、`repeat_risk` 等重点字段。
- 新增 `demo_outputs/agent_trace_sample.json`
  - 保存本次运行的逐步 `agent_trace`。
- 新增 `docs/DEMO_RESULT.md`
  - 记录 demo 输入/输出路径、故意设置的格式问题、运行方式、重点字段、限制和验收情况。
- 更新 `docs/DEMO_CASE.md`、`docs/DEMO_SCRIPT.md`、`README.md`
  - 将 demo 文件状态从推荐路径更新为当前已内置的模拟输入和 local 输出样例。
- 更新 `PROJECT_STATUS.md` 和 `TODO.md`
  - 标记当前版本和下一阶段任务。

### 未修改范围

- 没有修改核心业务逻辑。
- 没有修改 `agent_pipeline.py`。
- 没有修改 `/agent/run`。
- 没有修改 `paper_agent.py`。
- 没有修改 formatter、analyzer、language reviewer。
- 没有修改前端交互。
- 没有修改已有返回字段结构或测试断言。
- 没有修改 `package.json`、lock 文件或 `requirements.txt`。

### v0.6.3 运行与验收

- 基线检查：PASS
  - `git status --short` 初始为空。
  - `git log --oneline --decorate -5` 显示 HEAD 位于 `v0.6.2-demo-samples`。
- DOCX 输入生成：PASS
  - `messy_paper_sample.docx` 和 `template_sample.docx` 已生成。
- DOCX 结构检查：PASS
  - 三个 DOCX 均可通过 `python-docx` 打开并读取段落和表格。
- local 处理流程：PASS
  - 直接调用现有 `run_agent_pipeline(...)`，未启动常驻服务。
  - `status=ok`，`mode=local`，`classification.document_type=academic_paper`，`confidence=0.95`。
  - `before_score=80`，`after_score=86`。
  - local 模式保持 `ai_score=null`、`ai_used=false`。
- DOCX 渲染视觉 QA：SKIPPED
  - 当前环境缺少 LibreOffice/`soffice`，`render_docx.py` 无法生成 PNG。
- 完整后端测试、smoke test、前端构建：SKIPPED
  - 本轮只新增 DOCX/JSON/Markdown 演示资产与文档，未修改 Python/前端业务代码、测试断言或依赖文件。

## 2026-06-14 v0.6.2-demo-samples

### 修改目标

在 `v0.6.1-demo-polish` 稳定节点基础上，补充固定演示样本目录说明和面试演示案例文档，让项目更适合作为暑期实习面试展示材料。

### 修改范围

- 新增 `demo_inputs/README.md`
  - 说明演示输入样本目录用途。
  - 推荐待修改论文和模板文件命名：`messy_paper_sample.docx`、`template_sample.docx`。
  - 明确当前不虚构真实 DOCX 文件，后续可放入脱敏后的真实样本。
- 新增 `demo_outputs/README.md`
  - 说明演示输出结果目录用途。
  - 推荐输出文件命名：`formatted_result_sample.docx`、`report_sample.json`、`agent_trace_sample.json`。
  - 明确未真实运行前不声称这些输出已经生成。
- 新增 `docs/DEMO_CASE.md`
  - 固定面试演示案例说明，覆盖输入样本特征、处理流程、重点观察字段和 1 分钟讲解话术。
- 更新 `docs/DEMO_SCRIPT.md`
  - 在演示准备和演示输出部分补充推荐样本路径。
  - 明确这些路径是建议命名，不代表仓库已经内置真实样本。
- 更新 `README.md`
  - 标记当前版本为 `v0.6.2-demo-samples`。
  - 增加 Demo Samples / 演示样本说明。
- 更新 `PROJECT_STATUS.md` 和 `TODO.md`
  - 记录 v0.6.2 当前状态。
  - 将后续任务调整为 `v0.6.3-real-demo-files`、`v0.7-task-state`、`v0.8-trace-ui`。

### 未修改范围

- 没有修改核心业务逻辑。
- 没有修改 `agent_pipeline`。
- 没有修改 `/agent/run`。
- 没有修改 formatter、analyzer、language reviewer。
- 没有修改前端交互。
- 没有修改已有返回字段结构或测试断言。
- 没有修改依赖文件或 lock 文件。
- 没有新增真实 DOCX 文件或真实运行输出样本。

### v0.6.2 验收说明

- 本轮只修改 Markdown 文档和演示目录说明。
- 未运行完整后端测试、smoke test 或 `npm run build`，原因是未修改任何 Python/前端业务代码、测试断言或依赖文件。
- 验收命令：`git status --short`。

## 2026-06-14 v0.5.4-summer-internship-showcase

### 修改目标

将当前 AI论文格式修改Agent 整理为可展示版本，在不大规模重构、不改变前端上传/预览/下载功能的前提下，补齐统一调度层、标准化 trace 和架构说明。

### 修改范围

- 新增 `paper-ai/backend/services/agent_pipeline.py`
  - 作为 `/agent/run` 的统一调度层。
  - 调用现有 `paper_agent.run_paper_agent(...)`。
  - 标准化 `agent_trace`，每一步包含 `step`、`status`、`duration_ms`、`fallback_used`、`message`。
  - 保留旧解释型 trace 到 `agent_trace_detail`。
  - 将 `after_analysis.reference_check` 和 `after_analysis.figure_table_check` 同步为顶层兼容字段。
- 更新 `paper-ai/backend/main.py`
  - `/agent/run` 改为调用 `run_agent_pipeline(...)`。
  - 上传、预览、下载路由保持不变。
- 更新 `paper-ai/backend/services/paper_agent.py`
  - 为现有 `steps` 增加 `duration_ms` 和 `fallback_used`。
  - 标记非标准论文确认、未上传模板、模板 warning、local 跳过 AI、AI fallback 等场景。
- 更新 `paper-ai/backend/test_smoke_agent_flow.py`
  - 增加对新 `agent_trace` 列表结构的 smoke 校验。
  - 增加顶层 `reference_check`、`figure_table_check` 兼容字段校验。
- 更新 `docs/ARCHITECTURE.md`
  - 说明系统架构、处理流程、兼容字段和 fallback 策略。

### v0.5.4 测试结果

- `python -m py_compile`：PASS
- 现有后端测试：PASS
- `npm run build`：PASS
- 结论：上传处理主流程、local 模式、ai fallback、模板上传、预览、下载和兼容字段校验均通过 smoke test。

## 2026-06-14 v0.6.1-demo-polish

### 修改目标

将项目整理为暑期实习面试可展示版本。本轮只增强展示文档，不修改核心业务逻辑。

### 修改范围

- 更新 `README.md`
  - 补充项目定位、当前版本、功能、技术栈、处理流程、启动方式、测试命令和项目亮点。
  - 明确当前是格式 Agent，不是论文代写、正式查重或深度内容改写系统。
- 更新 `docs/ARCHITECTURE.md`
  - 补充 mermaid 架构图。
  - 说明 `agent_pipeline.py`、`agent_trace`、`agent_trace_detail`、local/ai fallback 和旧字段兼容。
- 新增 `docs/DEMO_SCRIPT.md`
  - 整理面试演示流程，包括开场介绍、架构讲解、上传主流程、trace 展示、fallback 说明和测试展示。
- 新增 `docs/archive/INTERVIEW_QA.md`
  - 整理 18 个高频问答，覆盖 pipeline、trace、fallback、评分、参考文献、图表编号、兼容字段、测试覆盖和项目边界。
- 更新 `PROJECT_STATUS.md`
  - 标记当前版本为 `v0.6.1 / demo-polish`。
- 更新 `TODO.md`
  - 规划 `v0.6.2 demo 样本`、`v0.7 task_state`、`v0.8 trace UI`。

### 未修改范围

- 未修改核心业务逻辑。
- 未修改 formatter/analyzer/language reviewer。
- 未修改 `agent_pipeline` 核心执行逻辑。
- 未修改 `/agent/run` 接口行为。
- 未修改前端交互。
- 未修改已有返回字段结构。
- 未修改测试断言。
- 未修改依赖文件或 lock 文件。

### v0.6.1 测试结果

- `python -m py_compile`：PASS
  - 覆盖 `main.py`、`agent_pipeline.py`、`paper_agent.py`、`agent_orchestrator.py`、`document_classifier.py`、`docx_analyzer.py`、`docx_formatter.py`、`language_reviewer.py`、`plagiarism_checker.py`、`preview_service.py`、`template_extractor.py`。
- 现有后端测试：PASS
  - `test_reference_checker.py`
  - `test_figure_table_checker.py`
  - `test_risk_level_system.py`
  - `test_composite_numbering.py`
  - `test_formatter_mixed_heading.py`
  - `test_score_consistency.py`
  - `test_agent_orchestrator_trace.py`
- 主流程 smoke test：PASS
  - `test_smoke_agent_flow.py`
  - 覆盖上传处理主流程、local 模式、模板上传、AI fallback、预览、下载、`agent_trace`、`reference_check`、`figure_table_check`。
- `npm run build`：PASS
- 最终结论：PASS。v0.6.1 适合作为暑期实习面试展示文档版本；本轮没有修改核心业务逻辑。
