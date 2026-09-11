# 项目简介

本项目是一个基于 FastAPI + Next.js 的 AI 论文格式修改 Agent。当前目标是把原本分散的论文工具整合成“一次上传，Agent 自动处理，在线预览，确认后下载”的论文修改流程。

当前 Agent 更接近“格式 Agent”：格式修复能力已经可用，内容级修改能力仍然偏弱。最近真实性审计显示，local 模式会真实修改 Word 格式、标题、行距、缩进、字体和部分标签；AI 模式目前主要做少量词语级替换，还不是深度论文润色。

# 当前功能

已经实现：

- 文档分类：识别标准论文、课程作业、实验报告、简历、未知文档。
- 格式修复：统一标题、正文样式、字体、行距、缩进、页边距，清理部分模板占位内容。
- AI审校：调用 DeepSeek/OpenAI API 或本地 fallback 规则，输出语言建议与 AI 评分。
- 重复风险预检：检测相似段落、重复句子，给出风险等级和重复风险处理建议。
- 在线预览：将最终 docx 渲染成基础 HTML 预览。
- 修改报告：返回修复项、前后评分对比、修改次数、未修复问题和人工复查建议。
- local模式：只做本地格式修复、重复风险预检和本地评分。
- ai模式：在 local 格式修复基础上增加 AI/语言审校评分与建议。

# 项目结构

真实目录结构如下：

```text
paper-ai/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── dev.log
│   ├── uploads/
│   ├── outputs/
│   ├── templates/
│   │   └── template.docx
│   └── services/
│       ├── __init__.py
│       ├── document_classifier.py
│       ├── docx_analyzer.py
│       ├── docx_formatter.py
│       ├── language_reviewer.py
│       ├── paper_agent.py
│       ├── plagiarism_checker.py
│       ├── preview_service.py
│       └── template_extractor.py
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── next.config.ts
    ├── tsconfig.json
    ├── next-env.d.ts
    ├── dev.log
    ├── dev.err.log
    └── app/
        ├── globals.css
        ├── layout.tsx
        └── page.tsx
```

核心文件说明：

- `paper-ai/backend/main.py`：FastAPI 入口。只负责路由、文件保存、下载、预览接口，不应承载复杂业务逻辑。
- `paper-ai/backend/services/paper_agent.py`：Agent 主流程入口，核心函数是 `run_paper_agent(...)`。
- `paper-ai/backend/services/document_classifier.py`：docx 文档类型识别。
- `paper-ai/backend/services/docx_analyzer.py`：评分系统，计算 local_score、ai_score、final_score 和 breakdown。
- `paper-ai/backend/services/docx_formatter.py`：实际 Word 格式修复。
- `paper-ai/backend/services/template_extractor.py`：模板 docx 样式提取，并提供默认容错值。
- `paper-ai/backend/services/language_reviewer.py`：AI/本地语言审校建议与 AI 评分解析。
- `paper-ai/backend/services/plagiarism_checker.py`：重复风险检测/相似度预检。
- `paper-ai/backend/services/preview_service.py`：最终 docx 转 HTML 预览。
- `paper-ai/backend/run_real_doc_regression.py`：读取测试库 manifest 并批量执行分类、Agent、报告、预览、下载和 local AI 字段校验，输出回归结果。
- `paper-ai/frontend/app/page.tsx`：前端主页面，包含上传、模式选择、启动 Agent、执行过程、结果面板、预览和下载。
- `paper-ai/frontend/app/globals.css`：前端样式。

# Agent执行流程

真实执行流程在 `services/paper_agent.py` 中：

1. 识别文档类型：调用 `classify_document(paper_path)`。
2. 如果不是标准论文且 `requires_confirmation=true`，并且前端没有传 `allow_non_paper=true`，则返回 `status=requires_confirmation`。
3. 读取论文文件，确认 docx 存在。
4. 分析本地格式：调用 `check_repeat_risk(...)` 和 `analyze_docx(...)` 得到 `before_score`。
5. 识别模板格式：如果上传模板，调用 `extract_template_profile(template_path)`；否则使用通用论文规则。
6. 修复标题与正文格式：调用 `apply_paper_format(...)`，生成 `_formatted_*.docx`。
7. 如果 `mode=ai`：
   - 调用 `review_language_with_status(...)`。
   - 调用 `apply_language_suggestions(...)`。
   - 生成 `_language_*.docx`。
8. 如果 `mode=local`：
   - 跳过 AI 语言审校。
   - 最终文件为 `_formatted_*.docx`。
9. 重复风险预检：调用 `check_repeat_risk(final_path)`。
10. 最终复查：调用 `analyze_docx(...)`，local 模式不传 `ai_scores`，ai 模式传入 language reviewer 的 AI 评分。
11. 生成修改报告：调用 `build_modification_report(...)`。
12. 返回 JSON，包括：
    - `steps`
    - `before_score`
    - `after_score`
    - `score_breakdown`
    - `repeat_risk`
    - `download_url`
    - `filename`
    - `before_analysis`
    - `after_analysis`
    - `modification_report`
    - `language_review`

