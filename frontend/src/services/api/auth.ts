// frontend/src/services/api/auth.ts
/**
 * Authentication API service.
 */

import apiClient from './client';
import { LoginCredentials, RegisterData, AuthResponse, User } from '../../types';

export const authApi = {
  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // OAuth2 password flow expects form data
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await apiClient.post<AuthResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    // Store token
    apiClient.setToken(response.access_token);
    
    return response;
  },

  /**
   * Register new user
   */
  async register(data: RegisterData): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', data);
    return response;
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response;
  },

  /**
   * Logout user
   */
  logout(): void {
    apiClient.clearToken();
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return apiClient.isAuthenticated();
  },
};