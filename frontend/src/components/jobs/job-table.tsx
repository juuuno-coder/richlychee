"use client";

import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { JobStatusBadge } from "@/components/jobs/job-status-badge";
import { formatDate } from "@/lib/utils";
import type { Job } from "@/types";

interface JobTableProps {
  jobs: Job[];
  limit?: number;
}

export function JobTable({ jobs, limit }: JobTableProps) {
  const displayed = limit ? jobs.slice(0, limit) : jobs;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>파일명</TableHead>
          <TableHead>상태</TableHead>
          <TableHead className="text-right">전체</TableHead>
          <TableHead className="text-right">성공</TableHead>
          <TableHead className="text-right">실패</TableHead>
          <TableHead>생성일</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {displayed.map((job) => (
          <TableRow key={job.id}>
            <TableCell>
              <Link href={`/jobs/${job.id}`} className="text-primary hover:underline">
                {job.original_filename}
              </Link>
            </TableCell>
            <TableCell>
              <JobStatusBadge status={job.status} />
            </TableCell>
            <TableCell className="text-right">{job.total_rows}</TableCell>
            <TableCell className="text-right text-green-600">{job.success_count}</TableCell>
            <TableCell className="text-right text-red-600">{job.failure_count}</TableCell>
            <TableCell className="text-muted-foreground">{formatDate(job.created_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
