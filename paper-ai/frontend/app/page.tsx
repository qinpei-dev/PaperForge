"use client";

import { useMemo, useState } from "react";

type AgentStep = { name: string; status: "running" | "done" | "error"; message: string };
type AgentTraceItem = {
  step?: string;
  status?: string;
  duration_ms?: number;
  fallback_used?: boolean;
  message?: string;
};
type RuntimeTraceItem = AgentTraceItem & { state?: string };
type ScoreDimension = { key: string; label: string; score: number; group: "local" | "ai"; status: string; issues: string[] };
type Classification = {
  document_type: string;
  label: string;
  confidence: number;
  matched_features: string[];
  warning: string;
  requires_confirmation: boolean;
};
type ScoreBreakdown = {
  format_score?: number;
  risk_score?: number;
  ai_language_score?: number | null;
  local_score: number;
  ai_score: number | null;
  final_score: number;
  score_confidence?: number;
  score_explanation?: string;
  ai_used: boolean;
  ai_added_value: string[];
};
type ReferenceCheck = {
  has_reference_section: boolean;
  reference_count: number;
  citation_count: number;
  reference_numbers: number[];
  citation_numbers: number[];
  missing_reference_numbers: number[];
  uncited_reference_numbers: number[];
  duplicate_reference_numbers: number[];
  numbering_gaps: number[];
  issues: string[];
};
type FigureTableCheck = {
  figure_numbers: number[];
  table_numbers: number[];
  figure_gaps: number[];
  table_gaps: number[];
  duplicate_figures: number[];
  duplicate_tables: number[];
  missing_figure_captions: string[];
  missing_table_captions: string[];
  missing_referenced_figures: number[];
  missing_referenced_tables: number[];
  issues: string[];
};
type Analysis = {
  reference_check?: ReferenceCheck;
  figure_table_check?: FigureTableCheck;
  report: {
    score: number;
    summary: string;
    breakdown: ScoreDimension[];
    local_breakdown: ScoreDimension[];
    ai_breakdown: ScoreDimension[];
    score_breakdown: ScoreBreakdown;
    recommendations: string[];
  };
};
type RepeatRisk = { level: string; score: number; suggestions: string[] };
type ScoreComparison = { key: string; label: string; before: number; after: number; delta: number; status: string };
type FormatDiffSummary = {
  before_score: number;
  after_score: number;
  score_delta: number;
  auto_fix_count: number;
  changed_dimension_count: number;
  needs_manual_review_count: number;
  format_change_count: number;
  language_change_count: number;
  summary: string;
};
type ModificationReport = {
  summary: string;
  fixed_issues: string[];
  before_after: ScoreComparison[];
  format_diff_summary: FormatDiffSummary;
  changed_dimensions: ScoreComparison[];
  score_delta_by_dimension: Record<string, number>;
  auto_fix_count: number;
  needs_manual_review_count: number;
  change_counts: { format_changes: number; language_changes: number; total: number };
  unresolved_issues: string[];
  manual_review_items: string[];
  score_explanation?: string;
  template_used: string | null;
};
type Workflow = { current_state?: string; replan_count?: number; trace?: AgentTraceItem[] };
type Verification = {
  passed?: boolean;
  verified_rules?: string[];
  passed_rules?: string[];
  failed_rules?: string[];
  structural_integrity?: { status?: string; unsafe_reasons?: unknown[] };
  score?: number;
  verification_score?: number;
  verification_summary?: { total?: number; verified?: number; failed?: number; unsupported?: number };
  conflict_summary?: { conflicts?: number };
};
type Decision = { action?: string; reason?: string; risk?: string; evidence?: unknown[] };
type HumanReview = {
  reason?: string;
  affected_targets?: string[];
  related_rule_ids?: string[];
  suggested_action?: string;
  items?: unknown[];
};
type ReplanHistory = { plan?: { plan_id?: string }; decision?: Decision };
type ProvenanceChange = { action?: string; rule_type?: string; target?: { semantic_role?: string; paragraph_index?: number }; before?: unknown; expected?: unknown; after?: unknown; verification_scope?: string; verification_status?: string; verification_evidence?: { reason?: string; actual?: unknown } };
type Provenance = { changes?: ProvenanceChange[]; summary?: { planned_steps?: number; executed_steps?: number; unsupported_steps?: number; change_count?: number; conflicts?: number; verification?: { total?: number; verified?: number; failed?: number; unsupported?: number } } };
type ContentIssue = { paragraph_index?: number; issue_type?: string; original_text?: string; suggested_text?: string; reason?: string; action_policy?: string; source?: string; verification_status?: string };
type ContentReview = { issues?: ContentIssue[]; counts?: { AUTO_FIX?: number; SUGGEST_ONLY?: number; HITL_REQUIRED?: number }; provenance?: { auto_fixes?: ContentIssue[]; suggestions?: ContentIssue[]; hitl?: ContentIssue[] }; verification?: { total?: number; verified?: number; failed?: number } };
type AgentResult = {
  status: "ok" | "requires_confirmation";
  mode?: string;
  requires_confirmation: boolean;
  classification: Classification;
  steps: AgentStep[];
  before_score: number;
  after_score: number;
  score_breakdown: ScoreBreakdown;
  repeat_risk: RepeatRisk;
  download_url: string;
  filename: string;
  after_analysis: Analysis;
  modification_report: ModificationReport;
  agent_trace?: AgentTraceItem[];
  agent_trace_detail?: Record<string, unknown>;
  task_id?: string;
  task_state_path?: string;
  workflow?: Workflow | null;
  verification?: Verification | null;
  decision?: Decision | null;
  human_review?: HumanReview | null;
  replan_history?: ReplanHistory[];
  execution_plan?: { plan_id?: string };
  runtime_trace?: RuntimeTraceItem[];
  provenance?: Provenance | null;
  content_review?: ContentReview | null;
};
type PreviewResult = { title: string; html: string };

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
const defaultSteps = ["识别文档类型", "读取论文", "分析本地格式", "识别模板格式", "修复标题样式", "AI增强审校", "重复风险预检", "最终复查", "生成最终报告"];

