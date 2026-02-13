"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { JobTable } from "@/components/jobs/job-table";
import { EmptyState } from "@/components/common/empty-state";
import { PageLoading } from "@/components/common/loading-spinner";
import { useJobs } from "@/hooks/use-jobs";
import { Plus } from "lucide-react";

export default function JobsPage() {
  const { jobs, isLoading } = useJobs();

  if (isLoading) return <PageLoading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">작업 관리</h1>
        <Link href="/jobs/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />새 작업
          </Button>
        </Link>
      </div>

      <Card>
        <CardContent className="pt-6">
          {jobs.length === 0 ? (
            <EmptyState
              title="작업이 없습니다"
              description="엑셀 파일을 업로드하여 새 작업을 시작하세요."
              action={
                <Link href="/jobs/new">
                  <Button>새 작업 만들기</Button>
                </Link>
              }
            />
          ) : (
            <JobTable jobs={jobs} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
