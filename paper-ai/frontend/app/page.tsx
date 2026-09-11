"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiUrl } from "../lib/api-client";
import { authorizationHeaders, getStoredAuthUser, suppressPreviewAutoLogin } from "../lib/auth";

type AgentStep = { name: string; status: "running" | "done" | "error"; message: string };
type AgentTraceItem = {
  step?: string;
  status?: string;
  duration_ms?: number;
  fallback_used?: boolean;
  message?: string;
};
type RuntimeTraceItem = AgentTraceItem & { state?: string };
type ScoreDimension = { key: string; label: string; score: number; group: "local" | "ai"; status: string; issues: string[] };
type Classification = {
  document_type: string;
  label: string;
  confidence: number;
  matched_features: string[];
  warning: string;
  requires_confirmation: boolean;
};
type ScoreBreakdown = {
  format_score?: number;
  risk_score?: number;
  ai_language_score?: number | null;
  local_score: number;
  ai_score: number | null;
  final_score: number;
  score_confidence?: number;
  score_explanation?: string;
  ai_used: boolean;
  ai_added_value: string[];
};
type ReferenceCheck = {
  has_reference_section: boolean;
  reference_count: number;
  citation_count: number;
  reference_numbers: number[];
  citation_numbers: number[];
  missing_reference_numbers: number[];
  uncited_reference_numbers: number[];
  duplicate_reference_numbers: number[];
  numbering_gaps: number[];
  issues: string[];
};
type FigureTableCheck = {
  figure_numbers: number[];
  table_numbers: number[];
  figure_gaps: number[];
  table_gaps: number[];
  duplicate_figures: number[];
  duplicate_tables: number[];
  missing_figure_captions: string[];
  missing_table_captions: string[];
  missing_referenced_figures: number[];
  missing_referenced_tables: number[];
  issues: string[];
};
type Analysis = {
  reference_check?: ReferenceCheck;
  figure_table_check?: FigureTableCheck;
  report: {
    score: number;
    summary: string;
    breakdown: ScoreDimension[];
    local_breakdown: ScoreDimension[];
    ai_breakdown: ScoreDimension[];
    score_breakdown: ScoreBreakdown;
    recommendations: string[];
  };
};
type RepeatRisk = { level: string; score: number; suggestions: string[] };
type ScoreComparison = { key: string; label: string; before: number; after: number; delta: number; status: string };
type FormatDiffSummary = {
  before_score: number;
  after_score: number;
  score_delta: number;
  auto_fix_count: number;
  changed_dimension_count: number;
  needs_manual_review_count: number;
  format_change_count: number;
  language_change_count: number;
  summary: string;
};
type ModificationReport = {
  summary: string;
  fixed_issues: string[];
  before_after: ScoreComparison[];
  format_diff_summary: FormatDiffSummary;
  changed_dimensions: ScoreComparison[];
  score_delta_by_dimension: Record<string, number>;
  auto_fix_count: number;
  needs_manual_review_count: number;
  change_counts: { format_changes: number; language_changes: number; total: number };
  unresolved_issues: string[];
  manual_review_items: string[];
  score_explanation?: string;
  template_used: string | null;
};
type Workflow = { current_state?: string; replan_count?: number; trace?: AgentTraceItem[] };
type Verification = {
  passed?: boolean;
  verified_rules?: string[];
  passed_rules?: string[];
  failed_rules?: string[];
  structural_integrity?: { status?: string; unsafe_reasons?: unknown[] };
  score?: number;
  verification_score?: number;
  verification_summary?: { total?: number; verified?: number; failed?: number; unsupported?: number };
  conflict_summary?: { conflicts?: number };
};
type Decision = { action?: string; reason?: string; risk?: string; evidence?: unknown[] };
type HumanReview = {
  reason?: string;
  affected_targets?: string[];
  related_rule_ids?: string[];
  suggested_action?: string;
  items?: unknown[];
};
type ReplanHistory = { plan?: { plan_id?: string }; decision?: Decision };
type ProvenanceChange = { action?: string; rule_type?: string; target?: { semantic_role?: string; paragraph_index?: number }; before?: unknown; expected?: unknown; after?: unknown; verification_scope?: string; verification_status?: string; verification_evidence?: { reason?: string; actual?: unknown } };
type Provenance = { changes?: ProvenanceChange[]; summary?: { planned_steps?: number; executed_steps?: number; unsupported_steps?: number; change_count?: number; conflicts?: number; verification?: { total?: number; verified?: number; failed?: number; unsupported?: number } } };
type ContentIssue = { issue_id?: string; paragraph_index?: number; issue_type?: string; original_text?: string; suggested_text?: string; reason?: string; action_policy?: string; source?: string; verification_status?: string; status?: string };
type ContentReview = { issues?: ContentIssue[]; counts?: { AUTO_FIX?: number; SUGGEST_ONLY?: number; HITL_REQUIRED?: number }; provenance?: { auto_fixes?: ContentIssue[]; suggestions?: ContentIssue[]; accepted?: ContentIssue[]; hitl?: ContentIssue[] }; verification?: { total?: number; verified?: number; failed?: number } };
type ReviewSummary = { formatting?: Record<string, number>; content?: Record<string, number>; overall?: Record<string, number> };
type TemplateOption = { id?: string; template_id: string; name: string; school: string; document_type: string; version: string; status: string; scope?: string; original_filename?: string | null };
type TemplateIdentity = { id: string; version: string; name: string; school?: string; document_type?: string };
type AgentResult = {
  status: "ok" | "requires_confirmation";
  mode?: string;
  requires_confirmation: boolean;
  classification: Classification;
  steps: AgentStep[];
  before_score: number;
  after_score: number;
  score_breakdown: ScoreBreakdown;
  repeat_risk: RepeatRisk;
  download_url: string;
  filename: string;
  after_analysis: Analysis;
  modification_report: ModificationReport;
  agent_trace?: AgentTraceItem[];
  agent_trace_detail?: Record<string, unknown>;
  task_id?: string;
  task_state_path?: string;
  workflow?: Workflow | null;
  verification?: Verification | null;
  decision?: Decision | null;
  human_review?: HumanReview | null;
  replan_history?: ReplanHistory[];
  execution_plan?: { plan_id?: string };
  runtime_trace?: RuntimeTraceItem[];
  provenance?: Provenance | null;
  content_review?: ContentReview | null;
  review_summary?: ReviewSummary;
  change_evidence?: unknown[];
  pending_actions?: ContentIssue[];
  content_score?: { before_content_score?: number; after_content_score?: number; delta?: number; verified_changes_count?: number; unresolved_issue_count?: number; score_delta_reasons?: string[] };
  template?: TemplateIdentity;
};
type PreviewResult = { title: string; html: string };
type AuthUser = { email: string; is_admin?: boolean };
type MembershipInfo = { tenant_id: string; role: "owner" | "admin" | "member"; permissions: string[] };
type WorkspaceOption = { tenant_id: string; name: string; role: "owner" | "admin" | "member" };
type TenantMember = { user_id: string; email: string; role: "owner" | "admin" | "member" };
type TenantInvitation = { id: string; email: string; role: "admin" | "member"; status: string; expires_at: string };
type OwnershipTransfer = { id: string; to_user_id: string; status: string; expires_at: string; accept_url?: string };
type AuditEvent = { id: string; event_type: string; target_id?: string; created_at: string; metadata?: Record<string, unknown> };
type UsageSummary = {
  tenant_id: string;
  metric: string;
  period_start: string;
  period_end: string;
  quota: { limit: number };
  usage: { used: number };
  remaining: number;
};

const defaultSteps = ["识别文档类型", "读取论文", "分析本地格式", "识别模板格式", "修复标题样式", "AI增强审校", "重复风险预检", "最终复查", "生成最终报告"];

function isAuthenticationFailure(response: Response) {
  return response.status === 401 || response.status === 403;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

async function readResponseData(response: Response): Promise<Record<string, unknown>> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return { detail: text };
  }
}

function apiErrorMessage(data: Record<string, unknown>, fallback: string) {
  const envelopeError = isRecord(data.error) ? data.error : null;
  const envelopeMessage = envelopeError && isRecord(envelopeError.message) ? envelopeError.message : null;
  const detailRecord = isRecord(data.detail) ? data.detail : null;
  const quotaError = envelopeMessage?.code === "QUOTA_EXCEEDED" ? envelopeMessage : detailRecord?.code === "QUOTA_EXCEEDED" ? detailRecord : null;
  if (quotaError) {
    const usage = isRecord(quotaError.usage) ? quotaError.usage : null;
    const quota = usage && isRecord(usage.quota) ? usage.quota : null;
    const current = usage && isRecord(usage.usage) ? usage.usage : null;
    const limit = typeof quota?.limit === "number" ? quota.limit : null;
    const used = typeof current?.used === "number" ? current.used : null;
    const remaining = usage && typeof usage.remaining === "number" ? usage.remaining : null;
    const periodEnd = usage && typeof usage.period_end === "string" ? usage.period_end : "";
    const resetHint = periodEnd ? `，本周期将于 ${new Date(periodEnd).toLocaleDateString("zh-CN")} 结束` : "";
    if (limit !== null && used !== null) return `本月 Agent 运行额度已用尽（${used}/${limit}），剩余 ${remaining ?? 0} 次${resetHint}。`;
    return "本月 Agent 运行额度已用尽，请稍后再试。";
  }
  const detail = data.detail;
  if (typeof detail === "string") return detail;
  if (isRecord(detail)) {
    const failedStep = typeof detail.failed_step === "string" ? detail.failed_step : "";
    const error = typeof detail.error === "string" ? detail.error : "";
    if (failedStep || error) return failedStep ? `Agent 在「${failedStep}」失败：${error || "未返回详细错误"}` : error;
    const message = typeof detail.message === "string" ? detail.message : "";
    if (message) return message;
  }
  const message = typeof data.message === "string" ? data.message : "";
  return message || fallback;
}

