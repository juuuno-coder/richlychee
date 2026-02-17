// API 타입 정의

export interface User {
  id: string;
  email: string;
  name: string;
  provider: string;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Credential {
  id: string;
  label: string;
  naver_client_id: string;
  is_verified: boolean;
  last_verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export type JobStatus =
  | "PENDING"
  | "VALIDATING"
  | "UPLOADING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export interface Job {
  id: string;
  status: JobStatus;
  original_filename: string;
  dry_run: boolean;
  total_rows: number;
  processed_rows: number;
  success_count: number;
  failure_count: number;
  validation_errors: ValidationItem[] | null;
  validation_warnings: ValidationItem[] | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface ValidationItem {
  row: number;
  field: string;
  message: string;
}

export interface ProductResult {
  id: string;
  row_index: number;
  product_name: string;
  success: boolean;
  naver_product_id: string | null;
  error_message: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// 구독 요금제 타입
export interface SubscriptionPlan {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  price_monthly: number;
  price_yearly: number;
  limits: {
    crawl_jobs_per_month: number;
    products_per_crawl: number;
    product_registrations_per_month: number;
    concurrent_crawls: number;
    schedules: number;
    price_alerts: number;
    stored_products: number;
  };
  is_active: boolean;
  is_popular: boolean;
}

export interface UserSubscription {
  id: string;
  user_id: string;
  plan: SubscriptionPlan;
  status: string;
  billing_cycle: string;
  starts_at: string;
  ends_at: string;
  auto_renew: boolean;
  usage: Record<string, number>;
  usage_reset_at: string;
}

export interface UsageStats {
  plan: {
    name: string;
    display_name: string;
    is_popular: boolean;
  };
  limits: Record<string, number>;
  usage: Record<string, number>;
  usage_reset_at: string;
  features: Record<string, {
    limit: number;
    current: number;
    remaining: number;
    usage_percent: number;
  }>;
}

// 크롤링 타입
export type CrawlJobStatus =
  | "PENDING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export interface CrawlJob {
  id: string;
  user_id: string;
  status: CrawlJobStatus;
  target_url: string;
  target_type: string;
  crawl_config: Record<string, any> | null;
  total_items: number;
  crawled_items: number;
  success_count: number;
  failure_count: number;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface CrawledProduct {
  id: string;
  crawl_job_id: string;
  user_id: string;
  original_title: string;
  original_price: number;
  original_currency: string;
  original_images: string[];
  original_url: string;
  product_name: string | null;
  sale_price: number | null;
  category_id: string | null;
  is_registered: boolean;
  naver_product_id: string | null;
  crawled_at: string;
}

export interface CrawlPreset {
  id: string;
  name: string;
  site_url: string;
  description: string;
  crawler_type: string;
  usage_count: number;
}

// 결제 타입
export type PaymentStatus =
  | "pending"
  | "paid"
  | "failed"
  | "refunded"
  | "cancelled";

export interface Payment {
  id: string;
  user_id: string;
  subscription_id: string;
  payment_id: string;
  order_id: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  payment_method: string | null;
  plan_name: string;
  billing_cycle: string;
  portone_response: any;
  refund_reason: string | null;
  refunded_at: string | null;
  created_at: string;
}

export interface PaymentPrepareResponse {
  order_id: string;
  payment_id: string;
  amount: number;
  currency: string;
  plan_name: string;
  billing_cycle: string;
  customer_name: string;
  customer_email: string;
}

export interface PaymentVerifyResponse {
  success: boolean;
  status: string;
  message: string;
}
