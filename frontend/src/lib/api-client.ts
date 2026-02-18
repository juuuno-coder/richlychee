import axios from "axios";
import { getSession } from "next-auth/react";

const apiClient = axios.create({
  baseURL: "",
  headers: { "Content-Type": "application/json" },
});

// 요청 인터셉터: JWT 토큰 자동 주입
apiClient.interceptors.request.use(async (config) => {
  const session = await getSession();
  if (session?.accessToken) {
    config.headers.Authorization = `Bearer ${session.accessToken}`;
  }
  return config;
});

// 응답 인터셉터: 401 시 세션 무효화
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        const { signOut } = await import("next-auth/react");
        await signOut({ callbackUrl: "/login" });
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// 서버 사이드용 fetcher
export async function apiFetcher<T>(url: string): Promise<T> {
  const session = await getSession();
  const res = await apiClient.get<T>(url, {
    headers: session?.accessToken
      ? { Authorization: `Bearer ${session.accessToken}` }
      : {},
  });
  return res.data;
}

// 구독 요금제 API
export const subscriptionApi = {
  getPlans: () => apiClient.get("/api/v1/subscriptions/plans"),
  getMySubscription: () => apiClient.get("/api/v1/subscriptions/my"),
  getUsage: () => apiClient.get("/api/v1/subscriptions/usage"),
  upgrade: (planId: string, billingCycle: string) =>
    apiClient.post("/api/v1/subscriptions/upgrade", { plan_id: planId, billing_cycle: billingCycle }),
  cancel: () => apiClient.post("/api/v1/subscriptions/cancel"),
};

// 크롤링 API
export const crawlApi = {
  // 크롤링 작업
  listJobs: (params?: { status?: string; page?: number; size?: number }) =>
    apiClient.get("/api/v1/crawl-jobs", { params }),
  createJob: (data: { target_url: string; target_type: string; crawl_config?: any }) =>
    apiClient.post("/api/v1/crawl-jobs", data),
  getJob: (id: string) => apiClient.get(`/api/v1/crawl-jobs/${id}`),
  startJob: (id: string) => apiClient.post(`/api/v1/crawl-jobs/${id}/start`),
  cancelJob: (id: string) => apiClient.post(`/api/v1/crawl-jobs/${id}/cancel`),
  deleteJob: (id: string) => apiClient.delete(`/api/v1/crawl-jobs/${id}`),
  getJobProducts: (id: string, params?: { page?: number; size?: number }) =>
    apiClient.get(`/api/v1/crawl-jobs/${id}/products`, { params }),

  // 크롤링된 상품
  listProducts: (params?: { crawl_job_id?: string; page?: number; size?: number }) =>
    apiClient.get("/api/v1/crawled-products", { params }),
  getProduct: (id: string) => apiClient.get(`/api/v1/crawled-products/${id}`),
  updateProduct: (id: string, data: any) => apiClient.put(`/api/v1/crawled-products/${id}`, data),
  deleteProduct: (id: string) => apiClient.delete(`/api/v1/crawled-products/${id}`),
  adjustPrice: (productIds: string[], adjustmentType: string, adjustmentValue: number) =>
    apiClient.post("/api/v1/crawled-products/adjust-price", {
      product_ids: productIds,
      adjustment_type: adjustmentType,
      adjustment_value: adjustmentValue,
    }),
  register: (productIds: string[], credentialId: string, dryRun: boolean = false) =>
    apiClient.post("/api/v1/crawled-products/register", {
      product_ids: productIds,
      credential_id: credentialId,
      dry_run: dryRun,
    }),
  export: (params?: { crawl_job_id?: string }) =>
    apiClient.get("/api/v1/crawled-products/export", { params, responseType: "blob" }),

  // 원클릭 크롤링
  quickCrawl: (url: string, autoStart: boolean = true) =>
    apiClient.post("/api/v1/quick-crawl", { url, auto_start: autoStart }),
  getPresets: () => apiClient.get("/api/v1/quick-crawl/presets"),
  detectConfig: (url: string) => apiClient.post(`/api/v1/quick-crawl/detect?url=${encodeURIComponent(url)}`),
};

// 결제 API
export const paymentApi = {
  prepare: (planId: string, billingCycle: string) =>
    apiClient.post("/api/v1/payments/prepare", { plan_id: planId, billing_cycle: billingCycle }),
  verify: (paymentId: string, portonePaymentId: string) =>
    apiClient.post("/api/v1/payments/verify", { payment_id: paymentId, portone_payment_id: portonePaymentId }),
  cancel: (paymentId: string, reason: string) =>
    apiClient.post("/api/v1/payments/cancel", { payment_id: paymentId, reason }),
  getHistory: (params?: { page?: number; size?: number }) =>
    apiClient.get("/api/v1/payments/history", { params }),
  getDetail: (paymentId: string) => apiClient.get(`/api/v1/payments/${paymentId}`),
};
