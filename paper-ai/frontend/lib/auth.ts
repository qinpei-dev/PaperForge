import type { AuthUser } from "../types";
import { apiUrl } from "./api-client";

const TOKEN_KEY = "paperforge_token";
const USER_KEY = "paperforge_user";
const ACTIVE_TENANT_KEY = "paperforge_active_tenant";
const WORKSPACE_KEY = "paperforge_workspace";
const PREVIEW_LOGOUT_KEY = "paperforge_preview_logout";
let previewLoginPromise: Promise<boolean> | null = null;

export function isPreviewEnvironment() {
  const configuredEnvironment = process.env.NEXT_PUBLIC_PAPERFORGE_APP_ENV || process.env.NODE_ENV;
  return ["local", "development", "dev", "preview"].includes(configuredEnvironment || "");
}

export function isPreviewAutoLoginEnabled() {
  return isPreviewEnvironment() && process.env.NEXT_PUBLIC_PAPERFORGE_PREVIEW_AUTO_LOGIN === "true";
}

export function authorizationHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem(TOKEN_KEY);
  const tenantId = localStorage.getItem(ACTIVE_TENANT_KEY);
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(tenantId ? { "X-Tenant-ID": tenantId } : {}),
  };
}

export function getAccessToken() {
  return typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY);
}

export function getActiveTenantId() {
  return typeof window === "undefined" ? null : localStorage.getItem(ACTIVE_TENANT_KEY);
}

export function getStoredAuthUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const rawUser = localStorage.getItem(USER_KEY);
    if (!rawUser) return null;
    const user = JSON.parse(rawUser) as unknown;
    return user && typeof user === "object" && "email" in user && typeof user.email === "string" && user.email.trim()
      ? { email: user.email, is_admin: "is_admin" in user && user.is_admin === true }
      : null;
  } catch {
    return null;
  }
}

export function storeAuthSession(accessToken: string, user: AuthUser, workspace: { id?: string; name?: string }) {
  if (typeof window !== "undefined") sessionStorage.removeItem(PREVIEW_LOGOUT_KEY);
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(WORKSPACE_KEY, JSON.stringify(workspace));
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(WORKSPACE_KEY);
}

export function suppressPreviewAutoLogin() {
  if (typeof window !== "undefined" && isPreviewEnvironment()) sessionStorage.setItem(PREVIEW_LOGOUT_KEY, "true");
}

export function tryPreviewAutoLogin(): Promise<boolean> {
  if (!isPreviewAutoLoginEnabled()) return Promise.resolve(false);
  if (typeof window !== "undefined" && sessionStorage.getItem(PREVIEW_LOGOUT_KEY) === "true") return Promise.resolve(false);
  if (getAccessToken()) return Promise.resolve(true);
  if (previewLoginPromise) return previewLoginPromise;

  previewLoginPromise = (async () => {
    try {
      const response = await fetch(apiUrl("/auth/preview-login"), { method: "POST", cache: "no-store" });
      if (!response.ok) return false;
      const data = await response.json() as { access_token?: unknown; user?: AuthUser; workspace_id?: unknown; workspace_name?: unknown };
      if (typeof data.access_token !== "string" || !data.user || typeof data.user.email !== "string") return false;
      if (sessionStorage.getItem(PREVIEW_LOGOUT_KEY) === "true") return false;
      storeAuthSession(data.access_token, data.user, {
        id: typeof data.workspace_id === "string" ? data.workspace_id : undefined,
        name: typeof data.workspace_name === "string" ? data.workspace_name : undefined,
      });
      return true;
    } catch {
      return false;
    }
  })().finally(() => {
    previewLoginPromise = null;
  });
  return previewLoginPromise;
}