function apiUrl(path: string) {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

async function readResponseData(response: Response): Promise<Record<string, unknown>> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return { detail: text };
  }
}

function apiErrorMessage(data: Record<string, unknown>, fallback: string) {
  const detail = data.detail;
  if (typeof detail === "string") return detail;
  if (isRecord(detail)) {
    const failedStep = typeof detail.failed_step === "string" ? detail.failed_step : "";
    const error = typeof detail.error === "string" ? detail.error : "";
    if (failedStep || error) return failedStep ? `Agent 在「${failedStep}」失败：${error || "未返回详细错误"}` : error;
    const message = typeof detail.message === "string" ? detail.message : "";
    if (message) return message;
  }
  const message = typeof data.message === "string" ? data.message : "";
  return message || fallback;
}

function networkErrorMessage(error: unknown, fallback: string, requestUrl?: string) {
  const suffix = requestUrl ? `请求地址：${requestUrl}。请确认后端服务地址和端口可访问。` : "";
  if (error instanceof Error && error.message) {
    return suffix ? `${fallback}：${error.message}。${suffix}` : `${fallback}（${error.message}）`;
  }
  return suffix ? `${fallback}。${suffix}` : fallback;
}

export default function Home() {
  const [paperFile, setPaperFile] = useState<File | null>(null);
  const [paperFilename, setPaperFilename] = useState("");
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [templateFilename, setTemplateFilename] = useState("");
  const [agentMode, setAgentMode] = useState<"local" | "ai">("ai");
  const [classification, setClassification] = useState<Classification | null>(null);
  const [confirmedNonPaper, setConfirmedNonPaper] = useState(false);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [previewError, setPreviewError] = useState("");
  const [message, setMessage] = useState("");
  const [running, setRunning] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);

  const visibleSteps = useMemo(() => {
    if (result?.steps.length) {
      const previewStep = preview ? [{ name: "生成在线预览", status: "done" as const, message: "已生成可在线查看的论文预览。" }] : [];
      return [...result.steps, ...previewStep];
    }
    return defaultSteps.map((name) => ({ name, status: "running" as const, message: "等待 Agent 调度" }));
  }, [result, preview]);

  const hasPaper = Boolean(paperFile);
  const needsConfirmation = classification?.requires_confirmation === true;
  const canRun = hasPaper && (!needsConfirmation || confirmedNonPaper);
  const buttonDisabled = running || !canRun;

  async function onPaperChange(file: File | null) {
    setPaperFile(file);
    setPaperFilename(file?.name ?? "");
    setClassification(null);
    setConfirmedNonPaper(false);
    setResult(null);
    setPreview(null);
    setPreviewError("");
    if (!file) {
      setMessage("");
      return;
    }
    await classifyFile(file);
  }

  function onTemplateChange(file: File | null) {
    setTemplateFile(file);
    setTemplateFilename(file?.name ?? "");
  }

  async function classifyFile(file: File) {
    const formData = new FormData();
    formData.append("paper", file);
    setClassifying(true);
    setMessage("正在识别文档类型...");
    try {
      const requestUrl = apiUrl("/document/classify");
      const response = await fetch(requestUrl, { method: "POST", body: formData });
      const data = await readResponseData(response);
      if (!response.ok) {
        setMessage(apiErrorMessage(data, "文档类型识别失败。"));
        return;
      }
      const nextClassification = data as Classification;
      setClassification(nextClassification);
      setMessage(nextClassification.requires_confirmation ? "该文档可能不适合直接套用论文格式，请确认后继续。" : "已识别为标准论文，可以启动 Agent。");
    } catch (error) {
      setMessage(networkErrorMessage(error, "文档类型识别失败。你仍可在确认文件无误后启动 Agent", apiUrl("/document/classify")));
    } finally {
      setClassifying(false);
    }
  }

  async function runAgent() {
    if (!paperFile) {
      setMessage("请先上传论文 docx 文件。");
      return;
    }
    if (needsConfirmation && !confirmedNonPaper) {
      setMessage("该文档可能不是标准论文，必须勾选确认后才能继续。");
      return;
    }

    const formData = new FormData();
    const allowNonPaper = Boolean(confirmedNonPaper || !classification);
    formData.append("paper", paperFile);
    formData.append("mode", agentMode);
    formData.append("allow_non_paper", String(allowNonPaper));
    if (templateFile) formData.append("template", templateFile);

    setRunning(true);
    setPreview(null);
    setPreviewError("");
    setResult(null);
    setMessage("论文修改 Agent 正在自主处理文档...");
    try {
      const requestUrl = apiUrl("/agent/run");
      const response = await fetch(requestUrl, { method: "POST", body: formData });
      const data = await readResponseData(response);
      const status = typeof data.status === "string" ? data.status : "";
      if (status === "requires_confirmation") {
        setClassification(data.classification as Classification);
        setMessage(typeof data.message === "string" ? data.message : "该文档可能不适合直接套用论文格式，请确认后继续。");
        return;
      }
      if (!response.ok || status === "error") {
        setMessage(apiErrorMessage(data, "Agent 执行失败。"));
        return;
      }
      const nextResult = data as unknown as AgentResult;
      setResult(nextResult);
      setClassification(nextResult.classification);
      setMessage("Agent 修改完成，正在生成在线预览。");
      const previewReady = await loadPreview(nextResult.filename);
      setMessage(previewReady ? "Agent 修改完成，已生成修改报告和在线预览。" : "Agent 修改完成，修改报告和下载文件已生成，在线预览暂不可用。");
    } catch (error) {
      setMessage(networkErrorMessage(error, "Agent 启动失败", apiUrl("/agent/run")));
    } finally {
      setRunning(false);
    }
  }

  async function loadPreview(filename: string): Promise<boolean> {
    setPreviewLoading(true);
    setPreviewError("");
    try {
      const requestUrl = apiUrl(`/preview/${encodeURIComponent(filename)}`);
      const response = await fetch(requestUrl);
      const data = await readResponseData(response);
      if (!response.ok) {
        const detail = apiErrorMessage(data, "在线预览生成失败。");
        setPreviewError(detail);
        setMessage(detail);
        return false;
      }
      setPreview(data as PreviewResult);
      return true;
    } catch (error) {
      const detail = networkErrorMessage(error, "在线预览生成失败", apiUrl(`/preview/${encodeURIComponent(filename)}`));
      setPreviewError(detail);
      setMessage(detail);
      return false;
    } finally {
      setPreviewLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="workspace">
        <section className="landing-shell" aria-label="产品首页与处理工作台">
          <header className="hero">
            <div className="hero-copy">
              <p className="eyebrow">AI Paper Agent</p>
              <h1>AI论文格式修改Agent</h1>
              <p className="hero-lead">面向 DOCX 论文/报告的本地格式 Agent：模板格式审查、自动排版、修改报告和 Agent Trace 可观测，一次上传即可进入处理链路。</p>
              <div className="hero-badges" aria-label="当前能力">
                <span>格式 Agent</span>
                <span>同步处理</span>
                <span>本地 fallback</span>
              </div>
              <div className="capability-grid" aria-label="核心能力">
                <div>
                  <strong>模板格式对齐</strong>
                  <span>读取模板规则，统一标题、正文、段落和页边距。</span>
                </div>
                <div>
                  <strong>修改报告生成</strong>
                  <span>汇总评分变化、修复项、风险项和人工复查建议。</span>
                </div>
                <div>
                  <strong>Agent Trace 可观测</strong>
                  <span>展示处理步骤、耗时和本地规则兜底状态。</span>
                </div>
              </div>
            </div>

            <div className="hero-visual" aria-label="演示仪表盘预览">
              <div className="hero-visual-head">
                <span>Live Dashboard</span>
                <strong>{result ? `${result.before_score} -> ${result.after_score}` : "80 -> 86"}</strong>
              </div>
              <div className="hero-score-line">
                <span>格式规则分</span>
                <b>{result?.score_breakdown.format_score ?? result?.score_breakdown.local_score ?? 86}</b>
              </div>
              <div className="hero-metric-grid">
                <span>报告</span>
                <span>Trace</span>
                <span>预览</span>
              </div>
              <ol>
                <li>识别文档类型</li>
                <li>模板规则匹配</li>
                <li>生成修改报告</li>
              </ol>
            </div>
          </header>

          <section className="setup-panel" aria-label="上传与运行">
            <div className="section-title">
              <span>开始处理</span>
              <strong>{paperFilename ? "论文已选择" : "等待上传"}</strong>
            </div>
            <p className="section-note">先上传论文 DOCX；模板 DOCX 可选，用于提供学校或学院格式规则参考。</p>

            <section className="upload-grid" aria-label="上传文件">
              <FilePicker title="论文 docx" description="必选。Agent 会读取并生成格式处理结果。" filename={paperFilename} onChange={onPaperChange} required />
              <FilePicker title="模板 docx" description="可选。上传后会优先参考模板样式。" filename={templateFilename} onChange={onTemplateChange} />
            </section>

            <section className="mode-switch" aria-label="Agent 模式">
              <button className={agentMode === "local" ? "active" : ""} onClick={() => setAgentMode("local")} type="button">
                本地规则模式
                <span>只执行格式修复与重复风险预检</span>
              </button>
              <button className={agentMode === "ai" ? "active" : ""} onClick={() => setAgentMode("ai")} type="button">
                AI增强模式
                <span>增加语言、逻辑和学术表达评估</span>
              </button>
            </section>

            <div className="action-row">
              <button className="agent-button" disabled={buttonDisabled} onClick={runAgent}>
                {running ? "Agent 执行中..." : result ? "重新运行Agent" : "启动论文修改 Agent"}
              </button>
              {result ? (
                <button className="secondary-button" disabled={previewLoading} onClick={() => loadPreview(result.filename)}>
                  {previewLoading ? "生成预览中..." : "刷新在线预览"}
                </button>
              ) : null}
            </div>
          </section>
        </section>

        {classification ? <ClassificationCard classification={classification} confirmed={confirmedNonPaper} onConfirm={setConfirmedNonPaper} /> : null}

        {message ? <p className={message.includes("失败") || message.includes("必须") ? "message error" : "message"}>{message}</p> : null}

        {(running || result) ? <ProgressPanel running={running} steps={visibleSteps} /> : null}

        {result?.download_url ? (
          <section className="result-panel" aria-label="Agent 结果">
            <div className="result-heading">
              <div>
                <p className="eyebrow">Result Overview</p>
                <h2>处理结果总览</h2>
                <p>核心评分、修改报告、检查结果和 Agent 执行过程都在这里汇总展示。</p>
              </div>
              <a className="download compact" href={apiUrl(result.download_url)} download>
                下载最终docx
              </a>
            </div>

            <div className="completion-strip">
              <span>Agent修改完成</span>
              <span>已生成修改报告</span>
              <span>{preview ? "已生成在线预览" : previewError ? "在线预览暂不可用" : "正在生成在线预览"}</span>
            </div>

            <ScoreOverview result={result} />

            <RuntimeSummary result={result} />

            <ContentReviewPanel review={result.content_review} />

            <section className="report-panel">
              <div className="section-title">
                <span>Agent修改报告</span>
                <strong>{result.modification_report.change_counts.total} 项处理</strong>
              </div>
              <p className="report-summary">{result.modification_report.summary}</p>
              <DiffReport report={result.modification_report} />
              {result.modification_report.score_explanation ? <p className="score-explanation">{result.modification_report.score_explanation}</p> : null}
              {result.score_breakdown.ai_added_value.length ? <ReportList title="AI语言参考说明" items={result.score_breakdown.ai_added_value} /> : null}
              <div className="report-grid">
                <ReportList title="已修复的问题" items={result.modification_report.fixed_issues} />
                <ReportList title="未能自动修复的问题" items={result.modification_report.unresolved_issues} />
              </div>
            </section>

            <ScoreModules title="格式规则评分" items={result.after_analysis.report.local_breakdown} />
            {result.score_breakdown.ai_used ? <ScoreModules title="AI语言参考评分" items={result.after_analysis.report.ai_breakdown} /> : null}

            <section className="checks-grid" aria-label="检查结果">
              {result.after_analysis.reference_check ? <ReferenceCheckPanel check={result.after_analysis.reference_check} /> : null}
              {result.after_analysis.figure_table_check ? <FigureTableCheckPanel check={result.after_analysis.figure_table_check} /> : null}
            </section>

            <section className="risk-box">
              <div className="section-title">
                <span>重复风险与人工复查</span>
                <strong>相似度预检 {result.repeat_risk.score}/100</strong>
              </div>
              <div className="report-grid">
                <ReportList title="重复风险处理建议" items={result.repeat_risk.suggestions} />
                <ReportList title="建议人工复查项" items={result.modification_report.manual_review_items} />
              </div>
            </section>

            <TracePanel result={result} />

            <section className="preview-panel">
              <div className="section-title">
                <span>在线预览与下载</span>
                <strong>{preview?.title ?? (previewError ? "预览暂不可用" : "预览生成中")}</strong>
              </div>
              {previewLoading ? <div className="preview-status">正在生成修改后的论文预览...</div> : null}
              {previewError ? (
                <div className="preview-error">
                  <strong>在线预览生成失败</strong>
                  <span>{previewError}</span>
                </div>
              ) : null}
              {preview ? <article className="doc-preview" dangerouslySetInnerHTML={{ __html: preview.html }} /> : null}
              {!preview && !previewError ? <div className="preview-loading">正在生成修改后的论文预览...</div> : null}
              <a className="download" href={apiUrl(result.download_url)} download>
                下载最终docx
              </a>
            </section>
          </section>
        ) : null}
      </section>
    </main>
  );
}

