/**
 * Type definitions for KasaAI Drive.
 */

export interface DriveItem {
  id: string
  name: string
  type: 'file' | 'folder'
  parent_id: string | null
  size: number
  mime_type: string | null
  created_at: string
  modified_at: string
  owner_id: string | null
  is_starred: boolean
  is_deleted: boolean
  permissions: Permission[]
  share_link: ShareLink | null
  metadata: Record<string, any>
}

export interface Permission {
  user_id: string
  role: 'view' | 'comment' | 'edit' | 'manage'
  granted_at: string
  granted_by: string
}

export interface ShareLink {
  token: string
  created_at: string
  created_by: string
  expires_at: string | null
  is_public: boolean
}

export interface FolderContents {
  items: DriveItem[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface Breadcrumb {
  id: string | null
  name: string
}

export interface SearchResults {
  items: DriveItem[]
  total: number
  skip: number
  limit: number
  query: string
}

export interface User {
  user_id: string
  email: string
  organization_id: string
  role: string
}

export interface UploadProgress {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  error?: string
}

export type ViewMode = 'grid' | 'list'
export type SortBy = 'name' | 'modified_at' | 'size' | 'type'
export type SortOrder = 'asc' | 'desc'
export type FileType = 'folder' | 'document' | 'image' | 'video' | 'audio' | null
