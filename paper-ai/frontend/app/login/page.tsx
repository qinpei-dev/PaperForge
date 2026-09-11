"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiUrl } from "../../lib/api-client";
import { isPreviewAutoLoginEnabled, storeAuthSession, tryPreviewAutoLogin } from "../../lib/auth";
import { userFacingError } from "../../lib/error-messages";
import { AuthLayout } from "../../components/auth/AuthLayout";
import styles from "../../components/auth/AuthLayout.module.css";

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
      if (!response.ok) throw new Error(userFacingError(data.detail, "登录失败，请检查账号信息后重试。"));
      storeAuthSession(data.access_token, data.user, { id: data.workspace_id, name: data.workspace_name });
      router.push("/dashboard");
    } catch (reason) {
      setError(userFacingError(reason, "登录暂时不可用，请稍后重试。"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      eyebrow="欢迎回来"
      title="登录 PaperForge"
      description="继续进入你的论文处理工作空间。"
      switchPrompt="没有账号？"
      switchLabel="注册"
      switchHref="/register"
    >
      <form onSubmit={submit} className={styles.form}>
        <label className={styles.field}>
          邮箱
          <input
            className={styles.input}
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <label className={styles.field}>
          密码
          <input
            className={styles.input}
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && <p className={styles.error} role="alert">{error}</p>}
        <button className={styles.submitButton} type="submit" disabled={loading}>
          {loading ? "登录中…" : "登录"}
        </button>
      </form>
    </AuthLayout>
  );
}
