/**
 * User Favorites Service
 * Handles API calls for managing user favorite templates
 */

import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL } from '@/config/api-config';

export interface UserFavorite {
  id: string;
  template_id: string;
  created_at: string;
}

export interface UserFavoritesResponse {
  favorites: UserFavorite[];
  total: number;
}

export interface ToggleFavoriteResponse {
  success: boolean;
  is_favorite: boolean;
  message: string;
}

export interface FavoriteStatusResponse {
  is_favorite: boolean;
  template_id: string;
}

class UserFavoritesService {
  /**
   * Get all favorite templates for the current user
   */
  async getUserFavorites(): Promise<UserFavoritesResponse> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/user-favorites/`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to fetch favorites');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching user favorites:', error);
      throw error;
    }
  }

  /**
   * Toggle favorite status for a template
   */
  async toggleFavorite(templateId: string): Promise<ToggleFavoriteResponse> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/user-favorites/toggle/${templateId}`, {
        method: 'POST',
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to toggle favorite');
      }

      return await response.json();
    } catch (error) {
      console.error('Error toggling favorite:', error);
      throw error;
    }
  }

  /**
   * Remove a template from favorites
   */
  async removeFavorite(templateId: string): Promise<{ success: boolean; message: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/user-favorites/${templateId}`, {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to remove favorite');
      }

      return await response.json();
    } catch (error) {
      console.error('Error removing favorite:', error);
      throw error;
    }
  }

  /**
   * Check if a template is favorited by the current user
   */
  async checkFavoriteStatus(templateId: string): Promise<FavoriteStatusResponse> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/user-favorites/check/${templateId}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to check favorite status');
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking favorite status:', error);
      throw error;
    }
  }

  /**
   * Get template IDs that are favorited by the current user
   */
  async getFavoriteTemplateIds(): Promise<string[]> {
    try {
      const favoritesResponse = await this.getUserFavorites();
      return favoritesResponse.favorites.map(fav => fav.template_id);
    } catch (error) {
      console.error('Error fetching favorite template IDs:', error);
      return []; // Return empty array on error to avoid breaking UI
    }
  }
}

export const userFavoritesService = new UserFavoritesService();