function ContentReviewPanel({ review }: { review?: ContentReview | null }) {
  if (!review) return null;
  const counts = review.counts ?? {};
  const items = review.issues ?? [];
  return (
    <section className="runtime-panel content-review-panel" aria-label="段落级内容审查">
      <div className="section-title"><span>段落级内容审查</span><strong>安全策略已生效</strong></div>
      <div className="content-review-counts">
        <span>自动修正：{counts.AUTO_FIX ?? 0}</span>
        <span>修改建议：{counts.SUGGEST_ONLY ?? 0}</span>
        <span>需人工复核：{counts.HITL_REQUIRED ?? 0}</span>
      </div>
      {items.length ? <ul className="runtime-change-list">{items.slice(0, 8).map((item, index) => <li key={`${item.paragraph_index}-${item.issue_type}-${index}`}>
        正文 #{item.paragraph_index ?? "—"} · {item.issue_type ?? "内容问题"} · {item.action_policy === "AUTO_FIX" ? "已自动修正" : item.action_policy === "HITL_REQUIRED" ? "需人工确认" : "建议修改"}
        {item.reason ? <small>：{item.reason}</small> : null}
        {item.action_policy !== "AUTO_FIX" && item.suggested_text ? <details><summary>查看原文与建议</summary><p>原文：{item.original_text}</p><p>建议：{item.suggested_text}</p></details> : null}
      </li>)}</ul> : <p>未发现需要处理的段落级内容问题。</p>}
    </section>
  );
}

