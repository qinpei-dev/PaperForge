"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Badge, Button, Card, Input } from "../../../../components";
import { apiUrl } from "../../../../lib/api-client";
import { authorizationHeaders, tryPreviewAutoLogin } from "../../../../lib/auth";
import { userFacingError } from "../../../../lib/error-messages";
import styles from "./page.module.css";

type TemplateOption = {
  id?: string;
  template_id: string;
  name: string;
  school: string;
  document_type: string;
  version: string;
  status: string;
  scope?: string;
};

type Classification = {
  label: string;
  confidence: number;
  warning: string;
  requires_confirmation: boolean;
};

type UsageSummary = {
  quota: { limit: number };
  usage: { used: number };
  remaining: number;
  period_end: string;
};

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

function responseMessage(data: Record<string, unknown>, fallback: string) {
  if (typeof data.detail === "string") return userFacingError(data.detail, fallback);
  if (isRecord(data.detail) && typeof data.detail.message === "string") return userFacingError(data.detail.message, fallback);
  if (isRecord(data.error) && typeof data.error.message === "string") return userFacingError(data.error.message, fallback);
  if (typeof data.message === "string") return userFacingError(data.message, fallback);
  return fallback;
}

function parseTemplateOption(value: unknown): TemplateOption | null {
  if (!isRecord(value) || typeof value.template_id !== "string" || typeof value.name !== "string" || typeof value.version !== "string") return null;
  return {
    id: typeof value.id === "string" ? value.id : undefined,
    template_id: value.template_id,
    name: value.name,
    school: typeof value.school === "string" ? value.school : "",
    document_type: typeof value.document_type === "string" ? value.document_type : "academic_paper",
    version: value.version,
    status: typeof value.status === "string" ? value.status : "active",
    scope: typeof value.scope === "string" ? value.scope : undefined,
  };
}

function templateIdFromFilename(filename: string) {
  const slug = filename
    .replace(/\.docx$/i, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 180);
  return slug || "workspace-template";
}

async function requestTemplates() {
  const response = await fetch(apiUrl("/templates"), { cache: "no-store", headers: authorizationHeaders() });
  const data = await readResponseData(response);
  if (!response.ok) throw new Error(responseMessage(data, "模板列表请求失败，请稍后重试。"));
  const options = Array.isArray(data.templates) ? data.templates.map(parseTemplateOption).filter((item): item is TemplateOption => item !== null) : [];
  const defaultId = typeof data.default_template_id === "string" ? data.default_template_id : options[0]?.template_id;
  const defaultVersion = typeof data.default_template_version === "string" ? data.default_template_version : options.find((item) => item.template_id === defaultId)?.version;
  return { options, defaultKey: defaultId && defaultVersion ? `${defaultId}@@${defaultVersion}` : "" };
}

function isDocx(file: File) {
  return file.name.toLowerCase().endsWith(".docx");
}

