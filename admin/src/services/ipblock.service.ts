// IP Block management service
import apiClient from './api';
import { IPBlock, IPBlockStats, IPBlockCreate, BlockReason } from '@/types';

const BASE_URL = '/api/admin/ip-blocks';

export const ipBlockService = {
  /**
   * Get blocked IPs
   */
  async getBlockedIPs(params?: {
    tenant_id?: string;
    reason?: BlockReason;
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<IPBlock[]> {
    try {
      const response = await apiClient.get<IPBlock[]>(BASE_URL, { params });
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error('Failed to fetch blocked IPs:', error);
      return [];
    }
  },

  /**
   * Get IP block statistics
   */
  async getStats(): Promise<IPBlockStats> {
    try {
      const response = await apiClient.get<IPBlockStats>(`${BASE_URL}/stats`);
      return response.data || { active_blocks: 0, by_reason: {}, blocked_last_24h: 0 };
    } catch (error) {
      console.error('Failed to fetch IP block stats:', error);
      return { active_blocks: 0, by_reason: {}, blocked_last_24h: 0 };
    }
  },

  /**
   * Check if an IP is blocked
   */
  async checkIP(ipAddress: string): Promise<{ ip_address: string; is_blocked: boolean; block_info: IPBlock | null }> {
    const response = await apiClient.get(`${BASE_URL}/check/${encodeURIComponent(ipAddress)}`);
    return response.data;
  },

  /**
   * Block an IP
   */
  async blockIP(data: IPBlockCreate): Promise<IPBlock> {
    const response = await apiClient.post<IPBlock>(BASE_URL, data);
    return response.data;
  },

  /**
   * Unblock an IP
   */
  async unblockIP(ipAddress: string, reason?: string): Promise<void> {
    await apiClient.post(`${BASE_URL}/${encodeURIComponent(ipAddress)}/unblock`, { reason });
  },

  /**
   * Delete a block record
   */
  async deleteBlock(blockId: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/${blockId}`);
  },

  /**
   * Cleanup expired blocks
   */
  async cleanupExpiredBlocks(): Promise<{ count: number }> {
    const response = await apiClient.post<{ count: number }>(`${BASE_URL}/cleanup-expired`);
    return response.data;
  },
};

