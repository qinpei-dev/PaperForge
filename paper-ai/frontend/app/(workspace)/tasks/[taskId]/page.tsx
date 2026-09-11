"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Badge, Button, Card, Loading } from "../../../../components";
import { apiUrl } from "../../../../lib/api-client";
import { authorizationHeaders } from "../../../../lib/auth";
import { userFacingError } from "../../../../lib/error-messages";
import { taskStatusLabel, workflowStatusLabel } from "../../../../lib/status-labels";
import styles from "./page.module.css";

type Artifact = { id: string; file_path: string; file_type: string; download_url?: string; preview_url?: string | null };
type WorkflowStep = { key: string; label: string; status: string };
type TraceItem = {
  step?: string;
  state?: string;
  component?: string;
  action?: string;
  status?: string;
  message?: string;
  duration_ms?: number;
  fallback_used?: boolean;
};
type TaskEvent = { event_type?: string; status?: string; workflow_stage?: string | null; progress?: number; message?: string; timestamp?: string };
type VerificationSummary = { total?: number; verified?: number; failed?: number; unsupported?: number; conflicts?: number };
type ModificationCounts = { format_changes?: number; language_changes?: number; total?: number };
type ReportSummary = { change_counts?: ModificationCounts };
type ScoreBreakdown = { final_score?: number | null; local_score?: number | null; ai_score?: number | null; ai_used?: boolean; ai_added_value?: string[] };
type Task = {
  id: string;
  paper_name?: string;
  status: string;
  workflow_stage?: string | null;
  current_stage?: string | null;
  progress?: number;
  score?: number | null;
  score_history?: { before?: number | null; after?: number | null };
  score_breakdown?: ScoreBreakdown | null;
  template?: { id?: string; version?: string; name?: string } | null;
  trace?: TraceItem[];
  workflow_steps?: WorkflowStep[];
  artifacts?: Artifact[];
  created_at?: string;
  status_explanation?: string | null;
  error_message?: string | null;
  retry_available?: boolean;
  verification_summary?: VerificationSummary | null;
};

const TERMINAL_STATUSES = ["completed", "failed", "cancelled", "interrupted"];
const TIMELINE = [
  { key: "pending", label: "等待处理", description: "任务已创建" },
  { key: "running", label: "处理中", description: "Agent 正在执行" },
  { key: "verifying", label: "质量验证", description: "检查处理结果" },
  { key: "completed", label: "已完成", description: "结果可以交付" },
  { key: "failed", label: "失败", description: "需要重试或检查" },
] as const;

function formatDate(value?: string) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString("zh-CN");
}

function formatScore(value?: number | null) {
  return typeof value === "number" ? `${value}` : "—";
}

function artifactName(artifact: Artifact) {
  return artifact.file_path.split(/[\\/]/).pop() || "paperforge-artifact";
}

function traceTitle(item: TraceItem) {
  return item.step || item.state || item.component || item.action || "Agent 工作流";
}

function traceDescription(item: TraceItem) {
  return item.message || item.action || item.component || "工作流节点已记录";
}

function traceTone(item: TraceItem) {
  if (item.fallback_used) return styles.traceFallback;
  if (["error", "failed", "fail"].includes(String(item.status).toLowerCase())) return styles.traceFailed;
  if (["running", "pending"].includes(String(item.status).toLowerCase())) return styles.traceRunning;
  return styles.traceSuccess;
}

function workflowPhase(task: Task) {
  if (task.status === "completed") return "completed";
  if (["failed", "cancelled", "interrupted"].includes(task.status)) {
    if (task.workflow_stage === "verifying") return "verifying";
    if (["analyzing", "planning", "executing"].includes(task.workflow_stage || "")) return "running";
    return "pending";
  }
  if (task.workflow_stage === "verifying") return "verifying";
  if (task.status === "running" || task.workflow_stage) return "running";
  return "pending";
}

function timelineTone(task: Task, key: string) {
  const phase = workflowPhase(task);
  if (key === "failed") return ["failed", "cancelled", "interrupted"].includes(task.status) ? styles.timelineCurrent : styles.timelinePending;
  const order = ["pending", "running", "verifying", "completed"];
  const phaseIndex = order.indexOf(phase);
  const itemIndex = order.indexOf(key);
  if (key === phase) return styles.timelineCurrent;
  if (phase !== "pending" && itemIndex >= 0 && itemIndex < phaseIndex) return styles.timelineComplete;
  return styles.timelinePending;
}

