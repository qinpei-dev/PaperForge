# PaperForge

**Verified Academic Document Agent**

PaperForge 是一套面向学术文档的可信智能处理 Agent，围绕 **检测 → 规划 → 执行 → 验证 → 人工确认 → 证据追踪** 构建完整闭环。

它不是简单的论文格式修改工具，而是将 Document Model、Rule Engine、Planner、Executor、Verification、Provenance、Risk Policy、Human-in-the-Loop 和 verified scoring 统一到一条可追踪执行链路中的学术文档 Agent 系统。

> **A Verified Agent System for Academic Document Review & Transformation**

## 核心能力

- Document Model、Rule Engine、Planner 与 Conflict Check。
- Executor 使用 paragraph / section locator 执行局部 DOCX 修改。
- Target-level Verification：重新读取输出 DOCX，比较 before / expected / after。
- Content Review：`AUTO_FIX`、`SUGGEST_ONLY`、`HITL_REQUIRED`。
- Stale Conflict、Confirmed DOCX、Provenance、`review_summary`、`change_evidence`、`pending_actions`。
- Verified Score Update：suggestion 不算 applied，未验证的修改不涨分。
- Local deterministic fallback、AI failure fallback、Legacy compatibility。
- Preview / Download 与可解释 Agent Trace。

## Verified execution loop

```text
DOCX Input
↓
Document Model
↓
Rule Engine
↓
Planner
↓
Conflict Check
↓
Executor
↓
Re-read Output DOCX
↓
Verification
↓
Decision / HITL
↓
Provenance + Evidence
↓
Verified Score Update
↓
Confirmed DOCX / Preview / Download
```

## 安全边界

- suggestion 不算 applied；detected issue 不算 fixed。
- verification failed 不涨分；HITL 未处理不涨分。
- AI 不得绕过 local risk policy，禁止全文替换正文。
- stale suggestion 返回 conflict。
- 高风险实验数据、数字、结论、引用、定义、方法、公式不自动写回。
- 不承诺全自动论文写作、深度论文代写、正式查重系统、工业级多租户 SaaS 或完整异步 Agent 平台。

## V2 第二次大升级验收

- 26 项核心能力 PASS。
- A～F 端到端场景 PASS。
- Safety Audit、Provenance / Verification、Score Credibility PASS。
- Frontend build PASS。
- Real DOCX Regression：10/10 PASS，0 warning，0 blocking FAIL。
- AI failure fallback PASS，Legacy compatibility PASS。

验收基线：`main` / `c0bcc2f80dd46d15df1d1067ef1174cd05e36d4d`（2026-09-08）。当前状态为 **Release Freeze**。

## 技术栈与目录

- Backend：FastAPI、Python、python-docx。
- Frontend：Next.js、React、TypeScript。
- 核心目录仍保留 `paper-ai/`，不因品牌改名而移动，以保持 Docker、脚本和历史路径兼容。

## 快速开始

Backend：

```powershell
cd paper-ai/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend：

```powershell
cd paper-ai/frontend
npm install
npm run dev
```

默认访问：前端 `http://127.0.0.1:3000`，后端健康检查 `http://127.0.0.1:8000/health`。

## 环境变量与 Docker

```powershell
Copy-Item paper-ai/backend/.env.example paper-ai/backend/.env
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
docker compose up --build
```

生产或服务器部署时，在构建前通过 `NEXT_PUBLIC_API_BASE_URL` 指向后端地址；通过后端 `CORS_ORIGINS` 以逗号分隔增加前端 origin。默认 localhost CORS 行为保持不变。完整说明见 [Docker 部署文档](docs/DOCKER_DEPLOYMENT.md)。

配置检查：

```powershell
docker compose config --quiet
```

## 回归测试

```powershell
cd paper-ai/backend
python -m py_compile main.py
python test_p2_content_review_closure.py
python test_p2_closure.py
python test_score_consistency.py
python test_smoke_agent_flow.py

cd ../frontend
npm run build
```

完整 DOCX 回归使用项目内测试资产运行 `run_real_doc_regression.py`；公开 clone 不要求默认携带所有脱敏样本。

## 当前边界

深度语义润色仍有限；复杂目录、脚注、公式、复杂表格、交叉引用、异步恢复、checkpoint/resume 和审批后继续执行尚未完成。最终提交前仍建议人工复核。

## 历史版本

`PaperOps Agent v2.0` 是历史开发阶段代号；`v1.0-showcase` 是上一阶段稳定展示版本。历史文档保留原称以维护记录真实性，当前正式品牌统一为 PaperForge。

## License

MIT License
