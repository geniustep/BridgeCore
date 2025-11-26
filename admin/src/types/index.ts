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
  created_at: string;
  endpoint: string;
  method: string;
  status_code: number;
  response_time_ms: number | null;
  client_ip: string | null;
  user_agent: string | null;
  request_body_size: number | null;
  response_body_size: number | null;
  odoo_model: string | null;
  odoo_method: string | null;
  error_message: string | null;
}

export interface ErrorLog {
  id: number;
  tenant_id: string;
  user_id: string | null;
  created_at: string;
  error_type: string;
  error_message: string;
  stack_trace: string | null;
  endpoint: string | null;
  request_id: string | null;
  request_data: Record<string, any> | null;
  severity: 'low' | 'medium' | 'high' | 'critical';
  resolved: boolean;
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
  database?: string;
  version?: string;
  user_info?: {
    uid?: number;
    username?: string;
    name?: string;
    company_id?: number;
    partner_id?: number;
    session_id?: string;
  };
  details?: {
    authenticated?: boolean;
    uid?: number;
    database_query_success?: boolean;
    user_data?: {
      name?: string;
      login?: string;
      email?: string;
    };
    server_serie?: string;
    [key: string]: any;
  };
}

// ============= Multi-System Types =============

export type SystemType = 'odoo' | 'moodle' | 'sap' | 'salesforce' | 'dynamics' | 'custom';
export type SystemStatus = 'active' | 'inactive' | 'error' | 'testing';

export interface ExternalSystem {
  id: string;
  system_type: SystemType;
  name: string;
  description: string | null;
  version: string | null;
  status: SystemStatus;
  is_enabled: boolean;
  default_config: Record<string, any> | null;
  capabilities: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TenantSystem {
  id: string;
  tenant_id: string;
  system_id: string;
  connection_config: Record<string, any>;
  is_active: boolean;
  is_primary: boolean;
  last_connection_test: string | null;
  last_successful_connection: string | null;
  connection_error: string | null;
  custom_config: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  external_system?: ExternalSystem;
}

export interface TenantSystemCreate {
  tenant_id: string;
  system_id: string;
  connection_config: Record<string, any>;
  is_active?: boolean;
  is_primary?: boolean;
  custom_config?: Record<string, any>;
}

export interface TenantSystemUpdate {
  connection_config?: Record<string, any>;
  is_active?: boolean;
  is_primary?: boolean;
  custom_config?: Record<string, any>;
}

export interface OdooConnectionConfig {
  url: string;
  database: string;
  username: string;
  password: string;
}

export interface MoodleConnectionConfig {
  url: string;
  token: string;
  service?: string;
}

export interface SystemConnectionTestRequest {
  system_type: SystemType;
  connection_config: Record<string, any>;
}

export interface SystemConnectionTestResponse {
  success: boolean;
  message: string;
  system_info?: {
    type: string;
    sitename?: string;
    version?: string;
    url?: string;
    uid?: number;
    database?: string;
  };
  error?: string;
  tested_at: string;
}
