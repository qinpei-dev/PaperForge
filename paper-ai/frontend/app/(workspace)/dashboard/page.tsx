"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Badge, Button, Card, EmptyState, Loading } from "../../../components";
import { apiUrl } from "../../../lib/api-client";
import { authorizationHeaders, clearAuthSession, getAccessToken, isPreviewEnvironment, isUiPreviewSession, suppressPreviewAutoLogin, tryPreviewAutoLogin } from "../../../lib/auth";
import { userFacingError } from "../../../lib/error-messages";
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
      if (isUiPreviewSession()) {
        const savedUser = localStorage.getItem("paperforge_user");
        const savedWorkspace = localStorage.getItem("paperforge_workspace");
        if (savedUser) setEmail((JSON.parse(savedUser) as { email?: string }).email || "");
        if (savedWorkspace) setWorkspace((JSON.parse(savedWorkspace) as { name?: string }).name || "Preview Workspace");
        setLoading(false);
        setUsageLoading(false);
        return;
      }
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
        if (!cancelled) setError(userFacingError(reason, "任务数据暂时无法加载，请稍后重试。"));
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
        if (!cancelled) setUsageError(userFacingError(reason, "本月额度暂时无法加载，请稍后重试。"));
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
      <header className={styles.header}>
        <div className={styles.headerMain}>
          <div className={styles.headerMeta}>
            <span className={styles.workspacePill}>{workspace || "PaperForge Workspace"}</span>
            {usage ? (
              <span className={styles.quotaPill}>
                本月额度: <strong>{usage.usage.used}</strong> / {usage.quota.limit} 次
                {usage.remaining === 0 ? <span className={styles.quotaWarning}>已用尽</span> : null}
              </span>
            ) : null}
          </div>
          <h1>欢迎回来{email ? `，${email.split("@")[0]}` : ""}</h1>
          <p className={styles.lead}>集中管理论文处理任务，跟踪格式修复与验证进度。</p>
        </div>
        <div className={styles.headerActions}>
          <Button onClick={openNewTask} className={styles.createTaskButton}>
            ＋ 新建论文任务
          </Button>
        </div>
      </header>

      <div className={styles.statsStrip}>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>总任务数</span>
          <strong className={styles.statValue}>{tasks.length}</strong>
        </div>
        <div className={styles.statDivider} aria-hidden="true" />
        <div className={styles.statItem}>
          <span className={styles.statLabel}>已完成</span>
          <strong className={styles.statValue}>{completedCount}</strong>
        </div>
        <div className={styles.statDivider} aria-hidden="true" />
        <div className={styles.statItem}>
          <span className={styles.statLabel}>处理中</span>
          <strong className={styles.statValue}>{processingCount}</strong>
        </div>
        <div className={styles.statDivider} aria-hidden="true" />
        <div className={styles.statItem}>
          <span className={styles.statLabel}>剩余额度</span>
          <strong className={styles.statValue}>{usage ? `${usage.remaining} 次` : "—"}</strong>
        </div>
      </div>

      <Card className={styles.recentCard} aria-labelledby="recent-tasks-title">
        <div className={styles.sectionHeading}>
          <div>
            <h2 id="recent-tasks-title">最近任务</h2>
            <p className={styles.sectionSub}>最近处理的学术论文与验证状态</p>
          </div>
          <Link className={styles.sectionLink} href="/tasks">查看全部任务 →</Link>
        </div>

        {error ? <p className={styles.errorMessage} role="alert">{error}</p> : null}

        {loading ? (
          <div className={styles.loadingBox}><Loading label="正在加载任务列表…" /></div>
        ) : tasks.length === 0 ? (
          <div className={styles.emptyState}>
            <EmptyState
              title={isPreviewEnvironment() ? "这是一个全新的 Preview Workspace" : "开始你的第一篇论文"}
              description={isPreviewEnvironment() ? "当前工作区暂无测试任务，你的上传内容会按当前工作空间严格隔离。" : "上传 DOCX 论文后，PaperForge 会自动解析模板、修复格式并重新验证输出。"}
            />
            <div className={styles.emptyActions}>
              <Button onClick={openNewTask}>创建第一个论文任务 <span aria-hidden="true">→</span></Button>
            </div>
          </div>
        ) : (
          <div className={styles.tableWrap}>
            <div className={styles.tableHeader}>
              <span className={styles.colDoc}>文档名称</span>
              <span className={styles.colStatus}>状态</span>
              <span className={styles.colDate}>创建时间</span>
              <span className={styles.colResult}>处理阶段 / 评分</span>
              <span className={styles.colAction}>操作</span>
            </div>
            <div className={styles.taskList}>
              {tasks.slice(0, 5).map((task) => (
                <article className={styles.taskRow} key={task.id}>
                  <div className={styles.colDoc}>
                    <span className={styles.docIcon} aria-hidden="true">DOCX</span>
                    <strong className={styles.docTitle} title={task.title || task.paper_name || "PaperForge 论文任务"}>
                      {task.title || task.paper_name || "PaperForge 论文任务"}
                    </strong>
                  </div>
                  <div className={styles.colStatus}>
                    <Badge className={statusTone(task.status)}>{taskStatusLabel(task.status)}</Badge>
                  </div>
                  <div className={styles.colDate}>
                    <span>{formatDate(task.created_at)}</span>
                  </div>
                  <div className={styles.colResult}>
                    <span className={styles.resultText}>
                      {task.workflow_stage ? workflowStatusLabel(task.workflow_stage) : task.score === null || task.score === undefined ? "—" : `${task.score} 分`}
                    </span>
                  </div>
                  <div className={styles.colAction}>
                    <Button variant="secondary" className={styles.detailButton} onClick={() => router.push(`/tasks/${task.id}`)}>
                      进入详情
                    </Button>
                  </div>
                </article>
              ))}
            </div>
          </div>
        )}
      </Card>
    </section>
  );
}
