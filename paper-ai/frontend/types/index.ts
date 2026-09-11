export type TaskStatus =
  | "pending"
  | "created"
  | "analyzing"
  | "planning"
  | "executing"
  | "verifying"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "interrupted";

export type WorkspaceRole = "owner" | "admin" | "member";

export type AuthUser = {
  email: string;
  is_admin?: boolean;
};

export type WorkspaceOption = {
  tenant_id: string;
  name: string;
  role: WorkspaceRole;
};
