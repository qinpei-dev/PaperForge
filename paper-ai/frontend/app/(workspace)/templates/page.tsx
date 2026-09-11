import Link from "next/link";

export default function TemplatesPage() {
  return <section className="workspace-page"><header className="workspace-page-heading"><div><p className="eyebrow">TEMPLATES</p><h1>模板库</h1><p>模板仍沿用现有的安全上传、租户隔离和任务 provenance 流程。</p></div><Link className="app-primary-link" href="/tasks/new">新建任务并选择模板</Link></header><section className="workspace-panel workspace-empty"><strong>模板管理已保留在新建任务流程</strong><p>在新建论文任务中上传或选择 DOCX 模板，现有 API 会继续按当前工作空间处理，不改变任何业务逻辑。</p><Link href="/tasks/new">前往选择模板</Link></section></section>;
}
