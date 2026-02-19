# Author Selector Frontend Implementation Guide

## Overview
This document outlines the implementation of the author selection system for the InkWave book upload interface. The backend APIs are complete and ready to use.

## Backend APIs Available

### 1. List Authors
```typescript
GET /api/v1/authors/
Query params:
  - limit: number (1-100, default: 50)
  - offset: number (default: 0)

Response:
{
  "authors": [
    {
      "user_id": "author_cecb671bb6b2",
      "display_name": "Archbishop Nicholas Duncan-Williams",
      "email": "archbishop.duncan-williams@inkwave.author",
      "first_name": "Nicholas",
      "last_name": "Duncan-Williams",
      "bio": "Presiding Archbishop and General Overseer...",
      "avatar_url": null,
      "username": "archbishop_duncan_williams",
      "books_count": 20,
      "created_at": "2025-12-05T..."
    }
  ],
  "total": 1
}
```

### 2. Search Authors (Autocomplete)
```typescript
GET /api/v1/authors/search?q={query}&limit=10

Response: Same format as List Authors
Searches: display_name, first_name, last_name, username
```

### 3. Create Author (Admin Only)
```typescript
POST /api/v1/authors/
Body:
{
  "display_name": "Author Name",
  "first_name": "First", // optional
  "last_name": "Last", // optional
  "bio": "Biography...", // optional
  "email": "author@email.com", // optional
  "avatar_url": "https://..." // optional
}

Response: Author object
```

### 4. Book Upload with Author
```typescript
POST /api/v1/books/upload
FormData:
  - file: PDF file
  - title: string
  - author: string (author name - still required)
  - author_id: string (NEW - optional, links to author account)
  - description: string
  - ... (other fields)
```

## Implementation Plan

### Step 1: Create API Functions

**File**: `src/lib/api.ts` or `src/api/authors.ts`

```typescript
// Add to existing api object or create new authors module

export interface Author {
  user_id: string;
  display_name: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  bio?: string;
  avatar_url?: string;
  username?: string;
  books_count: number;
  created_at: string;
}

export interface AuthorSearchResponse {
  authors: Author[];
  total: number;
}

export interface CreateAuthorRequest {
  display_name: string;
  first_name?: string;
  last_name?: string;
  bio?: string;
  email?: string;
  avatar_url?: string;
}

const authorsApi = {
  // List all authors
  list: async (limit = 50, offset = 0): Promise<AuthorSearchResponse> => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/authors/`, {
      params: { limit, offset },
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return response.data;
  },

  // Search authors (autocomplete)
  search: async (query: string, limit = 10): Promise<AuthorSearchResponse> => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/authors/search`, {
      params: { q: query, limit },
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return response.data;
  },

  // Create new author
  create: async (data: CreateAuthorRequest): Promise<Author> => {
    const response = await axios.post(`${API_BASE_URL}/api/v1/authors/`, data, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return response.data;
  },

  // Get author by ID
  getById: async (authorId: string): Promise<Author> => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/authors/${authorId}`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return response.data;
  }
};

// Add to main api export
export const api = {
  ...existingApi,
  authors: authorsApi
};
```

### Step 2: Create AuthorSelector Component

**File**: `src/components/AuthorSelector.tsx`

```typescript
/**
 * AuthorSelector Component
 *
 * Autocomplete dropdown for selecting existing authors or creating new ones.
 * Features:
 * - Type-ahead search
 * - Displays author avatar, name, and book count
 * - "Create New Author" button
 * - Opens modal for new author creation
 */

import { useState, useEffect, useRef } from 'react';
import { Search, User, Plus, Book } from 'lucide-react';
import { api, Author } from '../lib/api';
import { debounce } from '../utils/debounce';

interface AuthorSelectorProps {
  selectedAuthor: Author | null;
  onSelect: (author: Author | null) => void;
  onCreateNew: () => void;
}