function parseUsageSummary(data: Record<string, unknown>): UsageSummary | null {
  const quota = isRecord(data.quota) ? data.quota : null;
  const usage = isRecord(data.usage) ? data.usage : null;
  const limit = typeof quota?.limit === "number" ? quota.limit : typeof quota?.agent_runs === "number" ? quota.agent_runs : null;
  const used = typeof usage?.used === "number" ? usage.used : typeof usage?.agent_runs === "number" ? usage.agent_runs : null;
  if (typeof data.tenant_id !== "string" || limit === null || used === null || typeof data.remaining !== "number" || typeof data.period_start !== "string" || typeof data.period_end !== "string") return null;
  return { tenant_id: data.tenant_id, metric: typeof data.metric === "string" ? data.metric : "agent_run", period_start: data.period_start, period_end: data.period_end, quota: { limit }, usage: { used }, remaining: data.remaining };
}

function networkErrorMessage(error: unknown, fallback: string, requestUrl?: string) {
  const suffix = requestUrl ? `请求地址：${requestUrl}。请确认后端服务地址和端口可访问。` : "";
  if (error instanceof Error && error.message) {
    return suffix ? `${fallback}：${error.message}。${suffix}` : `${fallback}（${error.message}）`;
  }
  return suffix ? `${fallback}。${suffix}` : fallback;
}

