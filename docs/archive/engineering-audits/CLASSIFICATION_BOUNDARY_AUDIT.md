# Classification Boundary Audit: generated reports_*

生成日期：2026-06-07

## 审计范围

本轮只分析 `generated_manifest.csv` 中 3 个分类失败样本：

- `reports_001`
- `reports_002`
- `reports_003`

本轮未修改：

- formatter
- agent
- frontend
- API
- document classifier

## 结论

这 3 个样本不是阻断级问题。

推荐处理方式：**C. 标记为边界样本，不计入阻断级 FAIL**。

当前测试规则已按该建议执行：`generated_manifest.csv` 中 3 个 `reports_*` 样本通过 `known_risks=non_paper_confirmation;classification_boundary` 标记，`run_real_doc_regression.py` 将其统计为 `BOUNDARY_WARNING`，不计入 blocking FAIL。

理由：

- 3 个样本的 Agent 主链路均成功：格式处理、报告、预览、下载都通过。
- local 模式字段正确：`ai_score=null`、`ai_used=false`。
- 失败点只在分类预期：manifest 预期为 `lab_report`，实际分类为 `academic_paper`。
- DOCX 内容本身是“报告意图 + 论文结构”的混合样本，只有一个强实验报告特征 `实验目的`，但有多个论文式结构特征。
- 直接增强分类器去把这类样本强判为 `lab_report`，可能会让真实论文中出现“实验目的”的章节被误判为实验报告。

可选后续：

- 若目标是让回归全绿，可把这 3 个样本在 manifest 中改为 `academic_paper|lab_report`。
- 若目标是测试严格实验报告分类，应新增更像真实实验报告的样本，而不是用当前 hybrid 样本强推分类器修改。

## 失败样本汇总

数据来源：

- `regression_results/real_doc_report_generated_20260607/summary.csv`
- 当前分类器 `classify_document(...)`
- DOCX 解析结果

| Case | 文件名 | Manifest 预期 | 实际分类 | 置信度 | 分类理由 | 回归状态 |
| --- | --- | --- | --- | ---: | --- | --- |
| `reports_001` | `generated/reports/reports_001.docx` | `lab_report` | `academic_paper` | 0.70 | `标题编号结构`、`正文段落数量较多` | FAIL |
| `reports_002` | `generated/reports/reports_002.docx` | `lab_report` | `academic_paper` | 0.70 | `标题编号结构`、`正文段落数量较多` | FAIL |
| `reports_003` | `generated/reports/reports_003.docx` | `lab_report` | `academic_paper` | 0.70 | `标题编号结构`、`正文段落数量较多` | FAIL |

回归错误均为：

```text
classification expected lab_report, got academic_paper
```

## DOCX 内容解析

### reports_001

基础结构：

- 文件：`test_documents/generated/reports/reports_001.docx`
- 段落数：26
- 表格数：0
- 文件大小：37164 bytes

分类特征：

- Academic features：`标题编号结构`、`正文段落数量较多`
- Lab report features：`实验目的`
- Heading-like paragraph count：3

前部内容摘要：

```text
Reports Test Thesis 001
作者：测试用户
学院：数据与智能工程学院
专业：信息管理与信息系统
实验目的
本报告用于验证非标准论文文档的分类和确认流程。
1 章节标题
...
1.5 小节标题
...
2.混排标题：第7段围绕性能展开说明...
```

判断：内容明确包含 `实验目的` 和“本报告”字样，但标题使用 `Test Thesis`，并有作者/学院/专业、编号章节、小节标题和大量正文段落。因此当前规则判为 `academic_paper` 是可解释的。

### reports_002

基础结构：

- 文件：`test_documents/generated/reports/reports_002.docx`
- 段落数：26
- 表格数：0
- 文件大小：37170 bytes

分类特征：

- Academic features：`标题编号结构`、`正文段落数量较多`
- Lab report features：`实验目的`
- Heading-like paragraph count：3

