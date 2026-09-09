"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

type User = { email?: string };
type Workspace = { name?: string };
type Task = { id: string; title?: string; status: string; score?: number | null; created_at?: string };

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User>({});
  const [workspace, setWorkspace] = useState<Workspace>({});
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("paperforge_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    const savedUser = localStorage.getItem("paperforge_user");
    const savedWorkspace = localStorage.getItem("paperforge_workspace");
    if (savedUser) setUser(JSON.parse(savedUser) as User);
    if (savedWorkspace) setWorkspace(JSON.parse(savedWorkspace) as Workspace);
    fetch(`${API_BASE}/tasks`, { headers: { Authorization: `Bearer ${token}` } }).then(async (response) => {
      if (response.status === 401) throw new Error("登录已过期");
      if (!response.ok) throw new Error("任务数据加载失败");
      const data = await response.json() as Task[];
      setTasks(data);
    }).catch((reason) => {
      setError(reason instanceof Error ? reason.message : "任务数据加载失败");
    });
  }, [router]);

  function logout() {
    localStorage.removeItem("paperforge_token");
    localStorage.removeItem("paperforge_user");
    localStorage.removeItem("paperforge_workspace");
    router.push("/login");
  }

  return <main className="dashboard-page"><div className="dashboard-header"><div><p className="eyebrow">PAPERFORGE SaaS</p><h1>工作空间 Dashboard</h1></div><button className="secondary-button" onClick={logout}>退出登录</button></div><section className="dashboard-grid"><article className="dashboard-card"><span className="card-label">当前用户</span><strong>{user.email || "—"}</strong></article><article className="dashboard-card"><span className="card-label">Workspace</span><strong>{workspace.name || "—"}</strong></article><article className="dashboard-card"><span className="card-label">任务数量</span><strong>{tasks.length}</strong></article></section>{error && <p className="error-text">{error}</p>}<section className="dashboard-card task-center"><div className="dashboard-section-heading"><div><span className="card-label">最近任务</span><h2>任务中心</h2></div><Link className="dashboard-link" href="/">新建任务 →</Link></div>{tasks.length === 0 ? <p className="muted-text">还没有任务，上传一篇论文开始处理。</p> : <div className="task-list">{tasks.slice(0, 10).map((task) => <Link className="task-row" href={`/tasks/${task.id}`} key={task.id}><span><strong>{task.title || "PaperForge Documents"}</strong><small>{task.created_at ? new Date(task.created_at).toLocaleString("zh-CN") : "—"}</small></span><span className={`task-status task-status-${task.status}`}><b>{task.status}</b>{task.score === null || task.score === undefined ? "—" : `${task.score} 分`}</span></Link>)}</div>}</section><Link className="dashboard-link" href="/">进入论文处理工作台 →</Link></main>;
}
