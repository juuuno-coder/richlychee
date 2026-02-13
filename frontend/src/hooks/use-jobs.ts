import useSWR from "swr";
import { apiFetcher } from "@/lib/api-client";
import type { Job, PaginatedResponse, ProductResult } from "@/types";

export function useJobs(status?: string) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  params.set("size", "100");

  const { data, error, isLoading, mutate } = useSWR<PaginatedResponse<Job>>(
    `/api/v1/jobs?${params.toString()}`,
    apiFetcher
  );

  return {
    jobs: data?.items || [],
    total: data?.total || 0,
    isLoading,
    error,
    mutate,
  };
}

export function useJobDetail(jobId: string) {
  const { data: job, error, isLoading, mutate: mutateJob } = useSWR<Job>(
    jobId ? `/api/v1/jobs/${jobId}` : null,
    apiFetcher,
    {
      refreshInterval: (data) => {
        if (!data) return 0;
        const active = ["VALIDATING", "UPLOADING", "RUNNING"];
        return active.includes(data.status) ? 3000 : 0;
      },
    }
  );

  const { data: resultsData } = useSWR<PaginatedResponse<ProductResult>>(
    jobId ? `/api/v1/jobs/${jobId}/results?size=200` : null,
    apiFetcher,
    {
      refreshInterval: job && ["RUNNING"].includes(job.status) ? 5000 : 0,
    }
  );

  return {
    job,
    results: resultsData?.items || [],
    isLoading,
    error,
    mutateJob,
  };
}
