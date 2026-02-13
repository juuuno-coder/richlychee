import useSWR from "swr";
import { apiFetcher } from "@/lib/api-client";
import type { Credential } from "@/types";

export function useCredentials() {
  const { data, error, isLoading, mutate } = useSWR<Credential[]>(
    "/api/v1/credentials",
    apiFetcher
  );

  return {
    credentials: data || [],
    isLoading,
    error,
    mutate,
  };
}
