# Demo Screenshot Guide

版本：`v1.0-showcase / 暑期实习展示版`

本文档用于整理面试、简历、作品集和演示时可使用的截图/录屏素材清单。当前稳定演示基线是 tag `v1.0-showcase`，指向 commit `10904db`。`main` 分支包含该 tag 之后的公开前文档和面试材料补充，不代表 `v1.0-showcase` tag 已移动。`v0.9.4-demo-screenshot-package` 是上一阶段截图包 tag。

## 已归档真实截图

2026-06-27 已补充一组真实网页运行截图，目录为：

```text
docs/archive/screenshots/
```

这组截图来自浏览器真实页面，不是设计稿或占位图。当前共 10 张，覆盖首页、上传工作台、运行中状态、结果 dashboard、检查模块、TracePanel、在线预览和下载入口。

说明：这些截图仍可作为 v1.0-showcase 的展示素材。若后续重新截图，应保持同一演示口径：`v1.0-showcase` 是稳定展示 tag，`main` 是 tag 之后的公开前文档补充，`v0.9.4-demo-screenshot-package` 仅作为上一阶段截图包 tag 保留。

| 文件 | 内容 | 备注 |
| --- | --- | --- |
| `01_home_overview_real.png` | 首页完整首屏 | 可作为 README / 作品集主图 |
| `02_home_hero_real.png` | Hero 与能力卡片局部 | 用于项目定位展示 |
| `03_upload_waiting_real.png` | 等待上传状态 | 展示初始工作台 |
| `04_running_agent_real.png` | 已选择论文并进入运行中 | 展示同步执行入口 |
| `05_agent_steps_summary_real.png` | Agent 执行过程摘要列表 | 展示步骤级处理结果 |
| `06_result_dashboard_real.png` | 结果 dashboard | 本次真实运行评分为 `81 -> 87` |
| `07_checks_reference_figures_real.png` | 参考文献、图表编号和重复风险检查 | 展示检查模块 |
| `08_trace_expanded_real.png` | TracePanel 展开 | 9 个步骤、task_id 和 task_state_path 摘要 |
| `09_preview_cropped_real.png` | 在线预览局部窄宽截图 | 作为 QA 记录，显示预览阅读体验仍可优化 |
| `10_preview_download_real.png` | 在线预览与最终 docx 下载入口 | 展示预览和下载闭环 |

说明：历史固定 demo 输出样例为 `80 -> 86`，本次真实网页截图为 `81 -> 87`。二者都可以使用，但在简历、作品集或面试话术中应明确对应截图或样例来源。

## A. 截图清单

| 序号 | 建议文件名 | 截图内容 | 重点展示 |
| --- | --- | --- | --- |
| 1 | `01_home_hero.png` | 首页 Hero 区 | 项目名称、AI 产品页观感、核心能力概览 |
| 2 | `02_upload_workspace.png` | 上传工作台 | 论文上传、模板上传、模式选择和启动入口 |
| 3 | `03_files_selected.png` | 已选择论文和模板 | demo 文件已就绪，适合展示真实操作前状态 |
| 4 | `04_running_agent.png` | 运行中状态 | Agent 正在处理，不需要展示为异步队列 |
| 5 | `05_result_dashboard.png` | 结果 dashboard | 结果总览、评分变化、报告入口和检查模块 |
| 6 | `06_score_delta_80_to_86.png` | before/after 评分 | 固定 demo 示例 `80 -> 86` |
| 7 | `07_report_summary.png` | 修改报告 | 格式修复摘要、修改项、人工复核建议 |
| 8 | `08_reference_figure_table_check.png` | 参考文献与图表检查 | `reference_check` 和 `figure_table_check` 的工程闭环 |
| 9 | `09_trace_collapsed.png` | TracePanel 默认折叠 | 结果页不拥挤，Agent 过程可按需展开 |
| 10 | `10_trace_expanded_9_steps.png` | TracePanel 展开 | 9 步执行流程、耗时、fallback 状态 |
| 11 | `11_preview_html.png` | 在线预览 | 生成 DOCX 后可在页面内预览 |
| 12 | `12_download_docx.png` | 下载入口 | 最终格式化 DOCX 可下载 |
| 13 | `13_mobile_390px.png` | 390px 窄屏适配 | 小屏无横向溢出，长文本可换行 |

## B. 每张截图的用途

