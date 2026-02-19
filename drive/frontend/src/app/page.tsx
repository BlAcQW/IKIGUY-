'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { supabase, signOut } from '@/lib/supabase'
import { driveAPI } from '@/lib/api'
import type { DriveItem } from '@/types'

const DEFAULT_ORG_ID = process.env.NEXT_PUBLIC_DEFAULT_ORG_ID || 'ai_labs_ltd'

export default function DrivePage() {
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [items, setItems] = useState<DriveItem[]>([])
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null)
  const [breadcrumbs, setBreadcrumbs] = useState<Array<{ id: string | null; name: string }>>([{ id: null, name: 'My Drive' }])
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [showNewFolderDialog, setShowNewFolderDialog] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const [selectedItem, setSelectedItem] = useState<DriveItem | null>(null)
  const [userEmail, setUserEmail] = useState('')

  // Check authentication
  useEffect(() => {
    checkAuth()
  }, [])

  async function checkAuth() {
    const { data: { session } } = await supabase.auth.getSession()

    if (!session) {
      // Redirect to login - for now, just show message
      setIsAuthenticated(false)
      setIsLoading(false)
      return
    }

    setIsAuthenticated(true)
    setUserEmail(session.user.email || '')
    loadFolderContents(currentFolderId)
  }

  // Load folder contents
  const loadFolderContents = useCallback(async (folderId: string | null) => {
    try {
      setIsLoading(true)
      const data = await driveAPI.getFolderContents(folderId || null)
      setItems(data.items || [])

      // Update breadcrumbs
      if (folderId) {
        const crumbs = await driveAPI.getBreadcrumbs(folderId)
        setBreadcrumbs(crumbs.map(c => ({ id: c.id, name: c.name })))
      } else {
        setBreadcrumbs([{ id: null, name: 'My Drive' }])
      }
    } catch (error: any) {
      console.error('Failed to load folder contents:', error)
      if (error.response?.status === 401) {
        setIsAuthenticated(false)
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isAuthenticated) {
      loadFolderContents(currentFolderId)
    }
  }, [currentFolderId, isAuthenticated, loadFolderContents])

  // Handle folder click
  const handleFolderClick = (folderId: string) => {
    setCurrentFolderId(folderId)
  }

  // Handle breadcrumb click
  const handleBreadcrumbClick = (folderId: string | null) => {
    setCurrentFolderId(folderId)
  }

  // Handle file upload
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return

    setIsUploading(true)
    try {
      for (let i = 0; i < files.length; i++) {
        await driveAPI.uploadFile(files[i], currentFolderId, DEFAULT_ORG_ID)
      }
      // Reload folder contents
      await loadFolderContents(currentFolderId)
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Failed to upload files. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  // Handle create folder
  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return

    try {
      await driveAPI.createFolder(newFolderName, currentFolderId, DEFAULT_ORG_ID)
      setShowNewFolderDialog(false)
      setNewFolderName('')
      await loadFolderContents(currentFolderId)
    } catch (error) {
      console.error('Failed to create folder:', error)
      alert('Failed to create folder. Please try again.')
    }
  }

  // Handle download
  const handleDownload = async (item: DriveItem) => {
    try {
      const blob = await driveAPI.downloadFile(item.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = item.name
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Failed to download file.')
    }
  }

  // Handle delete
  const handleDelete = async (item: DriveItem) => {
    if (!confirm(`Are you sure you want to delete "${item.name}"?`)) return

    try {
      if (item.type === 'folder') {
        await driveAPI.deleteFolder(item.id)
      } else {
        await driveAPI.deleteFile(item.id)
      }
      await loadFolderContents(currentFolderId)
    } catch (error) {
      console.error('Delete failed:', error)
      alert('Failed to delete item.')
    }
  }

  // Handle sign out
  const handleSignOut = async () => {
    await signOut()
    setIsAuthenticated(false)
  }

  // Login form
  if (!isAuthenticated && !isLoading) {
    return <LoginForm onSuccess={checkAuth} />
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 p-4">
        <h1 className="text-2xl font-bold text-blue-600 mb-8">KasaAI Drive</h1>

        <nav className="space-y-2">
          <button
            onClick={() => setCurrentFolderId(null)}
            className="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 font-medium text-gray-700"
          >
            📁 My Drive
          </button>
          <button className="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 text-gray-600">
            👥 Shared with me
          </button>
          <button className="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 text-gray-600">
            🕒 Recent
          </button>
          <button className="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 text-gray-600">
            ⭐ Starred
          </button>
          <button className="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 text-gray-600">
            🗑️ Trash
          </button>
        </nav>

        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-medium text-sm text-gray-700 mb-2">Storage</h3>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: '0%' }}></div>
          </div>
          <p className="text-xs text-gray-600">{items.length} items</p>
        </div>

        <div className="mt-auto pt-8">
          <button
            onClick={handleSignOut}
            className="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 text-gray-600 text-sm"
          >
            🚪 Sign Out
          </button>
          <p className="text-xs text-gray-500 mt-2 px-4 truncate">{userEmail}</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1">
              {/* Search bar */}
              <div className="flex-1 max-w-2xl">
                <input
                  type="text"
                  placeholder="Search in Drive"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* View toggle */}
              <div className="flex items-center space-x-2 border border-gray-300 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded ${viewMode === 'grid' ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
                >
                  Grid
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
                >
                  List
                </button>
              </div>

              {/* User menu */}
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium">
                {userEmail[0]?.toUpperCase() || 'U'}
              </div>
            </div>
          </div>

          {/* Breadcrumbs with Back Button */}
          <div className="mt-4 flex items-center space-x-3">
            {/* Back button */}
            {breadcrumbs.length > 1 && (
              <button
                onClick={() => handleBreadcrumbClick(breadcrumbs[breadcrumbs.length - 2].id)}
                className="flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                title="Go back"
              >
                <span className="mr-1">←</span>
                Back
              </button>
            )}

            {/* Breadcrumb trail */}
            <div className="flex items-center space-x-2 text-sm">
              {breadcrumbs.map((crumb, index) => (
                <span key={index} className="flex items-center">
                  {index > 0 && <span className="mx-2 text-gray-400">/</span>}
                  <button
                    onClick={() => handleBreadcrumbClick(crumb.id)}
                    className={`px-2 py-1 rounded hover:bg-gray-100 transition-colors ${
                      index === breadcrumbs.length - 1
                        ? 'text-gray-900 font-semibold'
                        : 'text-blue-600 hover:text-blue-800'
                    }`}
                    title={crumb.name}
                  >
                    {crumb.name}
                  </button>
                </span>
              ))}
            </div>
          </div>
        </header>

        {/* Toolbar */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowNewFolderDialog(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              📁 New Folder
            </button>
            <label className="px-4 py-2 bg-white text-gray-700 hover:bg-gray-100 rounded-lg border border-gray-300 cursor-pointer">
              📤 Upload Files
              <input
                type="file"
                multiple
                onChange={(e) => handleFileUpload(e.target.files)}
                className="hidden"
                disabled={isUploading}
              />
            </label>
            {isUploading && <span className="text-sm text-gray-600">Uploading...</span>}
          </div>

          <div className="text-sm text-gray-600">
            {items.length} item{items.length !== 1 ? 's' : ''}
          </div>
        </div>

        {/* File browser area */}
        <div className="flex-1 overflow-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-400">Loading...</div>
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <div className="text-6xl mb-4">📂</div>
              <h3 className="text-xl font-medium mb-2">This folder is empty</h3>
              <p className="text-sm">Upload files or create a new folder to get started</p>
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer group relative"
                  onDoubleClick={() => item.type === 'folder' && handleFolderClick(item.id)}
                >
                  <div className="w-full h-32 bg-gray-100 rounded mb-3 flex items-center justify-center">
                    <span className="text-4xl">{item.type === 'folder' ? '📁' : '📄'}</span>
                  </div>
                  <h3 className="font-medium text-sm truncate">{item.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    {item.type === 'folder' ? 'Folder' : `${(item.size / 1024).toFixed(1)} KB`}
                  </p>

                  {/* Action buttons */}
                  <div className="absolute top-2 right-2 hidden group-hover:flex space-x-1">
                    {item.type === 'file' && (
                      <button
                        onClick={() => handleDownload(item)}
                        className="p-1 bg-white rounded shadow hover:bg-gray-100"
                        title="Download"
                      >
                        ⬇️
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(item)}
                      className="p-1 bg-white rounded shadow hover:bg-gray-100"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-1">
              {/* List view header */}
              <div className="grid grid-cols-12 gap-4 px-4 py-2 text-sm font-medium text-gray-600 border-b">
                <div className="col-span-6">Name</div>
                <div className="col-span-2">Type</div>
                <div className="col-span-2">Modified</div>
                <div className="col-span-2">Size</div>
              </div>

              {/* List items */}
              {items.map((item) => (
                <div
                  key={item.id}
                  className="grid grid-cols-12 gap-4 px-4 py-3 hover:bg-gray-50 cursor-pointer rounded-lg group"
                  onDoubleClick={() => item.type === 'folder' && handleFolderClick(item.id)}
                >
                  <div className="col-span-6 flex items-center space-x-3">
                    <span className="text-2xl">{item.type === 'folder' ? '📁' : '📄'}</span>
                    <span className="font-medium text-sm truncate">{item.name}</span>
                  </div>
                  <div className="col-span-2 text-sm text-gray-600 capitalize">{item.type}</div>
                  <div className="col-span-2 text-sm text-gray-600">
                    {new Date(item.modified_at).toLocaleDateString()}
                  </div>
                  <div className="col-span-2 text-sm text-gray-600 flex items-center justify-between">
                    <span>
                      {item.type === 'folder' ? '-' : `${(item.size / 1024).toFixed(1)} KB`}
                    </span>
                    <div className="hidden group-hover:flex space-x-2">
                      {item.type === 'file' && (
                        <button
                          onClick={() => handleDownload(item)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Download"
                        >
                          ⬇️
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(item)}
                        className="text-red-600 hover:text-red-800"
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* New Folder Dialog */}
      {showNewFolderDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h2 className="text-xl font-bold mb-4">Create New Folder</h2>
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Folder name"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
              onKeyPress={(e) => e.key === 'Enter' && handleCreateFolder()}
              autoFocus
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowNewFolderDialog(false)
                  setNewFolderName('')
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateFolder}
                disabled={!newFolderName.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Login form component
function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState('admin@ailabsafrica.com')
  const [password, setPassword] = useState('Admin@2024!')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const { error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (authError) throw authError
      onSuccess()
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold text-blue-600 mb-6 text-center">KasaAI Drive</h1>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-4 text-center">
          Default credentials: admin@ailabsafrica.com / Admin@2024!
        </p>
      </div>
    </div>
  )
}
