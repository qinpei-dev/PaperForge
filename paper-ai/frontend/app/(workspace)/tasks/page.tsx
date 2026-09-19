"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge, Button } from "../../../components";
import { apiUrl } from "../../../lib/api-client";
import { authorizationHeaders } from "../../../lib/auth";
import { userFacingError } from "../../../lib/error-messages";
import { taskStatusLabel, workflowStatusLabel } from "../../../lib/status-labels";
import styles from "./page.module.css";

type Task = {
  id: string;
  title?: string;
  paper_name?: string;
  status: string;
  workflow_stage?: string | null;
  score?: number | null;
  created_at?: string;
};

const PROCESSING_STATUSES = ["pending", "created", "analyzing", "planning", "executing", "verifying", "running"];

function formatDate(value?: string) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString("zh-CN");
}

function statusTone(status: string) {
  if (status === "completed") return styles.statusSuccess;
  if (["failed", "cancelled", "interrupted"].includes(status)) return styles.statusDanger;
  if (PROCESSING_STATUSES.includes(status)) return styles.statusProgress;
  return styles.statusNeutral;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function loadTasks() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(apiUrl("/tasks"), { cache: "no-store", headers: authorizationHeaders() });
        if (!response.ok) throw new Error(response.status === 401 ? "登录已过期" : "任务数据加载失败");
        const data: unknown = await response.json();
        if (!cancelled) setTasks(Array.isArray(data) ? (data as Task[]) : []);
      } catch (reason) {
        if (!cancelled) setError(userFacingError(reason, "任务数据暂时无法加载，请稍后重试。"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadTasks();
    return () => {
      cancelled = true;
    };
  }, [retryCount]);

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerTitleGroup}>
          <p className={styles.eyebrow}>TASKS</p>
          <h1>任务中心</h1>
          <p className={styles.lead}>查看当前工作空间中的全部论文处理任务与状态。</p>
        </div>
        <Link href="/tasks/new" className={`pf-button pf-button--primary ${styles.newTaskButton}`}>
          ＋ 新建任务
        </Link>
      </header>

      {error ? (
        <p className={styles.inlineError} role="alert">
          {error}
        </p>
      ) : null}

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <h2>全部任务</h2>
          <span className={styles.countBadge}>{loading ? "加载中…" : `${tasks.length} 项`}</span>
        </div>

        {loading ? (
          <div className={styles.emptyState}>
            <strong>正在加载任务</strong>
            <p>正在读取当前工作空间的任务记录…</p>
          </div>
        ) : error ? (
          <div className={styles.emptyState}>
            <strong>任务暂时无法加载</strong>
            <p>请检查网络连接后重试。</p>
            <Button onClick={() => setRetryCount((count) => count + 1)}>重新加载</Button>
          </div>
        ) : tasks.length ? (
          <div className={styles.tableWrap}>
            <div className={styles.tableHeader}>
              <span className={styles.colDoc}>文档名称</span>
              <span className={styles.colStatus}>状态</span>
              <span className={styles.colDate}>创建时间</span>
              <span className={styles.colResult}>处理阶段 / 评分</span>
              <span className={styles.colAction}>操作</span>
            </div>
            <div className={styles.taskList}>
              {tasks.map((task) => (
                <Link className={styles.taskRow} href={`/tasks/${task.id}`} key={task.id}>
                  <div className={styles.colDoc}>
                    <span className={styles.docIcon} aria-hidden="true">
                      DOCX
                    </span>
                    <strong
                      className={styles.docTitle}
                      title={task.title || task.paper_name || "PaperForge 文档"}
                    >
                      {task.title || task.paper_name || "PaperForge 文档"}
                    </strong>
                  </div>
                  <div className={styles.colStatus}>
                    <Badge className={statusTone(task.status)}>{taskStatusLabel(task.status)}</Badge>
                  </div>
                  <div className={styles.colDate}>
                    <span>{formatDate(task.created_at)}</span>
                  </div>
                  <div className={styles.colResult}>
                    {task.workflow_stage
                      ? workflowStatusLabel(task.workflow_stage)
                      : task.score === null || task.score === undefined
                      ? "—"
                      : `${task.score} 分`}
                  </div>
                  <div className={styles.colAction}>
                    <span className={styles.actionLink}>进入详情 →</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ) : (
          <div className={styles.emptyState}>
            <strong>还没有任务</strong>
            <p>从论文处理工作台上传文件，即可在这里跟踪处理进度。</p>
            <Link href="/tasks/new" className="pf-button pf-button--primary">
              开始处理论文
            </Link>
          </div>
        )}
      </section>
    </section>
  );
}
