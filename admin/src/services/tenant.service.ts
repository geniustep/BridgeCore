// Tenant management service
import apiClient from './api';
import { API_ENDPOINTS } from '@/config/api';
import { Tenant, TenantCreate, TenantUpdate, TenantStatistics, ConnectionTestResult, RateLimitStatus } from '@/types';

export const tenantService = {
  /**
   * Get list of tenants
   */
  async getTenants(params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }): Promise<Tenant[]> {
    const response = await apiClient.get<Tenant[]>(API_ENDPOINTS.TENANTS, { params });
    return response.data;
  },

  /**
   * Get tenant by ID
   */
  async getTenant(id: string): Promise<Tenant> {
    const response = await apiClient.get<Tenant>(API_ENDPOINTS.TENANT(id));
    return response.data;
  },

  /**
   * Create new tenant
   */
  async createTenant(data: TenantCreate): Promise<Tenant> {
    const response = await apiClient.post<Tenant>(API_ENDPOINTS.TENANTS, data);
    return response.data;
  },

  /**
   * Update tenant
   */
  async updateTenant(id: string, data: TenantUpdate): Promise<Tenant> {
    const response = await apiClient.put<Tenant>(API_ENDPOINTS.TENANT(id), data);
    return response.data;
  },

  /**
   * Delete tenant (soft delete)
   */
  async deleteTenant(id: string): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.TENANT(id));
  },

  /**
   * Suspend tenant
   */
  async suspendTenant(id: string): Promise<void> {
    await apiClient.post(API_ENDPOINTS.TENANT_SUSPEND(id));
  },

  /**
   * Activate tenant
   */
  async activateTenant(id: string): Promise<void> {
    await apiClient.post(API_ENDPOINTS.TENANT_ACTIVATE(id));
  },

  /**
   * Test Odoo connection
   */
  async testConnection(id: string): Promise<ConnectionTestResult> {
    const response = await apiClient.post<ConnectionTestResult>(
      API_ENDPOINTS.TENANT_TEST(id)
    );
    return response.data;
  },

  /**
   * Get tenant statistics
   */
  async getStatistics(): Promise<TenantStatistics> {
    const response = await apiClient.get<TenantStatistics>(API_ENDPOINTS.TENANT_STATS);
    return response.data;
  },

  /**
   * Get rate limit status
   */
  async getRateLimitStatus(id: string): Promise<RateLimitStatus> {
    const response = await apiClient.get<RateLimitStatus>(`${API_ENDPOINTS.TENANT(id)}/rate-limit`);
    return response.data;
  },

  /**
   * Reset rate limit
   */
  async resetRateLimit(id: string, resetType: 'daily' | 'hourly' | 'all' = 'all'): Promise<{ message: string; reset_type: string; deleted_keys: number; keys: string[] }> {
    const response = await apiClient.post(`${API_ENDPOINTS.TENANT(id)}/rate-limit/reset?reset_type=${resetType}`);
    return response.data;
  },
};
