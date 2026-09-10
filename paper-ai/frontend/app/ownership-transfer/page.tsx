"use client";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

function OwnershipTransferAccept() {
  const token = useSearchParams().get("token") || "";
  const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);
  async function accept() {
    if (!token) { setMessage("邀请链接缺少 transfer token。 "); return; }
    setBusy(true);
    try { const auth = localStorage.getItem("paperforge_token"); const response = await fetch(`${API_BASE}/tenant-ownership-transfers/${encodeURIComponent(token)}/accept`, { method: "POST", headers: auth ? { Authorization: `Bearer ${auth}` } : {} }); const data = await response.json().catch(() => ({})); setMessage(response.ok ? "Ownership 已转移。请返回首页刷新 Workspace 角色。" : String(data.detail || "无法接受 ownership transfer。")); } finally { setBusy(false); }
  }
  return <main className="auth-page"><section className="auth-card"><p className="eyebrow">PaperForge</p><h1>接受 Workspace Ownership</h1><p>接受后，你将成为该 Workspace 的 Owner；原 Owner 会降为 Admin。此操作需要你明确确认。</p><button type="button" disabled={busy || !token} onClick={() => void accept()}>{busy ? "处理中…" : "接受 Ownership"}</button>{message ? <p>{message}</p> : null}</section></main>;
}

export default function OwnershipTransferAcceptPage() { return <Suspense fallback={<main className="auth-page">正在加载 Ownership Transfer…</main>}><OwnershipTransferAccept /></Suspense>; }
