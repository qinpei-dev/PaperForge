# Real DOCX Regression Report

生成日期：2026-06-07

版本记录：v0.5.1 / real-doc-regression-boundary-pass

## 结论

本轮真实文档回归测试以 `run_real_doc_regression.py` 为入口，覆盖 `manifest.csv` 与 `generated_manifest.csv` 两组样本。

总体结论：

- `manifest.csv`：10/10 PASS。
- `generated_manifest.csv`：21/24 PASS，3 个 `classification_boundary` warning，0 个 blocking FAIL。
- 指定 smoke：`test_smoke_agent_flow.py` PASS。
- 本轮未修改业务代码，未修改前端。

当前主链路稳定性结论：

- local 模式可正常执行。
- 输出 DOCX 可生成。
- 修改报告可生成。
- 在线预览可生成。
- 下载文件可生成。
- local 模式保持 `ai_score=null`、`ai_used=false`。

当前主要边界：

- `generated_manifest.csv` 中 3 个 `reports_*` 样本预期为 `lab_report`，实际被识别为 `academic_paper`。
- 这说明报告类 / 弱论文结构文档的分类边界仍需后续增强。
- 这 3 个样本的 Agent 主流程、报告、预览、下载均通过，当前按 `boundary_warning` 统计，不计入阻断级 FAIL。

## 回归命令

本轮执行命令：

```powershell
python .\run_real_doc_regression.py --manifest test_documents\manifest.csv --mode local --run-id real_doc_report_manifest_20260607
python .\run_real_doc_regression.py --manifest test_documents\generated_manifest.csv --mode local --run-id real_doc_report_generated_20260607
python .\run_real_doc_regression.py --manifest test_documents\heavy_manifest.csv --mode local
python .\test_smoke_agent_flow.py
```

用户要求的必跑命令已执行：

```powershell
python .\run_real_doc_regression.py --manifest test_documents\manifest.csv --mode local
python .\test_smoke_agent_flow.py
```

原样 `manifest.csv` 命令输出目录：

```text
regression_results/20260607_181919/
```

为满足两份 manifest 汇总，本轮额外执行了 `generated_manifest.csv` 回归。

## 结果汇总

| Manifest | 样本数 | PASS | boundary_warning | blocking FAIL | 结果目录 |
| --- | ---: | ---: | ---: | ---: | --- |
| `test_documents/manifest.csv` | 10 | 10 | 0 | 0 | `regression_results/20260607_185607/` |
| `test_documents/generated_manifest.csv` | 24 | 21 | 3 | 0 | `regression_results/20260607_185623/` |
| `test_documents/heavy_manifest.csv` | 1 | 1 | 0 | 0 | `regression_results/20260607_185651/` |

## manifest.csv 覆盖情况

`manifest.csv` 当前覆盖 10 个样本：

| 分类目录 | 样本数 | 预期文档类型 | 本轮结果 |
| --- | ---: | --- | --- |
| `clean` | 1 | `academic_paper` | PASS |
| `messy` | 2 | `academic_paper` | PASS |
| `references` | 4 | `academic_paper` | PASS |
| `figures_tables` | 2 | `academic_paper` | PASS |
| `template_mismatch` | 1 | `academic_paper|lab_report` | PASS |

本组样本全部为 `small` 文件分桶。

## generated_manifest.csv 覆盖情况

`generated_manifest.csv` 当前覆盖 24 个生成样本：

| 分类目录 | 样本数 | 预期文档类型 | 本轮结果 |
| --- | ---: | --- | --- |
| `clean` | 4 | `academic_paper` | PASS |
| `messy` | 4 | `academic_paper` | PASS |
| `references` | 4 | `academic_paper` | PASS |
| `figures_tables` | 4 | `academic_paper` | PASS |
| `reports` | 3 | `lab_report` | BOUNDARY_WARNING |
| `template_mismatch` | 3 | `academic_paper` | PASS |
| `medium` | 2 | `academic_paper` | PASS |

本组样本全部为 `small` 文件分桶。`medium` 是生成语料场景名，不代表本轮文件大小已进入 `medium` 文件分桶。

## Heavy DOCX Stress Regression

本轮已将 30MB-100MB 大文件压力样本纳入真实文档回归体系。

接入状态：

- 源文件存在：`D:\新下载\realistic_heavy_thesis.docx`
- 已复制到：`test_documents/real/realistic_heavy_thesis.docx`
- 新增 manifest：`test_documents/heavy_manifest.csv`
- case_id：`heavy_001`
- expected type：`academic_paper`
- known_risks：`heavy;stress;large_docx`

回归命令：

```powershell
python .\run_real_doc_regression.py --manifest test_documents\heavy_manifest.csv --mode local
```

回归结果：

| 项目 | 结果 |
| --- | --- |
| 样本数 | 1 |
| PASS | 1 |
| boundary_warning | 0 |
| blocking FAIL | 0 |
| 耗时 | 57.558s |
| 分类结果 | `academic_paper` |
| 修改前评分 | 81 |
| 修改后评分 | 84 |
| 输出 DOCX | 已生成 |
| 修改报告 | 已生成 |
| 在线预览 | 已生成 |
| 下载文件 | 已生成 |
| local `ai_used` | `false` |
| local `ai_score` | `null` |
| 超时 / 内存异常 | 未发现 |
| 文件体积异常 | 未发现 |

