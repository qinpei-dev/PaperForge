import { AppShell } from "../../components/app-shell";

export default function WorkspaceLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <AppShell>{children}</AppShell>;
}