- `01_home_hero.png`：适合 README、作品集首页、简历附件封面和答辩 PPT 开场。
- `02_upload_workspace.png`：适合说明主流程入口，放在面试演示或项目作品集。
- `03_files_selected.png`：适合证明 demo 使用固定输入文件，不是空页面展示。
- `04_running_agent.png`：适合录屏中短暂停顿，说明点击后进入同步处理流程。
- `05_result_dashboard.png`：适合 README、作品集和 PPT 中展示产品化结果页。
- `06_score_delta_80_to_86.png`：适合简历附件和面试追问，说明 before/after score 有可观察变化。
- `07_report_summary.png`：适合解释“不是只调模型”，而是生成结构化修改报告。
- `08_reference_figure_table_check.png`：适合展示格式 Agent 的检查能力。
- `09_trace_collapsed.png`：适合说明 TracePanel 默认不打扰主结果阅读。
- `10_trace_expanded_9_steps.png`：适合展示 Agent 可观测性和步骤级执行记录。
- `11_preview_html.png`：适合展示在线预览闭环。
- `12_download_docx.png`：适合展示最终交付物。
- `13_mobile_390px.png`：适合说明页面已做窄屏响应式检查，可用于移动端展示素材。

## C. 60-90 秒录屏脚本

1. 打开前端页面，停留在 Hero 区 5 秒。
   - 话术：这是一个面向高校论文模板的 AI 论文格式审查与自动排版 Agent。
2. 切到上传工作台，上传 demo 论文和 demo 模板。
   - 话术：输入是一篇人工构造的脱敏模拟论文，以及一份模板样本。
3. 选择本地规则模式。
   - 话术：本地模式不调用 AI，`ai_score=null`、`ai_used=false`，更适合稳定演示格式修复能力。
4. 点击启动 Agent，展示运行状态。
   - 话术：当前 `/agent/run` 仍是同步执行，不是异步队列。
5. 展示结果 dashboard 和评分变化。
   - 话术：固定 demo 中评分从 `80` 提升到 `86`。
6. 展示修改报告、参考文献检查和图表检查。
   - 话术：系统输出结构化报告，而不是只返回一段模型文本。
7. 展开 TracePanel。
   - 话术：这里是步骤级执行记录，能看到处理链路、耗时和 fallback 情况；这不是完整工业级调度平台。
8. 打开在线预览，再点击下载入口。
   - 话术：最终产物是格式化后的 DOCX，可以预览和下载。
9. 结尾说明边界。
   - 话术：它不是论文代写工具，也不是正式查重系统，当前重点是格式审查、模板对齐和工程化可观测。

## D. 自动化演示注意事项

- 自动化上传建议使用 ASCII 临时路径，推荐：`C:\Temp\paper-ai-demo\`。
- 可将 `demo_inputs/messy_paper_sample.docx` 和 `demo_inputs/template_sample.docx` 复制到上述临时目录后再用于浏览器自动化上传。
- 这样可以避免中文仓库路径在部分 Chromium/Edge CDP 文件句柄中触发读取异常。
- 前端默认 API base 为 `http://127.0.0.1:8000`。
- 如本地端口或 host 不同，可用 `NEXT_PUBLIC_API_BASE_URL` 覆盖。
- demo 结束后运行 `git status --short`，确认工作区干净。
- 后端模板上传副本和 `task_states/` 运行产物应继续被 `.gitignore` 忽略。
- 如果启动临时前后端服务，录屏或截图结束后要停止服务，避免 3000 / 8000 端口残留。

## E. 截图命名建议

```text
01_home_hero.png
02_upload_workspace.png
03_files_selected.png
04_running_agent.png
05_result_dashboard.png
06_score_delta_80_to_86.png
07_report_summary.png
08_reference_figure_table_check.png
09_trace_collapsed.png
10_trace_expanded_9_steps.png
11_preview_html.png
12_download_docx.png
13_mobile_390px.png
```

如后续补充录屏，可使用：

```text
demo_walkthrough_90s.mp4
demo_mobile_390px_check.mp4
```

## F. 边界提醒

- 不要把项目描述为论文代写工具。
- 不要把重复风险检测 / 相似度预检描述为正式查重。
- 不要声称当前已经是完整工业级 Agent。
- 不要声称当前已经支持异步队列。
- 不要声称当前已经支持完整断点续跑。
- 不要声称前端可以读取 `task_state` 文件内容。
- AI 内容修改能力仍有限，复杂模板、目录、脚注、公式、图片题注等场景仍可能需要人工复核。
- demo 样本是人工构造 / 脱敏模拟材料，不来自真实用户论文，也不来自 CAJ 原文。
- 已归档真实截图可用于展示主链路跑通，但截图中的样本文档特征不应被包装成正式内容审校或正式查重结论。
