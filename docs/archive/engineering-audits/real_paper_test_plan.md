# v0.3.5 Real Paper Stress Test Plan

## 测试目标

建立真实论文测试库和回归记录机制，用于验证当前 Agent 面对真实 DOCX 时的稳定性。

本阶段只建设测试资产目录和测试计划，不新增批量脚本，不修改业务代码。

## 测试范围

覆盖以下链路：

- 文档分类
- local 模式格式处理
- 修改报告生成
- 在线预览生成
- 下载文件生成
- 参考文献检查结果
- 图表编号检查结果
- 非标准论文确认流程

不覆盖以下内容：

- 不改 formatter
- 不改上传流程
- 不改下载流程
- 不改 preview API
- 不改前端页面
- 不新增业务功能

## 测试文档分类

### clean

格式较标准的论文，预期主流程全部 PASS。

### messy

格式混乱但仍属于论文的文档，预期 Agent 不崩溃，并能生成报告和人工复查建议。

### references

参考文献相关样本，覆盖缺失章节、编号跳号、重复编号、正文引用不存在、文末未引用等场景。

### figures_tables

图表编号相关样本，覆盖图号跳号、表号跳号、重复图表编号、正文引用不存在、Word 表格缺少表题等场景。

### template_mismatch

论文和模板不匹配、模板字段缺失、模板结构异常等样本，预期模板异常不阻断主流程。

### reports

实验报告、课程报告、开题报告、综述报告等非标准论文，预期分类能给出确认提示或合理类型。

## 脱敏规则

真实文档进入 `test_documents/` 前必须脱敏：

1. 删除或替换姓名、学号、身份证号、手机号、邮箱。
2. 删除或替换导师姓名、班级、学院、学校内部编号。
3. 删除签名、致谢中的真实个人信息。
4. 删除图片中的个人信息和二维码。
5. 用占位文本替换敏感内容，例如 `张三`、`2024000000`、`example@example.com`。
6. 提交前确认没有真实 DOCX 被 git 跟踪。

## manifest.csv 字段

每篇文档至少记录：

- `case_id`
- `file_name`
- `category`
- `document_type`
- `template_file`
- `expected_classification_success`
- `expected_format_success`
- `expected_report`
- `expected_preview`
- `expected_download`
- `expected_manual_review`
- `known_risks`
- `notes`

`document_type` 支持用 `|` 写多个可接受分类，例如 `academic_paper|lab_report`，用于记录模板错配、报告/论文边界等已知模糊样本。

## PASS / FAIL 标准

单篇文档 PASS 需要满足：

1. 分类结果符合预期，或非标准论文按预期进入确认流程。
2. 格式处理流程不异常中断。
3. 修改报告成功生成。
4. 在线预览成功生成。
5. 下载文件成功生成且非空。
6. 没有非预期误判。
7. 需要人工复查的风险能被记录。
8. local 模式保持 `ai_score=null` 且 `ai_used=false`。

单篇文档 FAIL 包括：

1. Agent 主流程异常中断。
2. 输出 DOCX 缺失。
3. 修改报告缺失。
4. 在线预览失败。
5. 下载失败。
6. 分类结果与预期明显不符。
7. 本应人工复查但没有任何提示。
8. local 模式出现 AI 评分字段异常。

## 运行流程

v0.5.0 新增 `run_real_doc_regression.py`，用于读取 `manifest.csv` 并批量执行本地回归。人工回归流程仍可保留：

1. 将脱敏 DOCX 放入对应分类目录。
2. 在 `test_documents/manifest.csv` 增加记录。
3. 通过现有上传入口或后端测试方式逐篇运行。
4. 检查分类、处理、报告、预览、下载结果。
5. 将结果保存到 `regression_results/<run_id>/`。

批量回归命令：

```powershell
python .\run_real_doc_regression.py --manifest test_documents\manifest.csv --mode local
python .\run_real_doc_regression.py --manifest test_documents\generated_manifest.csv --mode local --limit 3
```

脚本会输出 `summary.csv`、`summary.json` 和 `cases/<case_id>.json`。默认会在分类发现非标准论文需要确认时自动传入确认参数，以验证 Agent 主链路、报告、预览和下载不被阻断；如需只验证确认拦截流程，可增加 `--no-confirm-non-paper`。

## 回归结果建议格式

批量脚本保存：

```text
regression_results/
  2026-06-01_153000/
    summary.csv
    summary.json
    cases/
      clean_001.json
      references_001.json
    logs.txt
```

每篇论文结果记录：

- 文件名
- 文档类型
- 是否分类成功
- 是否格式修改成功
- 是否生成报告
- 是否生成预览
- 是否可下载
- 是否有误判
- 是否需要人工复查
- 总结果 PASS / FAIL
- 错误信息
- 运行耗时
- 文件大小分桶：`small`、`medium`、`large`

## CNKI / GB/T 7714 样本边界

可使用公开 CNKI 采编平台页面、公开投稿模板、公开投稿须知、公开 GB/T 7714 参考文献格式说明作为来源线索。不得下载或纳入需要登录、付费、验证码、授权受限的 CNKI 正文全文；用户合法提供的真实论文必须先脱敏再入库。

详见 `test_documents/CNKI_GBT7714_SOURCE_NOTES.md`。

## 当前阶段验收

v0.3.5 第一步验收标准：

- `test_documents/` 目录存在。
- 6 类测试文档目录存在。
- `manifest.csv` 有表头和 3 条脱敏占位样例。
- `regression_results/.gitkeep` 存在。
- `real_paper_test_plan.md` 存在。
- `PROJECT_STATUS.md` 和 `TODO.md` 已更新。
- 未修改业务代码。
- 未误加入真实 DOCX。
