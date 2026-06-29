// Alert management service
import apiClient from './api';
import { Alert, AlertCounts, AlertSeverity, AlertStatusType, AlertType } from '@/types';

const BASE_URL = '/api/admin/alerts';

export const alertService = {
  /**
   * Get alerts with filters
   */
  async getAlerts(params?: {
    tenant_id?: string;
    status?: AlertStatusType;
    severity?: AlertSeverity;
    alert_type?: AlertType;
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<Alert[]> {
    try {
      const response = await apiClient.get<Alert[]>(BASE_URL, { params });
      // Ensure we always return an array
      if (Array.isArray(response.data)) {
        return response.data;
      }
      console.warn('Alerts API returned non-array:', response.data);
      return [];
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      return [];
    }
  },

  /**
   * Get alert counts by severity
   */
  async getAlertCounts(): Promise<AlertCounts> {
    try {
      const response = await apiClient.get<AlertCounts>(`${BASE_URL}/count`);
      return response.data || { critical: 0, error: 0, warning: 0, info: 0, total: 0 };
    } catch (error) {
      console.error('Failed to fetch alert counts:', error);
      return { critical: 0, error: 0, warning: 0, info: 0, total: 0 };
    }
  },

  /**
   * Acknowledge an alert
   */
  async acknowledgeAlert(alertId: number): Promise<void> {
    await apiClient.post(`${BASE_URL}/${alertId}/acknowledge`);
  },

  /**
   * Resolve an alert
   */
  async resolveAlert(alertId: number): Promise<void> {
    await apiClient.post(`${BASE_URL}/${alertId}/resolve`);
  },

  /**
   * Dismiss an alert
   */
  async dismissAlert(alertId: number): Promise<void> {
    await apiClient.post(`${BASE_URL}/${alertId}/dismiss`);
  },

  /**
   * Bulk dismiss alerts
   */
  async bulkDismissAlerts(alertIds: number[]): Promise<{ count: number }> {
    const response = await apiClient.post<{ count: number }>(`${BASE_URL}/bulk-dismiss`, {
      alert_ids: alertIds,
    });
    return response.data;
  },

  /**
   * Cleanup expired alerts
   */
  async cleanupExpiredAlerts(): Promise<{ count: number }> {
    const response = await apiClient.post<{ count: number }>(`${BASE_URL}/cleanup-expired`);
    return response.data;
  },
};

