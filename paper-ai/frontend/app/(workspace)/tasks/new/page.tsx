"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Badge, Button, Card, Input } from "../../../../components";
import { apiUrl } from "../../../../lib/api-client";
import { authorizationHeaders } from "../../../../lib/auth";
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
  if (typeof data.detail === "string") return data.detail;
  if (isRecord(data.detail) && typeof data.detail.message === "string") return data.detail.message;
  if (isRecord(data.error) && typeof data.error.message === "string") return data.error.message;
  if (typeof data.message === "string") return data.message;
  return fallback;
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

  useEffect(() => {
    let cancelled = false;

    async function loadTemplates() {
      try {
        const response = await fetch(apiUrl("/templates"), { cache: "no-store", headers: authorizationHeaders() });
        const data = await readResponseData(response);
        if (cancelled || !response.ok) return;
        const options = Array.isArray(data.templates) ? data.templates.filter((item): item is TemplateOption => {
          return isRecord(item) && typeof item.template_id === "string" && typeof item.name === "string" && typeof item.version === "string";
        }) : [];
        setTemplates(options);
        const defaultId = typeof data.default_template_id === "string" ? data.default_template_id : options[0]?.template_id;
        const defaultVersion = typeof data.default_template_version === "string" ? data.default_template_version : options.find((item) => item.template_id === defaultId)?.version;
        if (defaultId && defaultVersion) setTemplateId(`${defaultId}@@${defaultVersion}`);
      } catch {
        if (!cancelled) setNotice("模板列表暂时无法加载，仍可使用临时模板或通用规则。");
      } finally {
        if (!cancelled) setLoadingTemplates(false);
      }
    }

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

    void Promise.all([loadTemplates(), loadUsage()]);
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
      setError(reason instanceof Error ? `任务创建失败：${reason.message}` : "任务创建失败，请稍后重试。 ");
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
          <div className={styles.templateList}>
            <label className={`${styles.templateOption} ${!templateId && !templateFile ? styles.templateOptionSelected : ""}`}><Input className={styles.radioInput} type="radio" name="template" checked={!templateId && !templateFile} onChange={() => { setTemplateId(""); setTemplateFile(null); }} /><span><strong>通用论文规则</strong><small>不指定模板，使用 PaperForge 默认格式规则</small></span><Badge>默认</Badge></label>
            {loadingTemplates ? <p className={styles.helperText}>正在加载可用模板…</p> : templates.map((item) => <label className={`${styles.templateOption} ${templateValue(item) === templateId && !templateFile ? styles.templateOptionSelected : ""}`} key={item.id ?? templateValue(item)}><Input className={styles.radioInput} type="radio" name="template" checked={templateValue(item) === templateId && !templateFile} disabled={Boolean(templateFile)} onChange={() => { setTemplateId(templateValue(item)); setTemplateFile(null); }} /><span><strong>{item.name}</strong><small>{item.scope === "tenant" ? "我的模板" : "平台模板"} · {item.school || "通用"} · v{item.version}</small></span><Badge>{item.status === "active" ? "可用" : item.status}</Badge></label>)}
            {!loadingTemplates && !templates.length ? <p className={styles.helperText}>暂无已保存模板，可直接使用通用规则。</p> : null}
          </div>
          <div className={styles.tempTemplate}><div><p className={styles.cardEyebrow}>临时模板</p><strong>只用于本次任务</strong><span>不会写入模板库，上传后优先于上方模板。</span></div><label className={styles.tempUpload}><Input type="file" accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(event) => selectTemplate(event.target.files?.[0] ?? null)} />{templateFile ? "重新选择" : "上传 DOCX"}</label></div>
          {templateFile ? <div className={styles.fileSummary}><div><strong>{templateFile.name}</strong><span>{formatBytes(templateFile.size)} · 临时模板</span></div><Button variant="secondary" onClick={() => { setTemplateFile(null); setNotice("已移除临时模板，将使用已选模板。 "); }}>移除</Button></div> : null}
          {selectedTemplate && !templateFile ? <p className={styles.helperText}>当前使用：{selectedTemplate.name} / v{selectedTemplate.version}</p> : null}
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
    </section>
  );
}
