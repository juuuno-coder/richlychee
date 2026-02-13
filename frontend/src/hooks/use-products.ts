import useSWR from "swr";
import { apiFetcher } from "@/lib/api-client";

export function useProducts(credentialId: string, keyword?: string) {
  const params = new URLSearchParams();
  if (credentialId) params.set("credential_id", credentialId);
  if (keyword) params.set("product_name", keyword);

  const { data, error, isLoading, mutate } = useSWR(
    credentialId ? `/api/v1/products?${params.toString()}` : null,
    apiFetcher
  );

  return {
    products: data || [],
    isLoading,
    error,
    mutate,
  };
}
