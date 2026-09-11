"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiUrl } from "../../lib/api-client";
import { isPreviewAutoLoginEnabled, storeAuthSession, tryPreviewAutoLogin } from "../../lib/auth";


export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isPreviewAutoLoginEnabled()) return;
    let cancelled = false;
    setLoading(true);
    void tryPreviewAutoLogin().then((ready) => {
      if (ready && !cancelled) router.replace("/dashboard");
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch(apiUrl("/auth/login"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "登录失败");
      storeAuthSession(data.access_token, data.user, { id: data.workspace_id, name: data.workspace_name });
      router.push("/dashboard");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return <main className="auth-page"><section className="auth-card"><p className="eyebrow">PAPERFORGE SaaS</p><h1>登录 PaperForge</h1><p className="muted">进入你的论文处理工作空间。</p><form onSubmit={submit} className="auth-form"><label>邮箱<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>密码<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>{error && <p className="error-text">{error}</p>}<button type="submit" disabled={loading}>{loading ? "登录中…" : "登录"}</button></form><p className="auth-switch">还没有账号？ <Link href="/register">注册</Link></p></section></main>;
}
