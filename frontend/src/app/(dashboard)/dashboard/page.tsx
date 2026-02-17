"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatsCards } from "@/components/dashboard/stats-cards";
import UsageStats from "@/components/dashboard/usage-stats";
import { JobTable } from "@/components/jobs/job-table";
import { EmptyState } from "@/components/common/empty-state";
import { PageLoading } from "@/components/common/loading-spinner";
import { useJobs } from "@/hooks/use-jobs";
import { Plus } from "lucide-react";

export default function DashboardPage() {
  const { jobs, isLoading } = useJobs();

  if (isLoading) return <PageLoading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">대시보드</h1>
        <Link href="/jobs/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />새 작업
          </Button>
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <StatsCards jobs={jobs} />
        </div>
        <UsageStats />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>최근 작업</CardTitle>
        </CardHeader>
        <CardContent>
          {jobs.length === 0 ? (
            <EmptyState
              title="아직 작업이 없습니다"
              description="새 작업을 만들어 상품을 등록해보세요."
              action={
                <Link href="/jobs/new">
                  <Button>새 작업 만들기</Button>
                </Link>
              }
            />
          ) : (
            <>
              <JobTable jobs={jobs} limit={5} />
              {jobs.length > 5 && (
                <div className="mt-4 text-center">
                  <Link href="/jobs">
                    <Button variant="outline">전체 보기</Button>
                  </Link>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
