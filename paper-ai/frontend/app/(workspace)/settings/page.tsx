import Link from "next/link";

export default function SettingsPage() {
  return <section className="workspace-page"><header className="workspace-page-heading"><div><p className="eyebrow">SETTINGS</p><h1>工作区设置</h1><p>成员、邀请、工作区名称与 ownership transfer 均继续使用既有权限模型。</p></div><Link className="app-primary-link" href="/">打开设置</Link></header><section className="workspace-panel workspace-empty"><strong>设置已保留在论文处理工作台</strong><p>当前页面提供统一入口；具体治理操作仍由原有界面和后端 RBAC 校验负责。</p><Link href="/">前往工作区设置</Link></section></section>;
}