function verificationTone(summary?: VerificationSummary | null) {
  if (!summary) return styles.badgeNeutral;
  if ((summary.failed || 0) > 0 || (summary.conflicts || 0) > 0) return styles.badgeWarning;
  return styles.badgeSuccess;
}

export default function TaskDetailPage() {
  const router = useRouter();
  const params = useParams<{ taskId: string }>();
  const taskId = params.taskId;
  const [task, setTask] = useState<Task | null>(null);
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [reportSummary, setReportSummary] = useState<ReportSummary | null>(null);
  const [error, setError] = useState("");
  const [streamMode, setStreamMode] = useState<"connecting" | "live" | "polling" | "closed">("connecting");
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewTitle, setPreviewTitle] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [retrying, setRetrying] = useState(false);

  async function downloadArtifact(artifact: Artifact) {
    try {
      const response = await fetch(apiUrl(artifact.download_url || `/artifacts/${encodeURIComponent(artifact.id)}/download`), { headers: authorizationHeaders() });
      if (!response.ok) {
        setError("产物下载失败，请稍后重试。");
        return;
      }
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = artifactName(artifact);
      link.click();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setError(userFacingError(reason, "产物下载暂时不可用，请稍后重试。"));
    }
  }

  async function previewArtifact(artifact: Artifact) {
    const filename = artifactName(artifact);
    setPreviewLoading(true);
    setError("");
    try {
      const response = await fetch(apiUrl(artifact.preview_url || `/preview/${encodeURIComponent(filename)}`), { headers: authorizationHeaders(), cache: "no-store" });
      const data = await response.json() as { html?: string; title?: string; detail?: string };
      if (!response.ok) throw new Error(userFacingError(data.detail, "在线预览失败，请稍后重试。"));
      setPreviewHtml(String(data.html || ""));
      setPreviewTitle(String(data.title || filename));
    } catch (reason) {
      setError(userFacingError(reason, "在线预览失败，请稍后重试。"));
    } finally {
      setPreviewLoading(false);
    }
  }

  async function retryTask() {
    setRetrying(true);
    setError("");
    try {
      const response = await fetch(apiUrl(`/tasks/${encodeURIComponent(taskId)}/retry`), { method: "POST", headers: authorizationHeaders() });
      const data = await response.json() as { detail?: string };
      if (!response.ok) throw new Error(userFacingError(data.detail, "任务重试失败，请稍后重试。"));
      window.location.reload();
    } catch (reason) {
      setError(userFacingError(reason, "任务重试失败，请稍后重试。"));
      setRetrying(false);
    }
  }

  useEffect(() => {
    if (!localStorage.getItem("paperforge_token")) {
      router.replace("/login");
      return;
    }

    const headers = authorizationHeaders();
    const taskController = new AbortController();
    const streamController = new AbortController();
    let stopped = false;
    let terminalReceived = false;
    let pollingActive = false;
    let lastEventId = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;

    const stopPolling = () => {
      pollingActive = false;
      if (timer) {
        clearTimeout(timer);
        timer = undefined;
      }
    };

    const loadTask = async (scheduleNext = false) => {
      try {
        const response = await fetch(apiUrl(`/tasks/${encodeURIComponent(taskId)}`), { headers, cache: "no-store", signal: taskController.signal });
        const data = await response.json() as Task & { detail?: string };
        if (!response.ok) throw new Error(userFacingError(data.detail, "任务详情暂时无法加载，请稍后重试。"));
        if (stopped) return;
        setError("");
        setTask(data);
        if (TERMINAL_STATUSES.includes(String(data.status))) {
          terminalReceived = true;
          stopPolling();
          setStreamMode("closed");
          return;
        }
        if (scheduleNext && pollingActive) timer = setTimeout(() => void loadTask(true), 2000);
      } catch (reason) {
        if (!stopped && reason instanceof Error && reason.name !== "AbortError") {
          setError(userFacingError(reason, "任务详情暂时无法加载，请稍后重试。"));
          if (scheduleNext && pollingActive) timer = setTimeout(() => void loadTask(true), 2000);
        }
      }
    };

    const startPolling = () => {
      if (stopped || terminalReceived || pollingActive) return;
      pollingActive = true;
      setStreamMode("polling");
      void loadTask(true);
    };

    const applyEvent = (event: TaskEvent) => {
      if (stopped) return;
      setEvents((previous) => [...previous, event].slice(-30));
      setTask((previous) => previous ? { ...previous, status: event.status || previous.status, workflow_stage: event.workflow_stage ?? previous.workflow_stage, progress: typeof event.progress === "number" ? event.progress : previous.progress } : previous);
      if (["artifact_created", "task_completed", "task_failed", "task_interrupted"].includes(String(event.event_type))) void loadTask(false);
      if (["task_completed", "task_failed", "task_interrupted"].includes(String(event.event_type))) {
        terminalReceived = true;
        stopPolling();
        setStreamMode("closed");
      }
    };

    const consumeBlocks = (blocks: string[]) => {
      for (const block of blocks) {
        const idLine = block.split(/\r?\n/).find((line) => line.startsWith("id:"));
        if (idLine) {
          const id = Number(idLine.slice(3).trim());
          if (Number.isFinite(id)) lastEventId = Math.max(lastEventId, id);
        }
        const data = block.split(/\r?\n/).filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trimStart()).join("\n");
        if (!data) continue;
        try {
          applyEvent(JSON.parse(data) as TaskEvent);
        } catch {
          // Ignore malformed SSE blocks and let polling keep the task view current.
        }
      }
    };

    const connectStream = async () => {
      try {
        const response = await fetch(apiUrl(`/tasks/${encodeURIComponent(taskId)}/events`), { headers: { ...headers, Accept: "text/event-stream", ...(lastEventId ? { "Last-Event-ID": String(lastEventId) } : {}) }, cache: "no-store", signal: streamController.signal });
        if (!response.ok || !response.body) throw new Error("SSE unavailable");
        if (stopped || terminalReceived) return;
        setError("");
        setStreamMode("live");
        reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (!stopped) {
          const chunk = await reader.read();
          buffer += decoder.decode(chunk.value || new Uint8Array(), { stream: !chunk.done });
          const blocks = buffer.split(/\r?\n\r?\n/);
          buffer = blocks.pop() || "";
          consumeBlocks(blocks);
          if (chunk.done) {
            consumeBlocks(buffer ? [buffer] : []);
            if (!terminalReceived) startPolling();
            if (!terminalReceived) setTimeout(() => { if (!stopped && !terminalReceived) void connectStream(); }, 1000);
            break;
          }
        }
      } catch (reason) {
        if (!stopped && !(reason instanceof Error && reason.name === "AbortError") && !terminalReceived) startPolling();
      }
    };

    const initialize = async () => {
      await loadTask(false);
      if (!stopped && !terminalReceived) void connectStream();
    };
    void initialize();
    return () => {
      stopped = true;
      stopPolling();
      taskController.abort();
      streamController.abort();
      void reader?.cancel();
    };
  }, [router, taskId]);

  const reportArtifact = useMemo(() => task?.artifacts?.find((artifact) => artifact.file_type === "report"), [task]);
  const docxArtifact = useMemo(() => task?.artifacts?.find((artifact) => artifact.file_type === "docx"), [task]);

  useEffect(() => {
    if (!reportArtifact) {
      setReportSummary(null);
      return;
    }
    const report = reportArtifact;
    let cancelled = false;
    async function loadReportSummary() {
      try {
        const response = await fetch(apiUrl(report.download_url || `/artifacts/${encodeURIComponent(report.id)}/download`), { headers: authorizationHeaders(), cache: "no-store" });
        if (!response.ok) return;
        const data = await response.json() as ReportSummary;
        if (!cancelled) setReportSummary(data);
      } catch {
        // The report remains downloadable when its optional summary cannot be read.
      }
    }
    void loadReportSummary();
    return () => { cancelled = true; };
  }, [reportArtifact]);

  if (!task) {
    return <section className={styles.page}><Link className={styles.backLink} href="/dashboard">← 返回任务中心</Link><Card className={styles.loadingCard}>{error ? <p className={styles.errorMessage}>{error}</p> : <Loading label="正在加载任务详情…" />}</Card></section>;
  }

  const traceItems = Array.isArray(task.trace) ? task.trace : [];
  const fallbackCount = traceItems.filter((item) => item.fallback_used).length;
  const score = task.score_history?.after ?? task.score;
  const modificationCount = reportSummary?.change_counts?.total;
  const verification = task.verification_summary;
  const verificationLabel = !verification ? "待验证" : (verification.failed || 0) > 0 || (verification.conflicts || 0) > 0 ? "需要复查" : "验证通过";
  const connectionLabel = streamMode === "live" ? "SSE 实时" : streamMode === "polling" ? "轮询 fallback" : streamMode === "closed" ? "已结束" : "连接中";

  return (
    <section className={styles.page}>
      <header className={styles.pageHeader}>
        <div className={styles.headerIntro}>
          <Link className={styles.backLink} href="/dashboard">← 返回任务中心</Link>
          <p className={styles.eyebrow}>TASK DETAIL</p>
          <div className={styles.titleRow}>
            <h1>{task.paper_name || "PaperForge 论文任务"}</h1>
            <Badge className={task.status === "completed" ? styles.badgeSuccess : ["failed", "cancelled", "interrupted"].includes(task.status) ? styles.badgeDanger : styles.badgeProgress}>{taskStatusLabel(task.status)}</Badge>
          </div>
          <p className={styles.createdAt}>创建于 {formatDate(task.created_at)}{task.template ? ` · 模板 ${task.template.name || task.template.id || "默认"} / v${task.template.version || "—"}` : ""}</p>
        </div>
        <div className={styles.headerActions}>
          {docxArtifact ? <Button variant="secondary" onClick={() => void downloadArtifact(docxArtifact)}>下载 DOCX</Button> : null}
          {task.retry_available ? <Button variant="primary" disabled={retrying} onClick={() => void retryTask()}>{retrying ? "正在重试…" : "重新执行"}</Button> : null}
        </div>
      </header>

      {error ? <p className={styles.errorMessage}>{error}</p> : null}
      {task.error_message && task.status !== "completed" ? <Card className={styles.errorCard}><strong>{task.status_explanation || "任务未完成"}</strong><p>{task.error_message}</p></Card> : null}

      <Card className={styles.resultCard} aria-labelledby="result-overview-title">
        <div className={styles.sectionHeading}><div><p className={styles.cardEyebrow}>RESULT OVERVIEW</p><h2 id="result-overview-title">结果概览</h2></div><Badge className={verificationTone(verification)}>{verificationLabel}</Badge></div>
        <div className={styles.resultGrid}>
          <div className={styles.primaryMetric}><span>总评分</span><strong>{formatScore(score)}</strong><small>{task.score_history?.before != null ? `修改前 ${formatScore(task.score_history.before)} · ${score != null ? "已更新" : "待评分"}` : "最终质量评分"}</small></div>
          <div className={styles.metric}><span>修改数量</span><strong>{modificationCount ?? "—"}</strong><small>{modificationCount == null ? "报告摘要加载中" : "项处理"}</small></div>
          <div className={styles.metric}><span>验证结果</span><strong>{verification ? `${verification.verified ?? 0}/${verification.total ?? 0}` : "—"}</strong><small>{verification ? `通过 / 总检查 · 失败 ${verification.failed ?? 0}` : "等待验证数据"}</small></div>
        </div>
      </Card>

      <Card className={styles.timelineCard} aria-labelledby="workflow-timeline-title">
        <div className={styles.sectionHeading}><div><p className={styles.cardEyebrow}>WORKFLOW TIMELINE</p><h2 id="workflow-timeline-title">处理流程</h2></div><span className={styles.stageSummary}>{workflowStatusLabel(task.workflow_stage) || taskStatusLabel(task.status)}{typeof task.progress === "number" ? ` · ${task.progress}%` : ""}</span></div>
        <ol className={styles.timeline}>
          {TIMELINE.map((item) => <li className={timelineTone(task, item.key)} key={item.key}><span className={styles.timelineDot} aria-hidden="true">{item.key === "completed" && task.status === "completed" ? "✓" : item.key === "failed" && ["failed", "cancelled", "interrupted"].includes(task.status) ? "!" : ""}</span><div><strong>{item.label}</strong><small>{item.key === "running" && task.workflow_stage ? workflowStatusLabel(task.workflow_stage) || item.description : item.description}</small></div></li>)}
        </ol>
      </Card>

      <Card className={styles.executionCard} aria-labelledby="agent-execution-title">
        <div className={styles.sectionHeading}><div><p className={styles.cardEyebrow}>AGENT EXECUTION</p><h2 id="agent-execution-title">Agent 执行</h2></div><Badge className={streamMode === "polling" ? styles.badgeWarning : styles.badgeNeutral}>{connectionLabel}</Badge></div>
        <div className={styles.executionSummary}>
          <div><span>当前阶段</span><strong>{workflowStatusLabel(task.workflow_stage) || taskStatusLabel(task.status)}</strong><small>{typeof task.progress === "number" ? `处理进度 ${task.progress}%` : "阶段信息随任务更新"}</small></div>
          <div><span>Fallback 状态</span><strong>{fallbackCount ? "已启用兜底" : "标准路径"}</strong><small>{fallbackCount ? `${fallbackCount} 个 Trace 节点使用 fallback` : "未检测到 fallback"}</small></div>
        </div>
        <details className={styles.traceDisclosure}>
          <summary><span>开发级 Trace</span><small>{traceItems.length + events.length} 条记录 · 默认折叠</small></summary>
          <div className={styles.traceBody}>
            {events.length ? <div><p className={styles.traceLabel}>实时事件</p><ol className={styles.traceList}>{events.slice().reverse().map((item, index) => <li className={item.status === "failed" ? styles.traceFailed : styles.traceRunning} key={`${item.timestamp || "event"}-${index}`}><div><strong>{item.message || item.event_type || "工作流更新"}</strong><small>{workflowStatusLabel(item.workflow_stage) || item.workflow_stage || "任务状态"}</small></div><span>{typeof item.progress === "number" ? `${item.progress}%` : ""}</span></li>)}</ol></div> : null}
            {traceItems.length ? <div><p className={styles.traceLabel}>Agent Trace</p><ol className={styles.traceList}>{traceItems.map((item, index) => <li className={traceTone(item)} key={`${traceTitle(item)}-${index}`}><div><strong>{traceTitle(item)}</strong><small>{traceDescription(item)}</small></div><span>{item.fallback_used ? "fallback" : item.duration_ms ? `${item.duration_ms} ms` : item.status || "记录"}</span></li>)}</ol></div> : null}
            {!events.length && !traceItems.length ? <p className={styles.muted}>暂无 Trace 记录，任务状态仍会通过 SSE/轮询更新。</p> : null}
          </div>
        </details>
      </Card>

      <Card className={styles.artifactsCard} aria-labelledby="artifacts-title">
        <div className={styles.sectionHeading}><div><p className={styles.cardEyebrow}>ARTIFACTS</p><h2 id="artifacts-title">交付物</h2></div><span className={styles.stageSummary}>{task.artifacts?.length || 0} 项</span></div>
        {task.artifacts?.length ? <div className={styles.artifactGrid}>{task.artifacts.map((artifact) => <article className={styles.artifact} key={artifact.id}><div className={styles.artifactIcon}>{artifact.file_type === "docx" ? "W" : "R"}</div><div className={styles.artifactInfo}><strong>{artifact.file_type === "docx" ? "输出 DOCX" : "修改报告"}</strong><small>{artifact.file_type === "docx" ? "已完成格式处理的论文文档" : "Agent 修改与验证摘要"}</small><code>{artifactName(artifact)}</code></div><div className={styles.artifactActions}><Button variant="secondary" onClick={() => void downloadArtifact(artifact)}>下载</Button>{artifact.file_type === "docx" ? <Button variant="primary" disabled={previewLoading} onClick={() => void previewArtifact(artifact)}>{previewLoading ? "预览中…" : "在线预览"}</Button> : null}</div></article>)}</div> : <p className={styles.muted}>任务完成后，输出 DOCX 与修改报告会显示在这里。</p>}
        {previewHtml ? <div className={styles.previewPanel}><div className={styles.previewHeading}><div><p className={styles.cardEyebrow}>PREVIEW</p><h3>{previewTitle || "在线预览"}</h3></div><Button variant="secondary" onClick={() => setPreviewHtml("")}>关闭预览</Button></div><article className={styles.docPreview} dangerouslySetInnerHTML={{ __html: previewHtml }} /></div> : null}
      </Card>
    </section>
  );
}
