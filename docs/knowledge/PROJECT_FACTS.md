# PaperForge 项目事实库（PROJECT_FACTS）

> 用途：记录长期稳定、已确认的项目事实，供小红书/抖音内容、项目介绍、简历、复盘等所有对外表达使用。
> 纪律：不写短期任务、不写猜测、不写"可能"。事实来源优先级与冲突处理规则见 `docs/knowledge/README.md`。
> 最后核验日期：2026-09-12

---

## 1. 项目身份

| 项 | 事实 | 证据来源 |
|---|---|---|
| 项目名称 | PaperForge | 仓库根目录 |
| 英文定位 | Verified Academic Document Agent | README.md |
| 中文定位 | 学术文档可信智能处理 Agent | PROJECT_STATUS.md |
| 产品主张 | 不只是修改论文，而是**验证每一次修改** | Landing 页 / Brand Visual System |
| 品牌视觉 | PaperForge Brand Visual System（Canva 品牌板，含 Logo/字体/色彩/Landing Hero） | PROJECT_STATUS.md / brand/ |
| 公开域名 | https://aetherislab.xyz（2026-09-12 实际抓取验证可访问） | docs/PRODUCTION_DEPLOYMENT.md + 线上抓取 |

## 2. 当前阶段与版本（权威状态 2026-09-12）

- 版本：**v3.7.5**；阶段：**CONTROLLED PUBLIC BETA LIVE**（受控公开 beta）
- release commit：`4ca4bf29a1eee67f05bcdd6c7b5dfd8a0841a018`（frontend/backend 均从此 commit 构建）
- 生产发布方式：canonical ACR run `34678107681` → 阿里云 ECS immutable images 部署
- 历史基线：`v2.0-paperforge` tag（2026-09-08）；`v1.0-showcase` tag（2026-07-01）

## 3. 公开地址

- 前端：https://aetherislab.xyz
- 浏览器 API：https://aetherislab.xyz/api
- 注意：登录后的工作区（含 Sidebar）页面**无公开截图**，线上运行状态无法从仓库单方验证；健康检查结果以部署记录为准。

## 4. 核心功能（已实现）

来源：PROJECT_STATUS.md / README.md / AI_CONTEXT.md

- 文档分类（标准论文/课程作业/实验报告/简历/未知）
- 格式修复（标题、正文样式、字体、行距、缩进、页边距等低风险动作）
- AI 审校（AI 模式 + local 本地规则双模式，AI 不可用时自动 fallback）
- 重复风险预检（"重复风险检测/相似度预检"，非正式查重）
- 在线预览（DOCX → HTML）
- 修改报告（修复项、前后评分、未修复项、人工复查建议）
- 参考文献检查、图表编号检查
- 验证闭环（Plan → Execute → Verify → Evidence，输出重读验证、HITL 人工复核）
- Agent Trace / 任务状态 / provenance 证据链
- 多租户隔离 + RBAC（owner/admin/member）、租户模板管理
- 持久化任务生命周期（durable task）+ SSE 实时事件
- 额度系统（默认每 tenant 每月 100 次 agent_run）
- 管理后台（ADMIN_EMAILS allowlist）、受控 beta 反馈控制台
- Landing 页（产品首页）

## 5. 技术栈

| 层 | 内容 | 证据来源 |
|---|---|---|
| 前端 | Next.js 15.5.24 / React 19.0.0 / TypeScript 5.7.2 | frontend/package.json |
| 后端 | FastAPI 0.115.6 / uvicorn 0.34.0 / python-docx 1.1.2 / markitdown[docx] 0.1.6 / SQLAlchemy 2.0.36 / Alembic 1.14.0 / psycopg[binary] 3.2.3 / PyJWT 2.10.1 / openai 1.59.7 | backend/requirements.txt |
| 数据库 | PostgreSQL（生产） | docker-compose.prod.yml / PROJECT_STATUS |
| 部署 | Docker Compose（PostgreSQL+backend+frontend 三服务）；阿里云 ECS；ACR 镜像仓库（immutable images）；Nginx 公网边缘（HTTPS/SSE） | docs/PRODUCTION_DEPLOYMENT.md |
| AI | DeepSeek API（生产已配置）；本地规则 fallback | PROJECT_STATUS / TODO（AI provider 验证 2026-09-12） |

