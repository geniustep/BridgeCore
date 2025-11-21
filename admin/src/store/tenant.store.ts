// Tenant store using Zustand
import { create } from 'zustand';
import { Tenant, TenantStatistics } from '@/types';
import { tenantService } from '@/services/tenant.service';

interface TenantState {
  tenants: Tenant[];
  currentTenant: Tenant | null;
  statistics: TenantStatistics | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchTenants: (params?: any) => Promise<void>;
  fetchTenant: (id: string) => Promise<void>;
  fetchStatistics: () => Promise<void>;
  suspendTenant: (id: string) => Promise<void>;
  activateTenant: (id: string) => Promise<void>;
  deleteTenant: (id: string) => Promise<void>;
  clearError: () => void;
}

export const useTenantStore = create<TenantState>((set, get) => ({
  tenants: [],
  currentTenant: null,
  statistics: null,
  isLoading: false,
  error: null,

  fetchTenants: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const tenants = await tenantService.getTenants(params);
      set({ tenants, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch tenants',
        isLoading: false,
      });
    }
  },

  fetchTenant: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const tenant = await tenantService.getTenant(id);
      set({ currentTenant: tenant, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch tenant',
        isLoading: false,
      });
    }
  },

  fetchStatistics: async () => {
    try {
      const statistics = await tenantService.getStatistics();
      set({ statistics });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch statistics',
      });
    }
  },

  suspendTenant: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await tenantService.suspendTenant(id);
      // Refresh tenants list
      await get().fetchTenants();
      set({ isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to suspend tenant',
        isLoading: false,
      });
      throw error;
    }
  },

  activateTenant: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await tenantService.activateTenant(id);
      // Refresh tenants list
      await get().fetchTenants();
      set({ isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to activate tenant',
        isLoading: false,
      });
      throw error;
    }
  },

  deleteTenant: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await tenantService.deleteTenant(id);
      // Refresh tenants list
      await get().fetchTenants();
      set({ isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to delete tenant',
        isLoading: false,
      });
      throw error;
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));