文件结构审计：

| 文件 | 大小 bytes | 段落数 | 表格数 | 图片数 |
| --- | ---: | ---: | ---: | ---: |
| source `realistic_heavy_thesis.docx` | 78,427,713 | 2489 | 80 | 100 |
| output `realistic_heavy_thesis_formatted_20260607185716.docx` | 78,429,007 | 2489 | 80 | 100 |

结论：heavy DOCX 已成功接入本地真实文档回归体系，当前 local 主链路在该 74.79MB 样本上 PASS。

## Boundary Warning 明细

| Case | 预期类型 | 实际类型 | Warning 原因 | 主链路状态 |
| --- | --- | --- | --- | --- |
| `reports_001` | `lab_report` | `academic_paper` | 分类结果不一致 | Agent / 报告 / 预览 / 下载均通过 |
| `reports_002` | `lab_report` | `academic_paper` | 分类结果不一致 | Agent / 报告 / 预览 / 下载均通过 |
| `reports_003` | `lab_report` | `academic_paper` | 分类结果不一致 | Agent / 报告 / 预览 / 下载均通过 |

该 warning 不属于前端、下载、预览、格式处理或 local AI 字段异常；它暴露的是分类器对报告类样本的边界判断仍偏宽。

这不是放宽主链路质量，而是把“分类边界”与“功能失败”拆开统计：

- `blocking FAIL`：处理崩溃、输出文件缺失、报告缺失、预览失败、下载失败、local AI 字段异常等。
- `boundary_warning`：已标记的可解释分类边界，例如 `lab_report` 与 `academic_paper` 之间的混合结构样本。

## 已覆盖文档类型与场景

当前测试体系已经覆盖：

- `academic_paper`：标准论文、弱格式论文、参考文献样本、图表编号样本、模板错配样本。
- `lab_report`：报告类样本作为预期分类存在，当前生成样本中暴露了分类边界 FAIL。
- `template_mismatch`：论文 / 报告结构与模板不匹配场景。
- `references`：参考文献编号跳号、重复编号、正文引用缺失、文末未引用等场景。
- `figures_tables`：图题、表题、图表编号跳号、重复编号等场景。
- `messy`：标题正文混排、字体/段落结构混乱、模板残留等场景。
- `clean`：标准论文结构与主链路健康检查。

## 测试体系边界

本测试体系目前不包含受限 CNKI 正文全文。

允许使用：

- 公开可下载的 DOCX 模板。
- 公开投稿须知、投稿模板、格式说明。
- 用户已授权使用的 DOCX。
- 完成脱敏的真实论文或报告。

不允许使用：

- 需要登录、付费、验证码或授权受限的 CNKI 正文全文。
- 未授权下载的 CAJ、PDF、DOCX 或镜像副本。
- 含姓名、学号、电话、邮箱、导师、签名、二维码、学校内部编号等敏感信息的原始文件。

产品表述继续使用：

- `重复风险检测`
- `相似度预检`

不得宣传为：

- 知网查重
- 维普查重
- 万方查重

## 后续如何加入真实样本

新增真实样本流程：

1. 获取合法、公开或已授权的 `.docx` 文件。
2. 如文件包含真实个人信息，先完成脱敏。
3. 将 `.docx` 放入：

```text
paper-ai/backend/test_documents/real/
```

4. 在 `paper-ai/backend/test_documents/manifest.csv` 增加一行，例如：

```csv
real_001,real/real_001.docx,real,academic_paper,,true,true,true,true,true,true,gbt7714_reference_format,公开或已授权真实论文样本；已脱敏
```

5. 运行回归：

```powershell
cd paper-ai\backend
python .\run_real_doc_regression.py --manifest test_documents\manifest.csv --mode local
```

6. 检查输出：

```text
paper-ai/backend/regression_results/<run_id>/summary.csv
paper-ai/backend/regression_results/<run_id>/summary.json
paper-ai/backend/regression_results/<run_id>/cases/<case_id>.json
```

## 后续建议

1. 将 `reports_*` 分类边界作为后续 P1 测试项：报告类样本不应被过度识别为标准论文。
2. 将真实 DOCX 样本按文件大小补齐：
   - `small`：小于 1MB。
   - `medium`：1-10MB。
   - `large`：大于等于 10MB。
3. 补充真实 GB/T 7714 参考文献格式样本，用于验证 `reference_check`。
4. 补充公开期刊投稿模板样本，用于验证模板错配和标题层级。
5. 继续保持受限 CNKI 正文全文不入库。

## 本轮 PASS / FAIL

| 检查项 | 结果 |
| --- | --- |
| `manifest.csv` local 回归 | PASS |
| `generated_manifest.csv` local 回归 | PASS with boundary warnings：21/24 PASS，3 个分类边界 warning，0 blocking FAIL |
| `heavy_manifest.csv` local 回归 | PASS：1/1 PASS，0 blocking FAIL |
| `test_smoke_agent_flow.py` | PASS |
| 业务代码修改 | PASS：未修改 |
| 前端修改 | PASS：未修改 |

最终结论：PASS with boundary warnings。

原因：`generated_manifest.csv` 中 3 个报告类样本分类结果与预期不一致，但这些样本已根据 `CLASSIFICATION_BOUNDARY_AUDIT.md` 标记为 `classification_boundary`；主链路与用户指定命令均通过，blocking FAIL 为 0。
