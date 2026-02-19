/**
 * Utility functions for KasaAI Drive.
 */

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { formatDistanceToNow, format } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format file size in human-readable format.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Format date as relative time (e.g., "2 hours ago") or absolute date.
 */
export function formatDate(dateString: string, relative: boolean = true): string {
  const date = new Date(dateString)

  if (relative) {
    return formatDistanceToNow(date, { addSuffix: true })
  }

  return format(date, 'MMM d, yyyy h:mm a')
}

/**
 * Get file icon based on MIME type.
 */
export function getFileIcon(mimeType: string | null): string {
  if (!mimeType) return 'file'

  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType.startsWith('video/')) return 'video'
  if (mimeType.startsWith('audio/')) return 'music'
  if (mimeType === 'application/pdf') return 'file-text'
  if (mimeType.includes('word') || mimeType.includes('document')) return 'file-text'
  if (mimeType.includes('sheet') || mimeType.includes('excel')) return 'table'
  if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) return 'presentation'
  if (mimeType.includes('zip') || mimeType.includes('rar') || mimeType.includes('archive')) return 'archive'
  if (mimeType.includes('text')) return 'file-text'

  return 'file'
}

/**
 * Get file color based on type.
 */
export function getFileColor(mimeType: string | null): string {
  if (!mimeType) return 'text-gray-500'

  if (mimeType.startsWith('image/')) return 'text-green-500'
  if (mimeType.startsWith('video/')) return 'text-purple-500'
  if (mimeType.startsWith('audio/')) return 'text-pink-500'
  if (mimeType === 'application/pdf') return 'text-red-500'
  if (mimeType.includes('word') || mimeType.includes('document')) return 'text-blue-500'
  if (mimeType.includes('sheet') || mimeType.includes('excel')) return 'text-green-600'
  if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) return 'text-orange-500'

  return 'text-gray-500'
}

/**
 * Download blob as file.
 */
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/**
 * Copy text to clipboard.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    console.error('Failed to copy:', err)
    return false
  }
}

/**
 * Validate file name.
 */
export function isValidFileName(name: string): boolean {
  const invalidChars = /[<>:"/\\|?*]/
  return !invalidChars.test(name) && name.length > 0 && name.length <= 255
}

/**
 * Get file extension from filename.
 */
export function getFileExtension(filename: string): string {
  const parts = filename.split('.')
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : ''
}

/**
 * Check if file is an image.
 */
export function isImageFile(mimeType: string | null): boolean {
  return mimeType?.startsWith('image/') || false
}

/**
 * Check if file is a video.
 */
export function isVideoFile(mimeType: string | null): boolean {
  return mimeType?.startsWith('video/') || false
}

/**
 * Check if file can be previewed in browser.
 */
export function canPreview(mimeType: string | null): boolean {
  if (!mimeType) return false

  return (
    mimeType.startsWith('image/') ||
    mimeType.startsWith('video/') ||
    mimeType === 'application/pdf' ||
    mimeType.startsWith('text/')
  )
}
