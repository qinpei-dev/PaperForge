"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiUrl } from "../../lib/api-client";
import { storeAuthSession } from "../../lib/auth";


export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch(apiUrl("/auth/register"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "注册失败");
      storeAuthSession(data.access_token, data.user, { id: data.workspace_id, name: data.workspace_name });
      router.push("/dashboard");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "注册失败");
    } finally {
      setLoading(false);
    }
  }

  return <main className="auth-page"><section className="auth-card"><p className="eyebrow">PAPERFORGE SaaS</p><h1>创建账号</h1><p className="muted">注册后会自动创建默认 Workspace。</p><form onSubmit={submit} className="auth-form"><label>邮箱<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>密码<input type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>{error && <p className="error-text">{error}</p>}<button type="submit" disabled={loading}>{loading ? "创建中…" : "注册"}</button></form><p className="auth-switch">已有账号？ <Link href="/login">登录</Link></p></section></main>;
}
