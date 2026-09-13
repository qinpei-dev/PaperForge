# PaperForge Day15-P0 Production Hardening 验收报告

日期：2026-09-11  
项目：PaperForge / Verified Academic Document Agent  
结论：**PASS（可进入受控生产发布检查；真实生产环境仍需执行现场恢复和边缘防护验证）**

## 1. 验收范围

本轮只处理生产可测试性和运行保护，不新增支付、会员、复杂权限或 AI 功能。既有 JWT、tenant isolation、quota、admin dashboard、Day11 durable task lifecycle 和 Agent 主流程保持兼容。

## 2. 需求验收矩阵

| 需求 | 实现 | 验收结果 |
|---|---|---|
| API 基础限流 | 全 API 进程内滑动窗口限流；`/health`、`/ready` 豁免；可由 `API_RATE_LIMIT_PER_MINUTE` 配置 | PASS；专项测试验证超限 `429` 和 `Retry-After` |
| 用户/租户任务并发 | `pending`、`running` 按 user/tenant 统计；默认 `2/4`；超限返回 `TASK_CONCURRENCY_LIMIT` | PASS；专项测试覆盖 user 和 tenant 两个边界 |
| 上传资源保护 | 请求体上限、分块哈希、DOCX ZIP 条目/展开量/压缩比/重复条目/危险路径/符号链接/文件名校验；DB/解析失败清理临时文件 | PASS；专项测试覆盖请求体、重复条目和高压缩比 |
| 数据库连接与事务 | PostgreSQL `pool_pre_ping`、pool size/overflow/timeout/recycle；请求异常 rollback；生产强制 `AUTO_CREATE_DB=false` | PASS；连接/rollback 测试与生产 Compose wiring 检查通过 |
| 备份恢复 | PostgreSQL dump、dump 完整性验证、uploads/outputs/template-storage/task-states/templates 五类文件卷备份恢复脚本；隔离恢复 runbook | PASS（脚本/流程验证）；真实生产 DB restore NOT RUN |
| production smoke test | 新增黑盒脚本，验证 health/readiness、登录、分类、local Agent、usage、预览、下载和 local AI 字段契约 | PASS；临时全新数据库 + Alembic head 的独立 Agent smoke PASS |

## 3. 测试证据

- `pytest -q test_day15_production_hardening.py`：**6 passed**。
- `pytest -q`：**98 passed**，无 blocking FAIL。
- `python -m py_compile main.py services/concurrency.py services/rate_limit.py db/session.py scripts/production_smoke_test.py`：PASS。
- 临时 SQLite 数据库执行 Alembic `0001 → 0011`：PASS。
- `python test_smoke_agent_flow.py`（隔离迁移数据库）：PASS；local `ai_score=null`、`ai_used=false`，AI 故障 fallback PASS，预览/下载 PASS。
- `docker compose --env-file .env.production.example -f docker-compose.prod.yml config --quiet`：PASS。
- frontend `npm run build`：PASS；包括 `/admin`、`/dashboard`、上传主页面等路由。
- 5 个 PowerShell 脚本语法解析：PASS。
- `git diff --check`：PASS。

## 4. 默认生产保护参数

- `API_RATE_LIMIT_PER_MINUTE=600`（单进程基础保护，边缘仍需分布式限流）。
- `MAX_ACTIVE_TASKS_PER_USER=2`。
- `MAX_ACTIVE_TASKS_PER_TENANT=4`。
- `MAX_REQUEST_BODY_BYTES=251658240`。
- `MAX_UPLOAD_BYTES=100MB`；DOCX 展开总量 `300MB`；ZIP 条目 `5000`；压缩比 `200`；文件名 `320` 字符。
- PostgreSQL pool：size `5`、overflow `10`、timeout `30s`、recycle `1800s`。

## 5. 生产操作前置条件

1. 使用不可变 backend/frontend image，并在目标生产环境设置真实 JWT、数据库密码、CORS、域名和备份目的地。
2. 先执行 `alembic upgrade head`，确认 `AUTO_CREATE_DB=false`，再启动 backend。
3. 迁移前执行 PostgreSQL backup，并用 `verify_postgres_backup.ps1` 检查 dump；同时归档五类文件卷。
4. 在隔离环境恢复 DB 和文件卷，运行 `production_smoke_test.py`；确认成功后才安排生产窗口。
5. 公网入口必须补 TLS、WAF/reverse proxy、分布式限流、请求体上限、访问日志和外部告警。

## 6. 未执行项与已知边界

- 未执行真实公网部署、真实 production PostgreSQL restore、真实 Docker volume restore、WAF/DDoS 压测和独立渗透测试。
- 应用内限流是单进程保护，不替代多副本共享限流。
- TaskWorker 仍是轻量进程内 worker；backend 重启时沿用 Day11 语义，将遗留任务标记为 `interrupted`，不伪造自动恢复。
- 项目内旧 `paperforge.db` 若未执行 Alembic 可能缺少新 schema；生产必须迁移后启动。
