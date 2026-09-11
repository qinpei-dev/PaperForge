# AGENTS.md

## 项目级 Agent 规则

本文件是当前项目的项目级规则文件。
每次 Codex / Cursor / Claude Code 在本仓库中执行任务时，都应优先参考本文件。

---

## Repository-Driven Development

PaperForge 从本轮开始采用 **Repository-Driven Development（仓库驱动开发）**。
聊天记录只是临时工作上下文，不是项目长期状态的 Source of Truth。任何 Agent
都必须以仓库事实为准，并在阶段性工作结束时回写仓库。

### Source of Truth

* Source code = 系统实现事实
* `PROJECT_STATUS.md` = 当前项目状态事实
* `TODO.md` = 下一步工作事实
* `docs/PRODUCTION_DEPLOYMENT.md` = 生产部署事实
* Git history = 项目历史事实
* Chat conversation = 临时工作上下文，不是长期 Source of Truth

聊天内容与仓库或运行环境冲突时，先核实真实代码、Git、部署和运行状态，再更新仓库文档。

## Agent 开工规则

任何 Agent 开始较大任务前，必须按以下顺序读取：

1. `AI_CONTEXT.md`
2. `PROJECT_STATUS.md`
3. `TODO.md`
4. 涉及部署/生产时读取 `docs/PRODUCTION_DEPLOYMENT.md`
5. 读取最近 `git log` 和当前 `HEAD` / 工作树状态
6. 读取与当前任务直接相关的设计、安全或 Release 文档

读取完成后，先总结：

1. 当前项目名称
2. 当前项目阶段
3. 当前 P0 任务
4. 当前已知 Bug
5. 当前开发规则

不要直接修改代码。

## Agent 收工规则

阶段性任务完成后，在 commit / push 前必须同步：

* 项目真实状态发生变化 → 更新 `PROJECT_STATUS.md`
* 待办发生变化 → 更新 `TODO.md`
* 部署/生产环境发生变化 → 更新 `docs/PRODUCTION_DEPLOYMENT.md`
* 架构或长期开发规则发生变化 → 更新 `AI_CONTEXT.md` 及必要的治理文档

禁止出现“代码或生产环境已经进入新阶段，但仓库状态文档仍停留在旧阶段”。

仓库中的旧 `ops/acr-build-v3.6` / `acr-build-v3.6.yml` 只保留为历史记录，已废弃，
不得用于当前或未来 PaperForge 生产发布；当前发布必须使用仓库标记的 canonical ACR pipeline。

## Secret Rule

仓库文档只能记录 Secret 名称、用途和是否 required。禁止写入 JWT secret 实际值、
AccessKey、password、token、私钥或任何生产凭据。

---

## 禁止事项

禁止：

1. 大规模重构
2. 删除已有功能
3. 重写已经正常工作的模块
4. 修改无关文件
5. 为了修一个 Bug 改动整个系统
6. 未经确认直接清空或替换核心文件

---

## 必须遵守

每次开发必须遵守：

1. 先分析，再修改
2. 优先最小改动
3. 优先修 Bug
4. 保持现有功能可用
5. 修改后必须回归测试
6. 输出 PASS / FAIL
7. 如项目状态变化，需要更新 PROJECT_STATUS.md 和 TODO.md

---

## 回归测试清单

每次修改后至少检查：

1. 上传论文是否正常
2. 上传模板是否正常
3. local 模式是否正常
4. ai 模式是否正常
5. Agent 是否能运行
6. 在线预览是否正常
7. 下载文件是否正常
8. 文档分类是否正常
9. 修改报告是否正常
10. 启动按钮是否不会永久 disabled

---

## 项目特殊规则

1. local 模式必须满足：

   * ai_score = null
   * ai_used = false

2. ai 模式必须满足：

   * 如果 LLM 调用失败，必须 fallback
   * 不允许因为 AI 失败导致主流程中断
   * 不允许让总评分异常下降

3. 查重相关表述必须使用：

   * 重复风险检测
   * 相似度预检

   禁止宣传为：

   * 知网查重
   * 维普查重
   * 万方查重

4. 当前项目优先级：

   * 先稳定格式 Agent
   * 再建设内容 Agent
   * 最后升级论文修改 Agent

---

## Token 优化规则

优先阅读：

* AGENTS.md
* AI_CONTEXT.md
* PROJECT_STATUS.md
* TODO.md

不要一上来扫描整个仓库。
只读取当前任务相关文件。
避免把无关模块放进上下文。

---

## 当前重点问题

当前优先处理：

1. 标题正文混排
2. C-51 等异常模板残留
3. 参考文献识别不足
4. AI 评分可信度不足
5. 内容级修改能力不足
6. 前端按钮和上传流程稳定性

---

## 工作方式

用户给出任务后：

第一步：分析问题
第二步：列出涉及文件
第三步：给出修复方案
第四步：修改代码
第五步：执行回归测试
第六步：输出 PASS / FAIL
第七步：必要时更新 PROJECT_STATUS.md 和 TODO.md
