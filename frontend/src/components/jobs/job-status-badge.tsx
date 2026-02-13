import { Badge } from "@/components/ui/badge";
import type { JobStatus } from "@/types";

const statusConfig: Record<JobStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info" }> = {
  PENDING: { label: "대기", variant: "secondary" },
  VALIDATING: { label: "검증 중", variant: "info" },
  UPLOADING: { label: "업로드 중", variant: "info" },
  RUNNING: { label: "진행 중", variant: "warning" },
  COMPLETED: { label: "완료", variant: "success" },
  FAILED: { label: "실패", variant: "destructive" },
  CANCELLED: { label: "취소", variant: "outline" },
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  const config = statusConfig[status];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
