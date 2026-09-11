"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type TaskStats = { total: number; status_summary: Record<string, number> };
type AdminStats = {
  generated_at: string;
  tenants: { total: number; active: number };
  users: { total: number };
  tasks: TaskStats;
  usage: {
    metric: string;
    period_start: string;
    period_end: string;
    used: number;
    all_time_used: number;
    monthly_quota_total: number;
    monthly_quota_remaining: number;
  };
};

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const STATUS_LABEL: Record<string, string> = {
  pending: "等待处理",
  running: "处理中",
  analyzing: "分析中",
  planning: "规划中",
  executing: "执行中",
  verifying: "验证中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
  interrupted: "已中断",
};

function apiUrl(path: string) {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

function adminHeaders(): Record<string, string> {
  const token = typeof window === "undefined" ? "" : localStorage.getItem("paperforge_token") || "";
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function responseData(response: Response): Promise<Record<string, unknown>> {
  try {
    const parsed: unknown = await response.json();
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed as Record<string, unknown> : {};
  } catch {
    return {};
  }
}

function errorMessage(data: Record<string, unknown>, fallback: string) {
  const envelope = data.error;
  if (envelope && typeof envelope === "object" && !Array.isArray(envelope)) {
    const message = (envelope as Record<string, unknown>).message;
    if (typeof message === "string") return message;
  }
  return typeof data.detail === "string" ? data.detail : fallback;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("zh-CN");
}

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [forbidden, setForbidden] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadStats() {
      if (!localStorage.getItem("paperforge_token")) {
        window.location.href = "/login";
        return;
      }
      try {
        const response = await fetch(apiUrl("/admin/stats"), { cache: "no-store", headers: adminHeaders() });
        const data = await responseData(response);
        if (cancelled) return;
        if (response.status === 401) {
          localStorage.removeItem("paperforge_token");
          window.location.href = "/login";
          return;
        }
        if (response.status === 403) {
          setForbidden(true);
          setError("当前账号不是平台管理员，不能访问运营后台。");
          return;
        }
        if (!response.ok) {
          setError(errorMessage(data, "后台统计暂时无法加载。"));
          return;
        }
        setStats(data as unknown as AdminStats);
      } catch {
        if (!cancelled) setError("后台统计暂时无法加载，请确认 API 服务可访问。");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadStats();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return <main className="admin-page"><p className="eyebrow">PAPERFORGE OPERATIONS</p><h1>Admin Dashboard</h1><p className="admin-muted">正在加载系统统计…</p></main>;
  }

  if (forbidden || error || !stats) {
    return <main className="admin-page"><div className="admin-header"><div><p className="eyebrow">PAPERFORGE OPERATIONS</p><h1>Admin Dashboard</h1></div><Link className="home-auth-link" href="/">返回工作台</Link></div><section className="admin-access-denied"><strong>{forbidden ? "访问被拒绝" : "暂时无法加载"}</strong><p>{error || "没有可展示的后台统计。"}</p><Link className="home-auth-link" href={forbidden ? "/" : "/admin"}>{forbidden ? "返回首页" : "重新加载"}</Link></section></main>;
  }

  const usagePercent = stats.usage.monthly_quota_total > 0 ? Math.min(100, Math.round((stats.usage.used / stats.usage.monthly_quota_total) * 100)) : 0;
  const statusEntries = Object.entries(stats.tasks.status_summary);
  return (
    <main className="admin-page">
      <header className="admin-header">
        <div><p className="eyebrow">PAPERFORGE OPERATIONS</p><h1>Admin Dashboard</h1><p className="admin-muted">最小运营视图 · 仅展示聚合统计，不包含租户或用户明细</p></div>
        <div className="admin-actions"><Link className="home-auth-link" href="/">返回工作台</Link><button className="home-auth-link logout-button" type="button" onClick={() => { localStorage.removeItem("paperforge_token"); localStorage.removeItem("paperforge_user"); window.location.href = "/login"; }}>退出登录</button></div>
      </header>

      <section className="admin-stat-grid" aria-label="系统核心统计">
        <StatCard label="Tenants" value={stats.tenants.total} note={`${stats.tenants.active} 个 active`} />
        <StatCard label="Users" value={stats.users.total} note="已注册账号" />
        <StatCard label="Tasks" value={stats.tasks.total} note="全部任务记录" />
        <StatCard label="Agent runs" value={stats.usage.used} note="本自然月使用量" />
      </section>

      <section className="admin-panel">
        <div className="admin-section-heading"><div><span className="card-label">TASK LIFECYCLE</span><h2>Task status summary</h2></div><span className="admin-badge">{stats.tasks.total} total</span></div>
        <div className="admin-status-list">{statusEntries.length ? statusEntries.map(([status, count]) => <div className="admin-status-row" key={status}><span>{STATUS_LABEL[status] || status}</span><strong>{count}</strong><div className="admin-bar"><i style={{ width: `${stats.tasks.total ? Math.round((count / stats.tasks.total) * 100) : 0}%` }} /></div></div>) : <p className="admin-muted">暂无任务记录。</p>}</div>
      </section>

      <section className="admin-panel">
        <div className="admin-section-heading"><div><span className="card-label">USAGE / QUOTA</span><h2>Usage summary</h2></div><span className="admin-badge">{stats.usage.metric}</span></div>
        <div className="admin-usage-grid"><div><span>本周期已使用</span><strong>{stats.usage.used}</strong></div><div><span>本周期剩余额度</span><strong>{stats.usage.monthly_quota_remaining}</strong></div><div><span>历史累计使用</span><strong>{stats.usage.all_time_used}</strong></div><div><span>租户月额度合计</span><strong>{stats.usage.monthly_quota_total}</strong></div></div>
        <div className="admin-bar admin-usage-bar"><i style={{ width: `${usagePercent}%` }} /></div>
        <p className="admin-muted">统计周期：{formatDate(stats.usage.period_start)} – {formatDate(stats.usage.period_end)} · 数据生成于 {formatDate(stats.generated_at)}</p>
      </section>
    </main>
  );
}

function StatCard({ label, value, note }: { label: string; value: number; note: string }) {
  return <div className="admin-stat-card"><span>{label}</span><strong>{value}</strong><small>{note}</small></div>;
}