# API接口

## GET `/health`

健康检查。

返回：

```json
{
  "status": "ok"
}
```

## POST `/document/classify`

上传 docx 并识别文档类型。

参数：

- `paper`: 必填，`.docx` 文件。

返回重点字段：

- `document_type`: `academic_paper | course_assignment | lab_report | resume | unknown`
- `label`: 中文类型名
- `confidence`: 0 到 1
- `matched_features`: 命中特征
- `warning`: 非标准论文提示
- `requires_confirmation`: 是否需要用户确认继续
- `filename`: 上传后的文件名

## POST `/agent/run`

启动论文修改 Agent。

参数：

- `paper`: 必填，论文 `.docx`。
- `template`: 可选，模板 `.docx`。
- `allow_non_paper`: 可选布尔值。非标准论文需要传 `true` 才允许继续。
- `mode`: 可选，`local` 或 `ai`，默认 `ai`。

返回重点字段：

- `status`: `ok | requires_confirmation | error`
- `mode`: `local | ai`
- `steps`: Agent 执行过程
- `before_score`: 修改前评分
- `after_score`: 修改后评分
- `score_breakdown`: `{ local_score, ai_score, final_score, ai_used, ai_added_value }`
- `repeat_risk`: 重复风险预检结果
- `download_url`: 最终 docx 下载地址
- `filename`: 输出文件名
- `after_analysis`: 最终分析结果
- `modification_report`: 修改报告

## GET `/usage`

登录后读取当前 `X-Tenant-ID`（未传时使用个人 tenant）的自然月 Agent 运行额度。返回 `tenant_id`、`period_start`、`period_end`、`quota.limit`、`usage.used` 和 `remaining`；额度按 tenant 统计，默认 100 次/月，可由 `DEFAULT_AGENT_RUN_QUOTA` 配置。

## GET `/admin/stats`

平台管理员专用的聚合运营统计接口。除 JWT 认证外，用户邮箱必须命中部署环境的 `ADMIN_EMAILS` allowlist；返回 tenant/user/task 总数、task status summary，以及当前周期/历史 `agent_run` usage 和额度汇总，不返回租户、用户或任务明细。tenant 内的 `admin` 角色不会自动获得该平台权限。

## GET `/preview/{filename}`

读取 `backend/outputs/{filename}` 并返回 HTML 预览。

参数：

- `filename`: 输出 docx 文件名。

返回：

```json
{
  "html": "...",
  "title": "..."
}
```

## GET `/download/{filename}`

下载 `backend/outputs/{filename}`。

参数：

- `filename`: 输出 docx 文件名。

返回：

- Word 文件流，media type 为 `application/vnd.openxmlformats-officedocument.wordprocessingml.document`。

# 当前已知问题

根据最近回归测试和真实性审计，当前已知问题：

- 标准论文识别已经放宽，但仍可能在结构较弱、摘要/关键词/参考文献缺失时识别不稳定。
- 模板提取已有容错，但复杂模板、页眉页脚、目录、脚注、图片题注、公式编号仍未完整处理。
- AI评分可信度待提升：`ai_score` 来自 LLM 或 fallback 分析，和真实文本修改量没有强绑定。
- 内容级修改能力不足：AI 模式目前主要做少量词语级替换，不是深度论文润色。
- AI模式和local模式输出可能非常接近：最近审计中 local -> ai 只有 6 段轻微文本变化，格式没有变化。
- 异常内容识别不足：例如 `C-51` 这类模板残留可能没有彻底清理。
- 关键词格式只做了标签修正，关键词内容规范性仍不足。
- 标题正文混排识别不足，例如 `4.结语：正文内容...` 这类情况可能不会拆分成标题和正文。
- 参考文献识别仍然偏弱，最近审计中参考文献基础格式评分曾出现 58。
- 前端 `page.tsx`、后端部分文件在 PowerShell `Get-Content` 下曾出现乱码显示，需要注意 UTF-8 编码和中文文案。
- 仓库中存在运行产物目录 `uploads/`、`outputs/`、`.next/`、`node_modules/`、日志文件等，长期维护时应避免让这些进入版本控制或 AI 上下文。

# 开发规范

1. 不允许大规模重构。
2. 优先修 Bug，保持现有功能可用。
3. 每次修改必须回归测试。
4. 修改前先分析实际代码和失败原因。
5. 不允许删除已有功能。
6. 前端修复优先保证可用性：上传论文、可选模板、local/ai 模式、启动按钮、结果、预览、下载。
7. 后端修复优先保证 Agent 主链路不中断：分类、格式修复、AI fallback、预览、下载。
8. 不要把正式查重表述成“知网查重”，只能使用“重复风险检测”“相似度预检”。
9. local 模式必须 `ai_score=null` 且 `ai_used=false`。
10. ai 模式如果 LLM 失败，应降级继续，不得让总评分异常下降。
11. CNKI / GB/T 7714 测试来源只能使用公开或已授权文件；不得自动下载登录、付费、验证码或授权受限的 CNKI 正文全文，真实论文入库前必须脱敏。

