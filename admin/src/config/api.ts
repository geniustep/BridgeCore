// API configuration

// Use relative path for production, absolute for local dev
// In production (https://bridgecore.geniura.com/admin/), requests go to same domain
// In local dev (http://localhost:8001), requests go to localhost:8001 which proxies to API
const isProduction = window.location.hostname !== 'localhost';
export const API_BASE_URL = isProduction ? '' : (import.meta.env.VITE_API_URL || 'http://localhost:8001');
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'BridgeCore Admin';

// Log API configuration on load
console.log('[API CONFIG]', {
  API_BASE_URL,
  isProduction,
  hostname: window.location.hostname,
  VITE_API_URL: import.meta.env.VITE_API_URL,
  APP_NAME,
  timestamp: new Date().toISOString()
});

// API endpoints - use /api prefix for clear separation from frontend routes
const API_PREFIX = '/api';

export const API_ENDPOINTS = {
  // Auth
  LOGIN: `${API_PREFIX}/admin/auth/login`,
  LOGOUT: `${API_PREFIX}/admin/auth/logout`,
  ME: `${API_PREFIX}/admin/auth/me`,

  // Tenants
  TENANTS: `${API_PREFIX}/admin/tenants`,
  TENANT: (id: string) => `${API_PREFIX}/admin/tenants/${id}`,
  TENANT_SUSPEND: (id: string) => `${API_PREFIX}/admin/tenants/${id}/suspend`,
  TENANT_ACTIVATE: (id: string) => `${API_PREFIX}/admin/tenants/${id}/activate`,
  TENANT_TEST: (id: string) => `${API_PREFIX}/admin/tenants/${id}/test-connection`,
  TENANT_STATS: `${API_PREFIX}/admin/tenants/statistics`,

  // Plans
  PLANS: `${API_PREFIX}/admin/plans`,
  PLAN: (id: string) => `${API_PREFIX}/admin/plans/${id}`,

  // Analytics
  ANALYTICS_OVERVIEW: `${API_PREFIX}/admin/analytics/overview`,
  ANALYTICS_TOP_TENANTS: `${API_PREFIX}/admin/analytics/top-tenants`,
  ANALYTICS_TENANT: (id: string) => `${API_PREFIX}/admin/analytics/tenants/${id}`,
  ANALYTICS_TENANT_DAILY: (id: string) => `${API_PREFIX}/admin/analytics/tenants/${id}/daily`,

  // Logs
  LOGS_USAGE: `${API_PREFIX}/admin/logs/usage`,
  LOGS_USAGE_SUMMARY: `${API_PREFIX}/admin/logs/usage/summary`,
  LOGS_ERRORS: `${API_PREFIX}/admin/logs/errors`,
  LOGS_ERRORS_SUMMARY: `${API_PREFIX}/admin/logs/errors/summary`,
  LOGS_ERROR_RESOLVE: (id: number) => `${API_PREFIX}/admin/logs/errors/${id}/resolve`,
};

// Local storage keys
export const STORAGE_KEYS = {
  TOKEN: 'bridgecore_admin_token',
  ADMIN: 'bridgecore_admin_user',
};
