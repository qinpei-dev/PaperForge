"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Badge, Button, Card, EmptyState, Loading } from "../../../components";
import { apiUrl } from "../../../lib/api-client";
import { authorizationHeaders, clearAuthSession, getAccessToken, isPreviewEnvironment, suppressPreviewAutoLogin, tryPreviewAutoLogin } from "../../../lib/auth";
import { taskStatusLabel, workflowStatusLabel } from "../../../lib/status-labels";
import styles from "./page.module.css";

type Task = {
  id: string;
  title?: string;
  paper_name?: string;
  status: string;
  workflow_stage?: string | null;
  progress?: number;
  score?: number | null;
  created_at?: string;
};

type UsageSummary = {
  period_start: string;
  period_end: string;
  quota: { limit: number };
  usage: { used: number };
  remaining: number;
};

const PROCESSING_STATUSES = ["pending", "created", "analyzing", "planning", "executing", "verifying", "running"];

function formatDate(value?: string) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString("zh-CN");
}

function formatPeriod(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString("zh-CN");
}

function statusTone(status: string) {
  if (status === "completed") return styles.statusSuccess;
  if (["failed", "cancelled", "interrupted"].includes(status)) return styles.statusDanger;
  if (PROCESSING_STATUSES.includes(status)) return styles.statusProgress;
  return styles.statusNeutral;
}

