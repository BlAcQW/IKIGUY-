/**
 * DataTable Component
 *
 * Reusable table component with pagination, search, filtering, and actions.
 */

import { useState } from 'react'
import { Search, ChevronLeft, ChevronRight, Edit, Trash2 } from 'lucide-react'

export interface Column<T> {
  key: string
  label: string
  render?: (item: T) => React.ReactNode
  sortable?: boolean
  width?: string
}

export interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  searchPlaceholder?: string
  onSearch?: (query: string) => void
  onEdit?: (item: T) => void
  onDelete?: (item: T) => void
  onRowClick?: (item: T) => void
  pagination?: {
    page: number
    pageSize: number
    total: number
    onPageChange: (page: number) => void
  }
  infiniteScroll?: {
    hasMore: boolean
    loadingMore: boolean
    observerTarget: React.RefObject<HTMLDivElement>
  }
  emptyMessage?: string
}

export default function DataTable<T extends { id: string }>({
  data,
  columns,
  loading = false,
  searchPlaceholder = 'Search...',
  onSearch,
  onEdit,
  onDelete,
  onRowClick,
  pagination,
  infiniteScroll,
  emptyMessage = 'No data available'
}: DataTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (value: string) => {
    setSearchQuery(value)
    onSearch?.(value)
  }

  const handlePrevPage = () => {
    if (pagination && pagination.page > 1) {
      pagination.onPageChange(pagination.page - 1)
    }
  }

  const handleNextPage = () => {
    if (pagination) {
      const totalPages = Math.ceil(pagination.total / pagination.pageSize)
      if (pagination.page < totalPages) {
        pagination.onPageChange(pagination.page + 1)
      }
    }
  }

  const showActions = onEdit || onDelete
  const totalPages = pagination ? Math.ceil(pagination.total / pagination.pageSize) : 1

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      {onSearch && (
        <div className="relative">
          <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden w-full">
        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        ) : data.length === 0 ? (
          <div className="p-8 text-center text-gray-500">{emptyMessage}</div>
        ) : (
          <>
            <div className="overflow-x-auto w-full">
              <table className="w-full divide-y divide-gray-200 table-fixed">
                <thead className="bg-gray-50">
                  <tr>
                    {columns.map((column) => (
                      <th
                        key={column.key}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        style={column.width ? { width: column.width } : undefined}
                      >
                        {column.label}
                      </th>
                    ))}
                    {showActions && (
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.map((item) => (
                    <tr
                      key={item.id}
                      className={`${onRowClick ? 'hover:bg-gray-50 cursor-pointer' : ''}`}
                      onClick={() => onRowClick?.(item)}
                    >
                      {columns.map((column) => (
                        <td
                          key={column.key}
                          className="px-6 py-4 text-sm text-gray-900 truncate"
                          style={column.width ? { width: column.width } : undefined}
                        >
                          {column.render
                            ? column.render(item)
                            : (item as any)[column.key] || '-'}
                        </td>
                      ))}
                      {showActions && (
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end space-x-2">
                            {onEdit && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  onEdit(item)
                                }}
                                className="text-blue-600 hover:text-blue-900"
                                title="Edit"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                            )}
                            {onDelete && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  onDelete(item)
                                }}
                                className="text-red-600 hover:text-red-900"
                                title="Delete"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination && (
              <div className="bg-gray-50 px-6 py-3 flex items-center justify-between border-t border-gray-200">
                <div className="text-sm text-gray-700">
                  Showing{' '}
                  <span className="font-medium">
                    {(pagination.page - 1) * pagination.pageSize + 1}
                  </span>{' '}
                  to{' '}
                  <span className="font-medium">
                    {Math.min(pagination.page * pagination.pageSize, pagination.total)}
                  </span>{' '}
                  of <span className="font-medium">{pagination.total}</span> results
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={handlePrevPage}
                    disabled={pagination.page === 1}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-700">
                    Page {pagination.page} of {totalPages}
                  </span>
                  <button
                    onClick={handleNextPage}
                    disabled={pagination.page >= totalPages}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Infinite Scroll Sentinel and Loading Indicator */}
            {infiniteScroll && (
              <>
                <div ref={infiniteScroll.observerTarget} className="h-1" />
                {infiniteScroll.loadingMore && (
                  <div className="bg-gray-50 px-6 py-4 flex items-center justify-center border-t border-gray-200">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-4 border-gray-300 border-t-blue-600"></div>
                    <p className="ml-3 text-sm text-gray-600">Loading more...</p>
                  </div>
                )}
                {!infiniteScroll.hasMore && data.length > 0 && (
                  <div className="bg-gray-50 px-6 py-4 text-center border-t border-gray-200">
                    <p className="text-sm text-gray-500">No more items to load</p>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
