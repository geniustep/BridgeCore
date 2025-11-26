/**
 * System Management Service
 * Handles multi-system integration (Odoo, Moodle, SAP, etc.)
 */
import api from './api';
import {
  ExternalSystem,
  TenantSystem,
  TenantSystemCreate,
  TenantSystemUpdate,
  SystemConnectionTestRequest,
  SystemConnectionTestResponse
} from '../types';

class SystemService {
  /**
   * Get all available external systems
   */
  async getAllSystems(enabledOnly: boolean = false): Promise<ExternalSystem[]> {
    const response = await api.get('/admin/systems', {
      params: { enabled_only: enabledOnly }
    });
    return response.data;
  }

  /**
   * Get specific external system
   */
  async getSystem(systemId: string): Promise<ExternalSystem> {
    const response = await api.get(`/admin/systems/${systemId}`);
    return response.data;
  }

  /**
   * Get all systems connected to a tenant
   */
  async getTenantSystems(tenantId: string, activeOnly: boolean = true): Promise<TenantSystem[]> {
    const response = await api.get(`/admin/tenants/${tenantId}/systems`, {
      params: { active_only: activeOnly }
    });
    return response.data;
  }

  /**
   * Add a new system connection to a tenant
   */
  async addTenantSystem(tenantId: string, data: TenantSystemCreate): Promise<TenantSystem> {
    const response = await api.post(`/admin/tenants/${tenantId}/systems`, data);
    return response.data;
  }

  /**
   * Update tenant system connection
   */
  async updateTenantSystem(
    tenantId: string,
    connectionId: string,
    data: TenantSystemUpdate
  ): Promise<TenantSystem> {
    const response = await api.put(`/admin/tenants/${tenantId}/systems/${connectionId}`, data);
    return response.data;
  }

  /**
   * Delete tenant system connection
   */
  async deleteTenantSystem(tenantId: string, connectionId: string): Promise<void> {
    await api.delete(`/admin/tenants/${tenantId}/systems/${connectionId}`);
  }

  /**
   * Set a system as primary for the tenant
   */
  async setPrimarySystem(tenantId: string, connectionId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/admin/tenants/${tenantId}/systems/${connectionId}/set-primary`);
    return response.data;
  }

  /**
   * Test connection to external system (without saving)
   */
  async testConnection(data: SystemConnectionTestRequest): Promise<SystemConnectionTestResponse> {
    const response = await api.post('/admin/test-connection', data);
    return response.data;
  }

  /**
   * Test an existing tenant system connection
   */
  async testExistingConnection(tenantId: string, connectionId: string): Promise<SystemConnectionTestResponse> {
    const response = await api.post(`/admin/tenants/${tenantId}/systems/${connectionId}/test`);
    return response.data;
  }

  /**
   * Get system-specific configuration template
   */
  getConfigTemplate(systemType: string): Record<string, any> {
    const templates: Record<string, any> = {
      odoo: {
        url: '',
        database: '',
        username: '',
        password: ''
      },
      moodle: {
        url: '',
        token: '',
        service: 'moodle_mobile_app'
      },
      sap: {
        url: '',
        client: '',
        username: '',
        password: ''
      },
      salesforce: {
        instance_url: '',
        client_id: '',
        client_secret: '',
        username: '',
        password: '',
        security_token: ''
      }
    };

    return templates[systemType] || {};
  }

  /**
   * Validate connection config based on system type
   */
  validateConfig(systemType: string, config: Record<string, any>): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    switch (systemType) {
      case 'odoo':
        if (!config.url) errors.push('URL is required');
        if (!config.database) errors.push('Database is required');
        if (!config.username) errors.push('Username is required');
        if (!config.password) errors.push('Password is required');
        break;

      case 'moodle':
        if (!config.url) errors.push('URL is required');
        if (!config.token) errors.push('Token is required');
        break;

      case 'sap':
        if (!config.url) errors.push('URL is required');
        if (!config.client) errors.push('Client is required');
        if (!config.username) errors.push('Username is required');
        if (!config.password) errors.push('Password is required');
        break;

      case 'salesforce':
        if (!config.instance_url) errors.push('Instance URL is required');
        if (!config.username) errors.push('Username is required');
        if (!config.password) errors.push('Password is required');
        break;
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

export default new SystemService();
