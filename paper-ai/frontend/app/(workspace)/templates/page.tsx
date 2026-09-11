import Link from "next/link";

export default function TemplatesPage() {
  return <section className="workspace-page"><header className="workspace-page-heading"><div><p className="eyebrow">TEMPLATES</p><h1>模板库</h1><p>模板仍沿用现有的安全上传、租户隔离和任务 provenance 流程。</p></div><Link className="app-primary-link" href="/">管理模板</Link></header><section className="workspace-panel workspace-empty"><strong>模板管理已保留在论文处理工作台</strong><p>在工作台上传或选择 DOCX 模板后，现有 API 会继续按当前工作空间处理，不改变任何业务逻辑。</p><Link href="/">前往模板管理</Link></section></section>;
}