export default function Home() {
  const router = useRouter();
  const [paperFile, setPaperFile] = useState<File | null>(null);
  const [paperFilename, setPaperFilename] = useState("");
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [templateFilename, setTemplateFilename] = useState("");
  const [templates, setTemplates] = useState<TemplateOption[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [managedTemplateFile, setManagedTemplateFile] = useState<File | null>(null);
  const [managedTemplateName, setManagedTemplateName] = useState("");
  const [managedTemplateVersion, setManagedTemplateVersion] = useState("1.0");
  const [managedTemplateSchool, setManagedTemplateSchool] = useState("通用");
  const [managedTemplateType, setManagedTemplateType] = useState("academic_paper");
  const [uploadingTemplate, setUploadingTemplate] = useState(false);
  const [agentMode, setAgentMode] = useState<"local" | "ai">("ai");
  const [classification, setClassification] = useState<Classification | null>(null);
  const [confirmedNonPaper, setConfirmedNonPaper] = useState(false);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [previewError, setPreviewError] = useState("");
  const [message, setMessage] = useState("");
  const [running, setRunning] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [membership, setMembership] = useState<MembershipInfo | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceOption[]>([]);
  const [activeTenantId, setActiveTenantId] = useState("");
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [usageLoading, setUsageLoading] = useState(false);
  const [usageError, setUsageError] = useState("");
  const [members, setMembers] = useState<TenantMember[]>([]);
  const [invitations, setInvitations] = useState<TenantInvitation[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"admin" | "member">("member");
  const [invitationLink, setInvitationLink] = useState("");
  const [tenantName, setTenantName] = useState("");
  const [ownershipTransfer, setOwnershipTransfer] = useState<OwnershipTransfer | null>(null);
  const [transferTargetId, setTransferTargetId] = useState("");
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [authenticationRequired, setAuthenticationRequired] = useState(false);

  const visibleSteps = useMemo(() => {
    if (result?.steps.length) {
      const previewStep = preview ? [{ name: "生成在线预览", status: "done" as const, message: "已生成可在线查看的论文预览。" }] : [];
      return [...result.steps, ...previewStep];
    }
    return defaultSteps.map((name) => ({ name, status: "running" as const, message: "等待 Agent 调度" }));
  }, [result, preview]);

  const hasPaper = Boolean(paperFile);
  const needsConfirmation = classification?.requires_confirmation === true;
  const canRun = hasPaper && (!needsConfirmation || confirmedNonPaper);
  const buttonDisabled = running || !canRun;

  useEffect(() => {
    setAuthUser(getStoredAuthUser());
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadWorkspaces() {
      if (!authUser) { setWorkspaces([]); setActiveTenantId(""); return; }
      try {
        const response = await fetch(apiUrl("/workspaces"), { cache: "no-store", headers: authorizationHeaders() });
        const data = await readResponseData(response);
        const options = Array.isArray(data) ? data.filter((item): item is WorkspaceOption => isRecord(item) && typeof item.tenant_id === "string" && typeof item.name === "string" && (item.role === "owner" || item.role === "admin" || item.role === "member")) : [];
        if (cancelled) return;
        setWorkspaces(options);
        const saved = localStorage.getItem("paperforge_active_tenant");
        const next = options.find((item) => item.tenant_id === saved)?.tenant_id ?? options[0]?.tenant_id ?? "";
        if (next) localStorage.setItem("paperforge_active_tenant", next); else localStorage.removeItem("paperforge_active_tenant");
        setActiveTenantId(next);
      } catch { if (!cancelled) { setWorkspaces([]); setActiveTenantId(""); } }
    }
    void loadWorkspaces();
    return () => { cancelled = true; };
  }, [authUser]);

  useEffect(() => {
    let cancelled = false;
    async function loadMembership() {
      if (!authUser) { setMembership(null); return; }
      try {
        const response = await fetch(apiUrl("/tenants/membership/me"), { cache: "no-store", headers: authorizationHeaders() });
        const data = await readResponseData(response);
        if (response.ok && !cancelled && typeof data.tenant_id === "string" && (data.role === "owner" || data.role === "admin" || data.role === "member")) {
          setMembership({ tenant_id: data.tenant_id, role: data.role, permissions: Array.isArray(data.permissions) ? data.permissions.filter((item): item is string => typeof item === "string") : [] });
        }
      } catch {
        // Role display is advisory UX; server-side RBAC remains authoritative.
      }
    }
    void loadMembership();
    return () => { cancelled = true; };
  }, [authUser, activeTenantId, result]);

  useEffect(() => {
    let cancelled = false;
    async function loadTemplates() {
      try {
        const response = await fetch(apiUrl("/templates"), { cache: "no-store", headers: authorizationHeaders() });
        const data = await readResponseData(response);
        if (!response.ok || cancelled) {
          if (isAuthenticationFailure(response) && !cancelled) requireAuthentication();
          return;
        }
        const options = Array.isArray(data.templates) ? data.templates as TemplateOption[] : [];
        setTemplates(options);
        const defaultId = typeof data.default_template_id === "string" ? data.default_template_id : options[0]?.template_id;
        const defaultVersion = typeof data.default_template_version === "string" ? data.default_template_version : options.find((item) => item.template_id === defaultId)?.version;
        if (defaultId && defaultVersion) setTemplateId(`${defaultId}@@${defaultVersion}`);
      } catch {
        // The legacy upload/default flow remains usable if registry discovery is unavailable.
      }
    }
    void loadTemplates();
    return () => { cancelled = true; };
  }, [activeTenantId, authUser]);

  useEffect(() => {
    let cancelled = false;
    async function loadUsage() {
      if (!authUser || !activeTenantId) {
        setUsage(null);
        setUsageError("");
        setUsageLoading(false);
        return;
      }
      setUsageLoading(true);
      setUsageError("");
      try {
        const requestUrl = apiUrl("/usage");
        const response = await fetch(requestUrl, { cache: "no-store", headers: authorizationHeaders() });
        const data = await readResponseData(response);
        if (cancelled) return;
        if (!response.ok) {
          if (isAuthenticationFailure(response)) requireAuthentication();
          setUsage(null);
          setUsageError(apiErrorMessage(data, "Usage 数据暂时无法加载。"));
          return;
        }
        const parsed = parseUsageSummary(data);
        if (!parsed) {
          setUsage(null);
          setUsageError("Usage 数据格式异常，请稍后重试。");
          return;
        }
        setUsage(parsed);
      } catch (error) {
        if (!cancelled) {
          setUsage(null);
          setUsageError(networkErrorMessage(error, "Usage 数据暂时无法加载", apiUrl("/usage")));
        }
      } finally {
        if (!cancelled) setUsageLoading(false);
      }
    }
    void loadUsage();
    return () => { cancelled = true; };
  }, [authUser, activeTenantId]);

  useEffect(() => {
    let cancelled = false;
    async function loadGovernance() {
      if (!authUser || !activeTenantId || !membership) { setMembers([]); setInvitations([]); return; }
      try {
        const memberResponse = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/members`), { cache: "no-store", headers: authorizationHeaders() });
        const memberData = await readResponseData(memberResponse);
        if (memberResponse.ok && Array.isArray(memberData) && !cancelled) setMembers(memberData as unknown as TenantMember[]);
        if (membership.role === "owner") {
          const invitationResponse = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/invitations`), { cache: "no-store", headers: authorizationHeaders() });
          const invitationData = await readResponseData(invitationResponse);
          if (invitationResponse.ok && Array.isArray(invitationData) && !cancelled) setInvitations(invitationData as unknown as TenantInvitation[]);
          const transferResponse = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/ownership-transfer`), { cache: "no-store", headers: authorizationHeaders() });
          if (transferResponse.ok && !cancelled) setOwnershipTransfer(await transferResponse.json() as OwnershipTransfer | null);
        } else if (!cancelled) setInvitations([]);
        if (membership.role === "owner" || membership.role === "admin") {
          const auditResponse = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/audit-events?limit=8`), { cache: "no-store", headers: authorizationHeaders() });
          const auditData = await readResponseData(auditResponse); if (auditResponse.ok && Array.isArray(auditData.events) && !cancelled) setAuditEvents(auditData.events as unknown as AuditEvent[]);
        } else if (!cancelled) setAuditEvents([]);
      } catch { if (!cancelled) { setMembers([]); setInvitations([]); } }
    }
    void loadGovernance();
    return () => { cancelled = true; };
  }, [authUser, activeTenantId, membership?.role]);

  function requireAuthentication() {
    setAuthenticationRequired(true);
    setMessage("请先登录后再继续。");
  }

  function logout() {
    suppressPreviewAutoLogin();
    localStorage.removeItem("paperforge_token");
    localStorage.removeItem("paperforge_user");
    localStorage.removeItem("paperforge_workspace");
    localStorage.removeItem("paperforge_active_tenant");
    setAuthUser(null);
    setMembership(null);
    setUsage(null);
    setUsageError("");
    setAuthenticationRequired(false);
    setMessage("已退出登录。");
  }

  function switchWorkspace(tenantId: string) {
    localStorage.setItem("paperforge_active_tenant", tenantId);
    setActiveTenantId(tenantId);
    setMembership(null); setTemplates([]); setMembers([]); setInvitations([]); setInvitationLink(""); setOwnershipTransfer(null); setAuditEvents([]); setTenantName("");
    setUsage(null); setUsageError("");
    setResult(null); setPreview(null); setClassification(null); setMessage("已切换 Workspace，正在加载该空间的数据。");
  }

  async function updateMember(member: TenantMember, role: "admin" | "member") {
    if (!activeTenantId || member.role === role) return;
    const response = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/members/${encodeURIComponent(member.user_id)}`), { method: "PATCH", headers: { ...authorizationHeaders(), "Content-Type": "application/json" }, body: JSON.stringify({ role }) });
    const data = await readResponseData(response);
    if (!response.ok) { setMessage(apiErrorMessage(data, "成员角色更新失败。")); return; }
    setMembers((items) => items.map((item) => item.user_id === member.user_id ? data as unknown as TenantMember : item));
  }

  async function removeMember(member: TenantMember) {
    if (!activeTenantId) return;
    const response = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/members/${encodeURIComponent(member.user_id)}`), { method: "DELETE", headers: authorizationHeaders() });
    if (!response.ok) { setMessage(apiErrorMessage(await readResponseData(response), "成员移除失败。")); return; }
    setMembers((items) => items.filter((item) => item.user_id !== member.user_id));
  }

  async function createInvitation() {
    if (!activeTenantId || !inviteEmail.trim()) return;
    const response = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/invitations`), { method: "POST", headers: { ...authorizationHeaders(), "Content-Type": "application/json" }, body: JSON.stringify({ email: inviteEmail.trim(), role: inviteRole }) });
    const data = await readResponseData(response);
    if (!response.ok) { setMessage(apiErrorMessage(data, "创建邀请失败。")); return; }
    const invitation = data as unknown as TenantInvitation & { invitation_url?: string };
    setInvitations((items) => [invitation, ...items]); setInvitationLink(invitation.invitation_url ? `${window.location.origin}${invitation.invitation_url}` : ""); setInviteEmail("");
  }

  async function addExistingMember() {
    if (!activeTenantId || !inviteEmail.trim()) return;
    const response = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/members`), { method: "POST", headers: { ...authorizationHeaders(), "Content-Type": "application/json" }, body: JSON.stringify({ email: inviteEmail.trim(), role: inviteRole }) });
    const data = await readResponseData(response);
    if (!response.ok) { setMessage(apiErrorMessage(data, "添加成员失败；对方可能尚未注册。")); return; }
    setMembers((items) => [...items, data as unknown as TenantMember]); setInviteEmail(""); setMessage("已添加现有用户为 Workspace 成员。");
  }

  async function revokeInvitation(invitation: TenantInvitation) {
    if (!activeTenantId) return;
    const response = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/invitations/${encodeURIComponent(invitation.id)}`), { method: "DELETE", headers: authorizationHeaders() });
    if (!response.ok) { setMessage(apiErrorMessage(await readResponseData(response), "撤销邀请失败。")); return; }
    setInvitations((items) => items.map((item) => item.id === invitation.id ? { ...item, status: "revoked" } : item));
  }

  async function saveTenantName() { if (!activeTenantId || !tenantName.trim()) return; const response = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}`), { method: "PATCH", headers: { ...authorizationHeaders(), "Content-Type": "application/json" }, body: JSON.stringify({ display_name: tenantName.trim() }) }); const data = await readResponseData(response); if (!response.ok) { setMessage(apiErrorMessage(data, "Workspace 名称保存失败。")); return; } setWorkspaces((items) => items.map((item) => item.tenant_id === activeTenantId ? { ...item, name: String(data.name) } : item)); setMessage("Workspace 名称已更新。"); }
  async function beginTransfer() { if (!activeTenantId || !transferTargetId) return; const response = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/ownership-transfer`), { method: "POST", headers: { ...authorizationHeaders(), "Content-Type": "application/json" }, body: JSON.stringify({ to_user_id: transferTargetId }) }); const data = await readResponseData(response); if (!response.ok) { setMessage(apiErrorMessage(data, "发起 ownership transfer 失败。")); return; } setOwnershipTransfer(data as unknown as OwnershipTransfer); setMessage("Ownership transfer 已创建，等待目标成员明确接受。"); }
  async function cancelTransfer() { if (!activeTenantId || !ownershipTransfer) return; const response = await fetch(apiUrl(`/tenants/${encodeURIComponent(activeTenantId)}/ownership-transfer/${encodeURIComponent(ownershipTransfer.id)}`), { method: "DELETE", headers: authorizationHeaders() }); if (!response.ok) { setMessage(apiErrorMessage(await readResponseData(response), "取消 transfer 失败。")); return; } setOwnershipTransfer(null); }

  async function onPaperChange(file: File | null) {
    setPaperFile(file);
    setPaperFilename(file?.name ?? "");
    setClassification(null);
    setConfirmedNonPaper(false);
    setResult(null);
    setPreview(null);
    setPreviewError("");
    if (!file) {
      setMessage("");
      return;
    }
    await classifyFile(file);
  }

  function onTemplateChange(file: File | null) {
    setTemplateFile(file);
    setTemplateFilename(file?.name ?? "");
  }

  async function uploadManagedTemplate() {
    if (!managedTemplateFile || !managedTemplateName.trim() || !managedTemplateVersion.trim()) {
      setMessage("请选择模板文件，并填写模板名称和版本。");
      return;
    }
    const formData = new FormData();
    formData.append("file", managedTemplateFile);
    formData.append("name", managedTemplateName.trim());
    formData.append("version", managedTemplateVersion.trim());
    formData.append("school", managedTemplateSchool.trim() || "通用");
    formData.append("document_type", managedTemplateType.trim() || "academic_paper");
    setUploadingTemplate(true);
    try {
      const response = await fetch(apiUrl("/templates"), { method: "POST", headers: authorizationHeaders(), body: formData });
      const data = await readResponseData(response);
      if (!response.ok) {
        if (isAuthenticationFailure(response)) requireAuthentication();
        else setMessage(apiErrorMessage(data, "模板上传失败。"));
        return;
      }
      const created = data as unknown as TemplateOption;
      setTemplates((current) => [...current.filter((item) => item.id !== created.id), created]);
      setTemplateId(`${created.template_id}@@${created.version}`);
      setManagedTemplateFile(null);
      setMessage("我的模板已上传、完成规则解析并加入 Registry。");
    } catch (error) {
      setMessage(networkErrorMessage(error, "模板上传失败", apiUrl("/templates")));
    } finally { setUploadingTemplate(false); }
  }

  async function classifyFile(file: File) {
    const formData = new FormData();
    formData.append("paper", file);
    setClassifying(true);
    setMessage("正在识别文档类型...");
    try {
      const requestUrl = apiUrl("/document/classify");
      const response = await fetch(requestUrl, { method: "POST", headers: authorizationHeaders(), body: formData });
      const data = await readResponseData(response);
      if (!response.ok) {
        if (isAuthenticationFailure(response)) requireAuthentication();
        else setMessage(apiErrorMessage(data, "文档类型识别失败。"));
        return;
      }
      const nextClassification = data as Classification;
      setClassification(nextClassification);
      setMessage(nextClassification.requires_confirmation ? "该文档可能不适合直接套用论文格式，请确认后继续。" : "已识别为标准论文，可以启动 Agent。");
    } catch (error) {
      setMessage(networkErrorMessage(error, "文档类型识别失败。你仍可在确认文件无误后启动 Agent", apiUrl("/document/classify")));
    } finally {
      setClassifying(false);
    }
  }

  async function runAgent() {
    if (!paperFile) {
      setMessage("请先上传论文 docx 文件。");
      return;
    }
    if (needsConfirmation && !confirmedNonPaper) {
      setMessage("该文档可能不是标准论文，必须勾选确认后才能继续。");
      return;
    }
    if (usage && usage.remaining <= 0) {
      setMessage(`本周期 Agent 运行额度已用尽（${usage.usage.used}/${usage.quota.limit}），请在额度周期结束后再试。`);
      return;
    }

    const formData = new FormData();
    const allowNonPaper = Boolean(confirmedNonPaper || !classification);
    formData.append("paper", paperFile);
    formData.append("mode", agentMode);
    formData.append("allow_non_paper", String(allowNonPaper));
    if (templateFile) formData.append("template", templateFile);
    else if (templateId) {
      const [selectedId, selectedVersion] = templateId.split("@@", 2);
      formData.append("template_id", selectedId);
      if (selectedVersion) formData.append("template_version", selectedVersion);
    }

    setRunning(true);
    setPreview(null);
    setPreviewError("");
    setResult(null);
    setMessage("PaperForge 正在按计划处理文档，并在输出后执行验证...");
    try {
      const requestUrl = apiUrl("/tasks");
      const response = await fetch(requestUrl, { method: "POST", headers: authorizationHeaders(), body: formData });
      const data = await readResponseData(response);
      const status = typeof data.result_status === "string" ? data.result_status : typeof data.status === "string" ? data.status : "";
      if (status === "requires_confirmation") {
        setClassification(data.classification as Classification);
        setMessage(typeof data.message === "string" ? data.message : "该文档可能不适合直接套用论文格式，请确认后继续。");
        return;
      }
      if (!response.ok || status === "error") {
        if (isAuthenticationFailure(response)) requireAuthentication();
        else setMessage(apiErrorMessage(data, "Agent 执行失败。"));
        return;
      }
      if (status === "pending" && typeof data.task_id === "string") {
        setMessage("任务已创建，正在后台处理，即将进入任务详情。");
        router.push(`/tasks/${encodeURIComponent(data.task_id)}`);
        return;
      }
      const nextResult = (data.result || data) as AgentResult;
      if (typeof data.task_id === "string") nextResult.task_id = data.task_id;
      setResult(nextResult);
      setClassification(nextResult.classification);
      setMessage("Agent 修改完成，正在生成在线预览。");
      const previewReady = await loadPreview(nextResult.filename);
      setMessage(previewReady ? "Agent 修改完成，已生成修改报告和在线预览。" : "Agent 修改完成，修改报告和下载文件已生成，在线预览暂不可用。");
    } catch (error) {
      setMessage(networkErrorMessage(error, "Agent 启动失败", apiUrl("/agent/run")));
    } finally {
      setRunning(false);
    }
  }

  async function loadPreview(filename: string): Promise<boolean> {
    setPreviewLoading(true);
    setPreviewError("");
    try {
      const requestUrl = apiUrl(`/preview/${encodeURIComponent(filename)}`);
      const response = await fetch(requestUrl);
      const data = await readResponseData(response);
      if (!response.ok) {
        if (isAuthenticationFailure(response)) {
          requireAuthentication();
          return false;
        }
        const detail = apiErrorMessage(data, "在线预览生成失败。");
        setPreviewError(detail);
        setMessage(detail);
        return false;
      }
      setPreview(data as PreviewResult);
      return true;
    } catch (error) {
      const detail = networkErrorMessage(error, "在线预览生成失败", apiUrl(`/preview/${encodeURIComponent(filename)}`));
      setPreviewError(detail);
      setMessage(detail);
      return false;
    } finally {
      setPreviewLoading(false);
    }
  }

  async function applySuggestion(issue: ContentIssue) {
    if (!result || !issue.issue_id || typeof issue.paragraph_index !== "number" || !issue.original_text || !issue.suggested_text) return;
    const formData = new FormData();
    formData.append("filename", result.filename);
    formData.append("issue_id", issue.issue_id);
    formData.append("paragraph_index", String(issue.paragraph_index));
    formData.append("original", issue.original_text);
    formData.append("suggested", issue.suggested_text);
    formData.append("issue_type", issue.issue_type ?? "content");
    formData.append("reason", issue.reason ?? "用户确认采纳该建议");
    try {
      const response = await fetch(apiUrl("/agent/apply-suggestion"), { method: "POST", headers: authorizationHeaders(), body: formData });
      const data = await readResponseData(response);
      if (!response.ok) {
        if (isAuthenticationFailure(response)) requireAuthentication();
        else setMessage(apiErrorMessage(data, "建议采纳失败，正文未覆盖。"));
        return;
      }
      const change = data.change as ContentIssue;
      const nextReview = result.content_review ? { ...result.content_review, provenance: { ...result.content_review.provenance, accepted: [...(result.content_review.provenance?.accepted ?? []), change] }, issues: (result.content_review.issues ?? []).map((item) => item.issue_id === issue.issue_id ? { ...item, status: "accepted", verification_status: "verified" } : item) } : result.content_review;
      setResult({ ...result, filename: String(data.output), download_url: String(data.download_url), content_review: nextReview, review_summary: data.review_summary as ReviewSummary, change_evidence: data.change_evidence as unknown[], pending_actions: data.pending_actions as ContentIssue[], content_score: data.content_score as AgentResult["content_score"] });
      setPreview(null);
      await loadPreview(String(data.output));
      setMessage("建议已采纳、写入新的确认版 DOCX，并完成重读验证。");
    } catch (error) {
      setMessage(networkErrorMessage(error, "建议采纳失败，正文未覆盖。", apiUrl("/agent/apply-suggestion")));
    }
  }

  return (
    <main className="page">
      <section className="workspace">
        <section className="landing-shell" aria-label="产品首页与处理工作台">
          <header className="hero">
            <div className="hero-copy">
              <nav className="home-auth" aria-label="账户操作">
                {authUser ? <>
                  <span className="home-user" title={authUser.email}>{authUser.email}</span>
                  {workspaces.length ? <label className="workspace-switcher"><span className="sr-only">切换 Workspace</span><select value={activeTenantId} onChange={(event) => switchWorkspace(event.target.value)}>{workspaces.map((item) => <option key={item.tenant_id} value={item.tenant_id}>{item.name}</option>)}</select></label> : null}
                  {membership && <span className="tenant-role" title={`Workspace ${membership.tenant_id}`}>{membership.role === "owner" ? "Owner" : membership.role === "admin" ? "Admin" : "Member"}</span>}
                  <Link className="home-auth-link" href="/dashboard">工作台</Link>
                  {authUser.is_admin ? <Link className="home-auth-link" href="/admin">运营后台</Link> : null}
                  <button className="home-auth-link logout-button" type="button" onClick={logout}>退出登录</button>
                </> : <>
                  <Link className="home-auth-link" href="/login">登录</Link>
                  <Link className="home-auth-link home-auth-register" href="/register">注册</Link>
                </>}
              </nav>
              <p className="eyebrow">PaperForge</p>
              <h1>AI论文智能处理平台</h1>
              <p className="hero-lead">上传论文与格式模板，自动完成分析、修改、验证和报告生成。</p>
              <div className="hero-actions">
                <a className="hero-cta" href="#start-processing">开始处理</a>
                <Link className="hero-secondary-cta" href={authUser ? "/dashboard" : "/login"}>{authUser ? "进入工作台" : "登录"}</Link>
              </div>
              <p className="hero-meta">DOCX · Template Intelligence · Verified workflow</p>
            </div>

            <div className="hero-capabilities" aria-label="PaperForge V4 能力">
              <div className="hero-capabilities-heading">
                <span>V4 WORKSPACE</span>
                <strong>从上传到验证</strong>
              </div>
              <article className="hero-capability-card">
                <div className="hero-capability-index">01</div>
                <div>
                  <span className="hero-capability-label">Template Intelligence</span>
                  <h2>让模板成为规则</h2>
                  <p>解析模板并提取格式规则，为后续处理提供稳定约束。</p>
                  <div className="hero-capability-tags"><span>模板解析</span><span>格式规则提取</span></div>
                </div>
              </article>
              <article className="hero-capability-card">
                <div className="hero-capability-index">02</div>
                <div>
                  <span className="hero-capability-label">Agent Workflow</span>
                  <h2>每一步都可验证</h2>
                  <div className="workflow-steps" aria-label="Agent Workflow"><span>Plan</span><i>→</i><span>Execute</span><i>→</i><span>Verify</span></div>
                </div>
              </article>
              <article className="hero-capability-card">
                <div className="hero-capability-index">03</div>
                <div>
                  <span className="hero-capability-label">Evidence-based Review</span>
                  <h2>结果有据可查</h2>
                  <div className="hero-capability-tags"><span>Trace</span><span>Report</span><span>Artifact</span></div>
                </div>
              </article>
            </div>
          </header>

          {authUser ? <UsageQuotaCard usage={usage} loading={usageLoading} error={usageError} /> : null}

          {authUser && !workspaces.length ? <section className="governance-panel empty-workspace"><h2>没有可用 Workspace</h2><p>当前账号没有有效 Workspace。请联系空间 Owner 获取邀请后刷新页面。</p></section> : null}
          {authUser && membership?.role === "owner" ? <section className="governance-panel" aria-label="成员与邀请管理">
            <div className="section-title"><span>成员管理</span><strong>{members.length} 位成员</strong></div>
            <div className="member-list">{members.map((item) => <div className="member-row" key={item.user_id}><span title={item.email}>{item.email}</span><b>{item.role === "owner" ? "Owner" : item.role === "admin" ? "Admin" : "Member"}</b>{item.role !== "owner" ? <span className="member-actions"><select value={item.role} onChange={(event) => void updateMember(item, event.target.value as "admin" | "member")}><option value="admin">Admin</option><option value="member">Member</option></select><button type="button" onClick={() => void removeMember(item)}>删除</button></span> : null}</div>)}</div>
            <div className="invite-form"><h3>添加成员或创建邀请</h3><input value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} type="email" placeholder="name@example.com" aria-label="邀请邮箱" /><select value={inviteRole} onChange={(event) => setInviteRole(event.target.value as "admin" | "member")}><option value="member">Member</option><option value="admin">Admin</option></select><button type="button" onClick={() => void addExistingMember()}>添加已注册用户</button><button type="button" onClick={() => void createInvitation()}>创建邀请</button></div>
            {invitationLink ? <p className="invitation-link">复制邀请链接：<code>{invitationLink}</code></p> : null}
            {invitations.length ? <div className="invitation-list">{invitations.map((item) => <div className="member-row" key={item.id}><span>{item.email}</span><b>{item.role} · {item.status}</b>{item.status === "pending" ? <button type="button" onClick={() => void revokeInvitation(item)}>撤销</button> : null}</div>)}</div> : null}
            <div className="invite-form"><h3>Workspace Settings</h3><input value={tenantName} onChange={(event) => setTenantName(event.target.value)} placeholder={workspaces.find((item) => item.tenant_id === activeTenantId)?.name || "Workspace 名称"} /><button type="button" onClick={() => void saveTenantName()}>保存</button></div>
            <div className="invite-form"><h3>Ownership Transfer</h3>{ownershipTransfer ? <><p>待成员接受，24 小时内有效。</p><button type="button" onClick={() => void cancelTransfer()}>取消转让</button></> : <><select value={transferTargetId} onChange={(event) => setTransferTargetId(event.target.value)}><option value="">选择成员</option>{members.filter((item) => item.role !== "owner").map((item) => <option value={item.user_id} key={item.user_id}>{item.email}</option>)}</select><button type="button" onClick={() => void beginTransfer()}>发起转让</button></>}</div>
          </section> : null}
          {authUser && (membership?.role === "owner" || membership?.role === "admin") ? <section className="governance-panel"><div className="section-title"><span>Audit Log</span><strong>{auditEvents.length} 条</strong></div><div className="invitation-list">{auditEvents.map((item) => <div className="member-row" key={item.id}><span>{item.event_type}</span><b>{new Date(item.created_at).toLocaleString()}</b></div>)}</div></section> : null}

          <section className="setup-panel" id="start-processing" aria-label="上传与运行">
            <div className="section-title">
              <span>开始处理</span>
              <strong>{paperFilename ? "论文已选择" : "等待上传"}</strong>
            </div>
            <p className="section-note">先上传论文 DOCX；模板 DOCX 可选，用于提供学校或学院格式规则参考。</p>

            <section className="upload-grid" aria-label="上传文件">
              <FilePicker title="论文 docx" description="必选。Agent 会读取并生成格式处理结果。" filename={paperFilename} onChange={onPaperChange} required />
              <FilePicker title="模板 docx" description="可选。上传后会优先参考模板样式。" filename={templateFilename} onChange={onTemplateChange} />
            </section>

            <label className="template-selector">
              <span>系统模板</span>
              <select value={templateId} disabled={Boolean(templateFile)} onChange={(event) => setTemplateId(event.target.value)}>
                {templates.map((item) => <option key={item.id ?? `${item.scope ?? "platform"}-${item.template_id}-${item.version}`} value={`${item.template_id}@@${item.version}`}>{item.scope === "tenant" ? "我的模板 · " : "平台模板 · "}{item.name} · {item.school} · v{item.version}</option>)}
              </select>
              <small>{templateFile ? "已上传兼容模板，本次优先使用上传文件。" : "选择 Registry 中的模板；默认保持通用论文规则。"}</small>
            </label>

            <details className="template-selector">
              <summary>我的模板：上传并保存到当前租户</summary>
              <p>仅接受 DOCX；上传后会校验模板结构并保存为可复用的版本化资源。</p>
              <input accept=".docx" type="file" onChange={(event) => setManagedTemplateFile(event.target.files?.[0] ?? null)} />
              <input value={managedTemplateName} placeholder="模板名称" onChange={(event) => setManagedTemplateName(event.target.value)} />
              <input value={managedTemplateVersion} placeholder="版本，例如 1.0" onChange={(event) => setManagedTemplateVersion(event.target.value)} />
              <input value={managedTemplateSchool} placeholder="学校" onChange={(event) => setManagedTemplateSchool(event.target.value)} />
              <input value={managedTemplateType} placeholder="文档类型" onChange={(event) => setManagedTemplateType(event.target.value)} />
              <button className="secondary-button" type="button" disabled={uploadingTemplate} onClick={uploadManagedTemplate}>{uploadingTemplate ? "上传并解析中…" : "保存我的模板"}</button>
            </details>

            <section className="mode-switch" aria-label="Agent 模式">
              <button className={agentMode === "local" ? "active" : ""} onClick={() => setAgentMode("local")} type="button">
                本地规则模式
                <span>只执行格式修复与重复风险预检</span>
              </button>
              <button className={agentMode === "ai" ? "active" : ""} onClick={() => setAgentMode("ai")} type="button">
                AI增强模式
                <span>增加语言、逻辑和学术表达评估</span>
              </button>
            </section>

            <div className="action-row">
              <button className="agent-button" disabled={buttonDisabled} onClick={runAgent}>
                {running ? "正在处理并验证..." : result ? "再次处理" : "开始处理"}
              </button>
              {result ? (
                <button className="secondary-button" disabled={previewLoading} onClick={() => loadPreview(result.filename)}>
                  {previewLoading ? "生成预览中..." : "刷新在线预览"}
                </button>
              ) : null}
            </div>
          </section>
        </section>

        {classification ? <ClassificationCard classification={classification} confirmed={confirmedNonPaper} onConfirm={setConfirmedNonPaper} /> : null}

        {message ? <p className={/失败|必须|额度|用尽|无法/.test(message) ? "message error" : "message"}>{message}</p> : null}
        {authenticationRequired ? <section className="auth-required" aria-label="登录后继续">
          <strong>请先登录后再继续。</strong>
          <span>登录后可保存我的模板、创建受保护任务并继续处理。</span>
          <div><Link className="home-auth-link home-auth-register" href="/login">去登录</Link><Link className="home-auth-link" href="/register">注册账号</Link></div>
        </section> : null}

        {(running || result) ? <ProgressPanel running={running} steps={visibleSteps} /> : null}

        {result?.download_url ? (
          <section className="result-panel" aria-label="Agent 结果">
            <div className="result-heading">
              <div>
                <p className="eyebrow">Result Overview</p>
                <h2>处理结果总览</h2>
                <p>核心评分、修改报告、检查结果和 Agent 执行过程都在这里汇总展示。</p>
              </div>
              <a className="download compact" href={apiUrl(result.download_url)} download>
                下载最终docx
              </a>
            </div>

            <div className="completion-strip">
              <span>Agent修改完成</span>
              <span>已生成修改报告</span>
              <span>{preview ? "已生成在线预览" : previewError ? "在线预览暂不可用" : "正在生成在线预览"}</span>
            </div>

            <ScoreOverview result={result} />

            {result.template ? <p className="template-provenance">Template: {result.template.name} / v{result.template.version}（{result.template.id}）</p> : null}

            <RuntimeSummary result={result} />

              <ContentReviewPanel review={result.content_review} summary={result.review_summary} onApply={applySuggestion} />

            <section className="report-panel">
              <div className="section-title">
                <span>Agent修改报告</span>
                <strong>{result.modification_report.change_counts.total} 项处理</strong>
              </div>
              <p className="report-summary">{result.modification_report.summary}</p>
              <DiffReport report={result.modification_report} />
              {result.modification_report.score_explanation ? <p className="score-explanation">{result.modification_report.score_explanation}</p> : null}
              {result.score_breakdown.ai_added_value.length ? <ReportList title="AI语言参考说明" items={result.score_breakdown.ai_added_value} /> : null}
              <div className="report-grid">
                <ReportList title="已修复的问题" items={result.modification_report.fixed_issues} />
                <ReportList title="未能自动修复的问题" items={result.modification_report.unresolved_issues} />
              </div>
            </section>

            <ScoreModules title="格式规则评分" items={result.after_analysis.report.local_breakdown} />
            {result.score_breakdown.ai_used ? <ScoreModules title="AI语言参考评分" items={result.after_analysis.report.ai_breakdown} /> : null}

            <section className="checks-grid" aria-label="检查结果">
              {result.after_analysis.reference_check ? <ReferenceCheckPanel check={result.after_analysis.reference_check} /> : null}
              {result.after_analysis.figure_table_check ? <FigureTableCheckPanel check={result.after_analysis.figure_table_check} /> : null}
            </section>

            <section className="risk-box">
              <div className="section-title">
                <span>重复风险与人工复查</span>
                <strong>相似度预检 {result.repeat_risk.score}/100</strong>
              </div>
              <div className="report-grid">
                <ReportList title="重复风险处理建议" items={result.repeat_risk.suggestions} />
                <ReportList title="建议人工复查项" items={result.modification_report.manual_review_items} />
              </div>
            </section>

            <TracePanel result={result} />

            <section className="preview-panel">
              <div className="section-title">
                <span>在线预览与下载</span>
                <strong>{preview?.title ?? (previewError ? "预览暂不可用" : "预览生成中")}</strong>
              </div>
              {previewLoading ? <div className="preview-status">正在生成修改后的论文预览...</div> : null}
              {previewError ? (
                <div className="preview-error">
                  <strong>在线预览生成失败</strong>
                  <span>{previewError}</span>
                </div>
              ) : null}
              {preview ? <article className="doc-preview" dangerouslySetInnerHTML={{ __html: preview.html }} /> : null}
              {!preview && !previewError ? <div className="preview-loading">正在生成修改后的论文预览...</div> : null}
              <a className="download" href={apiUrl(result.download_url)} download>
                下载最终docx
              </a>
            </section>
          </section>
        ) : null}
      </section>
    </main>
  );
}

function ContentReviewPanel({ review, summary, onApply }: { review?: ContentReview | null; summary?: ReviewSummary; onApply?: (issue: ContentIssue) => void }) {
  if (!review) return null;
  const counts = review.counts ?? {};
  const items = review.issues ?? [];
  return (
    <section className="runtime-panel content-review-panel" aria-label="段落级内容审查">
      <div className="section-title"><span>段落级内容审查</span><strong>安全策略已生效</strong></div>
      <div className="content-review-counts">
        <span>统一摘要：格式已验证 {summary?.formatting?.verified ?? 0} / 内容已验证 {summary?.content?.verified ?? 0}</span>
        <span>自动修正：{counts.AUTO_FIX ?? 0}</span>
        <span>修改建议：{counts.SUGGEST_ONLY ?? 0}</span>
        <span>需人工复核：{counts.HITL_REQUIRED ?? 0}</span>
      </div>
      {items.length ? <ul className="runtime-change-list">{items.slice(0, 8).map((item, index) => <li key={`${item.paragraph_index}-${item.issue_type}-${index}`}>
        正文 #{item.paragraph_index ?? "—"} · {item.issue_type ?? "内容问题"} · {item.action_policy === "AUTO_FIX" ? "已自动修正" : item.status === "accepted" ? "已采纳、已应用、已验证" : item.action_policy === "HITL_REQUIRED" ? "需人工确认" : "建议修改（尚未写入文档）"}
        {item.reason ? <small>：{item.reason}</small> : null}
        {item.action_policy !== "AUTO_FIX" && item.suggested_text ? <details><summary>查看原文与建议</summary><p>原文：{item.original_text}</p><p>建议：{item.suggested_text}</p></details> : null}
        {item.action_policy === "SUGGEST_ONLY" && item.status !== "accepted" && item.issue_id ? <button className="secondary-button compact" type="button" onClick={() => onApply?.(item)}>采纳此建议</button> : null}
        {item.action_policy === "HITL_REQUIRED" ? <small>该项涉及高风险内容，不能通过此按钮自动写回。</small> : null}
      </li>)}</ul> : <p>未发现需要处理的段落级内容问题。</p>}
    </section>
  );
}

function UsageQuotaCard({ usage, loading, error }: { usage: UsageSummary | null; loading: boolean; error: string }) {
  if (loading && !usage) {
    return <section className="usage-quota-panel" aria-label="Usage 与 Quota"><div className="usage-quota-heading"><div><span className="card-label">USAGE / QUOTA</span><h2>本月使用额度</h2></div><span className="usage-loading">加载中…</span></div></section>;
  }
  if (!usage) {
    return <section className="usage-quota-panel usage-quota-unavailable" aria-label="Usage 与 Quota"><div className="usage-quota-heading"><div><span className="card-label">USAGE / QUOTA</span><h2>本月使用额度</h2></div></div><p>{error || "登录后即可查看当前 Workspace 的使用额度。"}</p></section>;
  }
  const limit = usage.quota.limit;
  const used = usage.usage.used;
  const remaining = usage.remaining;
  const progress = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <section className="usage-quota-panel" aria-label="Usage 与 Quota">
      <div className="usage-quota-heading">
        <div><span className="card-label">USAGE / QUOTA</span><h2>本月使用额度</h2><p>当前 Workspace 的 Agent 运行额度</p></div>
        <span className={`usage-status ${remaining === 0 ? "exhausted" : ""}`}>{remaining === 0 ? "额度已用尽" : "额度可用"}</span>
      </div>
      <div className="usage-quota-grid">
        <div className="usage-stat"><span>Monthly limit</span><strong>{limit}</strong><small>次 / 月</small></div>
        <div className="usage-stat"><span>Used</span><strong>{used}</strong><small>本周期已使用</small></div>
        <div className="usage-stat"><span>Remaining</span><strong>{remaining}</strong><small>本周期剩余</small></div>
      </div>
      <div className="usage-progress" aria-label={`已使用 ${progress}%`}><span style={{ width: `${progress}%` }} /></div>
      <p className="usage-period">统计周期：{new Date(usage.period_start).toLocaleDateString("zh-CN")} – {new Date(usage.period_end).toLocaleDateString("zh-CN")} · 数据按 tenant 隔离</p>
      {error ? <p className="usage-inline-error">{error}</p> : null}
    </section>
  );
}

function ClassificationCard({ classification, confirmed, onConfirm }: { classification: Classification; confirmed: boolean; onConfirm: (value: boolean) => void }) {
  return (
    <section className={classification.requires_confirmation ? "classification warning" : "classification"}>
      <div>
        <span>文档类型</span>
        <strong>{classification.label}</strong>
      </div>
      <div>
        <span>置信度</span>
        <strong>{Math.round(classification.confidence * 100)}%</strong>
      </div>
      <p>匹配特征：{classification.matched_features.length ? classification.matched_features.join("、") : "暂无明显特征"}</p>
      {classification.warning ? <p>{classification.warning}</p> : null}
      {classification.requires_confirmation ? (
        <label className="confirm-line">
          <input type="checkbox" checked={confirmed} onChange={(event) => onConfirm(event.target.checked)} />
          我确认继续按论文格式处理
        </label>
      ) : null}
    </section>
  );
}

function ProgressPanel({ running, steps }: { running: boolean; steps: AgentStep[] }) {
  return (
    <section className="agent-panel" aria-label="Agent 执行进度">
      <div className="section-title">
        <span>处理进度</span>
        {running ? <strong>正在处理</strong> : <strong>已完成</strong>}
      </div>
      <ol className="timeline">
        {steps.map((step) => (
          <li className={step.status} key={step.name}>
            <span className="step-icon">{step.status === "done" ? "✓" : step.status === "error" ? "!" : "•"}</span>
            <div>
              <strong>{step.name}</strong>
              <p>{step.message}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function TracePanel({ result }: { result: AgentResult }) {
  const traceItems = Array.isArray(result.agent_trace) ? result.agent_trace : [];
  const hasTaskStateSummary = Boolean(result.task_id || result.task_state_path);
  const traceDetail = isRecord(result.agent_trace_detail) ? result.agent_trace_detail : null;
  const hasTraceDetail = Boolean(traceDetail && Object.keys(traceDetail).length);

  if (!traceItems.length && !hasTaskStateSummary && !hasTraceDetail) {
    return null;
  }

  return (
    <details className="trace-panel">
      <summary>
        <span>执行轨迹</span>
        <strong>{traceItems.length ? `${traceItems.length} 个步骤` : "任务状态摘要"}</strong>
      </summary>

      <div className="trace-intro">
        <p>这里展示处理步骤、耗时、兜底策略和需要人工复核的事项。</p>
        <p>PaperForge 当前采用同步处理；任务状态摘要用于解释本次结果，不代表异步队列或断点续跑。</p>
      </div>

      {hasTaskStateSummary ? (
        <div className="trace-state">
          {result.task_id ? (
            <div>
              <span>任务 ID</span>
              <code>{result.task_id}</code>
            </div>
          ) : null}
          {result.task_state_path ? (
            <div>
              <span>后端任务状态文件路径</span>
              <code>{result.task_state_path}</code>
            </div>
          ) : null}
          <p className="trace-state-note">该路径用于开发/演示排查；前端当前不会读取该文件内容，也不代表异步队列或任务恢复能力。</p>
        </div>
      ) : null}

      {!traceItems.length ? <p className="trace-empty">本次结果未返回 agent_trace 步骤列表，仅展示任务状态摘要。</p> : null}

      {traceItems.length ? (
        <ol className="trace-list">
          {traceItems.map((item, index) => {
            const tone = traceStatusTone(item.status, item.fallback_used);
            return (
              <li className={`trace-step ${tone}`} key={`${item.step ?? "trace"}-${index}`}>
                <span className={`trace-step-index ${tone}`} aria-label={`步骤 ${index + 1}`}>
                  {index + 1}
                </span>
                <div className="trace-step-body">
                  <div className="trace-item-head">
                    <strong>{formatTraceStepName(item.step, index)}</strong>
                    <span className={`trace-status ${tone}`}>{traceStatusLabel(item.status, item.fallback_used)}</span>
                  </div>
                  <p>{formatTraceMessage(item.message)}</p>
                  <div className="trace-meta">
                    <span>{formatTraceDuration(item.duration_ms)}</span>
                    <span className={item.fallback_used ? "trace-fallback-badge" : undefined}>
                      {item.fallback_used ? "已使用 fallback / 本地规则兜底" : "未标记 fallback"}
                    </span>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      ) : null}

      {hasTraceDetail && traceDetail ? (
        <div className="trace-detail-card">
          <div className="trace-detail-head">
            <span>agent_trace_detail</span>
            <strong>详细执行说明</strong>
          </div>
          <p>以下为本次任务返回的补充执行证据；字段缺失时以前面的步骤流为准。</p>
          <pre className="trace-detail-json">{formatTraceDetail(traceDetail)}</pre>
        </div>
      ) : null}
    </details>
  );
}

const runtimeWorkflow = [
  ["ANALYZING", "分析文档"],
  ["PLANNING", "生成执行计划"],
  ["EXECUTING", "执行安全修改"],
  ["VERIFYING", "验证修改结果"],
  ["REPLANNING", "重新规划"],
  ["COMPLETED", "执行完成"],
  ["HUMAN_REVIEW_REQUIRED", "需要人工复核"],
  ["FAILED", "执行失败"],
] as const;

function RuntimeSummary({ result }: { result: AgentResult }) {
  const workflow = result.workflow;
  const verification = result.verification;
  const decision = result.decision;
  const review = result.human_review;
  const history = Array.isArray(result.replan_history) ? result.replan_history : [];
  const traceStates = new Set((result.runtime_trace ?? []).map((item) => item.state));
  const currentState = workflow?.current_state;
  const passedRules = verification?.verified_rules ?? verification?.passed_rules ?? [];
  const failedRules = verification?.failed_rules ?? [];
  const integrity = verification?.structural_integrity?.status;
  const score = verification?.verification_score ?? verification?.score;
  const provenance = result.provenance && !Array.isArray(result.provenance) ? result.provenance : null;
  const changes = provenance?.changes ?? [];
  const summary = provenance?.summary;
  const targetVerified = changes.filter((change) => change.verification_scope === "target" && change.verification_status === "verified");
  const verificationSummary = verification?.verification_summary ?? summary?.verification;
  const conflictCount = verification?.conflict_summary?.conflicts ?? summary?.conflicts ?? 0;

  if (!workflow && !verification && !decision && !review && !history.length && !provenance) return null;

  return (
    <section className="runtime-panel" aria-label="Runtime Workflow">
      {workflow ? (
        <div>
          <div className="section-title"><span>Runtime Workflow</span><strong>{runtimeStateLabel(currentState)}</strong></div>
          <ol className="runtime-workflow">
            {runtimeWorkflow.map(([state, label]) => {
              const active = currentState === state;
              const completed = traceStates.has(state) || (currentState === "COMPLETED" && !["HUMAN_REVIEW_REQUIRED", "FAILED"].includes(state));
              const tone = active ? runtimeStateTone(state) : completed ? "success" : "pending";
              return <li className={tone} key={state}><span>{active ? "•" : completed ? "✓" : "○"}</span><strong>{label}</strong></li>;
            })}
          </ol>
        </div>
      ) : null}

      {verification ? (
        <div className="runtime-card">
          <div className="section-title"><span>验证结果摘要</span><strong className={integrity && integrity !== "SAFE" ? "runtime-warning" : ""}>{integrity === "UNSAFE" ? "发现结构风险" : integrity === "WARNING" ? "存在结构提示" : "结构检查通过"}</strong></div>
          <p>目标验证：共 {verificationSummary?.total ?? "—"} 项，通过 {verificationSummary?.verified ?? "—"}，失败 {verificationSummary?.failed ?? "—"}，unsupported {verificationSummary?.unsupported ?? "—"}；冲突 {conflictCount} 项。{typeof score === "number" ? `验证评分 ${score}。` : ""}</p>
          <details className="runtime-details"><summary>开发者/高级详情</summary><pre>{formatRuntimeDetail(verification)}</pre></details>
        </div>
      ) : null}

      {provenance ? (
        <div className="runtime-card">
          <div className="section-title"><span>实际修改</span><strong>{summary?.change_count ?? changes.length} 项</strong></div>
          <p>已执行 PlanStep {summary?.executed_steps ?? "—"} 项；目标级验证通过 {targetVerified.length} 项；HITL / unsupported {summary?.unsupported_steps ?? "—"} 项；计划冲突 {conflictCount} 项。</p>
          {targetVerified.length ? <ul className="runtime-change-list">{targetVerified.slice(0, 5).map((change, index) => <li key={`${change.action}-${change.target?.paragraph_index}-${index}`}>{change.target?.semantic_role === "figure_caption" ? "图题" : change.target?.semantic_role === "table_caption" ? "表题" : "标题"}：{String(change.before ?? "未设置")} → {String(change.after ?? "未设置")}（已验证）</li>)}</ul> : null}
        </div>
      ) : null}

      {decision ? <div className={`runtime-card decision-card ${decisionTone(decision.action)}`}><div className="section-title"><span>最终决策</span><strong>{decisionLabel(decision.action)}</strong></div><p>{decision.reason || "决策引擎未返回补充说明。"}</p></div> : null}

      {review ? <div className="human-review-panel"><div className="section-title"><span>需要人工复核</span><strong>自动流程已安全停止</strong></div><p><b>原因：</b>{review.reason || "检测到需要人工确认的风险。"}</p><p><b>涉及规则/步骤：</b>{[...(review.related_rule_ids ?? []), ...(review.affected_targets ?? [])].join("、") || "未提供"}</p>{review.items?.length ? <ul className="runtime-change-list">{review.items.slice(0, 5).map((item, index) => <li key={index}>{formatRuntimeDetail(item)}</li>)}</ul> : null}<p><b>建议操作：</b>{review.suggested_action || "请人工确认后再决定后续处理。"}</p></div> : null}

      {history.length ? <details className="runtime-card replan-card"><summary>系统已自动重新规划 {history.length} 次</summary><ol>{history.map((item, index) => <li key={`${item.plan?.plan_id ?? "plan"}-${index}`}>旧 Plan ID：{item.plan?.plan_id ?? "未记录"}；新 Plan ID：{history[index + 1]?.plan?.plan_id ?? result.execution_plan?.plan_id ?? "未记录"}；原因：{item.decision?.reason ?? "未记录"}</li>)}</ol></details> : null}
    </section>
  );
}

function runtimeStateLabel(state?: string) {
  return runtimeWorkflow.find(([value]) => value === state)?.[1] ?? "运行状态未返回";
}

function runtimeStateTone(state: string) {
  if (state === "HUMAN_REVIEW_REQUIRED") return "review";
  if (state === "FAILED") return "failed";
  return "running";
}

function decisionLabel(action?: string) {
  return ({ COMPLETE: "完成：验证通过", REPLAN: "重新规划：尝试安全修复", HUMAN_REVIEW: "人工复核：需人工确认", FAIL: "失败：无法安全继续" } as Record<string, string>)[action ?? ""] ?? "决策未返回";
}

function decisionTone(action?: string) {
  if (action === "HUMAN_REVIEW" || action === "REPLAN") return "warning";
  if (action === "FAIL") return "failed";
  return "success";
}

function formatRuntimeDetail(detail: unknown) {
  try { return JSON.stringify(detail, null, 2); } catch { return "运行时详情无法格式化展示。"; }
}

function formatTraceStepName(step: string | undefined, index: number) {
  return step?.trim() ? step : `未命名步骤 ${index + 1}`;
}

function formatTraceMessage(message?: string) {
  return message?.trim() ? message : "该步骤未返回简短说明。";
}

function formatTraceDetail(detail: Record<string, unknown>) {
  try {
    return JSON.stringify(detail, null, 2);
  } catch {
    return "agent_trace_detail 无法格式化展示。";
  }
}

function ScoreOverview({ result }: { result: AgentResult }) {
  const formatScore = result.score_breakdown.format_score ?? result.score_breakdown.local_score;
  const aiLanguageScore = result.score_breakdown.ai_language_score ?? result.score_breakdown.ai_score;
  const aiIsReferenceOnly = typeof aiLanguageScore === "number" && aiLanguageScore < formatScore;
  const scoreDelta = result.after_score - result.before_score;
  const deltaLabel = scoreDelta > 0 ? `+${scoreDelta}` : String(scoreDelta);
  const modeLabel = result.mode === "local" ? "本地规则模式" : result.mode === "ai" ? "AI增强模式" : "当前模式";

  return (
    <div className="score-overview">
      <div className="score-card primary">
        <span>评分变化</span>
        <div className="score-pair">
          <b>{result.before_score}</b>
          <i>→</i>
          <strong>{result.after_score}</strong>
        </div>
        <p>提升值 {deltaLabel}。{result.after_analysis.report.summary}</p>
      </div>
      <div className="score-card score-change">
        <span>格式规则分</span>
        <b>{formatScore}</b>
        <span>风险稳定分</span>
        <b>{result.score_breakdown.risk_score ?? "待评估"}</b>
        <span>AI语言参考分</span>
        <b>{aiLanguageScore ?? "未启用"}</b>
        <small>可信度 {result.score_breakdown.score_confidence ?? "待评估"}</small>
        {aiIsReferenceOnly ? <p className="score-note">AI语言评分仅作参考，不影响最终评分。</p> : null}
      </div>
      <div className={`score-card risk-pill ${riskTone(result.repeat_risk.level)}`}>
        <span>重复风险</span>
        <strong>{result.repeat_risk.level}</strong>
        <small>{result.repeat_risk.score}/100</small>
        <div className="result-meta">
          <span>{modeLabel}</span>
          <span>{result.score_breakdown.ai_used ? "AI参考已参与" : "AI参考未参与评分"}</span>
          {result.task_id ? <span>任务 ID：{result.task_id}</span> : null}
        </div>
      </div>
    </div>
  );
}

function ScoreModules({ title, items }: { title: string; items: ScoreDimension[] }) {
  return (
    <section className="module-panel">
      <div className="section-title">
        <span>{title}</span>
        <strong>{items.length} 项</strong>
      </div>
      <div className="module-grid">
        {items.map((item) => (
          <ScoreModule key={item.key} item={item} />
        ))}
      </div>
    </section>
  );
}

function FilePicker({ title, description, filename, required = false, onChange }: { title: string; description: string; filename: string; required?: boolean; onChange: (file: File | null) => void }) {
  return (
    <label className="file-card">
      <span>
        {title}
        <b>{required ? "必选" : "可选"}</b>
      </span>
      <p>{description}</p>
      <strong>{filename || "选择 Word 文件"}</strong>
      <input accept=".docx" type="file" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
    </label>
  );
}

function ScoreModule({ item }: { item: ScoreDimension }) {
  return (
    <div className="module-card">
      <div>
        <span>{item.label}</span>
        <strong>{item.score}</strong>
      </div>
      <div className="bar">
        <i style={{ width: `${item.score}%` }} />
      </div>
      <p>{item.status}</p>
      {item.issues.length ? <small>{item.issues[0]}</small> : <small>自动检查未发现明显风险。</small>}
    </div>
  );
}

function ReportList({ title, items }: { title: string; items: string[] }) {
  const safeItems = items.length ? items : ["暂无需要展示的内容。"];
  return (
    <div className="report-list">
      <h2>{title}</h2>
      <ul>
        {safeItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function ReferenceCheckPanel({ check }: { check: ReferenceCheck }) {
  const summaryItems = [
    `参考文献章节：${check.has_reference_section ? "已识别" : "未识别"}`,
    `文末条目：${check.reference_count} 条`,
    `正文引用：${check.citation_count} 处`,
  ];
  const relationItems = [
    `文末编号：${formatNumbers(check.reference_numbers)}`,
    `正文引用编号：${formatNumbers(check.citation_numbers)}`,
    `跳号：${formatNumbers(check.numbering_gaps)}`,
    `重复编号：${formatNumbers(check.duplicate_reference_numbers)}`,
    `正文引用不存在：${formatNumbers(check.missing_reference_numbers)}`,
    `文末未引用：${formatNumbers(check.uncited_reference_numbers)}`,
  ];
  const issueItems = check.issues.length ? check.issues : ["自动检查未发现明显参考文献风险。"];
  return (
    <section className="module-panel">
      <div className="section-title">
        <span>参考文献检查</span>
        <strong>{check.reference_count} 条文献</strong>
      </div>
      <div className="report-grid">
        <ReportList title="检查概览" items={summaryItems} />
        <ReportList title="编号与引用" items={relationItems} />
      </div>
      <ReportList title="参考文献风险" items={issueItems} />
    </section>
  );
}

function FigureTableCheckPanel({ check }: { check: FigureTableCheck }) {
  const summaryItems = [
    `图题编号：${formatNumbers(check.figure_numbers)}`,
    `表题编号：${formatNumbers(check.table_numbers)}`,
    `图编号跳号：${formatNumbers(check.figure_gaps)}`,
    `表编号跳号：${formatNumbers(check.table_gaps)}`,
  ];
  const riskItems = [
    `重复图编号：${formatNumbers(check.duplicate_figures)}`,
    `重复表编号：${formatNumbers(check.duplicate_tables)}`,
    `正文引用图号不存在：${formatNumbers(check.missing_referenced_figures)}`,
    `正文引用表号不存在：${formatNumbers(check.missing_referenced_tables)}`,
  ];
  const captionItems = [...check.missing_figure_captions, ...check.missing_table_captions];
  const issueItems = check.issues.length ? check.issues : ["自动检查未发现明显图表编号风险。"];
  return (
    <section className="module-panel">
      <div className="section-title">
        <span>图表编号检查</span>
        <strong>{check.figure_numbers.length} 图 / {check.table_numbers.length} 表</strong>
      </div>
      <div className="report-grid">
        <ReportList title="编号概览" items={summaryItems} />
        <ReportList title="引用与重复" items={riskItems} />
      </div>
      {captionItems.length ? <ReportList title="题注缺失风险" items={captionItems} /> : null}
      <ReportList title="图表风险" items={issueItems} />
    </section>
  );
}

function DiffReport({ report }: { report: ModificationReport }) {
  const changedItems = report.changed_dimensions.length
    ? report.changed_dimensions.map((item) => `${item.label}：${item.before} → ${item.after}（${formatDelta(item.delta)}）`)
    : ["各评分维度保持稳定，本次主要完成格式规范化处理。"];
  return (
    <div className="diff-report">
      <div className="diff-summary">
        <div>
          <span>自动处理</span>
          <strong>{report.auto_fix_count}</strong>
        </div>
        <div>
          <span>变化维度</span>
          <strong>{report.format_diff_summary.changed_dimension_count}</strong>
        </div>
        <div>
          <span>人工复查</span>
          <strong>{report.needs_manual_review_count}</strong>
        </div>
      </div>
      <p>{report.format_diff_summary.summary}</p>
      <div className="report-grid">
        <ReportList title="改了什么" items={changedItems} />
        <ReportList title="仍需人工复查" items={report.manual_review_items} />
      </div>
    </div>
  );
}

function formatNumbers(numbers: number[]) {
  return numbers.length ? numbers.join("、") : "无";
}

function formatDelta(delta: number) {
  if (delta > 0) return `+${delta}`;
  return String(delta);
}

function formatTraceDuration(duration?: number) {
  return typeof duration === "number" && Number.isFinite(duration) ? `${duration} ms` : "未记录耗时";
}

function traceStatusLabel(status?: string, fallbackUsed?: boolean) {
  const normalized = normalizeTraceStatus(status, fallbackUsed);
  if (!normalized) return "未记录状态";
  if (normalized === "success") return "success";
  if (normalized === "warning") return "warning";
  if (normalized === "fallback") return "fallback";
  if (normalized === "failed") return "failed";
  if (normalized === "running") return "running";
  if (normalized === "skipped") return "skipped";
  return status?.trim() || "未记录状态";
}

function traceStatusTone(status?: string, fallbackUsed?: boolean) {
  const normalized = normalizeTraceStatus(status, fallbackUsed);
  if (normalized === "success") return "success";
  if (normalized === "warning") return "warning";
  if (normalized === "fallback") return "fallback";
  if (normalized === "failed") return "failed";
  if (normalized === "running") return "running";
  if (normalized === "skipped") return "skipped";
  return "neutral";
}

function normalizeTraceStatus(status?: string, fallbackUsed?: boolean) {
  const normalized = status?.trim().toLowerCase();
  if (normalized === "error" || normalized === "failed" || normalized === "failure") return "failed";
  if (normalized === "warning" || normalized === "warn") return "warning";
  if (normalized === "fallback") return "fallback";
  if (normalized === "running") return "running";
  if (normalized === "skipped" || normalized === "skip") return "skipped";
  if (fallbackUsed) return "fallback";
  if (!normalized) return "";
  if (normalized === "done" || normalized === "ok" || normalized === "succeeded" || normalized === "success") return "success";
  return normalized;
}

function riskTone(level: string) {
  if (level === "高") return "risk-high";
  if (level === "中") return "risk-medium";
  return "risk-low";
}
