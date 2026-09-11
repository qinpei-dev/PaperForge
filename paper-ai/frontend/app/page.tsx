
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getStoredAuthUser } from "../lib/auth";

type AuthUser = { email: string };

const workflowSteps = [
  { number: "01", title: "上传论文", detail: "把 DOCX 文件放进工作流", tone: "blue" },
  { number: "02", title: "解析模板", detail: "识别格式规则与文档结构", tone: "slate" },
  { number: "03", title: "处理并验证", detail: "智能处理并复查结果", tone: "blue" },
  { number: "04", title: "生成报告", detail: "预览、复核，然后下载", tone: "green" },
] as const;

const verificationRows = [
  { label: "模板解析完成", detail: "Template parsed · 格式规则已识别", status: "已完成", tone: "blue" },
  { label: "修改已验证", detail: "Changes verified · 修改已重新读取并确认", status: "已验证", tone: "green" },
  { label: "报告已生成", detail: "Report generated · 修改报告已准备完成", status: "已就绪", tone: "blue" },
  { label: "在线预览可用", detail: "Preview available · 可以在线查看最终文档", status: "已就绪", tone: "green" },
] as const;

function ProductWindow({ detailed = false }: { detailed?: boolean }) {
  return (
    <div className={`product-window ${detailed ? "product-window-detailed" : "product-window-hero"}`}>
      <div className="product-window-bar">
        <div className="window-dots" aria-hidden="true"><i /><i /><i /></div>
        <span className="window-title">paperforge / 当前任务</span>
        <span className="window-mode">LOCAL + AI</span>
      </div>
      <div className="product-window-layout">
        <aside className="product-window-sidebar">
          <div className="product-window-brand"><span className="product-window-mark">PF</span><span>PaperForge</span></div>
          <nav aria-label="产品窗口导航">
            <span className="product-window-nav active">概览 · Overview</span>
            <span className="product-window-nav">文档 · Documents</span>
            <span className="product-window-nav">模板 · Templates</span>
            <span className="product-window-nav">报告 · Reports</span>
          </nav>
          <p className="product-window-side-note">Every change stays visible.</p>
        </aside>

        <div className="product-window-main">
          <div className="product-window-heading">
            <div>
              <span className="product-window-kicker">论文处理工作流 · DOCUMENT WORKFLOW</span>
              <h3>处理已完成 · Analysis complete</h3>
            </div>
            <span className="verified-pill"><span /> VERIFIED</span>
          </div>

          <div className="document-card">
            <span className="document-icon">DOCX</span>
            <div><strong>当前论文.docx</strong><small>已关联所选模板.docx</small></div>
            <span className="document-check" aria-label="文件已处理">✓</span>
          </div>

          <div className="product-status-grid">
            {verificationRows.map((row) => (
              <div className={`product-status-card ${row.tone}`} key={row.label}>
                <span className="product-status-mark">✓</span>
                <strong>{row.label}</strong>
                <small>{row.status}</small>
              </div>
            ))}
          </div>

          {detailed ? (
            <div className="product-report-panel">
              <div className="product-report-heading"><span>验证结果 · Verification result</span><span className="report-ready">报告已就绪 · REPORT READY</span></div>
              <div className="product-report-rows">
                {verificationRows.map((row) => (
                  <div className="product-report-row" key={`${row.label}-report`}>
                    <div><span className={`report-dot ${row.tone}`} /><strong>{row.label}</strong></div>
                    <span>{row.detail}</span>
                    <b>{row.status}</b>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="product-window-footer"><span>报告已生成 · Report generated · 在线预览可用 · Preview available</span><span aria-hidden="true">↗</span></div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const storedUser = getStoredAuthUser();
    setAuthUser(storedUser ? { email: storedUser.email } : null);
  }, []);

  const taskHref = authUser ? "/tasks/new" : "/login";

  return (
    <main className="landing-page">
      <header className="landing-nav">
        <Link className="landing-brand" href="/" aria-label="PaperForge 首页">
          <span className="landing-brand-mark" aria-hidden="true">PF</span>
          <span>PaperForge</span>
        </Link>

        <nav className="landing-nav-links" aria-label="主导航">
          <a href="#app-preview">产品预览</a>
          <a href="#workflow">工作流程</a>
          <a href="#verification">验证结果</a>
        </nav>

        <div className="landing-nav-actions">
          {authUser ? <span className="landing-user" title={authUser.email}>{authUser.email}</span> : <Link className="landing-login" href="/login">登录</Link>}
          <Link className="landing-nav-cta" href={taskHref}>开始处理</Link>
        </div>
      </header>

      <section className="landing-hero" aria-labelledby="hero-title">
        <div className="landing-hero-copy">
          <p className="landing-eyebrow"><span aria-hidden="true" />可信学术文档处理 · Verified academic document workflow</p>
          <h1 id="hero-title">不只是修改论文，<br /><em>而是验证每一次修改。</em></h1>
          <p className="landing-hero-lead">上传论文和模板，让 PaperForge 智能处理文档、验证修改，并把结果整理成一份可复核的报告。</p>
          <div className="landing-hero-actions">
            <Link className="landing-primary-button" href={taskHref}>开始处理 <span aria-hidden="true">→</span></Link>
            <a className="landing-secondary-button" href="#workflow">查看工作流程 <span aria-hidden="true">↓</span></a>
          </div>
          <p className="landing-hero-note"><span aria-hidden="true">✓</span> DOCX 工作流 · 模板解析 · 修改验证 · 在线预览</p>
        </div>

        <div className="hero-product-frame" aria-label="PaperForge 产品窗口预览">
          <div className="hero-product-label"><span className="preview-dot" />产品实时预览 · LIVE PRODUCT PREVIEW</div>
          <ProductWindow />
        </div>
      </section>

      <section className="landing-product-section" id="app-preview" aria-labelledby="app-preview-title">
        <div className="landing-section-heading product-section-heading">
          <p className="landing-eyebrow">PAPERFORGE 产品预览 · INSIDE PAPERFORGE</p>
          <h2 id="app-preview-title">从文件到报告，<br />每一步都留在同一个窗口里。</h2>
          <p>不是一个只会输出答案的工具。PaperForge 把输入、处理、验证和交付放进一条能被查看的工作流。</p>
        </div>
        <div className="product-showcase">
          <ProductWindow detailed />
          <div className="showcase-notes">
            <div className="showcase-note"><span>01</span><div><strong>模板先被解析</strong><p>先确认文档规则，再开始处理，避免结果脱离模板要求。</p></div></div>
            <div className="showcase-note"><span>02</span><div><strong>修改后重新读取</strong><p>每个关键步骤都会回到输出文件复查，而不是只依赖过程日志。</p></div></div>
            <div className="showcase-note"><span>03</span><div><strong>结果可预览、可下载</strong><p>报告和最终文档一起交付，方便你继续复核或直接使用。</p></div></div>
          </div>
        </div>
      </section>

      <section className="landing-workflow" id="workflow" aria-labelledby="workflow-title">
        <div className="landing-section-heading">
          <p className="landing-eyebrow">论文处理工作流 · THE WORKFLOW</p>
          <h2 id="workflow-title">一条清楚的路径，<br />从上传走到交付。</h2>
          <p>你不需要猜处理进行到哪一步。每一步都有明确的输入、状态和下一步。</p>
        </div>
        <div className="workflow-rail">
          {workflowSteps.map((step, index) => (
            <article className="workflow-rail-item" key={step.number}>
              <span className={`workflow-rail-number ${step.tone}`}>{step.number}</span>
              <div><h3>{step.title}</h3><p>{step.detail}</p></div>
              {index < workflowSteps.length - 1 ? <span className="workflow-rail-arrow" aria-hidden="true">→</span> : null}
            </article>
          ))}
        </div>
      </section>

      <section className="landing-verification" id="verification" aria-labelledby="verification-title">
        <div className="verification-copy">
          <p className="landing-eyebrow">验证结果 · VERIFICATION RESULT</p>
          <h2 id="verification-title">结果不是一句“完成了”。</h2>
          <p>PaperForge 用真实状态告诉你：模板是否解析、修改是否验证、报告是否生成、预览是否可用。</p>
          <Link className="landing-inline-link" href={taskHref}>开始一个真实任务 <span aria-hidden="true">→</span></Link>
        </div>
        <div className="verification-panel">
          <div className="verification-panel-top"><div><span className="verification-panel-kicker">任务结果 · TASK RESULT</span><h3>当前论文.docx</h3></div><span className="verified-pill"><span /> VERIFIED</span></div>
          <div className="verification-list">
            {verificationRows.map((row) => (
              <div className="verification-list-row" key={`result-${row.label}`}>
                <div className="verification-list-name"><span className={`report-dot ${row.tone}`} /><div><strong>{row.label}</strong><small>{row.detail}</small></div></div>
                <b>{row.status}</b>
              </div>
            ))}
          </div>
          <div className="verification-panel-footer"><span>可开始复核 · Ready for review</span><span>打开报告 · Open report ↗</span></div>
        </div>
      </section>

      <section className="landing-final-cta" aria-labelledby="final-cta-title">
        <div>
          <p className="landing-eyebrow">准备开始复核 · READY TO REVIEW</p>
          <h2 id="final-cta-title">把下一次论文处理，<br />交给一条可验证的工作流。</h2>
        </div>
        <div className="landing-final-actions">
          <Link className="landing-primary-button" href={taskHref}>上传论文开始处理 <span aria-hidden="true">→</span></Link>
          {!authUser ? <Link className="landing-text-link" href="/register">还没有账号？注册</Link> : <Link className="landing-text-link" href="/dashboard">查看工作台</Link>}
        </div>
      </section>

      <footer className="landing-footer">
        <Link className="landing-brand" href="/"><span className="landing-brand-mark" aria-hidden="true">PF</span><span>PaperForge</span></Link>
        <span>可信学术文档处理工作流 · Verified academic document workflow.</span>
      </footer>
    </main>
  );
}
