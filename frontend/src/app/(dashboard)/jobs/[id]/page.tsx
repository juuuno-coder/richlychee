"use client";

import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { JobStatusBadge } from "@/components/jobs/job-status-badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageLoading } from "@/components/common/loading-spinner";
import { EmptyState } from "@/components/common/empty-state";
import { useJobDetail } from "@/hooks/use-jobs";
import { formatDate, formatDuration } from "@/lib/utils";
import apiClient from "@/lib/api-client";
import { Download, XCircle, CheckCircle2, AlertCircle } from "lucide-react";

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  const { job, results, isLoading, mutateJob } = useJobDetail(jobId);

  if (isLoading) return <PageLoading />;
  if (!job) return <EmptyState title="작업을 찾을 수 없습니다" />;

  const isActive = ["VALIDATING", "UPLOADING", "RUNNING"].includes(job.status);
  const progress = job.total_rows > 0 ? (job.processed_rows / job.total_rows) * 100 : 0;

  const handleCancel = async () => {
    if (!confirm("작업을 취소하시겠습니까?")) return;
    await apiClient.post(`/api/v1/jobs/${jobId}/cancel`);
    mutateJob();
  };

  const handleExport = () => {
    window.open(`/api/v1/jobs/${jobId}/results/export`, "_blank");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold">{job.original_filename}</h1>
          <div className="flex items-center gap-2">
            <JobStatusBadge status={job.status} />
            {job.dry_run && <Badge variant="outline">테스트 모드</Badge>}
          </div>
        </div>
        <div className="flex gap-2">
          {isActive && (
            <Button variant="destructive" onClick={handleCancel}>
              <XCircle className="mr-2 h-4 w-4" />취소
            </Button>
          )}
          {job.status === "COMPLETED" && (
            <Button variant="outline" onClick={handleExport}>
              <Download className="mr-2 h-4 w-4" />결과 다운로드
            </Button>
          )}
        </div>
      </div>

      {/* 진행률 */}
      {isActive && (
        <Card>
          <CardContent className="pt-6">
            <div className="mb-2 flex justify-between text-sm">
              <span>{job.processed_rows} / {job.total_rows}</span>
              <span>{progress.toFixed(1)}%</span>
            </div>
            <Progress value={progress} />
          </CardContent>
        </Card>
      )}

      {/* 통계 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">전체</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{job.total_rows}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">처리됨</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{job.processed_rows}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-green-600">성공</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{job.success_count}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-red-600">실패</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{job.failure_count}</div>
          </CardContent>
        </Card>
      </div>

      {/* 시간 정보 */}
      <Card>
        <CardContent className="flex gap-8 pt-6 text-sm">
          <div>
            <span className="text-muted-foreground">생성: </span>
            {formatDate(job.created_at)}
          </div>
          {job.started_at && (
            <div>
              <span className="text-muted-foreground">시작: </span>
              {formatDate(job.started_at)}
            </div>
          )}
          {job.finished_at && (
            <div>
              <span className="text-muted-foreground">소요: </span>
              {formatDuration(job.started_at || job.created_at, job.finished_at)}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 오류 메시지 */}
      {job.error_message && (
        <Card className="border-destructive">
          <CardContent className="flex items-center gap-2 pt-6 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {job.error_message}
          </CardContent>
        </Card>
      )}

      {/* 결과 테이블 */}
      {results && results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>상품별 결과</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>행</TableHead>
                  <TableHead>상품명</TableHead>
                  <TableHead>결과</TableHead>
                  <TableHead>상품 ID</TableHead>
                  <TableHead>오류</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {results.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.row_index + 1}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{r.product_name}</TableCell>
                    <TableCell>
                      {r.success ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-600" />
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{r.naver_product_id || "-"}</TableCell>
                    <TableCell className="max-w-[300px] truncate text-red-600">
                      {r.error_message || "-"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
