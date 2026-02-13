import useSWR from "swr";
import { apiFetcher } from "@/lib/api-client";

export function useCategories(keyword: string, credentialId: string) {
  const shouldFetch = keyword.length > 0 && credentialId;
  const { data, error, isLoading } = useSWR(
    shouldFetch
      ? `/api/v1/categories/search?keyword=${encodeURIComponent(keyword)}&credential_id=${credentialId}`
      : null,
    apiFetcher,
    { dedupingInterval: 500 }
  );

  return {
    categories: (data as any[]) || [],
    isLoading,
    error,
  };
}