function ClassificationCard({ classification, confirmed, onConfirm }: { classification: Classification; confirmed: boolean; onConfirm: (value: boolean) => void }) {
  return (
    <section className={classification.requires_confirmation ? "classification warning" : "classification"}>
      <div>
        <span>文档类型</span>
        <strong>{classification.label}</strong>
      </div>
      <div>
        <span>置信度</span>
        <strong>{Math.round(classification.confidence * 100)}%</strong>
      </div>
      <p>匹配特征：{classification.matched_features.length ? classification.matched_features.join("、") : "暂无明显特征"}</p>
      {classification.warning ? <p>{classification.warning}</p> : null}
      {classification.requires_confirmation ? (
        <label className="confirm-line">
          <input type="checkbox" checked={confirmed} onChange={(event) => onConfirm(event.target.checked)} />
          我确认继续按论文格式处理
        </label>
      ) : null}
    </section>
  );
}

function ProgressPanel({ running, steps }: { running: boolean; steps: AgentStep[] }) {
  return (
    <section className="agent-panel" aria-label="Agent 执行进度">
      <div className="section-title">
        <span>Agent执行过程</span>
        {running ? <strong>自主处理中</strong> : <strong>已完成</strong>}
      </div>
      <ol className="timeline">
        {steps.map((step) => (
          <li className={step.status} key={step.name}>
            <span className="step-icon">{step.status === "done" ? "✓" : step.status === "error" ? "!" : "•"}</span>
            <div>
              <strong>{step.name}</strong>
              <p>{step.message}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function TracePanel({ result }: { result: AgentResult }) {
  const traceItems = Array.isArray(result.agent_trace) ? result.agent_trace : [];
  const hasTaskStateSummary = Boolean(result.task_id || result.task_state_path);
  const traceDetail = isRecord(result.agent_trace_detail) ? result.agent_trace_detail : null;
  const hasTraceDetail = Boolean(traceDetail && Object.keys(traceDetail).length);

  if (!traceItems.length && !hasTaskStateSummary && !hasTraceDetail) {
    return null;
  }

  return (
    <details className="trace-panel">
      <summary>
        <span>执行轨迹</span>
        <strong>{traceItems.length ? `${traceItems.length} 个步骤` : "任务状态摘要"}</strong>
      </summary>

      <div className="trace-intro">
        <p>agent_trace 是步骤级执行记录，用于查看格式检查过程、耗时、fallback 和需人工复核项。</p>
        <p>当前仍是同步执行接口，不是异步队列，也不是完整断点续跑；前端不会读取 task_state 文件内容。</p>
      </div>

      {hasTaskStateSummary ? (
        <div className="trace-state">
          {result.task_id ? (
            <div>
              <span>任务 ID</span>
              <code>{result.task_id}</code>
            </div>
          ) : null}
          {result.task_state_path ? (
            <div>
              <span>后端任务状态文件路径</span>
              <code>{result.task_state_path}</code>
            </div>
          ) : null}
          <p className="trace-state-note">该路径用于开发/演示排查；前端当前不会读取该文件内容，也不代表异步队列或任务恢复能力。</p>
        </div>
      ) : null}

      {!traceItems.length ? <p className="trace-empty">本次结果未返回 agent_trace 步骤列表，仅展示任务状态摘要。</p> : null}

      {traceItems.length ? (
        <ol className="trace-list">
          {traceItems.map((item, index) => {
            const tone = traceStatusTone(item.status, item.fallback_used);
            return (
              <li className={`trace-step ${tone}`} key={`${item.step ?? "trace"}-${index}`}>
                <span className={`trace-step-index ${tone}`} aria-label={`步骤 ${index + 1}`}>
                  {index + 1}
                </span>
                <div className="trace-step-body">
                  <div className="trace-item-head">
                    <strong>{formatTraceStepName(item.step, index)}</strong>
                    <span className={`trace-status ${tone}`}>{traceStatusLabel(item.status, item.fallback_used)}</span>
                  </div>
                  <p>{formatTraceMessage(item.message)}</p>
                  <div className="trace-meta">
                    <span>{formatTraceDuration(item.duration_ms)}</span>
                    <span className={item.fallback_used ? "trace-fallback-badge" : undefined}>
                      {item.fallback_used ? "已使用 fallback / 本地规则兜底" : "未标记 fallback"}
                    </span>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      ) : null}

      {hasTraceDetail && traceDetail ? (
        <div className="trace-detail-card">
          <div className="trace-detail-head">
            <span>agent_trace_detail</span>
            <strong>详细执行说明</strong>
          </div>
          <p>以下为后端返回的旧解释型 trace 明细，仅用于排查和演示说明；字段缺失时以前面的步骤流为准。</p>
          <pre className="trace-detail-json">{formatTraceDetail(traceDetail)}</pre>
        </div>
      ) : null}
    </details>
  );
}

const runtimeWorkflow = [
  ["ANALYZING", "分析文档"],
  ["PLANNING", "生成执行计划"],
  ["EXECUTING", "执行安全修改"],
  ["VERIFYING", "验证修改结果"],
  ["REPLANNING", "重新规划"],
  ["COMPLETED", "执行完成"],
  ["HUMAN_REVIEW_REQUIRED", "需要人工复核"],
  ["FAILED", "执行失败"],
] as const;

function RuntimeSummary({ result }: { result: AgentResult }) {
  const workflow = result.workflow;
  const verification = result.verification;
  const decision = result.decision;
  const review = result.human_review;
  const history = Array.isArray(result.replan_history) ? result.replan_history : [];
  const traceStates = new Set((result.runtime_trace ?? []).map((item) => item.state));
  const currentState = workflow?.current_state;
  const passedRules = verification?.verified_rules ?? verification?.passed_rules ?? [];
  const failedRules = verification?.failed_rules ?? [];
  const integrity = verification?.structural_integrity?.status;
  const score = verification?.verification_score ?? verification?.score;
  const provenance = result.provenance && !Array.isArray(result.provenance) ? result.provenance : null;
  const changes = provenance?.changes ?? [];
  const summary = provenance?.summary;
  const targetVerified = changes.filter((change) => change.verification_scope === "target" && change.verification_status === "verified");
  const verificationSummary = verification?.verification_summary ?? summary?.verification;
  const conflictCount = verification?.conflict_summary?.conflicts ?? summary?.conflicts ?? 0;

  if (!workflow && !verification && !decision && !review && !history.length && !provenance) return null;

  return (
    <section className="runtime-panel" aria-label="Runtime Workflow">
      {workflow ? (
        <div>
          <div className="section-title"><span>Runtime Workflow</span><strong>{runtimeStateLabel(currentState)}</strong></div>
          <ol className="runtime-workflow">
            {runtimeWorkflow.map(([state, label]) => {
              const active = currentState === state;
              const completed = traceStates.has(state) || (currentState === "COMPLETED" && !["HUMAN_REVIEW_REQUIRED", "FAILED"].includes(state));
              const tone = active ? runtimeStateTone(state) : completed ? "success" : "pending";
              return <li className={tone} key={state}><span>{active ? "•" : completed ? "✓" : "○"}</span><strong>{label}</strong></li>;
            })}
          </ol>
        </div>
      ) : null}

      {verification ? (
        <div className="runtime-card">
          <div className="section-title"><span>验证结果摘要</span><strong className={integrity && integrity !== "SAFE" ? "runtime-warning" : ""}>{integrity === "UNSAFE" ? "发现结构风险" : integrity === "WARNING" ? "存在结构提示" : "结构检查通过"}</strong></div>
          <p>目标验证：共 {verificationSummary?.total ?? "—"} 项，通过 {verificationSummary?.verified ?? "—"}，失败 {verificationSummary?.failed ?? "—"}，unsupported {verificationSummary?.unsupported ?? "—"}；冲突 {conflictCount} 项。{typeof score === "number" ? `验证评分 ${score}。` : ""}</p>
          <details className="runtime-details"><summary>开发者/高级详情</summary><pre>{formatRuntimeDetail(verification)}</pre></details>
        </div>
      ) : null}

      {provenance ? (
        <div className="runtime-card">
          <div className="section-title"><span>实际修改</span><strong>{summary?.change_count ?? changes.length} 项</strong></div>
          <p>已执行 PlanStep {summary?.executed_steps ?? "—"} 项；目标级验证通过 {targetVerified.length} 项；HITL / unsupported {summary?.unsupported_steps ?? "—"} 项；计划冲突 {conflictCount} 项。</p>
          {targetVerified.length ? <ul className="runtime-change-list">{targetVerified.slice(0, 5).map((change, index) => <li key={`${change.action}-${change.target?.paragraph_index}-${index}`}>{change.target?.semantic_role === "figure_caption" ? "图题" : change.target?.semantic_role === "table_caption" ? "表题" : "标题"}：{String(change.before ?? "未设置")} → {String(change.after ?? "未设置")}（已验证）</li>)}</ul> : null}
        </div>
      ) : null}

      {decision ? <div className={`runtime-card decision-card ${decisionTone(decision.action)}`}><div className="section-title"><span>最终决策</span><strong>{decisionLabel(decision.action)}</strong></div><p>{decision.reason || "决策引擎未返回补充说明。"}</p></div> : null}

      {review ? <div className="human-review-panel"><div className="section-title"><span>需要人工复核</span><strong>自动流程已安全停止</strong></div><p><b>原因：</b>{review.reason || "检测到需要人工确认的风险。"}</p><p><b>涉及规则/步骤：</b>{[...(review.related_rule_ids ?? []), ...(review.affected_targets ?? [])].join("、") || "未提供"}</p>{review.items?.length ? <ul className="runtime-change-list">{review.items.slice(0, 5).map((item, index) => <li key={index}>{formatRuntimeDetail(item)}</li>)}</ul> : null}<p><b>建议操作：</b>{review.suggested_action || "请人工确认后再决定后续处理。"}</p></div> : null}

      {history.length ? <details className="runtime-card replan-card"><summary>系统已自动重新规划 {history.length} 次</summary><ol>{history.map((item, index) => <li key={`${item.plan?.plan_id ?? "plan"}-${index}`}>旧 Plan ID：{item.plan?.plan_id ?? "未记录"}；新 Plan ID：{history[index + 1]?.plan?.plan_id ?? result.execution_plan?.plan_id ?? "未记录"}；原因：{item.decision?.reason ?? "未记录"}</li>)}</ol></details> : null}
    </section>
  );
}

function runtimeStateLabel(state?: string) {
  return runtimeWorkflow.find(([value]) => value === state)?.[1] ?? "运行状态未返回";
}

function runtimeStateTone(state: string) {
  if (state === "HUMAN_REVIEW_REQUIRED") return "review";
  if (state === "FAILED") return "failed";
  return "running";
}

function decisionLabel(action?: string) {
  return ({ COMPLETE: "完成：验证通过", REPLAN: "重新规划：尝试安全修复", HUMAN_REVIEW: "人工复核：需人工确认", FAIL: "失败：无法安全继续" } as Record<string, string>)[action ?? ""] ?? "决策未返回";
}

function decisionTone(action?: string) {
  if (action === "HUMAN_REVIEW" || action === "REPLAN") return "warning";
  if (action === "FAIL") return "failed";
  return "success";
}

function formatRuntimeDetail(detail: unknown) {
  try { return JSON.stringify(detail, null, 2); } catch { return "运行时详情无法格式化展示。"; }
}

function formatTraceStepName(step: string | undefined, index: number) {
  return step?.trim() ? step : `未命名步骤 ${index + 1}`;
}

function formatTraceMessage(message?: string) {
  return message?.trim() ? message : "该步骤未返回简短说明。";
}

function formatTraceDetail(detail: Record<string, unknown>) {
  try {
    return JSON.stringify(detail, null, 2);
  } catch {
    return "agent_trace_detail 无法格式化展示。";
  }
}

function ScoreOverview({ result }: { result: AgentResult }) {
  const formatScore = result.score_breakdown.format_score ?? result.score_breakdown.local_score;
  const aiLanguageScore = result.score_breakdown.ai_language_score ?? result.score_breakdown.ai_score;
  const aiIsReferenceOnly = typeof aiLanguageScore === "number" && aiLanguageScore < formatScore;
  const scoreDelta = result.after_score - result.before_score;
  const deltaLabel = scoreDelta > 0 ? `+${scoreDelta}` : String(scoreDelta);
  const modeLabel = result.mode === "local" ? "本地规则模式" : result.mode === "ai" ? "AI增强模式" : "当前模式";

  return (
    <div className="score-overview">
      <div className="score-card primary">
        <span>评分变化</span>
        <div className="score-pair">
          <b>{result.before_score}</b>
          <i>→</i>
          <strong>{result.after_score}</strong>
        </div>
        <p>提升值 {deltaLabel}。{result.after_analysis.report.summary}</p>
      </div>
      <div className="score-card score-change">
        <span>格式规则分</span>
        <b>{formatScore}</b>
        <span>风险稳定分</span>
        <b>{result.score_breakdown.risk_score ?? "待评估"}</b>
        <span>AI语言参考分</span>
        <b>{aiLanguageScore ?? "未启用"}</b>
        <small>可信度 {result.score_breakdown.score_confidence ?? "待评估"}</small>
        {aiIsReferenceOnly ? <p className="score-note">AI语言评分仅作参考，不影响最终评分。</p> : null}
      </div>
      <div className={`score-card risk-pill ${riskTone(result.repeat_risk.level)}`}>
        <span>重复风险</span>
        <strong>{result.repeat_risk.level}</strong>
        <small>{result.repeat_risk.score}/100</small>
        <div className="result-meta">
          <span>{modeLabel}</span>
          <span>{result.score_breakdown.ai_used ? "AI参考已参与" : "AI参考未参与评分"}</span>
          {result.task_id ? <span>任务 ID：{result.task_id}</span> : null}
        </div>
      </div>
    </div>
  );
}

function ScoreModules({ title, items }: { title: string; items: ScoreDimension[] }) {
  return (
    <section className="module-panel">
      <div className="section-title">
        <span>{title}</span>
        <strong>{items.length} 项</strong>
      </div>
      <div className="module-grid">
        {items.map((item) => (
          <ScoreModule key={item.key} item={item} />
        ))}
      </div>
    </section>
  );
}

function FilePicker({ title, description, filename, required = false, onChange }: { title: string; description: string; filename: string; required?: boolean; onChange: (file: File | null) => void }) {
  return (
    <label className="file-card">
      <span>
        {title}
        <b>{required ? "必选" : "可选"}</b>
      </span>
      <p>{description}</p>
      <strong>{filename || "选择 Word 文件"}</strong>
      <input accept=".docx" type="file" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
    </label>
  );
}

function ScoreModule({ item }: { item: ScoreDimension }) {
  return (
    <div className="module-card">
      <div>
        <span>{item.label}</span>
        <strong>{item.score}</strong>
      </div>
      <div className="bar">
        <i style={{ width: `${item.score}%` }} />
      </div>
      <p>{item.status}</p>
      {item.issues.length ? <small>{item.issues[0]}</small> : <small>自动检查未发现明显风险。</small>}
    </div>
  );
}

function ReportList({ title, items }: { title: string; items: string[] }) {
  const safeItems = items.length ? items : ["暂无需要展示的内容。"];
  return (
    <div className="report-list">
      <h2>{title}</h2>
      <ul>
        {safeItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function ReferenceCheckPanel({ check }: { check: ReferenceCheck }) {
  const summaryItems = [
    `参考文献章节：${check.has_reference_section ? "已识别" : "未识别"}`,
    `文末条目：${check.reference_count} 条`,
    `正文引用：${check.citation_count} 处`,
  ];
  const relationItems = [
    `文末编号：${formatNumbers(check.reference_numbers)}`,
    `正文引用编号：${formatNumbers(check.citation_numbers)}`,
    `跳号：${formatNumbers(check.numbering_gaps)}`,
    `重复编号：${formatNumbers(check.duplicate_reference_numbers)}`,
    `正文引用不存在：${formatNumbers(check.missing_reference_numbers)}`,
    `文末未引用：${formatNumbers(check.uncited_reference_numbers)}`,
  ];
  const issueItems = check.issues.length ? check.issues : ["自动检查未发现明显参考文献风险。"];
  return (
    <section className="module-panel">
      <div className="section-title">
        <span>参考文献检查</span>
        <strong>{check.reference_count} 条文献</strong>
      </div>
      <div className="report-grid">
        <ReportList title="检查概览" items={summaryItems} />
        <ReportList title="编号与引用" items={relationItems} />
      </div>
      <ReportList title="参考文献风险" items={issueItems} />
    </section>
  );
}

function FigureTableCheckPanel({ check }: { check: FigureTableCheck }) {
  const summaryItems = [
    `图题编号：${formatNumbers(check.figure_numbers)}`,
    `表题编号：${formatNumbers(check.table_numbers)}`,
    `图编号跳号：${formatNumbers(check.figure_gaps)}`,
    `表编号跳号：${formatNumbers(check.table_gaps)}`,
  ];
  const riskItems = [
    `重复图编号：${formatNumbers(check.duplicate_figures)}`,
    `重复表编号：${formatNumbers(check.duplicate_tables)}`,
    `正文引用图号不存在：${formatNumbers(check.missing_referenced_figures)}`,
    `正文引用表号不存在：${formatNumbers(check.missing_referenced_tables)}`,
  ];
  const captionItems = [...check.missing_figure_captions, ...check.missing_table_captions];
  const issueItems = check.issues.length ? check.issues : ["自动检查未发现明显图表编号风险。"];
  return (
    <section className="module-panel">
      <div className="section-title">
        <span>图表编号检查</span>
        <strong>{check.figure_numbers.length} 图 / {check.table_numbers.length} 表</strong>
      </div>
      <div className="report-grid">
        <ReportList title="编号概览" items={summaryItems} />
        <ReportList title="引用与重复" items={riskItems} />
      </div>
      {captionItems.length ? <ReportList title="题注缺失风险" items={captionItems} /> : null}
      <ReportList title="图表风险" items={issueItems} />
    </section>
  );
}

function DiffReport({ report }: { report: ModificationReport }) {
  const changedItems = report.changed_dimensions.length
    ? report.changed_dimensions.map((item) => `${item.label}：${item.before} → ${item.after}（${formatDelta(item.delta)}）`)
    : ["各评分维度保持稳定，本次主要完成格式规范化处理。"];
  return (
    <div className="diff-report">
      <div className="diff-summary">
        <div>
          <span>自动处理</span>
          <strong>{report.auto_fix_count}</strong>
        </div>
        <div>
          <span>变化维度</span>
          <strong>{report.format_diff_summary.changed_dimension_count}</strong>
        </div>
        <div>
          <span>人工复查</span>
          <strong>{report.needs_manual_review_count}</strong>
        </div>
      </div>
      <p>{report.format_diff_summary.summary}</p>
      <div className="report-grid">
        <ReportList title="改了什么" items={changedItems} />
        <ReportList title="仍需人工复查" items={report.manual_review_items} />
      </div>
    </div>
  );
}

function formatNumbers(numbers: number[]) {
  return numbers.length ? numbers.join("、") : "无";
}

function formatDelta(delta: number) {
  if (delta > 0) return `+${delta}`;
  return String(delta);
}

function formatTraceDuration(duration?: number) {
  return typeof duration === "number" && Number.isFinite(duration) ? `${duration} ms` : "未记录耗时";
}

function traceStatusLabel(status?: string, fallbackUsed?: boolean) {
  const normalized = normalizeTraceStatus(status, fallbackUsed);
  if (!normalized) return "未记录状态";
  if (normalized === "success") return "success";
  if (normalized === "warning") return "warning";
  if (normalized === "fallback") return "fallback";
  if (normalized === "failed") return "failed";
  if (normalized === "running") return "running";
  if (normalized === "skipped") return "skipped";
  return status?.trim() || "未记录状态";
}

function traceStatusTone(status?: string, fallbackUsed?: boolean) {
  const normalized = normalizeTraceStatus(status, fallbackUsed);
  if (normalized === "success") return "success";
  if (normalized === "warning") return "warning";
  if (normalized === "fallback") return "fallback";
  if (normalized === "failed") return "failed";
  if (normalized === "running") return "running";
  if (normalized === "skipped") return "skipped";
  return "neutral";
}

function normalizeTraceStatus(status?: string, fallbackUsed?: boolean) {
  const normalized = status?.trim().toLowerCase();
  if (normalized === "error" || normalized === "failed" || normalized === "failure") return "failed";
  if (normalized === "warning" || normalized === "warn") return "warning";
  if (normalized === "fallback") return "fallback";
  if (normalized === "running") return "running";
  if (normalized === "skipped" || normalized === "skip") return "skipped";
  if (fallbackUsed) return "fallback";
  if (!normalized) return "";
  if (normalized === "done" || normalized === "ok" || normalized === "succeeded" || normalized === "success") return "success";
  return normalized;
}

function riskTone(level: string) {
  if (level === "高") return "risk-high";
  if (level === "中") return "risk-medium";
  return "risk-low";
}
