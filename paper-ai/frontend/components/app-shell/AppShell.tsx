"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { apiUrl } from "../../lib/api-client";
import { authorizationHeaders, clearAuthSession, getAccessToken, getStoredAuthUser, isPreviewEnvironment, suppressPreviewAutoLogin, tryPreviewAutoLogin } from "../../lib/auth";
import type { AuthUser, WorkspaceOption } from "../../types";

type NavigationItem = { href: string; label: string; icon: string };

const navigation: NavigationItem[] = [
  { href: "/dashboard", label: "概览", icon: "▦" },
  { href: "/tasks", label: "任务", icon: "◷" },
  { href: "/templates", label: "模板", icon: "▤" },
  { href: "/settings", label: "设置", icon: "⚙" },
];

function isActivePath(pathname: string, href: string) {
  return href === "/dashboard" ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const menuRef = useRef<HTMLDivElement>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceOption[]>([]);
  const [workspaceLoadState, setWorkspaceLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [activeTenantId, setActiveTenantId] = useState("");
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackCategory, setFeedbackCategory] = useState("bug");
  const [feedbackDescription, setFeedbackDescription] = useState("");
  const [feedbackContact, setFeedbackContact] = useState("");
  const [feedbackState, setFeedbackState] = useState<"idle" | "submitting" | "success" | "error">("idle");

  useEffect(() => {
    let cancelled = false;
    async function bootstrapAuthAndWorkspaces() {
      setWorkspaceLoadState("loading");
      const previewLoggedIn = !getAccessToken() && await tryPreviewAutoLogin();
      if (!getAccessToken()) {
        if (!cancelled) {
          setWorkspaceLoadState("error");
          router.replace("/login");
        }
        return;
      }
      if (!cancelled) setUser(getStoredAuthUser());
      if (previewLoggedIn && pathname !== "/dashboard") {
        router.replace("/dashboard");
        return;
      }
      try {
        const response = await fetch(apiUrl("/workspaces"), { cache: "no-store", headers: authorizationHeaders() });
        const data: unknown = await response.json();
        if (!response.ok || !Array.isArray(data) || cancelled) {
          if (!cancelled) {
            setWorkspaceLoadState("error");
            setWorkspaces([]);
          }
          return;
        }
        const options = data.filter((item): item is WorkspaceOption => {
          if (!item || typeof item !== "object") return false;
          const record = item as Record<string, unknown>;
          return typeof record.tenant_id === "string" && typeof record.name === "string" && ["owner", "admin", "member"].includes(String(record.role));
        });
        const savedTenantId = localStorage.getItem("paperforge_active_tenant");
        const nextTenantId = options.some((item) => item.tenant_id === savedTenantId) ? savedTenantId || "" : options[0]?.tenant_id || "";
        if (nextTenantId) localStorage.setItem("paperforge_active_tenant", nextTenantId);
        if (!cancelled) {
          setWorkspaces(options);
          setActiveTenantId(nextTenantId);
          setWorkspaceLoadState("ready");
        }
      } catch {
        if (!cancelled) {
          setWorkspaces([]);
          setWorkspaceLoadState("error");
        }
      }
    }
    void bootstrapAuthAndWorkspaces();
    return () => { cancelled = true; };
  }, [pathname, router]);

  useEffect(() => {
    function closeMenu(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setIsUserMenuOpen(false);
    }
    document.addEventListener("mousedown", closeMenu);
    return () => document.removeEventListener("mousedown", closeMenu);
  }, []);

  function switchWorkspace(tenantId: string) {
    localStorage.setItem("paperforge_active_tenant", tenantId);
    const nextWorkspace = workspaces.find((workspace) => workspace.tenant_id === tenantId);
    if (nextWorkspace) localStorage.setItem("paperforge_workspace", JSON.stringify({ id: nextWorkspace.tenant_id, name: nextWorkspace.name }));
    setActiveTenantId(tenantId);
    router.replace("/dashboard");
    router.refresh();
  }

  function logout() {
    suppressPreviewAutoLogin();
    clearAuthSession();
    localStorage.removeItem("paperforge_active_tenant");
    router.push("/login");
  }

  async function submitFeedback(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!feedbackDescription.trim() || feedbackState === "submitting") return;
    setFeedbackState("submitting");
    const taskMatch = pathname.match(/^\/tasks\/([^/]+)/);
    try {
      const response = await fetch(apiUrl("/feedback"), {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authorizationHeaders() },
        body: JSON.stringify({ category: feedbackCategory, description: feedbackDescription.trim(), contact: feedbackContact.trim() || null, route: pathname, task_id: taskMatch?.[1] || null }),
      });
      if (!response.ok) throw new Error("feedback request failed");
      setFeedbackState("success");
      setFeedbackDescription("");
      setFeedbackContact("");
    } catch {
      setFeedbackState("error");
    }
  }

  const activeWorkspace = workspaces.find((workspace) => workspace.tenant_id === activeTenantId);
  return (
    <div className="app-shell">
      <aside className="app-sidebar" aria-label="工作区导航">
        <Link className="app-brand" href="/dashboard"><span className="app-brand-mark">P</span><span>PaperForge</span></Link>
        <p className="app-sidebar-label">WORKSPACE</p>
        <nav className="app-nav">
          {navigation.map((item) => <Link className={`app-nav-link${isActivePath(pathname, item.href) ? " active" : ""}`} href={item.href} key={item.href}><span aria-hidden="true">{item.icon}</span>{item.label}</Link>)}
        </nav>
        <div className="app-sidebar-footer"><Link href="/tasks/new" className="app-new-task">＋ 新建论文处理</Link></div>
      </aside>
      <div className="app-content">
        <header className="app-topbar">
          <div className="app-topbar-context"><span className="app-topbar-kicker">PAPERFORGE</span><strong>{activeWorkspace?.name || "我的工作空间"}</strong></div>
          <div className="app-topbar-actions">
            {isPreviewEnvironment() ? <span className="preview-environment-badge">Preview Environment</span> : null}
            <label className="app-workspace-switcher"><span className="sr-only">切换工作空间</span><select aria-label="切换工作空间" value={activeTenantId} disabled={!workspaces.length} onChange={(event) => switchWorkspace(event.target.value)}>{workspaces.length ? workspaces.map((workspace) => <option value={workspace.tenant_id} key={workspace.tenant_id}>{workspace.name}</option>) : <option>{workspaceLoadState === "error" ? "工作区暂不可用" : workspaceLoadState === "ready" ? "暂无可用工作区" : "加载工作空间…"}</option>}</select></label>
            <div className="app-user-menu" ref={menuRef}><button className="app-user-trigger" type="button" aria-expanded={isUserMenuOpen} onClick={() => setIsUserMenuOpen((open) => !open)}><span className="app-avatar">{user?.email?.slice(0, 1).toUpperCase() || "P"}</span><span className="app-user-email">{user?.email || "账户"}</span><span aria-hidden="true">⌄</span></button>{isUserMenuOpen ? <div className="app-user-popover"><p>{user?.email || "当前账户"}</p><Link href="/settings" onClick={() => setIsUserMenuOpen(false)}>工作区设置</Link>{user?.is_admin ? <Link href="/admin">运营后台</Link> : null}<button type="button" onClick={logout}>退出登录</button></div> : null}</div>
          </div>
        </header>
        <main className="app-main">{children}</main>
      </div>
      <button className="feedback-fab" type="button" onClick={() => { setFeedbackOpen(true); setFeedbackState("idle"); }} aria-label="提交反馈">遇到问题？反馈</button>
      {feedbackOpen ? <div className="feedback-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setFeedbackOpen(false); }}><section className="feedback-modal" role="dialog" aria-modal="true" aria-labelledby="feedback-title"><div className="feedback-modal-heading"><div><p className="eyebrow">CONTROLLED BETA</p><h2 id="feedback-title">告诉我们哪里可以更好</h2></div><button className="feedback-close" type="button" onClick={() => setFeedbackOpen(false)} aria-label="关闭反馈">×</button></div>{feedbackState === "success" ? <div className="feedback-success"><strong>反馈已提交，感谢你的帮助。</strong><button className="app-primary-link" type="button" onClick={() => setFeedbackOpen(false)}>完成</button></div> : <form className="feedback-form" onSubmit={submitFeedback}><label>问题类型<select value={feedbackCategory} onChange={(event) => setFeedbackCategory(event.target.value)}><option value="bug">Bug / 功能异常</option><option value="slow">速度慢</option><option value="format">格式修改问题</option><option value="ai">AI 修改问题</option><option value="suggestion">使用建议</option><option value="other">其他</option></select></label><label>问题描述 <span>必填</span><textarea required minLength={1} maxLength={5000} rows={5} value={feedbackDescription} onChange={(event) => setFeedbackDescription(event.target.value)} placeholder="请描述你遇到的情况，越具体越有帮助。" /></label><label>联系方式 <span>选填</span><input maxLength={320} value={feedbackContact} onChange={(event) => setFeedbackContact(event.target.value)} placeholder="微信、邮箱或其他联系方式" /></label>{feedbackState === "error" ? <p className="feedback-error">提交失败，请稍后重试。</p> : null}<button className="app-primary-link feedback-submit" type="submit" disabled={feedbackState === "submitting"}>{feedbackState === "submitting" ? "提交中…" : "提交反馈"}</button></form>}</section></div> : null}
    </div>
  );
}
