/**
 * API client for KasaAI Drive backend.
 */

import axios, { AxiosInstance } from 'axios'
import { getAuthToken } from './supabase'
import type {
  DriveItem,
  FolderContents,
  Breadcrumb,
  SearchResults,
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://drive-api.ailabsafrica.com'

class DriveAPI {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add auth token to requests
    this.client.interceptors.request.use(async (config) => {
      const token = await getAuthToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
  }

  // ==================== FILES ====================

  async uploadFile(
    file: File,
    parentId: string | null,
    organizationId: string,
    onProgress?: (progress: number) => void
  ): Promise<DriveItem> {
    const formData = new FormData()
    formData.append('file', file)
    if (parentId) formData.append('parent_id', parentId)
    formData.append('organization_id', organizationId)

    const response = await this.client.post('/api/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = (progressEvent.loaded / progressEvent.total) * 100
          onProgress(Math.round(progress))
        }
      },
    })

    return response.data
  }

  async getFileInfo(fileId: string): Promise<DriveItem> {
    const response = await this.client.get(`/api/files/${fileId}`)
    return response.data
  }

  async downloadFile(fileId: string): Promise<Blob> {
    const response = await this.client.get(`/api/files/${fileId}/download`, {
      responseType: 'blob',
    })
    return response.data
  }

  async renameFile(fileId: string, newName: string): Promise<DriveItem> {
    const response = await this.client.put(`/api/files/${fileId}/rename`, {
      new_name: newName,
    })
    return response.data
  }

  async moveFile(fileId: string, newParentId: string | null): Promise<DriveItem> {
    const response = await this.client.put(`/api/files/${fileId}/move`, {
      new_parent_id: newParentId,
    })
    return response.data
  }

  async deleteFile(fileId: string, permanent: boolean = false): Promise<void> {
    await this.client.delete(`/api/files/${fileId}`, {
      params: { permanent },
    })
  }

  async toggleStar(fileId: string): Promise<DriveItem> {
    const response = await this.client.post(`/api/files/${fileId}/star`)
    return response.data
  }

  // ==================== FOLDERS ====================

  async createFolder(
    name: string,
    parentId: string | null,
    organizationId: string
  ): Promise<DriveItem> {
    const response = await this.client.post('/api/folders', {
      name,
      parent_id: parentId,
      organization_id: organizationId,
    })
    return response.data
  }

  async getFolderContents(
    folderId: string | null,
    skip: number = 0,
    limit: number = 100,
    sortBy: string = 'name',
    sortOrder: string = 'asc'
  ): Promise<FolderContents> {
    const id = folderId || 'root'
    const response = await this.client.get(`/api/folders/${id}/contents`, {
      params: { skip, limit, sort_by: sortBy, sort_order: sortOrder },
    })
    return response.data
  }

  async getBreadcrumbs(folderId: string | null): Promise<Breadcrumb[]> {
    const id = folderId || 'root'
    const response = await this.client.get(`/api/folders/${id}/breadcrumbs`)
    return response.data
  }

  async renameFolder(folderId: string, newName: string): Promise<DriveItem> {
    const response = await this.client.put(`/api/folders/${folderId}/rename`, {
      new_name: newName,
    })
    return response.data
  }

  async moveFolder(folderId: string, newParentId: string | null): Promise<DriveItem> {
    const response = await this.client.put(`/api/folders/${folderId}/move`, {
      new_parent_id: newParentId,
    })
    return response.data
  }

  async deleteFolder(folderId: string, permanent: boolean = false): Promise<void> {
    await this.client.delete(`/api/folders/${folderId}`, {
      params: { permanent },
    })
  }

  // ==================== SEARCH ====================

  async searchFiles(
    query: string,
    options?: {
      file_type?: string
      owner_id?: string
      date_from?: string
      date_to?: string
      skip?: number
      limit?: number
    }
  ): Promise<SearchResults> {
    const response = await this.client.get('/api/search', {
      params: { q: query, ...options },
    })
    return response.data
  }

  async getRecentFiles(limit: number = 20): Promise<DriveItem[]> {
    const response = await this.client.get('/api/search/recent', {
      params: { limit },
    })
    return response.data
  }

  async getStarredItems(): Promise<DriveItem[]> {
    const response = await this.client.get('/api/search/starred')
    return response.data
  }

  // ==================== SHARING ====================

  async shareWithUser(
    itemId: string,
    targetUserId: string,
    role: string = 'view'
  ): Promise<DriveItem> {
    const response = await this.client.post(`/api/share/${itemId}/user`, {
      target_user_id: targetUserId,
      role,
    })
    return response.data
  }

  async createShareLink(
    itemId: string,
    expiresInDays?: number,
    isPublic: boolean = true
  ): Promise<{ item_id: string; share_token: string; expires_at: string | null; is_public: boolean }> {
    const response = await this.client.post(`/api/share/${itemId}/link`, {
      expires_in_days: expiresInDays,
      is_public: isPublic,
    })
    return response.data
  }

  async revokeShareLink(itemId: string): Promise<void> {
    await this.client.delete(`/api/share/${itemId}/link`)
  }
}

export const driveAPI = new DriveAPI()
