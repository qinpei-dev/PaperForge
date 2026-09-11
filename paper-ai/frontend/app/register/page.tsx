"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiUrl } from "../../lib/api-client";
import { storeAuthSession } from "../../lib/auth";
import { userFacingError } from "../../lib/error-messages";
import { AuthLayout } from "../../components/auth/AuthLayout";
import styles from "../../components/auth/AuthLayout.module.css";

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
      if (!response.ok) throw new Error(userFacingError(data.detail, "注册失败，请检查输入后重试。"));
      storeAuthSession(data.access_token, data.user, { id: data.workspace_id, name: data.workspace_name });
      router.push("/dashboard");
    } catch (reason) {
      setError(userFacingError(reason, "注册暂时不可用，请稍后重试。"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      eyebrow="开始使用 PaperForge"
      title="创建你的工作区"
      description="注册后会自动创建默认 Workspace，开始处理论文。"
      switchPrompt="已有账号？"
      switchLabel="登录"
      switchHref="/login"
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
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="new-password"
            required
          />
        </label>
        {error && <p className={styles.error} role="alert">{error}</p>}
        <button className={styles.submitButton} type="submit" disabled={loading}>
          {loading ? "创建中…" : "注册"}
        </button>
      </form>
    </AuthLayout>
  );
}
