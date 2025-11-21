// Authentication service
import apiClient from './api';
import { API_ENDPOINTS, STORAGE_KEYS } from '@/config/api';
import { LoginRequest, LoginResponse, Admin } from '@/types';

export const authService = {
  /**
   * Login admin user
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>(
      API_ENDPOINTS.LOGIN,
      credentials
    );

    // Save token and admin info
    if (response.data.token) {
      localStorage.setItem(STORAGE_KEYS.TOKEN, response.data.token);
      localStorage.setItem(STORAGE_KEYS.ADMIN, JSON.stringify(response.data.admin));
    }

    return response.data;
  },

  /**
   * Logout admin user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post(API_ENDPOINTS.LOGOUT);
    } finally {
      // Clear local storage regardless of API response
      localStorage.removeItem(STORAGE_KEYS.TOKEN);
      localStorage.removeItem(STORAGE_KEYS.ADMIN);
    }
  },

  /**
   * Get current admin user info
   */
  async getCurrentAdmin(): Promise<Admin> {
    const response = await apiClient.get<Admin>(API_ENDPOINTS.ME);
    // Update local storage
    localStorage.setItem(STORAGE_KEYS.ADMIN, JSON.stringify(response.data));
    return response.data;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
    return !!token;
  },

  /**
   * Get stored admin info
   */
  getStoredAdmin(): Admin | null {
    const adminJson = localStorage.getItem(STORAGE_KEYS.ADMIN);
    if (!adminJson) return null;
    try {
      return JSON.parse(adminJson);
    } catch {
      return null;
    }
  },

  /**
   * Get stored token
   */
  getToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.TOKEN);
  },
};
