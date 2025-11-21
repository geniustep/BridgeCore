// Types for BridgeCore Admin Dashboard

export interface Admin {
  id: string;
  email: string;
  full_name: string;
  role: 'super_admin' | 'admin' | 'support';
  is_active: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  admin: Admin;
  token: string;
  token_type: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  contact_email: string;
  contact_phone: string | null;
  odoo_url: string;
  odoo_database: string;
  odoo_version: string | null;
  odoo_username: string;
  status: 'active' | 'suspended' | 'trial' | 'deleted';
  plan_id: string;
  trial_ends_at: string | null;
  subscription_ends_at: string | null;
  max_requests_per_day: number | null;
  max_requests_per_hour: number | null;
  allowed_models: string[];
  allowed_features: string[];
  created_by: string | null;
  last_active_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TenantCreate {
  name: string;
  slug: string;
  description?: string;
  contact_email: string;
  contact_phone?: string;
  odoo_url: string;
  odoo_database: string;
  odoo_version?: string;
  odoo_username: string;
  odoo_password: string;
  plan_id: string;
  max_requests_per_day?: number;
  max_requests_per_hour?: number;
  allowed_models?: string[];
  allowed_features?: string[];
  trial_ends_at?: string;
  subscription_ends_at?: string;
}

export interface TenantUpdate {
  name?: string;
  slug?: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  odoo_url?: string;
  odoo_database?: string;
  odoo_version?: string;
  odoo_username?: string;
  odoo_password?: string;
  status?: string;
  plan_id?: string;
  max_requests_per_day?: number;
  max_requests_per_hour?: number;
  allowed_models?: string[];
  allowed_features?: string[];
  trial_ends_at?: string;
  subscription_ends_at?: string;
}

export interface Plan {
  id: string;
  name: string;
  description: string | null;
  max_requests_per_day: number;
  max_requests_per_hour: number;
  max_users: number;
  max_storage_gb: number;
  features: string[];
  price_monthly: number;
  price_yearly: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UsageLog {
  id: number;
  tenant_id: string;
  user_id: string | null;
  timestamp: string;
  endpoint: string;
  method: string;
  model_name: string | null;
  request_size_bytes: number | null;
  response_size_bytes: number | null;
  response_time_ms: number | null;
  status_code: number;
  ip_address: string | null;
}

export interface ErrorLog {
  id: number;
  tenant_id: string;
  timestamp: string;
  error_type: string;
  error_message: string;
  stack_trace: string | null;
  endpoint: string | null;
  method: string | null;
  severity: 'low' | 'medium' | 'high' | 'critical';
  is_resolved: boolean;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_notes: string | null;
}

export interface SystemOverview {
  tenants: {
    total: number;
    active: number;
    trial: number;
    suspended: number;
  };
  usage_24h: {
    total_requests: number;
    successful_requests: number;
    success_rate_percent: number;
    avg_response_time_ms: number;
    total_data_transferred_mb: number;
  };
}

export interface TenantAnalytics {
  summary: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    success_rate_percent: number;
    unique_users: number;
  };
  performance: {
    avg_response_time_ms: number;
    max_response_time_ms: number;
    min_response_time_ms: number;
  };
  data_transfer: {
    total_bytes: number;
    total_mb: number;
    total_gb: number;
  };
  top_endpoints: Array<{ endpoint: string; count: number }>;
  top_models: Array<{ model: string; count: number }>;
  period_days: number;
}

export interface DailyStats {
  date: string;
  total_requests: number;
  successful_requests?: number;
  failed_requests?: number;
  avg_response_time_ms: number;
  unique_users?: number;
}

export interface TopTenant {
  tenant_id: string;
  tenant_name: string;
  tenant_slug: string;
  request_count: number;
  avg_response_time_ms: number;
}

export interface TenantStatistics {
  total: number;
  active: number;
  suspended: number;
  trial: number;
  deleted: number;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  url: string;
}
