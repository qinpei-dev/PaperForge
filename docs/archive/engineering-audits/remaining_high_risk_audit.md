# Remaining High Risk Audit

审计对象：

* `regression_results/real_26_summary_v044.csv`
* `regression_results/real_26_summary_v044.json`
* `v0.4.4_composite_numbering_report.md`
* `test_documents/real/` 下对应真实 DOCX 样本

本轮只做 AI-assisted 初步审计分析，不修改业务代码、formatter、API、测试或 DOCX。

## 总体结论

v0.4.4 已解决章节式图表编号被截断导致的一部分误报。剩余 high_risk 从 v0.4.3 的 15 降至 11，manual_review_required 从 6 降至 5。

剩余 11 个 high_risk 集中在 5 个 DOCX：

* `byau_journal_paper_template.docx`
* `nuaa_undergraduate_thesis_template_2026.docx`
* `sdut_academic_master_thesis_template_2024.docx`
* `sdut_academic_phd_thesis_template.docx`
* `sdut_professional_master_thesis_template_2024.docx`

AI-assisted 初步审计未发现明确真实 high_risk。剩余项主要来自模板示例、双语图表题名、参考文献格式示例和模板说明文字，仍需后续人工抽样确认。

## 剩余 high_risk 总数

| 指标 | 数量 |
| --- | ---: |
| 总样本数 | 16 |
| PASS | 16 |
| FAIL | 0 |
| high_risk | 11 |
| manual_review_required | 5 |
| warning | 18 |
| info | 22 |

## 每类 high_risk 来源

| high_risk 类型 | 次数 | 主要来源 | 初步判断 |
| --- | ---: | --- | --- |
| 参考文献重复编号 | 2 | 参考文献格式示例多次从 `[1]` 开始 | 疑似误报 |
| 正文引用编号未在文末参考文献中找到 | 2 | 模板说明中的 `文献[3]`、`文献[6-10]` 示例 | 疑似误报 |
| 表编号重复 | 1 | 中英文双语表题 `表1/Table 1`、`表2/Table 2` | 疑似误报 |
| 正文引用图号未找到图题 | 4 | 模板说明、附录编号示例、章节/附录编号语义 | 疑似误报 |
| 正文引用表号未找到表题 | 2 | 模板说明中举例引用表号 | 疑似误报 |

## 哪些是真高风险

本轮 AI-assisted 初步审计未发现明确真实 high_risk。

仍应保留为真实 high_risk 的场景：

* 正式论文正文中出现纯重复图号或表号，例如两个不同表都标为 `表2`。
* 正式论文正文引用了不存在的参考文献编号，例如正文引用 `[8]`，文末没有 `[8]`。
* 正式论文正文引用了不存在的图表编号，例如“见表3”，但全文没有 `表3` 或等价复合编号。

当前剩余样本的问题更接近模板语境误报，而不是正式论文正文错误。

## 哪些仍疑似误报

### 参考文献格式示例

涉及样本：

* `byau_journal_paper_template.docx`
* `sdut_academic_phd_thesis_template.docx`

来源判断：

这些模板在正式参考文献示例后追加不同文献类型写法，例如期刊、专著、会议论文、学位论文、标准、专利等。每类示例可能重新从 `[1]` 开始，导致 `duplicate_reference_numbers`。

初步判断：疑似误报，应按模板示例区域降级。

### 模板说明文字中的引用示例

涉及样本：

* `sdut_academic_master_thesis_template_2024.docx`
* `sdut_professional_master_thesis_template_2024.docx`

来源判断：

模板说明段落包含“文献[3]，文献[3,4]，文献[6-10]等”这类规则说明。当前引用检查器把这些说明文字当成正式正文引用，随后发现文末没有对应编号，触发 `missing_reference_numbers`。

初步判断：疑似误报，应识别“格式说明/编号说明/示例说明”上下文。

### 中英文双语图表标题

涉及样本：

* `byau_journal_paper_template.docx`

来源判断：

同一张表同时有中文题名和英文题名，例如 `表1 ...` 与 `Table 1 ...`。当前系统将其识别为两个独立表题，从而触发 `duplicate_tables`。

初步判断：疑似误报，应识别相邻中英文双语题名。

### 附录编号和章节编号语义

涉及样本：

* `sdut_academic_master_thesis_template_2024.docx`
* `sdut_professional_master_thesis_template_2024.docx`
* `sdut_academic_phd_thesis_template.docx`

来源判断：

模板说明中出现 `图A1`、`表B2`、`图1.1`、`表2.3` 等编号示例。v0.4.4 已支持复合编号独立识别，但仍未区分“说明文字中的编号示例”和“正文实际引用”。

初步判断：疑似误报，应结合段落语义降级。

### 模板型图表引用示例

涉及样本：

* `nuaa_undergraduate_thesis_template_2026.docx`

来源判断：

该模板包含大量格式说明、封面授权内容和示例图表。剩余 `missing_referenced_figures` / `missing_referenced_tables` 更接近模板说明或示例引用，而非正式论文正文缺失。

初步判断：疑似误报，应按模板/样例文档上下文降级。

## Top 5 剩余误报原因

| 排名 | 疑似误报原因 | 影响 |
| ---: | --- | --- |
| 1 | 模板说明文字中的引用编号示例被当成正文引用 | 触发参考文献缺失、图表引用缺失 |
| 2 | 参考文献格式示例反复从 `[1]` 开始 | 触发参考文献重复编号 |
| 3 | 中英文双语表题被识别为两张表 | 触发表编号重复 |
| 4 | 附录编号如 `图A1`、`表B2` 未与说明语境区分 | 触发图表引用缺失 |
| 5 | 模板/样例文档缺少“示例区域”识别 | 使模板内容按正式论文正文处理 |

## 是否来自课程报告或表单型文档

本轮剩余 11 个 high_risk 没有集中出现在课程报告或纯表单型文档中。

`ecnu_course_assessment_report_template.docx` 和 `seu_master_defense_meeting_form.docx` 在 v0.4.4 回归中没有 high_risk，说明表单型文档不是当前剩余 high_risk 的主要来源。

## 是否来自真正重复编号或引用不存在

AI-assisted 初步判断：本轮未发现明确属于正式论文正文的真正重复编号或引用不存在。

但这些规则本身仍然有效：

* 正文真实引用不存在的参考文献编号，应保持 high_risk。
* 正文真实引用不存在的图表编号，应保持 high_risk。
* 正文真实图表纯数字编号重复，应保持 high_risk。

后续优化应增加上下文识别，而不是直接降低这些规则的全局风险等级。

## 下一步建议

P1：模板说明/示例区域识别。识别“格式说明”“示例”“编号说明”“参考文献著录格式”等段落，将其中的引用编号和图表编号从正式正文检查中排除或降级。

P2：中英文双语图表题名合并。相邻出现 `表1` 与 `Table 1`、`图1` 与 `Figure 1` 时，应判断为同一图表的双语标题，不作为重复编号。

P3：附录与章节编号语义增强。支持 `图A1`、`表B2`、`图A-1`、`表B-2` 与模板说明语境的区分，避免说明性编号触发 high_risk。
