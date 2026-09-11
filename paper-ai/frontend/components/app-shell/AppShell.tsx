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
    </div>
  );
}