# 回归测试清单

每次修改后建议至少检查：

1. Backend `py_compile` 通过：
   - `backend/main.py`
   - `backend/services/paper_agent.py`
   - `backend/services/document_classifier.py`
   - `backend/services/docx_analyzer.py`
   - `backend/services/docx_formatter.py`
   - `backend/services/language_reviewer.py`
   - `backend/services/plagiarism_checker.py`
   - `backend/services/preview_service.py`
   - `backend/services/template_extractor.py`
2. Frontend `npm run build` 通过。
3. 首页 `http://127.0.0.1:3000` 返回 200。
4. `/health` 返回 200。
5. `/document/classify` 能识别标准论文。
6. `/document/classify` 对课程作业/实验报告返回非论文提示。
7. 不上传模板，只上传论文，可以启动 Agent。
8. 上传模板后也可以启动 Agent。
9. local 模式可以启动，返回 `ai_score=null`、`ai_used=false`。
10. ai 模式可以启动，LLM 成功或失败都不能中断主流程。
11. `/preview/{filename}` 返回 HTML。
12. `/download/{filename}` 能下载最终 docx。
13. `modification_report` 包含 summary、before_after、change_counts、manual_review_items。
14. 启动按钮不能因为 `templateFile` 为空、`preview` 为空、`result` 为空、`document_type=unknown` 而永久 disabled。
15. 非标准论文如果 `requires_confirmation=true`，必须显示确认 checkbox，勾选后才能启动。

# 下一阶段路线图

当前方向：

```text
格式Agent
↓
内容Agent
↓
论文修改Agent
```

## 阶段一：强化格式Agent

- 稳定文档分类。
- 增强模板提取容错。
- 改进参考文献识别。
- 清理异常模板残留，如 `C-51`。
- 处理标题正文混排。
- 让修改报告与实际修改量一致。

## 阶段二：建设内容Agent

- 系统识别口语化表达。
- 系统识别主观化表达。
- 系统识别情绪化表达。
- 识别逻辑不通顺、观点跳跃、因果不清。
- 识别关键词内容不规范。
- 识别重复表达和段落主题混乱。
- 输出段落级问题清单，而不是只做词语替换。

## 阶段三：升级为真正论文修改Agent

- 将修改分成三类：
  - 安全自动修改
  - 建议型修改
  - 需要人工确认的修改
- AI 评分绑定真实修改量和未解决问题数量。
- 报告明确区分：
  - 格式修改贡献
  - 内容修改贡献
  - AI实际改写句子
  - 未自动处理问题
- 在线预览中展示修改前后对照。
- 最终目标是让 Agent 不仅“排版正确”，还能够实质性提升论文语言、逻辑和学术表达质量。

# Day15-P0 Production Hardening

- 全 API 增加进程内基础限流；`/health` 和 `/ready` 豁免，生产仍必须在 reverse proxy/WAF 配置分布式限流。
- `pending` 与 `running` 任务按 user 和 tenant 实施并发上限，默认分别为 2 和 4；现有 quota 行锁用于 PostgreSQL admission check 的事务协调。
- DOCX 上传增加请求体上限、分块 SHA-256、压缩比、重复 ZIP 条目、危险路径/符号链接和文件名长度保护。
- 生产数据库由 Alembic 管理，应用强制 `AUTO_CREATE_DB=false`；连接池和请求异常 rollback 有显式配置。
- 备份/恢复入口包括 PostgreSQL dump 完整性验证、五类 Docker 文件卷归档/恢复和隔离环境 smoke rehearsal。
- `scripts/production_smoke_test.py` 覆盖 health/readiness、登录、分类、local Agent、usage、预览和下载，并校验 local `ai_score=null`、`ai_used=false`。

# Day16-P0 Production Release Closure

- 当前 `main` 与 `origin/main` 的 HEAD 均为 `3bce4e0`；Day13-Day15 变更仍在未提交工作树，release 前必须统一审阅并 commit。
- 生产 Compose release version 通过 `PAPERFORGE_RELEASE_VERSION` 标记 backend/frontend/postgres；Alembic production head 为 `0011_day13_usage_quota`。
- Task Detail 支持 verification summary、认证 artifact download、DOCX preview、failed/interrupted 说明和 retry；旧任务缺少新 result metadata 时安全降级。
- 分类上传临时文件会在请求结束删除；`scripts/cleanup_orphan_files.py` 默认 dry-run，`--apply` 才执行删除，且保护 Task/Artifact 引用文件。保留期由 `PAPERFORGE_RETENTION_DAYS` 配置。
- `deploy/nginx/paperforge.conf` 仅提供可复现 public-edge 配置，不代表已经部署；真实 TLS、registry、备份恢复、WAF 和生产 smoke 仍待目标环境验收。
