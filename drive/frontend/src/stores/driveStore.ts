/**
 * Zustand store for Drive application state.
 */

import { create } from 'zustand'
import type { DriveItem, ViewMode, SortBy, SortOrder, UploadProgress } from '@/types'

interface DriveState {
  // Current folder
  currentFolderId: string | null
  setCurrentFolderId: (id: string | null) => void

  // View settings
  viewMode: ViewMode
  setViewMode: (mode: ViewMode) => void
  sortBy: SortBy
  setSortBy: (sort: SortBy) => void
  sortOrder: SortOrder
  setSortOrder: (order: SortOrder) => void

  // Selection
  selectedItems: Set<string>
  toggleSelection: (id: string) => void
  selectAll: (items: DriveItem[]) => void
  clearSelection: () => void
  isSelected: (id: string) => boolean

  // Upload queue
  uploads: UploadProgress[]
  addUpload: (file: File) => void
  updateUploadProgress: (file: File, progress: number) => void
  setUploadStatus: (file: File, status: UploadProgress['status'], error?: string) => void
  clearUploads: () => void

  // UI state
  showUploadModal: boolean
  setShowUploadModal: (show: boolean) => void
  showShareModal: boolean
  setShowShareModal: (show: boolean) => void
  shareItem: DriveItem | null
  setShareItem: (item: DriveItem | null) => void

  // Search
  searchQuery: string
  setSearchQuery: (query: string) => void
  isSearching: boolean
  setIsSearching: (searching: boolean) => void
}

export const useDriveStore = create<DriveState>((set, get) => ({
  // Current folder
  currentFolderId: null,
  setCurrentFolderId: (id) => set({ currentFolderId: id }),

  // View settings
  viewMode: 'grid',
  setViewMode: (mode) => set({ viewMode: mode }),
  sortBy: 'name',
  setSortBy: (sort) => set({ sortBy: sort }),
  sortOrder: 'asc',
  setSortOrder: (order) => set({ sortOrder: order }),

  // Selection
  selectedItems: new Set(),
  toggleSelection: (id) =>
    set((state) => {
      const newSelection = new Set(state.selectedItems)
      if (newSelection.has(id)) {
        newSelection.delete(id)
      } else {
        newSelection.add(id)
      }
      return { selectedItems: newSelection }
    }),
  selectAll: (items) =>
    set({ selectedItems: new Set(items.map((item) => item.id)) }),
  clearSelection: () => set({ selectedItems: new Set() }),
  isSelected: (id) => get().selectedItems.has(id),

  // Upload queue
  uploads: [],
  addUpload: (file) =>
    set((state) => ({
      uploads: [
        ...state.uploads,
        {
          file,
          progress: 0,
          status: 'pending',
        },
      ],
    })),
  updateUploadProgress: (file, progress) =>
    set((state) => ({
      uploads: state.uploads.map((upload) =>
        upload.file === file ? { ...upload, progress } : upload
      ),
    })),
  setUploadStatus: (file, status, error) =>
    set((state) => ({
      uploads: state.uploads.map((upload) =>
        upload.file === file ? { ...upload, status, error } : upload
      ),
    })),
  clearUploads: () => set({ uploads: [] }),

  // UI state
  showUploadModal: false,
  setShowUploadModal: (show) => set({ showUploadModal: show }),
  showShareModal: false,
  setShowShareModal: (show) => set({ showShareModal: show }),
  shareItem: null,
  setShareItem: (item) => set({ shareItem: item }),

  // Search
  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),
  isSearching: false,
  setIsSearching: (searching) => set({ isSearching: searching }),
}))
