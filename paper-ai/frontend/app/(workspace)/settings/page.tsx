import Link from "next/link";

export default function SettingsPage() {
  return <section className="workspace-page"><header className="workspace-page-heading"><div><p className="eyebrow">SETTINGS</p><h1>工作区设置</h1><p>成员、邀请、工作区名称与 ownership transfer 均继续使用既有权限模型。</p></div><Link className="app-primary-link" href="/dashboard">返回工作台</Link></header><section className="workspace-panel workspace-empty"><strong>设置入口正在整理</strong><p>当前工作区的核心处理流程已经可用。成员与权限治理仍由后端 RBAC 保护，后续会在此页面提供完整设置入口。</p><Link href="/dashboard">返回工作台</Link></section></section>;
}
