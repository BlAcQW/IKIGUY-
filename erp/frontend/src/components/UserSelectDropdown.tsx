/**
 * UserSelectDropdown - Searchable dropdown for selecting organization users
 *
 * Features:
 * - Search/filter users by name or email
 * - Filter by role (admin, approver, user, etc.)
 * - Shows user name, email, and role badge
 * - Keyboard navigation support
 */

import { useState, useEffect, useRef, useMemo } from 'react'
import { Search, ChevronDown, X, User } from 'lucide-react'

interface OrganizationUser {
  user_id: string
  email: string
  first_name?: string
  last_name?: string
  display_name?: string
  role: string
  is_active?: boolean
}

interface UserSelectDropdownProps {
  users: OrganizationUser[]
  value: string
  onChange: (userId: string) => void
  placeholder?: string
  required?: boolean
  disabled?: boolean
  showRoleFilter?: boolean
  className?: string
  label?: string
}

const ROLE_COLORS: Record<string, string> = {
  universal_admin: 'bg-purple-100 text-purple-800',
  admin: 'bg-red-100 text-red-800',
  approver: 'bg-yellow-100 text-yellow-800',
  user: 'bg-blue-100 text-blue-800'
}

const ROLE_LABELS: Record<string, string> = {
  universal_admin: 'Universal Admin',
  admin: 'Admin',
  approver: 'Approver',
  user: 'User'
}

export default function UserSelectDropdown({
  users,
  value,
  onChange,
  placeholder = 'Select a user...',
  required = false,
  disabled = false,
  showRoleFilter = true,
  className = '',
  label
}: UserSelectDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [highlightedIndex, setHighlightedIndex] = useState(0)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Get unique roles from users
  const availableRoles = useMemo(() => {
    const roles = new Set(users.map(u => u.role))
    return Array.from(roles).sort()
  }, [users])

  // Filter users based on search and role
  const filteredUsers = useMemo(() => {
    return users.filter(user => {
      // Role filter
      if (roleFilter !== 'all' && user.role !== roleFilter) {
        return false
      }

      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        const fullName = `${user.first_name || ''} ${user.last_name || ''}`.toLowerCase()
        const displayName = (user.display_name || '').toLowerCase()
        const email = user.email.toLowerCase()

        return (
          fullName.includes(query) ||
          displayName.includes(query) ||
          email.includes(query) ||
          user.role.toLowerCase().includes(query)
        )
      }

      return true
    })
  }, [users, searchQuery, roleFilter])

  // Get selected user display
  const selectedUser = useMemo(() => {
    return users.find(u => u.user_id === value)
  }, [users, value])

  // Get user display name
  const getUserDisplayName = (user: OrganizationUser): string => {
    if (user.display_name) return user.display_name
    if (user.first_name || user.last_name) {
      return `${user.first_name || ''} ${user.last_name || ''}`.trim()
    }
    return user.email.split('@')[0]
  }

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Reset highlighted index when filtered users change
  useEffect(() => {
    setHighlightedIndex(0)
  }, [filteredUsers])

  // Focus input when dropdown opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
        e.preventDefault()
        setIsOpen(true)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev =>
          prev < filteredUsers.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : 0)
        break
      case 'Enter':
        e.preventDefault()
        if (filteredUsers[highlightedIndex]) {
          handleSelect(filteredUsers[highlightedIndex].user_id)
        }
        break
      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        break
    }
  }

  const handleSelect = (userId: string) => {
    onChange(userId)
    setIsOpen(false)
    setSearchQuery('')
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onChange('')
    setSearchQuery('')
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label} {required && '*'}
        </label>
      )}

      {/* Selected value display / trigger button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={`
          w-full px-3 py-2 text-left border rounded-md
          flex items-center justify-between
          ${disabled
            ? 'bg-gray-100 cursor-not-allowed text-gray-500'
            : 'bg-white cursor-pointer hover:border-gray-400'
          }
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : 'border-gray-300'}
        `}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {selectedUser ? (
            <>
              <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-gray-500" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-gray-900 truncate">
                  {getUserDisplayName(selectedUser)}
                </div>
                <div className="text-xs text-gray-500 truncate">
                  {selectedUser.email}
                </div>
              </div>
              <span className={`px-2 py-0.5 text-xs rounded-full flex-shrink-0 ${ROLE_COLORS[selectedUser.role] || 'bg-gray-100 text-gray-800'}`}>
                {ROLE_LABELS[selectedUser.role] || selectedUser.role}
              </span>
            </>
          ) : (
            <span className="text-gray-500">{placeholder}</span>
          )}
        </div>
        <div className="flex items-center gap-1 ml-2">
          {selectedUser && !required && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
          {/* Search input */}
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search users..."
                className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Role filter */}
          {showRoleFilter && availableRoles.length > 1 && (
            <div className="px-2 py-2 border-b border-gray-200">
              <div className="flex flex-wrap gap-1">
                <button
                  type="button"
                  onClick={() => setRoleFilter('all')}
                  className={`px-2 py-1 text-xs rounded-full transition-colors ${
                    roleFilter === 'all'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All Roles
                </button>
                {availableRoles.map(role => (
                  <button
                    key={role}
                    type="button"
                    onClick={() => setRoleFilter(role)}
                    className={`px-2 py-1 text-xs rounded-full transition-colors ${
                      roleFilter === role
                        ? 'bg-blue-600 text-white'
                        : `${ROLE_COLORS[role] || 'bg-gray-100 text-gray-700'} hover:opacity-80`
                    }`}
                  >
                    {ROLE_LABELS[role] || role}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* User list */}
          <div className="max-h-60 overflow-y-auto">
            {filteredUsers.length === 0 ? (
              <div className="px-3 py-4 text-sm text-gray-500 text-center">
                {searchQuery || roleFilter !== 'all'
                  ? 'No users match your filters'
                  : 'No users available'
                }
              </div>
            ) : (
              <ul className="py-1">
                {filteredUsers.map((user, index) => (
                  <li
                    key={user.user_id}
                    onClick={() => handleSelect(user.user_id)}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    className={`
                      px-3 py-2 cursor-pointer flex items-center gap-2
                      ${highlightedIndex === index ? 'bg-blue-50' : 'hover:bg-gray-50'}
                      ${user.user_id === value ? 'bg-blue-100' : ''}
                    `}
                  >
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-gray-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {getUserDisplayName(user)}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {user.email}
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 text-xs rounded-full flex-shrink-0 ${ROLE_COLORS[user.role] || 'bg-gray-100 text-gray-800'}`}>
                      {ROLE_LABELS[user.role] || user.role}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Footer with count */}
          <div className="px-3 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
            {filteredUsers.length} of {users.length} users
          </div>
        </div>
      )}
    </div>
  )
}
