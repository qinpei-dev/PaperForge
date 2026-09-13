# Real Web Screenshots - 2026-06-27

这组图片来自 2026-06-27 的真实网页运行截图，用于面试、作品集、README 附件和录屏素材整理。它们不是设计稿，也不是占位图。

## 截图清单

| 序号 | 文件 | 内容 | 适合用途 |
| --- | --- | --- | --- |
| 1 | `01_home_overview_real.png` | 首页完整首屏，包含 Hero、能力卡片、静态 dashboard 和上传工作台 | 作品集封面、README 主图 |
| 2 | `02_home_hero_real.png` | Hero 与能力卡片局部 | 项目定位展示 |
| 3 | `03_upload_waiting_real.png` | 等待上传状态 | 说明初始工作台 |
| 4 | `04_running_agent_real.png` | 已选择论文并进入 Agent 执行中 | 录屏运行节点 |
| 5 | `05_agent_steps_summary_real.png` | Agent 执行过程摘要列表 | 展示步骤级处理结果 |
| 6 | `06_result_dashboard_real.png` | 处理结果总览，评分 `81 -> 87` | 展示真实运行结果 |
| 7 | `07_checks_reference_figures_real.png` | 参考文献、图表编号和重复风险检查 | 展示检查模块 |
| 8 | `08_trace_expanded_real.png` | TracePanel 展开，包含 9 个步骤和 task state 摘要 | 展示 Agent 可观测性 |
| 9 | `09_preview_cropped_real.png` | 在线预览局部窄宽截图 | 记录预览裁切/滚动体验待优化点 |
| 10 | `10_preview_download_real.png` | 在线预览与最终 docx 下载入口 | 展示预览和下载闭环 |

## 使用建议

- README 或作品集首图优先使用 `01_home_overview_real.png`。
- 面试讲解主流程可按 `03 -> 04 -> 06 -> 08 -> 10` 的顺序展示。
- `09_preview_cropped_real.png` 建议作为真实 QA 记录保留，不作为最佳宣传图。
- 截图中的评分为本次真实运行结果 `81 -> 87`；历史固定 demo 文档中仍可能写 `80 -> 86`。
- 截图中的“参考文献 0 条文献”和“7 图 / 0 表”来自本次样本文档，不应解释为正式查重或完整内容审校能力。

## 边界说明

- 当前项目仍定位为格式 Agent。
- 不宣传为论文代写工具。
- 不宣传为正式查重系统。
- 重复相关能力仍应表述为“重复风险检测”或“相似度预检”。
- TracePanel 展示的是同步执行过程记录，不代表完整异步队列或断点续跑能力。
