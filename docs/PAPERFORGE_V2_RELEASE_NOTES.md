# PaperForge V2 Release Notes

发布日期：2026-09-08  
验收基线：`main` / `c0bcc2f80dd46d15df1d1067ef1174cd05e36d4d`  
状态：**READY / Release Freeze**

## 1. 正式品牌

正式名称：**PaperForge**  
英文副标题：**Verified Academic Document Agent**  
中文名称：**PaperForge 学术文档可信智能处理 Agent**

定位：**A Verified Agent System for Academic Document Review & Transformation**。

PaperForge 面向学术文档，围绕检测、规划、执行、验证、人工确认与证据追踪构建可解释的执行闭环。

## 2. V2 核心架构

`DOCX → Document Model → Rule Engine → Planner → Conflict Check → Executor → Re-read Output DOCX → Verification → Decision / HITL → Provenance + Evidence → Verified Score Update`。

核心组件包括 Document Model、Rule Engine、Planner、Executor、Verification、Provenance、Risk Policy 和 Human-in-the-Loop。

## 3. 第二次大升级解决的问题

- 格式修改从规则级结果推进到 paragraph / section locator 与 target-level verification。
- 内容审查建立段落级 issue model 和 `AUTO_FIX` / `SUGGEST_ONLY` / `HITL_REQUIRED` 策略。
- suggestion 仅在用户确认后写入；确认版 DOCX 会被重新读取并验证。
- stale suggestion 会被识别为 conflict，避免覆盖用户后续修改。
- Runtime、API、报告和前端统一暴露 `review_summary`、`change_evidence`、`pending_actions`。
- 评分改善只来自 verified auto fix 或 verified user acceptance。

## 4. 26 项能力矩阵

V2 验收矩阵共 26 项，全部 PASS：

1. 文档输入与分类；2. Document Model；3. Rule Engine；4. Planner；5. Conflict Check；
6. 稳定 execution ordering；7. paragraph locator；8. section locator；9. 局部格式执行；
10. 输出 DOCX 重读；11. target-level verification；12. unsupported 保护；13. provenance；
14. evidence aggregation；15. content issue model；16. AUTO_FIX；17. SUGGEST_ONLY；
18. HITL_REQUIRED；19. stale conflict；20. suggestion confirmation；21. confirmed DOCX；
22. review_summary；23. change_evidence；24. pending_actions；25. verified score update；
26. Local deterministic fallback / Legacy compatibility。

## 5. 安全与可信执行

- suggestion 不算 applied，detected issue 不算 fixed。
- verification failed 或 HITL 未处理不涨分。
- AI 不得绕过 local risk policy，禁止全文替换正文。
- 高风险实验数据、数字、结论、引用、定义、方法和公式不自动写回。

## 6. 验收结果

- A～F 端到端场景：PASS。
- Safety Audit：PASS。
- Provenance / Verification：PASS。
- Score Credibility：PASS。
- Frontend build：PASS。
- Real DOCX Regression：10/10 PASS。
- AI failure fallback：PASS。
- Legacy compatibility：PASS。
- warning：0；blocking FAIL：0。

## 7. 当前边界

深度语义润色仍有限；复杂目录、脚注、公式、复杂表格、交叉引用、异步恢复、checkpoint/resume 和审批后继续执行尚未完成。PaperForge 不是全自动论文写作工具、深度论文代写工具、正式查重系统或工业级多租户 SaaS。

## 8. Release Freeze

PaperForge V2 核心开发已经完成。当前进入 Release Freeze，不继续扩展 P3。后续仅允许封版文档、品牌包装、部署稳定性和 blocking regression 修复。

`PaperOps Agent v2.0` 作为历史开发阶段代号保留；`v1.0-showcase` 作为历史展示版本保留，不移动、删除或重建旧 tag。
