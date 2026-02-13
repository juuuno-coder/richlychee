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