export default function DashboardPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [usageLoading, setUsageLoading] = useState(true);
  const [error, setError] = useState("");
  const [usageError, setUsageError] = useState("");
  const [email, setEmail] = useState("");
  const [workspace, setWorkspace] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function bootstrapDashboard() {
      await tryPreviewAutoLogin();
      if (!getAccessToken()) {
        if (!cancelled) router.replace("/login");
        return;
      }

      const savedUser = localStorage.getItem("paperforge_user");
      const savedWorkspace = localStorage.getItem("paperforge_workspace");
      if (savedUser) {
        try {
          setEmail((JSON.parse(savedUser) as { email?: string }).email || "");
        } catch {
          setEmail("");
        }
      }
      if (savedWorkspace) {
        try {
          setWorkspace((JSON.parse(savedWorkspace) as { name?: string }).name || "");
        } catch {
          setWorkspace("");
        }
      }

      const headers = authorizationHeaders();

      async function loadTasks() {
      try {
        const response = await fetch(apiUrl("/tasks"), { cache: "no-store", headers });
        if (!response.ok) throw new Error(response.status === 401 ? "登录已过期" : "任务数据加载失败");
        const data: unknown = await response.json();
        if (!cancelled) setTasks(Array.isArray(data) ? data as Task[] : []);
      } catch (reason) {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "任务数据加载失败");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

      async function loadUsage() {
      try {
        const response = await fetch(apiUrl("/usage"), { cache: "no-store", headers });
        const data = await response.json() as Partial<UsageSummary>;
        if (!response.ok) throw new Error("本月额度暂时无法加载");
        if (!cancelled && data.quota && data.usage && typeof data.remaining === "number") {
          setUsage({
            period_start: typeof data.period_start === "string" ? data.period_start : "",
            period_end: typeof data.period_end === "string" ? data.period_end : "",
            quota: { limit: typeof data.quota.limit === "number" ? data.quota.limit : 0 },
            usage: { used: typeof data.usage.used === "number" ? data.usage.used : 0 },
            remaining: data.remaining,
          });
        }
      } catch (reason) {
        if (!cancelled) setUsageError(reason instanceof Error ? reason.message : "本月额度暂时无法加载");
      } finally {
        if (!cancelled) setUsageLoading(false);
      }
    }

      void loadTasks();
      void loadUsage();
    }

    void bootstrapDashboard();
    return () => { cancelled = true; };
  }, [router]);

  function openNewTask() {
    router.push("/tasks/new");
  }

  function logout() {
    suppressPreviewAutoLogin();
    clearAuthSession();
    router.push("/login");
  }

  const completedCount = tasks.filter((task) => task.status === "completed").length;
  const processingCount = tasks.filter((task) => PROCESSING_STATUSES.includes(task.status)).length;
  const usagePercent = usage ? Math.min(100, Math.round((usage.usage.used / Math.max(usage.quota.limit, 1)) * 100)) : 0;

  return (
    <section className={styles.dashboard} aria-busy={loading}>
      <Card className={styles.welcomeCard}>
        <div>
          <p className={styles.eyebrow}>PAPERFORGE WORKSPACE</p>
          <h1>欢迎回来{email ? `，${email.split("@")[0]}` : ""}</h1>
          <p className={styles.welcomeText}>集中管理论文处理任务，查看 Agent 进度，并快速获取可交付文档。</p>
        </div>
        <div className={styles.workspaceInfo}>
          <span>当前 Workspace</span>
          <strong>{workspace || "PaperForge Workspace"}</strong>
          <small>任务与额度均按当前工作空间统计</small>
        </div>
      </Card>

      <div className={styles.actionRow}>
        <Card className={styles.quickStartCard}>
          <div>
            <p className={styles.cardEyebrow}>QUICK START</p>
            <h2>开始一篇新论文</h2>
            <p>上传论文，可选配合模板，启动格式 Agent 处理流程。</p>
          </div>
          <Button onClick={openNewTask}>创建新论文任务 <span aria-hidden="true">→</span></Button>
        </Card>

        <Card className={styles.quotaCard} aria-label="本月使用额度">
          <div className={styles.sectionHeading}>
            <div>
              <p className={styles.cardEyebrow}>USAGE / QUOTA</p>
              <h2>本月使用额度</h2>
            </div>
            <Badge className={usage && usage.remaining === 0 ? styles.badgeWarning : styles.badgeSuccess}>
              {usage ? (usage.remaining === 0 ? "额度已用尽" : "额度可用") : "统计中"}
            </Badge>
          </div>
          {usageLoading && !usage ? <Loading label="正在加载额度…" /> : usage ? <>
            <div className={styles.quotaNumbers}>
              <div><span>已使用</span><strong>{usage.usage.used}</strong><small>/ {usage.quota.limit} 次</small></div>
              <div><span>剩余</span><strong>{usage.remaining}</strong><small>本周期可用</small></div>
            </div>
            <div className={styles.progressTrack} aria-label={`已使用 ${usagePercent}%`}><span style={{ width: `${usagePercent}%` }} /></div>
            <p className={styles.period}>周期：{formatPeriod(usage.period_start)} – {formatPeriod(usage.period_end)}</p>
          </> : <p className={styles.inlineMessage}>{usageError || "本月额度暂时无法加载。"}</p>}
        </Card>
      </div>

      <section aria-labelledby="dashboard-metrics-title">
        <div className={styles.sectionHeading}><div><p className={styles.cardEyebrow}>METRICS</p><h2 id="dashboard-metrics-title">工作台概览</h2></div></div>
        <div className={styles.metricsGrid}>
          <Card className={styles.metricCard}><span>总任务数</span><strong>{tasks.length}</strong><small>当前 Workspace</small></Card>
          <Card className={styles.metricCard}><span>已完成</span><strong>{completedCount}</strong><small>已生成交付结果</small></Card>
          <Card className={styles.metricCard}><span>处理中</span><strong>{processingCount}</strong><small>正在运行的任务</small></Card>
          <Card className={styles.metricCard}><span>本月使用量</span><strong>{usage ? usage.usage.used : "—"}</strong><small>{usage ? `/ ${usage.quota.limit} 次额度` : "等待额度数据"}</small></Card>
        </div>
      </section>

      <Card className={styles.recentCard} aria-labelledby="recent-tasks-title">
        <div className={styles.sectionHeading}>
          <div><p className={styles.cardEyebrow}>RECENT TASKS</p><h2 id="recent-tasks-title">最近任务</h2></div>
          <Link className={styles.sectionLink} href="/tasks">查看全部</Link>
        </div>
        {error ? <p className={styles.errorMessage}>{error}</p> : null}
        {loading ? <Loading label="正在加载任务…" /> : tasks.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyStateCopy}>
              <EmptyState
                title={isPreviewEnvironment() ? "这是一个全新的 Preview Workspace" : "从第一篇论文开始"}
                description={isPreviewEnvironment() ? "当前没有测试任务，正适合走一遍完整流程。你的上传内容会按当前 Workspace 隔离。" : "上传论文后，PaperForge 会完成格式检查、Agent 处理、结果验证，并提供在线预览和下载。"}
              />
              <p className={styles.emptyValue}>用一次处理，把论文从“待整理”推进到“可检查、可预览、可交付”。</p>
            </div>
            <div className={styles.emptyFlow} aria-label="示例流程">
              <p className={styles.emptyFlowTitle}>示例流程</p>
              <ol>
                <li><b>01</b><span>上传论文</span><small>选择 .docx 文件</small></li>
                <li><b>02</b><span>选择处理模式</span><small>Local 或 AI 增强</small></li>
                <li><b>03</b><span>查看并下载</span><small>预览验证后的结果</small></li>
              </ol>
            </div>
            <Button onClick={openNewTask}>创建第一个任务 <span aria-hidden="true">→</span></Button>
          </div>
        ) : <div className={styles.taskList}>
          {tasks.slice(0, 5).map((task) => <article className={styles.taskRow} key={task.id}>
            <div className={styles.taskMain}>
              <strong>{task.title || task.paper_name || "PaperForge 论文任务"}</strong>
              <span>{formatDate(task.created_at)}</span>
            </div>
            <div className={styles.taskMeta}>
              <Badge className={statusTone(task.status)}>{taskStatusLabel(task.status)}</Badge>
              <small>{task.workflow_stage ? workflowStatusLabel(task.workflow_stage) : task.score === null || task.score === undefined ? "等待评分" : `${task.score} 分`}</small>
            </div>
            <Button variant="secondary" className={styles.detailButton} onClick={() => router.push(`/tasks/${task.id}`)}>进入详情</Button>
          </article>)}
        </div>}
      </Card>

      <div className={styles.footerActions}>
        <Button variant="secondary" onClick={logout}>退出登录</Button>
      </div>
    </section>
  );
}
