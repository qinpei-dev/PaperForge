# PaperForge 项目历史事件（PROJECT_HISTORY）

> 用途：按时间顺序记录真实发生过的重要事件，供复盘、介绍、内容引用。
> 每条事件至少包含：日期、事件、证据来源、当前状态、是否适合对外宣传。
> 分类说明：产品开发 / Bug / 发布 / 部署 / 安全 / 测试 / 产品能力变化 属于 PaperForge 产品核心历史；"对外内容事件/Marketing"为营销运营行为，与产品技术事件分列，不混入版本发布、生产部署等技术事件。
> 规则：只收可查证事件；聊天口述事件必须标注"来源：用户一手确认"，不得伪装成 Git/代码证据。
> 最后核验日期：2026-09-12（依据 `git log` 111 条提交、全部 tag、PROJECT_STATUS.md、docs/PRODUCTION_DEPLOYMENT.md；本次新增"分类"列）

---

## 时间线

| 日期 | 分类 | 事件 | 证据来源 | 当前状态 | 是否适合对外宣传 |
|---|---|---|---|---|---|
| 2026-05-30 | 产品开发 | v0.2 格式核心通过（format core pass） | tag `v0.2-format-core-pass`（edb9970） | 已完成 | 受限：早期能力，已被后续版本取代，一般不单独讲 |
| 2026-05-31 | 产品开发 | v0.3.1–v0.3.4：格式差异报告、在线预览优化、参考文献检查、图表编号检查 | tags `v0.3.1`~`v0.3.4` | 已完成 | 是：核心功能清单 |
| 2026-06-01 | 产品开发 | v0.3.5–v0.4.1：真实论文测试语料结构、Agent Orchestrator Trace、风险等级系统、评分语义细化、beta 文档 | tags（v0.3.5~v0.4.1） | 已完成 | 是：工程化能力 |
| 2026-06-02 | 产品开发/测试 | v0.4.2–v0.4.5：16 份真实文档回归结果、高风险审计、复合图表编号支持 | tags（v0.4.2~v0.4.5） | 已完成 | 是：质量事实 |
| 2026-06-03 | 产品开发/测试 | v0.4.6–v0.4.7.1：重复风险检测超时保护；74.79MB/267 页 heavy DOCX 压力回归 PASS（local Agent 约 510.88s 完成，预览/下载/AI fallback 均通过） | tag `v0.4.6-repeat-risk-performance-guard`、`v0.4.7.1` + PROJECT_STATUS | 已完成 | 是：性能/压力事实（数字可引用，须注明为当时基线） |
| 2026-06-04 | 产品开发/性能优化 | v0.4.9：重复风险检测性能优化（377.9s→35.7s）；heavy 全链路 510.88s→51.21s | tag `v0.4.9-repeat-risk-performance-optimization` + PROJECT_STATUS | 已完成 | 是：性能优化事实 |
| 2026-06-07~08 | 测试/beta准备 | v0.5.1–v0.5.3：heavy 回归通过、beta readiness 审计（10/10 + 21 PASS + 3 boundary + 0 FAIL）、受控试用准备 | tags（v0.5.1~v0.5.3）+ docs/archive | 已完成 | 受限：内部过程，对外一般不细讲 |
| 2026-06-09 | Bug修复 | 封面页保护与模板指令过滤修复 | commit `ecc871f` | 已完成 | 是：质量事实 |
| 2026-06-14~18 | 产品开发 | v0.6.x–v0.7.x：demo 样本体系、任务状态最小化落盘 | tags（v0.6.1~v0.7.3） | 已完成 | 受限 |
| 2026-06-24~27 | 产品开发/UI | v0.8.x–v0.9.4：UI 布局打磨、运行流修复、fetch 兼容修复、截图素材指南；2026-06-27 归档 10 张真实网页截图 | tags（v0.8.4~v0.9.4）+ commit e169bfb | 已完成 | 是：截图素材存在（**早期界面 v0.9.x，引用须标注**） |
| 2026-07-01 | 版本发布 | v1.0-showcase 稳定展示版封版 | tag `v1.0-showcase`（10904db） | 已完成 | 是：历史稳定基线 |
| 2026-07-04 | 文档/对外 | 公开 README 与仓库展示准备、历史版本文档归档 | commits（76c719b/d890c4b 等） | 已完成 | 受限 |
| 2026-07-18 | 部署/产品能力 | 增加 Docker Compose 部署支持 | commit `f6ed7e5` | 已完成 | 是：部署能力 |
| 2026-08-04 | 安全/Bug修复 | 上传文档文件隔离修复 | commit `9c172c7` | 已完成 | 是：安全质量事实 |
| 2026-09-08 | 测试/验收 | **PaperForge V2 最终验收 READY**：26 项核心能力 PASS、A~F 端到端 PASS、真实 DOCX 回归 10/10、Safety Audit/Provenance/Score Credibility/Frontend build 均 PASS；项目更名 PaperForge（Verified Academic Document Agent） | tag `v2.0-paperforge`（966dc02）、验收基线 c0bcc2f、PROJECT_STATUS | 已完成 | 是：重要工程验收事实 |
| 2026-09-09 | 产品能力变化/架构 | 转型多租户 SaaS：v3.0 trace 驱动任务流、v3.1 agent runtime、v3.2 异步任务 worker；品牌资产建立 | commits（6aa4205/dde2712/d1a2337/7ee59bc）+ tags v3.0~v3.2 | 已完成 | 是：架构升级 |
| 2026-09-10 | 产品能力变化/安全 | 租户体系与模板平台：v3.3 SSE 实时任务、v3.4 AI Intelligence、v3.5 Template Intelligence、v3.6/v3.6.1 模板平台+生产认证 hotfix、v3.7/v3.7.1 多租户 SaaS；同日完成租户隔离/RBAC/成员治理/模板管理/路径穿越修复 | commits（88c8770~a459155）+ tags | 已完成 | 是：核心 SaaS 能力 |
| 2026-09-11 | 安全/产品能力 | 受控 beta 准备与加固：v3.7.2 controlled beta；token 撤销与边缘安全加固；可观测性（request ID/结构化日志）；durable task 生命周期；Landing 页产品化 | commits（425dc99~367356b）+ tag v3.7.2 | 已完成 | 是 |
| 2026-09-12 | 发布/部署 | **生产发布 v3.7.3→v3.7.5**：ACR immutable images 构建推送、ECS 部署、migration 0013、health/ready/首页 200；受控 beta 反馈入口与控制台上线；feedback ORM 映射修复；管理员白名单；DeepSeek AI provider 安全验证（生产容器 smoke：language_mode_ai=true、ai_used=true）；生产 E2E 与最终程序化审计 PASS | commits（729fe2f~245bb0c）+ PROJECT_STATUS + docs/PRODUCTION_DEPLOYMENT.md | 已完成 | 是：**核心宣传事实** |
| 2026-09-12 | 对外内容事件/Marketing | 营销首条发布：小红书 GkeAI《5个Prompt让ChatGPT效率翻倍》21:54 发布（初始获赞与收藏 3） | 营销项目记录（D:\豆包宣传\PUBLISH_LOG.md / 运营数据记录.csv） | 已完成 | 是：营销事件，数据为初始值（**非产品技术事件，与上方发布/部署分列**） |
| 日期未记录（来源：用户一手确认） | Bug（发现） | 用户实际查看 PaperForge 前端页面时发现：主体内容向下滚动时，左侧 Sidebar 不合理移动，Sidebar 下方出现明显空白，判断为实际 UI Bug | 来源：用户一手确认；代码佐证：`AppShell.tsx` 的 `<aside class="app-sidebar">` + `globals.css` 的 `position: sticky; top:0; height:100vh` 布局；**git log 无任何该问题修复提交** | 待确认：要求 Codex 检查中，仓库无修复记录 | 受限：可作"真实验收发现 Bug"的真实事件表述（见 CONTENT_EVIDENCE E002），**不得写"已修复"** |
| 日期未记录（来源：用户一手确认） | Bug（待定性） | 用户发现页面第一张视觉图片/展示框疑似倾斜，要求进一步确认是设计效果还是视觉问题 | 来源：用户一手确认；旧版 CSS 中 `.product-preview` 在移动端被 `transform:none` 复位，佐证桌面端曾带倾斜 transform（设计效果可能） | 待定性：设计还是问题未确认 | 受限：可写"需要判断是设计效果还是问题"，**不得下结论** |
| 日期未记录（来源：用户一手确认） | 内部过程 | 用户要求 Codex 对上述问题继续检查，并排查其他潜在 Bug/漏洞 | 来源：用户一手确认 | 进行中：无提交记录 | 否：内部过程，无已确认产出事实 |

---

## 统计口径

- 已收录事件：**23 条**（20 条产品技术/文档事件 + 1 条对外内容事件/Marketing + 2 条用户一手确认 Bug 事件 + 1 条用户一手确认内部过程项 = 23）
- 产品核心历史分类（技术事件）：产品开发、Bug、发布、部署、安全、测试、产品能力变化
- 对外内容事件/Marketing：独立分类，不与版本发布、生产部署等技术事件混为一类
- 全部事件依据：git log（111 commits）/ tags（56 个）/ PROJECT_STATUS / 生产部署文档 / 营销项目记录 / 用户一手确认（明确标注）
