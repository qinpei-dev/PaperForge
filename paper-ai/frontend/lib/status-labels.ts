import type { TaskStatus } from "../types";

export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  pending: "等待处理",
  created: "等待处理",
  analyzing: "文档解析",
  planning: "格式规划",
  executing: "自动修改",
  verifying: "质量验证",
  running: "处理中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
  interrupted: "已中断",
};

export const WORKFLOW_STATUS_LABELS: Record<string, string> = {
  analyzing: "分析中",
  planning: "规划中",
  executing: "执行中",
  verifying: "验证中",
  completed: "完成",
  failed: "失败",
};

export function taskStatusLabel(status: string) {
  return TASK_STATUS_LABELS[status as TaskStatus] || status;
}

export function workflowStatusLabel(status?: string | null) {
  return status ? WORKFLOW_STATUS_LABELS[status] || status : "";
}
