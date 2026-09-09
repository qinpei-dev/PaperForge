"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
type Artifact = { file_path: string; file_type: string };
type Task = { id: string; status: string; score?: number | null; uploaded_file?: string; trace?: unknown[]; artifacts?: Artifact[]; created_at?: string };

export default function TaskDetailPage() {
  const router = useRouter();
  const params = useParams<{ taskId: string }>();
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("paperforge_token");
    if (!token) { router.replace("/login"); return; }
    fetch(`${API_BASE}/tasks/${encodeURIComponent(params.taskId)}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(async (response) => { const data = await response.json(); if (!response.ok) throw new Error(data.detail || "任务加载失败"); setTask(data as Task); })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "任务加载失败"));
  }, [params.taskId, router]);

  return <main className="dashboard-page"><Link className="dashboard-link" href="/dashboard">← 返回任务中心</Link><section className="dashboard-card task-center"><p className="eyebrow">TASK DETAIL</p><h1>任务详情</h1>{error ? <p className="error-text">{error}</p> : !task ? <p className="muted-text">加载中…</p> : <><p>状态：<strong>{task.status}</strong></p><p>评分：<strong>{task.score ?? "—"}</strong></p><p>创建时间：{task.created_at ? new Date(task.created_at).toLocaleString("zh-CN") : "—"}</p><h2>输出文件</h2><ul>{(task.artifacts || []).map((artifact) => <li key={`${artifact.file_type}-${artifact.file_path}`}>{artifact.file_type}：{artifact.file_path}</li>)}</ul><h2>Agent Trace</h2><pre>{JSON.stringify(task.trace || [], null, 2)}</pre></>}</section></main>;
}
