import Link from "next/link";
import type { ReactNode } from "react";
import styles from "./AuthLayout.module.css";

const capabilities = [
  { index: "01", title: "模板解析", description: "识别论文结构与格式要求" },
  { index: "02", title: "格式自动修正", description: "统一标题、正文与页面规范" },
  { index: "03", title: "修改验证", description: "复查处理结果，保留可核验状态" },
  { index: "04", title: "可追踪处理报告", description: "记录变更、预览与下载结果" },
];

type AuthLayoutProps = {
  eyebrow: string;
  title: string;
  description: string;
  switchPrompt: string;
  switchLabel: string;
  switchHref: "/login" | "/register";
  children: ReactNode;
};

function Brand({ className = "" }: { className?: string }) {
  return (
    <span className={`${styles.brand} ${className}`.trim()}>
      <span className={styles.brandMark} aria-hidden="true">PF</span>
      <span>PaperForge</span>
    </span>
  );
}

export function AuthLayout({
  eyebrow,
  title,
  description,
  switchPrompt,
  switchLabel,
  switchHref,
  children,
}: AuthLayoutProps) {
  return (
    <main className={styles.page}>
      <div className={styles.frame}>
        <aside className={styles.brandPanel} aria-label="PaperForge 产品信息">
          <Link href="/" className={styles.brandLink} aria-label="返回 PaperForge 首页">
            <Brand />
          </Link>

          <div className={styles.brandCopy}>
            <p className={styles.brandKicker}>VERIFIED ACADEMIC WORKSPACE</p>
            <h1>让论文处理更清晰、可靠、可追踪。</h1>
            <p className={styles.brandDescription}>
              PaperForge 是一个智能论文格式处理平台，从模板解析到修改验证，将复杂的文档处理收进一个可复核的工作空间。
            </p>
          </div>

          <ul className={styles.capabilities}>
            {capabilities.map((capability) => (
              <li key={capability.index} className={styles.capability}>
                <span className={styles.capabilityIndex}>{capability.index}</span>
                <span>
                  <strong>{capability.title}</strong>
                  <small>{capability.description}</small>
                </span>
              </li>
            ))}
          </ul>

          <p className={styles.brandFoot}>PaperForge · Academic document workflow</p>
        </aside>

        <section className={styles.authPanel} aria-labelledby="auth-title">
          <Link href="/" className={styles.mobileBrandLink} aria-label="返回 PaperForge 首页">
            <Brand className={styles.mobileBrand} />
          </Link>

          <header className={styles.authHeader}>
            <p className={styles.authEyebrow}>{eyebrow}</p>
            <h2 id="auth-title">{title}</h2>
            <p className={styles.authDescription}>{description}</p>
          </header>

          {children}

          <p className={styles.authSwitch}>
            {switchPrompt} <Link href={switchHref}>{switchLabel}</Link>
          </p>
          <p className={styles.authFoot}>安全登录 · 进入你的论文处理工作空间</p>
        </section>
      </div>
    </main>
  );
}