function formatBytes(size: number) {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function templateValue(template: TemplateOption) {
  return `${template.template_id}@@${template.version}`;
}

export default function NewTaskPage() {
  const router = useRouter();
  const [paperFile, setPaperFile] = useState<File | null>(null);
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [templates, setTemplates] = useState<TemplateOption[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [templatePickerOpen, setTemplatePickerOpen] = useState(false);
  const [templateLoadError, setTemplateLoadError] = useState("");
  const [showManagedUpload, setShowManagedUpload] = useState(false);
  const [managedTemplateFile, setManagedTemplateFile] = useState<File | null>(null);
  const [managedTemplateName, setManagedTemplateName] = useState("");
  const [managedTemplateId, setManagedTemplateId] = useState("");
  const [managedTemplateVersion, setManagedTemplateVersion] = useState("1.0");
  const [managedTemplateSchool, setManagedTemplateSchool] = useState("通用");
  const [uploadingTemplate, setUploadingTemplate] = useState(false);
  const [templateUploadError, setTemplateUploadError] = useState("");
  const [agentMode, setAgentMode] = useState<"local" | "ai">("ai");
  const [classification, setClassification] = useState<Classification | null>(null);
  const [confirmedNonPaper, setConfirmedNonPaper] = useState(false);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [classifying, setClassifying] = useState(false);
  const [running, setRunning] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function loadTemplates({ selectDefault = false, preferredKey = "" }: { selectDefault?: boolean; preferredKey?: string } = {}) {
    setLoadingTemplates(true);
    setTemplateLoadError("");
    try {
      const result = await requestTemplates();
      setTemplates(result.options);
      if (preferredKey) {
        setTemplateId(preferredKey);
      } else if (selectDefault && !templateFile && !templateId && result.defaultKey) {
        setTemplateId(result.defaultKey);
      }
      return result.options;
    } catch (reason) {
      setTemplateLoadError(userFacingError(reason, "模板列表暂时无法加载，请稍后重试。"));
      return null;
    } finally {
      setLoadingTemplates(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function loadUsage() {
      try {
        const response = await fetch(apiUrl("/usage"), { cache: "no-store", headers: authorizationHeaders() });
        const data = await readResponseData(response);
        if (cancelled || !response.ok || !isRecord(data.quota) || !isRecord(data.usage)) return;
        if (typeof data.quota.limit !== "number" || typeof data.usage.used !== "number" || typeof data.remaining !== "number") return;
        setUsage({
          quota: { limit: data.quota.limit },
          usage: { used: data.usage.used },
          remaining: data.remaining,
          period_end: typeof data.period_end === "string" ? data.period_end : "",
        });
      } catch {
        // Quota is advisory here; the server remains authoritative at task creation.
      }
    }

    async function bootstrap() {
      await tryPreviewAutoLogin();
      if (cancelled) return;
      await Promise.all([loadTemplates({ selectDefault: true }), loadUsage()]);
    }

    void bootstrap();
    return () => { cancelled = true; };
  }, []);

  async function classifyFile(file: File) {
    const formData = new FormData();
    formData.append("paper", file);
    setClassifying(true);
    setError("");
    setNotice("正在识别文档类型…");
    try {
      const response = await fetch(apiUrl("/document/classify"), { method: "POST", headers: authorizationHeaders(), body: formData });
      const data = await readResponseData(response);
      if (!response.ok) {
        setNotice(responseMessage(data, "文档类型识别暂时不可用，确认文件无误后仍可继续创建。"));
        return;
      }
      setClassification(data as Classification);
      setConfirmedNonPaper(false);
      setNotice(data.requires_confirmation ? "该文档需要确认后才能套用论文处理流程。" : "已识别为标准论文，可以继续下一步。 ");
    } catch {
      setNotice("文档类型识别暂时不可用，确认文件无误后仍可继续创建。 ");
    } finally {
      setClassifying(false);
    }
  }

  function selectPaper(file: File | null) {
    if (!file) return;
    if (!isDocx(file)) {
      setError("论文文件必须是 .docx 格式。 ");
      return;
    }
    setPaperFile(file);
    setClassification(null);
    setConfirmedNonPaper(false);
    void classifyFile(file);
  }

  function selectTemplate(file: File | null) {
    if (!file) return;
    if (!isDocx(file)) {
      setError("临时模板必须是 .docx 格式。 ");
      return;
    }
    setTemplateFile(file);
    setTemplateId("");
    setError("");
    setNotice("临时模板已选择，本次任务将优先使用该文件。 ");
  }

  function selectManagedTemplateFile(file: File | null) {
    if (!file) return;
    if (!isDocx(file)) {
      setTemplateUploadError("模板文件必须是 .docx 格式。 ");
      return;
    }
    setManagedTemplateFile(file);
    setManagedTemplateName(file.name.replace(/\.docx$/i, ""));
    setManagedTemplateId(templateIdFromFilename(file.name));
    setTemplateUploadError("");
  }

  function chooseManagedTemplate(template: TemplateOption) {
    setTemplateId(templateValue(template));
    setTemplateFile(null);
    setTemplatePickerOpen(false);
    setShowManagedUpload(false);
    setTemplateUploadError("");
    setNotice(`已选择模板：${template.name} / v${template.version}。`);
  }

  async function uploadManagedTemplate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!managedTemplateFile) {
      setTemplateUploadError("请先选择要上传的 DOCX 模板。 ");
      return;
    }
    const name = managedTemplateName.trim();
    const templateKey = managedTemplateId.trim();
    const version = managedTemplateVersion.trim();
    const school = managedTemplateSchool.trim();
    if (!name || !templateKey || !version || !school) {
      setTemplateUploadError("请完整填写模板名称、Template ID、版本和学校/组织。 ");
      return;
    }

    const formData = new FormData();
    formData.append("file", managedTemplateFile);
    formData.append("name", name);
    formData.append("template_id", templateKey);
    formData.append("version", version);
    formData.append("school", school);
    formData.append("document_type", "academic_paper");
    setUploadingTemplate(true);
    setTemplateUploadError("");
    try {
      const response = await fetch(apiUrl("/templates"), { method: "POST", headers: authorizationHeaders(), body: formData });
      const data = await readResponseData(response);
      if (!response.ok) throw new Error(responseMessage(data, "模板上传失败，请检查文件和模板信息后重试。"));
      const uploadedTemplate = parseTemplateOption(data);
      if (!uploadedTemplate) throw new Error("模板上传成功，但返回数据不完整，请重新加载模板列表。 ");
      const preferredKey = templateValue(uploadedTemplate);
      setTemplates((current) => [...current.filter((item) => templateValue(item) !== preferredKey), uploadedTemplate]);
      setTemplateId(preferredKey);
      setTemplateFile(null);
      setManagedTemplateFile(null);
      setShowManagedUpload(false);
      await loadTemplates({ preferredKey });
      setTemplatePickerOpen(false);
      setNotice(`模板已上传并选中：${uploadedTemplate.name} / v${uploadedTemplate.version}。`);
    } catch (reason) {
      setTemplateUploadError(userFacingError(reason, "模板上传暂时不可用，请检查文件和模板信息后重试。 "));
    } finally {
      setUploadingTemplate(false);
    }
  }

  async function createTask() {
    if (!paperFile) {
      setError("请先上传论文 DOCX。 ");
      return;
    }
    if (classification?.requires_confirmation && !confirmedNonPaper) {
      setError("请先确认该文档可以按论文流程处理。 ");
      return;
    }
    if (usage && usage.remaining <= 0) {
      setError("本周期 Agent 运行额度已用尽，请稍后再试。 ");
      return;
    }

    const formData = new FormData();
    formData.append("paper", paperFile);
    formData.append("mode", agentMode);
    formData.append("allow_non_paper", String(Boolean(confirmedNonPaper || !classification)));
    if (templateFile) {
      formData.append("template", templateFile);
    } else if (templateId) {
      const [selectedId, selectedVersion] = templateId.split("@@", 2);
      formData.append("template_id", selectedId);
      if (selectedVersion) formData.append("template_version", selectedVersion);
    }

    setRunning(true);
    setError("");
    setNotice("正在创建任务，即将进入任务详情…");
    try {
      const response = await fetch(apiUrl("/tasks"), { method: "POST", headers: authorizationHeaders(), body: formData });
      const data = await readResponseData(response);
      if (!response.ok || data.result_status === "error") {
        setError(responseMessage(data, "任务创建失败，请检查文件和模板后重试。 "));
        return;
      }
      if (typeof data.task_id === "string") {
        router.push(`/tasks/${encodeURIComponent(data.task_id)}`);
        return;
      }
      setError("任务创建响应缺少 task_id，请稍后重试。 ");
    } catch (reason) {
      setError(`任务创建失败：${userFacingError(reason, "请稍后重试。 ")}`);
    } finally {
      setRunning(false);
    }
  }

  const needsConfirmation = classification?.requires_confirmation === true;
  const quotaExhausted = usage?.remaining === 0;
  const canCreate = Boolean(paperFile) && !running && !classifying && !quotaExhausted && (!needsConfirmation || confirmedNonPaper);
  const selectedTemplate = templates.find((item) => templateValue(item) === templateId);
  const quotaPercent = usage ? Math.min(100, Math.round((usage.usage.used / Math.max(usage.quota.limit, 1)) * 100)) : 0;

  return (
    <section className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <p className={styles.eyebrow}>NEW PAPER TASK</p>
          <h1>新建论文任务</h1>
          <p className={styles.lead}>上传一篇 DOCX，选择适合的格式规则，然后交给 PaperForge 验证处理。</p>
        </div>
        <Link className={styles.cancelLink} href="/dashboard">返回工作台</Link>
      </header>

      <div className={styles.stepRail} aria-label="创建步骤">
        {["上传论文", "选择模板", "处理模式", "确认运行"].map((label, index) => <div className={styles.stepRailItem} key={label}><span>{index + 1}</span><small>{label}</small></div>)}
      </div>

      {error ? <div className={styles.errorBanner} role="alert">{error}</div> : null}
      {notice ? <div className={styles.noticeBanner} role="status">{notice}</div> : null}

      <div className={styles.flow}>
        <Card className={styles.stepCard}>
          <div className={styles.stepHeader}><span className={styles.stepNumber}>01</span><div><p className={styles.cardEyebrow}>STEP 1</p><h2>上传论文</h2><p>只接受 DOCX 文件。上传后会先做文档类型识别。</p></div><Badge>{paperFile ? "已选择" : "必需"}</Badge></div>
          <label className={`${styles.dropzone} ${dragActive ? styles.dropzoneActive : ""} ${paperFile ? styles.dropzoneFilled : ""}`} onDragEnter={(event) => { event.preventDefault(); setDragActive(true); }} onDragOver={(event) => event.preventDefault()} onDragLeave={() => setDragActive(false)} onDrop={(event) => { event.preventDefault(); setDragActive(false); selectPaper(event.dataTransfer.files[0] ?? null); }}>
            <Input className={styles.fileInput} type="file" accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(event) => selectPaper(event.target.files?.[0] ?? null)} />
            <span className={styles.uploadIcon} aria-hidden="true">↑</span>
            <strong>{paperFile ? "重新选择论文文件" : "拖拽 DOCX 到这里，或点击上传"}</strong>
            <span>支持 .docx，建议文件小于 20 MB</span>
          </label>
          {paperFile ? <div className={styles.fileSummary}><div><strong>{paperFile.name}</strong><span>{formatBytes(paperFile.size)} · DOCX</span></div><Badge className={styles.successBadge}>文件已就绪</Badge></div> : null}
          {classifying ? <p className={styles.helperText}>正在识别文档类型…</p> : null}
          {classification ? <div className={classification.requires_confirmation ? styles.warningBox : styles.classificationBox}><div><strong>{classification.label || "已完成文档识别"}</strong><span>识别置信度 {Math.round((classification.confidence || 0) * 100)}%</span></div><p>{classification.warning || "该文档可以按论文流程继续处理。"}</p>{needsConfirmation ? <label className={styles.confirmLabel}><Input className={styles.checkboxInput} type="checkbox" checked={confirmedNonPaper} onChange={(event) => setConfirmedNonPaper(event.target.checked)} />我确认继续按论文流程处理此文档</label> : null}</div> : null}
        </Card>

        <Card className={styles.stepCard}>
          <div className={styles.stepHeader}><span className={styles.stepNumber}>02</span><div><p className={styles.cardEyebrow}>STEP 2</p><h2>选择模板</h2><p>模板用于提供学校、学院或专业的格式规则参考。</p></div><Badge>可选</Badge></div>
          <div className={styles.templateSelection}>
            <button className={styles.templateTrigger} type="button" aria-haspopup="dialog" aria-expanded={templatePickerOpen} onClick={() => setTemplatePickerOpen(true)}>
              <span className={styles.templateTriggerCopy}><small>当前模板</small><strong>{templateFile?.name || selectedTemplate?.name || "通用论文规则"}</strong><span>{templateFile ? "临时模板 · 只用于本次任务" : selectedTemplate ? `${selectedTemplate.scope === "tenant" ? "我的模板" : "平台模板"} · v${selectedTemplate.version}` : "可打开列表切换或上传模板"}</span></span>
              <span className={styles.templateTriggerAction}>选择模板 <span aria-hidden="true">→</span></span>
            </button>
            {templateLoadError ? <p className={styles.templateLoadHint} role="status">模板列表加载失败，请点击“选择模板”后重新加载。</p> : null}
          </div>
          <div className={styles.tempTemplate}><div><p className={styles.cardEyebrow}>临时模板</p><strong>只用于本次任务</strong><span>不会写入模板库，上传后优先于上方模板。</span></div><label className={styles.tempUpload}><Input type="file" accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(event) => selectTemplate(event.target.files?.[0] ?? null)} />{templateFile ? "重新选择" : "上传 DOCX"}</label></div>
          {templateFile ? <div className={styles.fileSummary}><div><strong>{templateFile.name}</strong><span>{formatBytes(templateFile.size)} · 临时模板</span></div><Button variant="secondary" onClick={() => { setTemplateFile(null); setNotice("已移除临时模板，将使用已选模板。 "); }}>移除</Button></div> : null}
          {selectedTemplate && !templateFile ? <p className={styles.helperText}>当前使用：{selectedTemplate.name} / v{selectedTemplate.version} · 创建任务时将传递对应 template_id。</p> : null}
        </Card>

        <Card className={styles.stepCard}>
          <div className={styles.stepHeader}><span className={styles.stepNumber}>03</span><div><p className={styles.cardEyebrow}>STEP 3</p><h2>处理模式</h2><p>选择处理深度。两种模式都会执行格式验证与重复风险检测。</p></div><Badge>{agentMode === "ai" ? "AI 增强" : "Local"}</Badge></div>
          <div className={styles.modeGrid} role="radiogroup" aria-label="处理模式">
            <button className={`${styles.modeOption} ${agentMode === "local" ? styles.modeOptionSelected : ""}`} type="button" role="radio" aria-checked={agentMode === "local"} onClick={() => setAgentMode("local")}><span className={styles.modeIcon}>L</span><span><strong>Local 本地规则</strong><small>本地执行格式修复、文档验证与重复风险检测，不调用 AI。</small></span><Badge>稳定</Badge></button>
            <button className={`${styles.modeOption} ${agentMode === "ai" ? styles.modeOptionSelected : ""}`} type="button" role="radio" aria-checked={agentMode === "ai"} onClick={() => setAgentMode("ai")}><span className={styles.modeIcon}>AI</span><span><strong>AI 增强模式</strong><small>在本地格式处理基础上，增加语言与学术表达审校建议。</small></span><Badge>推荐</Badge></button>
          </div>
          <div className={styles.fallbackNote}><strong>AI 服务不可用时怎么办？</strong><span>AI 模式会自动 fallback 到本地规则流程，不会阻断任务，也不会让任务创建失败。</span></div>
          <details className={styles.advanced}><summary>高级信息</summary><p>两种模式都会保留任务执行轨迹、验证结果和修改报告；Local 模式保持 ai_score=null、ai_used=false。</p></details>
        </Card>

        <Card className={`${styles.stepCard} ${styles.confirmCard}`}>
          <div className={styles.stepHeader}><span className={styles.stepNumber}>04</span><div><p className={styles.cardEyebrow}>STEP 4</p><h2>确认运行</h2><p>确认输入后创建任务，后台处理完成后会自动进入 Task Detail。</p></div><Badge className={quotaExhausted ? styles.warningBadge : styles.successBadge}>{quotaExhausted ? "额度不足" : "准备就绪"}</Badge></div>
          <div className={styles.confirmGrid}><div><span>论文</span><strong>{paperFile?.name || "尚未上传"}</strong></div><div><span>模板</span><strong>{templateFile?.name || selectedTemplate?.name || "通用论文规则"}</strong></div><div><span>模式</span><strong>{agentMode === "ai" ? "AI 增强模式" : "Local 本地规则"}</strong></div><div><span>预计消耗额度</span><strong>1 次 Agent 运行</strong></div></div>
          {usage ? <div className={styles.quotaSummary}><div><span>本周期额度</span><strong>{usage.remaining} / {usage.quota.limit} 次剩余</strong></div><div className={styles.progressTrack}><span style={{ width: `${quotaPercent}%` }} /></div><small>{usage.period_end ? `周期结束：${new Date(usage.period_end).toLocaleDateString("zh-CN")}` : "额度以服务器最终校验为准"}</small></div> : <p className={styles.helperText}>额度将在创建时由服务器最终校验。</p>}
          <div className={styles.confirmActions}><Button onClick={() => void createTask()} disabled={!canCreate}>{running ? "创建中…" : "创建 Task 并进入详情"}</Button><Link href="/dashboard" className={styles.backLink}>稍后再做</Link></div>
          {needsConfirmation && !confirmedNonPaper ? <p className={styles.actionHint}>完成文档确认后才能创建任务。</p> : null}
          {quotaExhausted ? <p className={styles.actionHint}>本周期额度已用尽，当前按钮不可用。</p> : null}
        </Card>
      </div>

      {templatePickerOpen ? <div className={styles.modalBackdrop} role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setTemplatePickerOpen(false); }}>
        <section className={styles.templateModal} role="dialog" aria-modal="true" aria-labelledby="template-picker-title" onMouseDown={(event) => event.stopPropagation()}>
          <header className={styles.modalHeader}>
            <div><p className={styles.cardEyebrow}>TEMPLATE SELECTOR</p><h2 id="template-picker-title">选择模板</h2><p>选择当前工作空间可用的模板，或上传一个新的 managed template。</p></div>
            <button className={styles.modalClose} type="button" aria-label="关闭模板选择器" onClick={() => setTemplatePickerOpen(false)}>×</button>
          </header>

          <div className={styles.modalToolbar}><span className={styles.modalSectionLabel}>可用模板</span><Button variant="secondary" onClick={() => setShowManagedUpload((open) => !open)}>{showManagedUpload ? "收起上传" : "＋ 上传新模板"}</Button></div>
          {loadingTemplates ? <div className={styles.modalState}><span className={styles.loadingDot} aria-hidden="true" /><span>正在加载可用模板…</span></div> : templateLoadError && !templates.length ? <div className={styles.modalError} role="alert"><strong>模板加载失败</strong><p>{templateLoadError}</p><Button variant="secondary" onClick={() => void loadTemplates()}>重新加载</Button></div> : templates.length ? <>
            {templateLoadError ? <div className={styles.modalError} role="alert"><strong>模板列表刷新失败</strong><p>{templateLoadError}</p><Button variant="secondary" onClick={() => void loadTemplates()}>重新加载</Button></div> : null}
            <div className={styles.modalTemplateList}>
            <button className={`${styles.templateOption} ${!templateId && !templateFile ? styles.templateOptionSelected : ""}`} type="button" onClick={() => { setTemplateId(""); setTemplateFile(null); setTemplatePickerOpen(false); setNotice("已选择通用论文规则。 "); }}>
              <span className={styles.templateOptionCopy}><strong>通用论文规则</strong><small>不指定模板，使用 PaperForge 默认格式规则</small></span><Badge>默认</Badge>
            </button>
            {templates.map((item) => <button className={`${styles.templateOption} ${templateValue(item) === templateId && !templateFile ? styles.templateOptionSelected : ""}`} type="button" key={item.id ?? templateValue(item)} onClick={() => chooseManagedTemplate(item)}>
              <span className={styles.templateOptionCopy}><strong>{item.name}</strong><small>{item.scope === "tenant" ? "我的模板" : "平台模板"} · {item.school || "通用"} · v{item.version}</small></span><Badge>{item.status === "active" ? "可用" : item.status}</Badge>
            </button>)}
            </div>
          </> : <div className={styles.modalEmpty}><strong>暂无可用模板</strong><p>上传 DOCX 模板后即可用于论文格式处理。</p><Button onClick={() => setShowManagedUpload(true)}>上传模板</Button></div>}

          {showManagedUpload ? <form className={styles.managedUploadForm} onSubmit={(event) => void uploadManagedTemplate(event)}>
            <div><p className={styles.cardEyebrow}>MANAGED TEMPLATE</p><h3>上传新模板</h3><p>模板会保存到当前工作空间，上传完成后自动刷新并选中。</p></div>
            <label className={styles.uploadField}><span>DOCX 文件</span><Input type="file" accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document" required={!managedTemplateFile} onChange={(event) => selectManagedTemplateFile(event.target.files?.[0] ?? null)} /><small>{managedTemplateFile ? managedTemplateFile.name : "请选择 .docx 模板文件"}</small></label>
            <div className={styles.uploadFormGrid}>
              <label className={styles.uploadField}><span>模板名称</span><Input value={managedTemplateName} onChange={(event) => setManagedTemplateName(event.target.value)} placeholder="例如：本科毕业论文模板" /></label>
              <label className={styles.uploadField}><span>Template ID</span><Input value={managedTemplateId} onChange={(event) => setManagedTemplateId(event.target.value)} placeholder="例如：university-thesis" /></label>
              <label className={styles.uploadField}><span>版本</span><Input value={managedTemplateVersion} onChange={(event) => setManagedTemplateVersion(event.target.value)} placeholder="例如：1.0" /></label>
              <label className={styles.uploadField}><span>学校 / 组织</span><Input value={managedTemplateSchool} onChange={(event) => setManagedTemplateSchool(event.target.value)} placeholder="例如：成都大学" /></label>
            </div>
            {templateUploadError ? <p className={styles.uploadError} role="alert">{templateUploadError}</p> : null}
            <div className={styles.uploadActions}><Button type="submit" disabled={uploadingTemplate || !managedTemplateFile}>{uploadingTemplate ? "上传中…" : "上传并选择模板"}</Button><Button variant="secondary" type="button" onClick={() => setShowManagedUpload(false)} disabled={uploadingTemplate}>取消</Button></div>
          </form> : null}
        </section>
      </div> : null}
    </section>
  );
}