export default function AuthorSelector({
  selectedAuthor,
  onSelect,
  onCreateNew
}: AuthorSelectorProps) {
  const [query, setQuery] = useState('');
  const [authors, setAuthors] = useState<Author[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Debounced search function
  const searchAuthors = useRef(
    debounce(async (searchQuery: string) => {
      if (!searchQuery || searchQuery.length < 2) {
        setAuthors([]);
        return;
      }

      setLoading(true);
      try {
        const response = await api.authors.search(searchQuery);
        setAuthors(response.authors);
        setShowDropdown(true);
      } catch (error) {
        console.error('Failed to search authors:', error);
      } finally {
        setLoading(false);
      }
    }, 300)
  ).current;

  // Search on query change
  useEffect(() => {
    searchAuthors(query);
  }, [query]);

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (author: Author) => {
    onSelect(author);
    setQuery(author.display_name);
    setShowDropdown(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    if (!value) {
      onSelect(null);
    }
  };

  return (
    <div ref={wrapperRef} className="relative">
      {/* Input field */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => {
            if (authors.length > 0) setShowDropdown(true);
          }}
          placeholder="Search for author..."
          className="w-full pl-10 pr-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-500"></div>
          </div>
        )}
      </div>

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute z-50 w-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-96 overflow-y-auto">
          {/* Create New Author Button */}
          <button
            onClick={() => {
              onCreateNew();
              setShowDropdown(false);
            }}
            className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-700 transition-colors border-b border-gray-700"
          >
            <Plus className="w-5 h-5 text-purple-400" />
            <div className="flex-1 text-left">
              <div className="text-white font-medium">Create New Author</div>
              <div className="text-gray-400 text-sm">Add a new author to the system</div>
            </div>
          </button>

          {/* Author results */}
          {authors.length === 0 && !loading && query.length >= 2 && (
            <div className="px-4 py-8 text-center text-gray-400">
              No authors found. Create a new one?
            </div>
          )}

          {authors.map((author) => (
            <button
              key={author.user_id}
              onClick={() => handleSelect(author)}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-700 transition-colors"
            >
              {/* Avatar */}
              <div className="flex-shrink-0">
                {author.avatar_url ? (
                  <img
                    src={author.avatar_url}
                    alt={author.display_name}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>

              {/* Author info */}
              <div className="flex-1 text-left">
                <div className="text-white font-medium">{author.display_name}</div>
                <div className="text-gray-400 text-sm flex items-center gap-2">
                  <Book className="w-3 h-3" />
                  {author.books_count} {author.books_count === 1 ? 'book' : 'books'}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Selected author display */}
      {selectedAuthor && !showDropdown && (
        <div className="mt-2 px-4 py-2 bg-purple-900/20 border border-purple-500/30 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-gray-300">
              Selected: <span className="text-white font-medium">{selectedAuthor.display_name}</span>
            </span>
          </div>
          <button
            onClick={() => {
              onSelect(null);
              setQuery('');
            }}
            className="text-gray-400 hover:text-white text-sm"
          >
            Change
          </button>
        </div>
      )}
    </div>
  );
}
```

### Step 3: Create CreateAuthorModal Component

**File**: `src/components/CreateAuthorModal.tsx`

```typescript
/**
 * CreateAuthorModal Component
 *
 * Modal for creating a new author account.
 * Validates input and calls the authors API.
 */

import { useState } from 'react';
import { X, User, Mail, FileText, Image } from 'lucide-react';
import { api, Author } from '../lib/api';
import toast from 'react-hot-toast';

interface CreateAuthorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (author: Author) => void;
}

export default function CreateAuthorModal({
  isOpen,
  onClose,
  onSuccess
}: CreateAuthorModalProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    display_name: '',
    first_name: '',
    last_name: '',
    email: '',
    bio: '',
    avatar_url: ''
  });

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.display_name) {
      toast.error('Display name is required');
      return;
    }

    setLoading(true);
    try {
      const author = await api.authors.create(formData);
      toast.success(`Author "${author.display_name}" created successfully!`);
      onSuccess(author);
      onClose();
      // Reset form
      setFormData({
        display_name: '',
        first_name: '',
        last_name: '',
        email: '',
        bio: '',
        avatar_url: ''
      });
    } catch (error: any) {
      console.error('Failed to create author:', error);
      toast.error(error.response?.data?.detail || 'Failed to create author');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <h2 className="text-2xl font-bold text-white">Create New Author</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Display Name */}
          <div>
            <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
              <User className="w-4 h-4" />
              Display Name *
            </label>
            <input
              type="text"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              placeholder="Archbishop Nicholas Duncan-Williams"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
              required
            />
          </div>

          {/* First Name */}
          <div>
            <label className="text-sm font-medium text-gray-300 mb-2 block">
              First Name
            </label>
            <input
              type="text"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              placeholder="Nicholas"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>

          {/* Last Name */}
          <div>
            <label className="text-sm font-medium text-gray-300 mb-2 block">
              Last Name
            </label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              placeholder="Duncan-Williams"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>

          {/* Email */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <Mail className="w-4 h-4" />
              Email (optional)
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="author@example.com"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>

          {/* Bio */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <FileText className="w-4 h-4" />
              Bio (optional)
            </label>
            <textarea
              value={formData.bio}
              onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
              placeholder="Brief biography of the author..."
              rows={4}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors resize-none"
            />
          </div>

          {/* Avatar URL */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <Image className="w-4 h-4" />
              Avatar URL (optional)
            </label>
            <input
              type="url"
              value={formData.avatar_url}
              onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
              placeholder="https://example.com/avatar.jpg"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !formData.display_name}
              className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Author'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

### Step 4: Add debounce utility (if not exists)

**File**: `src/utils/debounce.ts`

```typescript
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };

    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
```

### Step 5: Update AuthorUploadPage.tsx

Replace the author input field (lines 580-594) with:

```typescript
// Add state for author selection
const [selectedAuthor, setSelectedAuthor] = useState<Author | null>(null);
const [showCreateAuthorModal, setShowCreateAuthorModal] = useState(false);

// Update handleSubmit to include author_id
const handleSubmit = async (e: React.FormEvent) => {
  // ... existing validation ...

  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('author', author); // Still required for display

  // Add author_id if selected
  if (selectedAuthor) {
    formData.append('author_id', selectedAuthor.user_id);
  }

  // ... rest of form data ...
};

// In the JSX, replace the author input with:
{/* Author Selection */}
<div>
  <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
    <User className="w-4 h-4" />
    Author *
  </label>
  <AuthorSelector
    selectedAuthor={selectedAuthor}
    onSelect={(author) => {
      setSelectedAuthor(author);
      if (author) {
        setAuthor(author.display_name);
      }
    }}
    onCreateNew={() => setShowCreateAuthorModal(true)}
  />
  {!selectedAuthor && (
    <p className="mt-2 text-sm text-gray-400">
      Or enter author name manually:
    </p>
  )}
  {!selectedAuthor && (
    <input
      type="text"
      value={author}
      onChange={(e) => setAuthor(e.target.value)}
      placeholder="Enter author name"
      className="mt-2 w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
      required
    />
  )}
</div>

{/* Create Author Modal */}
<CreateAuthorModal
  isOpen={showCreateAuthorModal}
  onClose={() => setShowCreateAuthorModal(false)}
  onSuccess={(newAuthor) => {
    setSelectedAuthor(newAuthor);
    setAuthor(newAuthor.display_name);
    toast.success(`Author "${newAuthor.display_name}" created!`);
  }}
/>
```

## Testing Checklist

- [ ] Author search works and shows results
- [ ] Selecting an author fills the author field
- [ ] "Create New Author" button opens modal
- [ ] Creating new author works and auto-selects it
- [ ] Book upload includes author_id when author is selected
- [ ] Book upload still works without author_id (backward compatible)
- [ ] Archbishop Duncan-Williams appears in search results
- [ ] UI is responsive and looks good
- [ ] Error handling works (network errors, validation errors)

## Notes

- The backend is complete and ready to use
- Archbishop Duncan-Williams already exists with ID: `author_cecb671bb6b2`
- All APIs require authentication (Bearer token)
- Author selection is optional - books can still be uploaded without linking to author account
- Frontend can be built and deployed independently

## Next Steps

1. Add the API functions to your api module
2. Create the AuthorSelector component
3. Create the CreateAuthorModal component
4. Update AuthorUploadPage to use the new components
5. Test thoroughly
6. Build and deploy frontend

## Contact

If you need help with the implementation or run into issues, refer to this document or check the backend API documentation at `/api/docs`.
