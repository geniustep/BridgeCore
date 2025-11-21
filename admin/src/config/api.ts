// API configuration

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'BridgeCore Admin';

// Log API configuration on load
console.log('[API CONFIG]', {
  API_BASE_URL,
  VITE_API_URL: import.meta.env.VITE_API_URL,
  APP_NAME,
  timestamp: new Date().toISOString()
});

// API endpoints
export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/admin/auth/login',
  LOGOUT: '/admin/auth/logout',
  ME: '/admin/auth/me',

  // Tenants
  TENANTS: '/admin/tenants',
  TENANT: (id: string) => `/admin/tenants/${id}`,
  TENANT_SUSPEND: (id: string) => `/admin/tenants/${id}/suspend`,
  TENANT_ACTIVATE: (id: string) => `/admin/tenants/${id}/activate`,
  TENANT_TEST: (id: string) => `/admin/tenants/${id}/test-connection`,
  TENANT_STATS: '/admin/tenants/statistics',

  // Plans
  PLANS: '/admin/plans',
  PLAN: (id: string) => `/admin/plans/${id}`,

  // Analytics
  ANALYTICS_OVERVIEW: '/admin/analytics/overview',
  ANALYTICS_TOP_TENANTS: '/admin/analytics/top-tenants',
  ANALYTICS_TENANT: (id: string) => `/admin/analytics/tenants/${id}`,
  ANALYTICS_TENANT_DAILY: (id: string) => `/admin/analytics/tenants/${id}/daily`,

  // Logs
  LOGS_USAGE: '/admin/logs/usage',
  LOGS_USAGE_SUMMARY: '/admin/logs/usage/summary',
  LOGS_ERRORS: '/admin/logs/errors',
  LOGS_ERRORS_SUMMARY: '/admin/logs/errors/summary',
  LOGS_ERROR_RESOLVE: (id: number) => `/admin/logs/errors/${id}/resolve`,
};

// Local storage keys
export const STORAGE_KEYS = {
  TOKEN: 'bridgecore_admin_token',
  ADMIN: 'bridgecore_admin_user',
};