## 6. 当前主要能力（生产已验证，2026-09-12）

- JWT 认证（含 token_version，可撤销全部旧会话）
- 多租户数据隔离 + RBAC 权限矩阵
- 租户模板上传/管理/版本（DOCX 安全校验）
- 持久化任务 + SSE 事件重放（Last-Event-ID）
- 额度/用量（tenant 维度月度配额）
- 管理员运营后台 + 反馈控制台
- AI 模式真实调用 DeepSeek：生产容器内 smoke 验证 `language_mode_ai=true`、`ai_used=true`、AI score 存在
- 生产探针：`/health`、`/ready`、公开首页均 200
- 2026-09-12 管理员登录、`/admin/stats`、`/admin/feedback` 页面验收 PASS，未认证 401、普通账号 403

## 7. 测试与验收基线（已确认）

- 2026-09-12：后端 `pytest -q` **107 passed**；前端 production `npm run build` **PASS**；`git diff --check` PASS；Python compileall PASS；Alembic head = `0013_beta_feedback`
- V2 最终验收（2026-09-08）：26 项核心能力 PASS、A~F 端到端场景 PASS、真实 DOCX 回归 10/10、Safety Audit PASS
- 压力回归：74.79MB/267 页 heavy DOCX 完整 local Agent PASS（v0.4.7.1 约 510.88s；v0.4.9 优化后 51.21s）
- 性能优化事实：重复风险检测 377.9s → 35.7s（v0.4.9）
- **重要缺失事实：仓库内无前端自动化 UI 测试（无 Playwright/Cypress 记录）**；"P0=0/P1=0"为人工浏览器 sweep 结论

## 8. 已确认的产品边界（宣传不得越界）

- 核心定位是**格式 Agent**：格式修复为主；AI 内容修改偏弱，主要为词语级替换
- **不是**：论文代写/生成工具、正式查重服务（只表述为"重复风险检测/相似度预检"）、深度学术润色、导师/编辑审查替代品
- 复杂 DOCX 结构支持有限：复杂表格、目录域、交叉引用、脚注/尾注、公式、批注、复杂页眉页脚、复杂图片/图表等
- 未实现：断点续跑/checkpoint resume、分布式队列/多副本调度、对象存储、企业 SSO/SCIM、支付/计费
- 已知限制（P1）：localStorage bearer token 的 XSS 暴露面；单进程限流（无 WAF/外部监控）；worker 重启后任务标记 interrupted（不做假恢复）
- 部署边界：ECS 沿用历史 bind mounts 结构；不得未经数据迁移审查直接切换仓库新版 named-volume Compose

## 9. 明确不能夸大的能力（对外宣传红线）

1. 不能宣称"深度润色/内容级改写"——当前 AI 模式主要做词语级替换
2. 不能宣称"全部测试通过/自动化 UI 测试通过"——仓库无前端自动化 UI 测试
3. 不能宣称"检查通过=产品无 Bug"——2026-09-12 存在"基础检查通过后人工验收仍发现 UI 问题"的真实事件（见 CONTENT_EVIDENCE E002）
4. 不能宣称"评分改善=真实内容修改量"——评分与真实修改量未强绑定
5. 不能把演示样本/旧截图描述为当前版本——真实网页截图（2026-06-27）为 v0.9.x 早期界面；测试库与 demo 样本均为脱敏/人工构造
6. 不能把"用户一手确认但未入库"的事伪装成 Git/代码证据——一律标注"来源：用户一手确认"

## 10. 样本与素材性质（对外引用时须说明）

- 测试库：`test_documents/` 10 个脱敏 DOCX；来源仅限公开/已授权，不含登录/付费/验证码受限全文（CNKI 边界见 docs）
- demo 输入输出：人工构造脱敏样本（demo_inputs/ demo_outputs/），不来自真实用户论文
- 真实网页截图：`docs/assets/screenshots/real-web-2026-06-27/` 共 10 张（早期界面，评分 81→87 等为当时数据）
- 营销项目素材：无当前版本产品截图；Sidebar 工作区需登录无公开截图

## 11. 事实维护规则

- 本文件只收长期稳定事实；短期任务、进行中状态、猜测一律不写
- 与当前 Git/代码冲突时：**以当前代码与 Git 为准**，并同步更新本文件
- 重大事实变化后更新"最后核验日期"与对应条目
