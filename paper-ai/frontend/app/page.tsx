"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getStoredAuthUser } from "../lib/auth";

type AuthUser = { email: string };

const workflowSteps = [
  { number: "01", label: "上传论文", detail: "论文 DOCX", tone: "blue" },
  { number: "02", label: "模板解析", detail: "识别格式规则", tone: "violet" },
  { number: "03", label: "AI Agent 处理", detail: "规划 · 执行 · 验证", tone: "amber" },
  { number: "04", label: "验证完成", detail: "报告与最终文档", tone: "green" },
] as const;

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
          <span className="landing-brand-mark" aria-hidden="true">P</span>
          <span>PaperForge</span>
        </Link>

        <nav className="landing-nav-links" aria-label="主导航">
          <a href="#workflow">工作流程</a>
          <a href="#capabilities">产品能力</a>
          {authUser ? <Link href="/dashboard">工作台</Link> : <Link href="/login">登录</Link>}
        </nav>

        <div className="landing-nav-actions">
          {authUser ? <span className="landing-user" title={authUser.email}>{authUser.email}</span> : <Link className="landing-login" href="/login">登录</Link>}
          <Link className="landing-nav-cta" href={taskHref}>开始处理</Link>
        </div>
      </header>

      <section className="landing-hero" aria-labelledby="hero-title">
        <div className="landing-hero-copy">
          <p className="landing-eyebrow"><span aria-hidden="true" />学术文档智能处理</p>
          <h1 id="hero-title">让论文格式修改<br /><em>从上传到验证，一次完成。</em></h1>
          <p className="landing-hero-lead">
            上传论文和格式模板，PaperForge 自动完成规则分析、文档处理、修改验证，并生成可下载报告。
          </p>
          <div className="landing-hero-actions">
            <Link className="landing-primary-button" href={taskHref}>开始处理 <span aria-hidden="true">→</span></Link>
            <a className="landing-secondary-button" href="#workflow">查看工作流程 <span aria-hidden="true">↓</span></a>
          </div>
          <p className="landing-hero-note"><span aria-hidden="true">✓</span> 支持 DOCX · 可选格式模板 · 每一步都有验证</p>
        </div>

        <div className="product-preview-wrap" aria-label="PaperForge 产品流程示意">
          <div className="product-preview-label"><span className="preview-dot" />产品界面预览 <span>示意结构</span></div>
          <div className="product-preview">
            <div className="preview-window-bar">
              <div className="preview-window-dots" aria-hidden="true"><i /><i /><i /></div>
              <span>新建论文任务</span>
              <span className="preview-window-status">工作流</span>
            </div>
            <div className="preview-window-content">
              <div className="preview-window-heading">
                <div>
                  <span className="preview-kicker">PAPERFORGE WORKFLOW</span>
                  <h2>从上传到验证</h2>
                </div>
                <span className="preview-structure-tag">界面结构示意</span>
              </div>
              <div className="preview-file-row">
                <span className="preview-file-icon" aria-hidden="true">DOC</span>
                <div><strong>你的论文文件</strong><small>上传后开始识别与处理</small></div>
                <span className="preview-file-action">上传</span>
              </div>
              <div className="preview-flow-list">
                {workflowSteps.map((step, index) => (
                  <div className="preview-flow-step" key={step.number}>
                    <div className={`preview-step-marker ${step.tone}`}><span>{step.number}</span></div>
                    <div className="preview-step-copy"><strong>{step.label}</strong><small>{step.detail}</small></div>
                    <span className={`preview-step-state ${index === 0 ? "current" : ""}`}>{index === 0 ? "待开始" : "后续步骤"}</span>
                    {index < workflowSteps.length - 1 ? <span className="preview-flow-line" aria-hidden="true" /> : null}
                  </div>
                ))}
              </div>
              <div className="preview-footer-row"><span>完成后可查看修改报告与最终文档</span><span className="preview-footer-arrow" aria-hidden="true">↗</span></div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-workflow" id="workflow" aria-labelledby="workflow-title">
        <div className="landing-section-heading">
          <p className="landing-eyebrow">A CLEARER WAY TO WORK</p>
          <h2 id="workflow-title">把复杂的论文处理，<br />变成一条清晰的路径。</h2>
          <p>从文件进入系统的那一刻起，你始终知道正在发生什么、下一步是什么。</p>
        </div>
        <div className="workflow-rail">
          {workflowSteps.map((step, index) => (
            <article className="workflow-rail-item" key={step.number}>
              <span className={`workflow-rail-number ${step.tone}`}>{step.number}</span>
              <div><h3>{step.label}</h3><p>{step.detail}</p></div>
              {index < workflowSteps.length - 1 ? <span className="workflow-rail-arrow" aria-hidden="true">→</span> : null}
            </article>
          ))}
        </div>
      </section>

      <section className="landing-capabilities" id="capabilities" aria-labelledby="capabilities-title">
        <div className="landing-section-heading compact">
          <p className="landing-eyebrow">BUILT FOR CAREFUL WORK</p>
          <h2 id="capabilities-title">每一次修改，都值得被认真对待。</h2>
        </div>
        <div className="capability-grid">
          <article className="capability-card">
            <span className="capability-index">01</span>
            <div className="capability-icon icon-document" aria-hidden="true"><i /><i /><i /></div>
            <h3>智能模板解析</h3>
            <p>自动识别学校、学院或期刊模板中的格式规范，减少手动对照和反复调整。</p>
          </article>
          <article className="capability-card">
            <span className="capability-index">02</span>
            <div className="capability-icon icon-agent" aria-hidden="true"><i /><i /><i /></div>
            <h3>AI Agent 自动处理</h3>
            <p>规划、执行、验证完整流程，让论文处理从一组零散操作变成连续的工作流。</p>
          </article>
          <article className="capability-card">
            <span className="capability-index">03</span>
            <div className="capability-icon icon-proof" aria-hidden="true"><i /></div>
            <h3>修改过程可追溯</h3>
            <p>保留处理轨迹、修改报告与最终文档，重要变化清楚可见，方便复核和交付。</p>
          </article>
        </div>
      </section>

      <section className="landing-final-cta" aria-labelledby="final-cta-title">
        <div>
          <p className="landing-eyebrow">READY WHEN YOU ARE</p>
          <h2 id="final-cta-title">从下一版论文开始，<br />让格式修改更有把握。</h2>
        </div>
        <div className="landing-final-actions">
          <Link className="landing-primary-button" href={taskHref}>上传论文开始处理 <span aria-hidden="true">→</span></Link>
          {!authUser ? <Link className="landing-text-link" href="/register">还没有账号？注册</Link> : <Link className="landing-text-link" href="/dashboard">查看工作台</Link>}
        </div>
      </section>

      <footer className="landing-footer">
        <Link className="landing-brand" href="/"><span className="landing-brand-mark" aria-hidden="true">P</span><span>PaperForge</span></Link>
        <span>让认真完成的论文，拥有同样认真的呈现。</span>
      </footer>
    </main>
  );
}