前部内容摘要：

```text
Reports Test Thesis 002
作者：测试用户
学院：数据与智能工程学院
专业：信息管理与信息系统
实验目的
本报告用于验证非标准论文文档的分类和确认流程。
1 章节标题
...
1.5 小节标题
...
2.混排标题：第7段围绕规则展开说明...
```

判断：与 `reports_001` 相同，是报告意图与论文结构混合。仅凭一个 `实验目的` 不足以稳定覆盖论文式结构特征。

### reports_003

基础结构：

- 文件：`test_documents/generated/reports/reports_003.docx`
- 段落数：26
- 表格数：0
- 文件大小：37172 bytes

分类特征：

- Academic features：`标题编号结构`、`正文段落数量较多`
- Lab report features：`实验目的`
- Heading-like paragraph count：3

前部内容摘要：

```text
Reports Test Thesis 003
作者：测试用户
学院：数据与智能工程学院
专业：信息管理与信息系统
实验目的
本报告用于验证非标准论文文档的分类和确认流程。
1 章节标题
...
1.5 小节标题
...
2.混排标题：第7段围绕模型展开说明...
```

判断：同样是 hybrid 样本。它更适合作为分类边界样本，而不是严格实验报告样本。

## 为什么会被判为 academic_paper

当前分类器逻辑是：

1. 先计算论文特征。
2. 再计算非论文特征。
3. 如果论文特征数量 `>= 2`，直接判为 `academic_paper`。
4. 只有论文特征不足时，才会根据非论文特征数量判定 `lab_report` 等类型。

这 3 个样本命中的论文特征为：

- `标题编号结构`
- `正文段落数量较多`

命中的实验报告特征只有：

- `实验目的`

因此它们满足 `academic_paper` 的优先判定条件。

## A / B / C 判断

### A. 修改 manifest 预期为 academic_paper|lab_report

适用场景：

- 希望 generated corpus 回归结果全绿。
- 接受这 3 个样本是 hybrid 边界文档。

优点：

- 符合当前样本文本事实。
- 不改业务代码。
- 不会引入分类器误伤风险。

缺点：

- 会降低 `reports` 类别对严格实验报告分类的约束力。

### B. 保持 lab_report，并增强分类器

适用场景：

- 明确产品要求：只要出现 `实验目的`，即使结构像论文，也应优先归为实验报告。

当前不推荐。

原因：

- 这 3 个样本只有一个实验报告强特征。
- 很多真实论文也可能包含 `实验目的`、`实验内容`、`实验结果` 等章节。
- 贸然增强分类器可能让理工科论文被误判为实验报告。
- 本轮用户明确要求不要直接改业务代码。

### C. 标记为边界样本，不计入阻断级 FAIL

当前推荐。

原因：

- 它保留了分类边界信号。
- 不掩盖 `reports` 样本暴露的问题。
- 不把非阻断分类边界误报为主链路阻断。
- 后续可通过测试规则或报告统计区分 `blocking_fail` 与 `boundary_fail`。

## 后续建议

1. 保留这 3 个样本作为 `boundary` 或 `reports_boundary` 场景。
2. 后续若允许修改测试数据，可把 manifest 预期改为 `academic_paper|lab_report`，或增加 `known_risks=classification_boundary`。
3. 另增严格实验报告样本，应至少包含多个实验报告特征：
   - `实验目的`
   - `实验内容`
   - `实验步骤`
   - `实验结果`
   - `实验分析`
   - `实验结论`
   - `实验器材`
4. 后续若要增强分类器，应先设计规则避免误伤理工科论文，例如要求 3 个以上实验报告特征、缺少摘要/关键词/参考文献、表单式结构明显，才判为 `lab_report`。

## 阻断级判断

当前不存在阻断级问题。

这 3 个样本的失败性质为：

```text
classification_boundary_fail
```

不是：

```text
agent_flow_fail
preview_fail
download_fail
report_fail
local_ai_field_fail
```
