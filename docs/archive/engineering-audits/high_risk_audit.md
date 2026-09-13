# High Risk Audit

审计对象：`regression_results/real_16_summary.csv`、`regression_results/real_16_summary.json` 及 `test_documents/real/` 下 16 个真实 DOCX 样本。

审计结论：AI-assisted 初步审计未发现明确真实 high_risk。15 个 high_risk 均被初步判断为疑似误报，仍需后续人工抽样确认。主要疑似误报来源包括模板说明、参考文献示例、章节式图表编号和表单结构。当前 Risk Level 对真实论文正稿仍有价值，但对“模板/样例/表单”上下文过于敏感。

## 总体统计

* 总样本数：16
* high_risk 数：15
* warning 数：18
* info 数：24
* manual_review_required：6
* AI-assisted 初步审计未发现明确真实 high_risk
* 15 个 high_risk 均被初步判断为疑似误报，仍需后续人工抽样确认

## 风险分类统计

| 风险项 | 次数 | 真实风险数 | 误报数 | 误报率 |
| --- | --: | -----: | ---: | ---: |
| 表编号存在重复 | 5 | 0 | 5 | 100% |
| 图编号存在重复 | 3 | 0 | 3 | 100% |
| 正文引用编号未在文末参考文献中找到 | 2 | 0 | 2 | 100% |
| 参考文献存在重复编号 | 2 | 0 | 2 | 100% |
| 正文引用的图号未找到对应图题 | 2 | 0 | 2 | 100% |
| 正文引用的表号未找到对应表题 | 1 | 0 | 1 | 100% |

## Top 风险分析

### 表编号存在重复

触发次数：5

是否真实风险：AI-assisted 初步判断为疑似误报。

典型样本：

* `nuaa_undergraduate_thesis_template_2026.docx`
* `sdut_academic_master_thesis_template_2024.docx`
* `sdut_professional_master_thesis_template_2024.docx`
* `xit_undergraduate_thesis_body_sample_2026.docx`

分析：

这些样本大量使用章节式表编号，例如 `表2.1`、`表2.2`、`表2.3` 或 `表2-1`、`表2-2`、`表2-3`。当前检查器只取第一个数字，导致它们都被折叠为 `表2`，从而误判为重复编号。`byau_journal_paper_template.docx` 还同时出现中文表题和英文 Table 标题，当前规则会把同一张表的中英文题名识别成两次编号。

建议：疑似误报场景降级 warning。真实论文中纯 `表2` 重复仍应保留 high_risk，但章节式编号和中英文双标题应进入模板白名单或解析为复合编号。

### 图编号存在重复

触发次数：3

是否真实风险：AI-assisted 初步判断为疑似误报。

典型样本：

* `nuaa_undergraduate_thesis_template_2026.docx`
* `sdut_academic_master_thesis_template_2024.docx`
* `sdut_professional_master_thesis_template_2024.docx`

分析：

触发原因和表编号类似。样本中实际是 `图3.1`、`图3.2`、`图1.1`、`图1.2`、`图1.3` 这类章节编号，当前检查器只读取首段数字，因此误判为 `图3` 或 `图1` 重复。

建议：降级 warning。后续应优先支持 `图1.1`、`图1-1`、`Fig. 1.1` 这类复合编号。

### 正文引用编号未在文末参考文献中找到

触发次数：2

是否真实风险：AI-assisted 初步判断为模板说明导致的疑似误报。

典型样本：

* `sdut_academic_master_thesis_template_2024.docx`
* `sdut_professional_master_thesis_template_2024.docx`

分析：

触发段落是模板中的格式说明，例如“文献[3]，文献[3,4]，文献[6-10]等”，并不是论文正文实际引用。文末参考文献区域也多为占位示例，所以不能按正式论文缺失引用处理。

建议：模板说明上下文降级 info；真实论文正文中的引用缺失仍保留 high_risk。后续还应支持 `[6-10]` 区间展开，避免把范围引用误读成多个缺失编号。

### 参考文献存在重复编号

触发次数：2

是否真实风险：AI-assisted 初步判断为参考文献示例导致的疑似误报。

典型样本：

* `byau_journal_paper_template.docx`
* `sdut_academic_phd_thesis_template.docx`

分析：

`byau_journal_paper_template.docx` 在正式参考文献后追加了多种参考文献写法示例，这些示例反复从 `[1]` 开始编号。`sdut_academic_phd_thesis_template.docx` 也存在模板示例段落重置编号的情况。对正式论文而言重复编号是高风险，但在“参考文献格式示例”中属于模板内容。

建议：模板/示例区域降级 info；正式参考文献章节内连续条目重复编号仍保留 high_risk。

### 正文引用的图号未找到对应图题

触发次数：2

是否真实风险：AI-assisted 初步判断为说明文字或章节式编号导致的疑似误报。

典型样本：

* `nuaa_undergraduate_thesis_template_2026.docx`
* `sdut_academic_phd_thesis_template.docx`

分析：

一类来自模板说明文字中对图号的举例，另一类来自章节式图号被截断成单数字后与图题匹配失败。当前规则没有区分“正文实际引用”和“模板规则说明”。

建议：降级 warning。模板说明段落应降级 info；真实正文引用缺失仍应保留 high_risk。

### 正文引用的表号未找到对应表题

触发次数：1

是否真实风险：AI-assisted 初步判断为模板说明导致的疑似误报。

典型样本：

* `nuaa_undergraduate_thesis_template_2026.docx`

分析：

该模板包含大量前置声明、授权书、表单表格和格式说明。触发表号更接近规则说明或表单结构，不是正式论文正文引用。

建议：降级 warning；表单型文档或模板说明上下文降级 info。

## 高风险白名单建议

* 模板疑似误报：文档标题或前几段包含“模板”“样例”“格式要求”“撰写规范”“说明”等字样时，参考文献和图表 high_risk 应先降级为 warning 或 info。
* logo 图片疑似误报：封面、页眉、校徽、学院标识等图片不应要求图题，保持 info。
* 表单型表格疑似误报：诚信承诺书、授权书、答辩表决票、封面信息表、签名表、分类号/学号表等 Word 表格不应触发表题 high_risk。
* 模板参考文献缺失疑似误报：参考文献“示例”“写法”“格式说明”区域里重复 `[1]` 或占位引用，应降级 info。
* 章节编号疑似误报：`图1.1`、`图1-1`、`表2.1`、`表2-1`、`Tab. 2.1` 应按复合编号处理，不能只取首位数字判断重复。

## 下一版本建议

P1：支持图表复合编号解析，覆盖 `图1.1`、`图1-1`、`表2.1`、`表2-1`、`Tab. 2.1`，避免章节编号被误判为重复。

P2：新增模板/样例/说明段落上下文降级规则，对模板说明中的参考文献示例和图表编号示例降级为 warning/info。

P3：优化表单型文档识别，对封面表、签名表、授权书、答辩表决票等表格密集结构降低图表题注风险等级。
