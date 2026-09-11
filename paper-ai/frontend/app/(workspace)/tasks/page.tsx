"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiUrl } from "../../../lib/api-client";
import { authorizationHeaders } from "../../../lib/auth";
import { taskStatusLabel, workflowStatusLabel } from "../../../lib/status-labels";

type Task = { id: string; title?: string; paper_name?: string; status: string; workflow_stage?: string | null; score?: number | null; created_at?: string };

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    async function loadTasks() {
      try {
        const response = await fetch(apiUrl("/tasks"), { cache: "no-store", headers: authorizationHeaders() });
        if (!response.ok) throw new Error(response.status === 401 ? "登录已过期" : "任务数据加载失败");
        const data: unknown = await response.json();
        if (!cancelled) setTasks(Array.isArray(data) ? data as Task[] : []);
      } catch (reason) { if (!cancelled) setError(reason instanceof Error ? reason.message : "任务数据加载失败"); }
    }
    void loadTasks();
    return () => { cancelled = true; };
  }, []);
  return <section className="workspace-page"><header className="workspace-page-heading"><div><p className="eyebrow">TASKS</p><h1>任务中心</h1><p>查看当前工作空间中的论文处理任务与处理状态。</p></div><Link className="app-primary-link" href="/tasks/new">新建任务</Link></header>{error ? <p className="workspace-inline-error">{error}</p> : null}<section className="workspace-panel"><div className="workspace-panel-heading"><h2>全部任务</h2><span>{tasks.length} 项</span></div>{tasks.length ? <div className="workspace-task-list">{tasks.map((task) => <Link className="workspace-task-row" href={`/tasks/${task.id}`} key={task.id}><div><strong>{task.title || task.paper_name || "PaperForge 文档"}</strong><small>{task.created_at ? new Date(task.created_at).toLocaleString("zh-CN") : "—"}</small></div><div><b>{taskStatusLabel(task.status)}</b><small>{task.workflow_stage ? workflowStatusLabel(task.workflow_stage) : task.score === null || task.score === undefined ? "尚无评分" : `${task.score} 分`}</small></div></Link>)}</div> : <div className="workspace-empty"><strong>还没有任务</strong><p>从论文处理工作台上传文件，即可在这里跟踪处理进度。</p><Link href="/tasks/new">开始处理论文</Link></div>}</section></section>;
}
