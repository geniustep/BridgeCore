// Analytics service
import apiClient from './api';
import { API_ENDPOINTS } from '@/config/api';
import { SystemOverview, TenantAnalytics, DailyStats, TopTenant } from '@/types';

export const analyticsService = {
  /**
   * Get system-wide overview
   */
  async getOverview(): Promise<SystemOverview> {
    const response = await apiClient.get<SystemOverview>(
      API_ENDPOINTS.ANALYTICS_OVERVIEW
    );
    return response.data;
  },

  /**
   * Get top tenants by activity
   */
  async getTopTenants(params?: {
    limit?: number;
    days?: number;
  }): Promise<TopTenant[]> {
    const response = await apiClient.get<TopTenant[]>(
      API_ENDPOINTS.ANALYTICS_TOP_TENANTS,
      { params }
    );
    return response.data;
  },

  /**
   * Get tenant analytics
   */
  async getTenantAnalytics(
    tenantId: string,
    days?: number
  ): Promise<TenantAnalytics> {
    const response = await apiClient.get<TenantAnalytics>(
      API_ENDPOINTS.ANALYTICS_TENANT(tenantId),
      { params: { days } }
    );
    return response.data;
  },

  /**
   * Get tenant daily statistics
   */
  async getTenantDailyStats(
    tenantId: string,
    days?: number
  ): Promise<DailyStats[]> {
    const response = await apiClient.get<DailyStats[]>(
      API_ENDPOINTS.ANALYTICS_TENANT_DAILY(tenantId),
      { params: { days } }
    );
    return response.data;
  },
};
