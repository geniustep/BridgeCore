// Logs service
import apiClient from './api';
import { API_ENDPOINTS } from '@/config/api';
import { UsageLog, ErrorLog } from '@/types';

export const logsService = {
  /**
   * Get usage logs
   */
  async getUsageLogs(params?: {
    tenant_id?: string;
    skip?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    method?: string;
    status_code?: number;
  }): Promise<UsageLog[]> {
    const response = await apiClient.get<UsageLog[]>(
      API_ENDPOINTS.LOGS_USAGE,
      { params }
    );
    return response.data;
  },

  /**
   * Get usage summary
   */
  async getUsageSummary(tenantId: string, days?: number): Promise<any> {
    const response = await apiClient.get(
      API_ENDPOINTS.LOGS_USAGE_SUMMARY,
      { params: { tenant_id: tenantId, days } }
    );
    return response.data;
  },

  /**
   * Get error logs
   */
  async getErrorLogs(params?: {
    tenant_id?: string;
    skip?: number;
    limit?: number;
    severity?: string;
    unresolved_only?: boolean;
  }): Promise<ErrorLog[]> {
    const response = await apiClient.get<ErrorLog[]>(
      API_ENDPOINTS.LOGS_ERRORS,
      { params }
    );
    return response.data;
  },

  /**
   * Get error summary
   */
  async getErrorSummary(tenantId: string, days?: number): Promise<any> {
    const response = await apiClient.get(
      API_ENDPOINTS.LOGS_ERRORS_SUMMARY,
      { params: { tenant_id: tenantId, days } }
    );
    return response.data;
  },

  /**
   * Resolve error
   */
  async resolveError(
    errorId: number,
    resolutionNotes?: string
  ): Promise<void> {
    await apiClient.post(API_ENDPOINTS.LOGS_ERROR_RESOLVE(errorId), {
      resolution_notes: resolutionNotes,
    });
  },
};
