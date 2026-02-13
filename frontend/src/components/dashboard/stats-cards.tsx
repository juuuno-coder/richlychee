"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ListTodo, Play, CheckCircle2, XCircle } from "lucide-react";
import type { Job } from "@/types";

interface StatsCardsProps {
  jobs: Job[];
}

export function StatsCards({ jobs }: StatsCardsProps) {
  const total = jobs.length;
  const running = jobs.filter((j) => ["VALIDATING", "UPLOADING", "RUNNING"].includes(j.status)).length;
  const completed = jobs.filter((j) => j.status === "COMPLETED").length;
  const failed = jobs.filter((j) => j.status === "FAILED").length;

  const stats = [
    { label: "총 작업", value: total, icon: ListTodo, color: "text-blue-600" },
    { label: "진행 중", value: running, icon: Play, color: "text-yellow-600" },
    { label: "성공", value: completed, icon: CheckCircle2, color: "text-green-600" },
    { label: "실패", value: failed, icon: XCircle, color: "text-red-600" },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">{stat.label}</CardTitle>
            <stat.icon className={`h-4 w-4 ${stat.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stat.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
