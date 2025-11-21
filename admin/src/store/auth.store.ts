// Auth store using Zustand
import { create } from 'zustand';
import { Admin } from '@/types';
import { authService } from '@/services/auth.service';

interface AuthState {
  admin: Admin | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadAdmin: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  admin: authService.getStoredAdmin(),
  isAuthenticated: authService.isAuthenticated(),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authService.login({ email, password });
      set({
        admin: response.admin,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      set({
        admin: null,
        isAuthenticated: false,
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await authService.logout();
    } finally {
      set({
        admin: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  },

  loadAdmin: () => {
    const admin = authService.getStoredAdmin();
    const isAuthenticated = authService.isAuthenticated();
    set({ admin, isAuthenticated });
  },

  clearError: () => {
    set({ error: null });
  },
}));
