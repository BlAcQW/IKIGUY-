/**
 * Hidden Books Page
 *
 * Admin page to view and manage hidden books.
 * Shows all books that have been hidden by admins with moderation actions.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  EyeOff,
  Eye,
  Trash2,
  Search,
  Loader,
  AlertCircle,
  Calendar,
  User,
} from 'lucide-react';
import { api } from '../../lib/api';
import toast from 'react-hot-toast';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import UnhideBookModal from '../../components/UnhideBookModal';
import PermanentDeleteBookModal from '../../components/PermanentDeleteBookModal';
import { useAuthStore } from '../../store/authStore';
import { generatePlaceholderCover, getBookCoverUrl } from '../../lib/bookCoverUtils';
import type { HiddenBook } from '../../types/book';

export default function HiddenBooksPage() {
  useEffect(() => {
    document.title = 'Hidden Books - InkWave';
  }, []);

  const navigate = useNavigate();
  const { user } = useAuthStore();

  const [books, setBooks] = useState<HiddenBook[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [perPage] = useState(20);

  const [bookToUnhide, setBookToUnhide] = useState<HiddenBook | null>(null);
  const [bookToDelete, setBookToDelete] = useState<HiddenBook | null>(null);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  useEffect(() => {
    loadHiddenBooks();
  }, [page]);

  const loadHiddenBooks = async () => {
    try {
      setLoading(true);
      const response = await api.admin.listHiddenBooks({
        page,
        per_page: perPage,
      });
      setBooks(response.data.books || []);
      setTotal(response.data.total || 0);
    } catch (error: any) {
      console.error('Failed to load hidden books:', error);
      toast.error('Failed to load hidden books');
    } finally {
      setLoading(false);
    }
  };

  const handleUnhide = async (reason?: string) => {
    if (!bookToUnhide) return;

    setActionInProgress(bookToUnhide.id);
    try {
      await api.admin.unhideBook(bookToUnhide.id, reason);
      toast.success(`"${bookToUnhide.title}" has been unhidden`);
      await loadHiddenBooks();
      setBookToUnhide(null);
    } catch (error: any) {
      console.error('Failed to unhide book:', error);
      toast.error(error.response?.data?.detail || 'Failed to unhide book');
    } finally {
      setActionInProgress(null);
    }
  };

  const handlePermanentDelete = async (reason: string) => {
    if (!bookToDelete) return;

    setActionInProgress(bookToDelete.id);
    try {
      await api.admin.permanentlyDeleteBook(bookToDelete.id, reason, true);
      toast.success(`"${bookToDelete.title}" has been permanently deleted`);
      await loadHiddenBooks();
      setBookToDelete(null);
    } catch (error: any) {
      console.error('Failed to delete book:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete book');
    } finally {
      setActionInProgress(null);
    }
  };

  const filteredBooks = books.filter(
    (book) =>
      book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      book.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
      book.hidden_reason?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalPages = Math.ceil(total / perPage);

  return (
    <AdminLayoutTabs
      currentPage="/admin/books/hidden"
      appName="InkWave"
      user={
        user
          ? {
              name: user.user_metadata?.display_name || user.email?.split('@')[0] || 'User',
              email: user.email || 'no-email@example.com',
            }
          : undefined
      }
      onBack={() => navigate('/admin')}
    >
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <EyeOff className="w-6 h-6 text-red-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Hidden Books</h1>
              <p className="text-sm text-gray-400">
                Manage books that have been hidden by admins
              </p>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title, author, or reason..."
              className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Hidden</p>
                <p className="text-2xl font-bold text-white">{total}</p>
              </div>
              <EyeOff className="w-8 h-8 text-red-400" />
            </div>
          </div>
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Current Page</p>
                <p className="text-2xl font-bold text-white">{page} / {totalPages || 1}</p>
              </div>
              <Calendar className="w-8 h-8 text-blue-400" />
            </div>
          </div>
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Showing</p>
                <p className="text-2xl font-bold text-white">{filteredBooks.length}</p>
              </div>
              <User className="w-8 h-8 text-green-400" />
            </div>
          </div>
        </div>

        {/* Books Table */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader className="w-8 h-8 text-purple-400 animate-spin" />
          </div>
        ) : filteredBooks.length === 0 ? (
          <div className="text-center py-20 bg-gray-800/50 border border-gray-700 rounded-lg">
            <EyeOff className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">No hidden books</h2>
            <p className="text-gray-400">
              {searchQuery
                ? 'No books match your search'
                : 'No books have been hidden yet'}
            </p>
          </div>
        ) : (
          <>
            <div className="bg-gray-800/50 border border-gray-700 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        Book
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        Hidden By
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        Reason
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        Date
                      </th>
                      <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {filteredBooks.map((book) => (
                      <motion.tr
                        key={book.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="hover:bg-gray-700/30 transition-colors"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <img
                              src={getBookCoverUrl(book.cover_url, book.title, book.author)}
                              alt={book.title}
                              className="w-12 h-16 object-cover rounded shadow"
                              onError={(e) => {
                                e.currentTarget.src = generatePlaceholderCover(
                                  book.title,
                                  book.author
                                );
                                e.currentTarget.onerror = null;
                              }}
                            />
                            <div>
                              <p className="text-white font-medium">{book.title}</p>
                              <p className="text-sm text-gray-400">by {book.author}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-gray-300">{book.hidden_by_email || 'Unknown'}</p>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm text-gray-400 max-w-xs truncate">
                            {book.hidden_reason || 'No reason provided'}
                          </p>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-gray-300">
                            {book.hidden_at
                              ? new Date(book.hidden_at).toLocaleDateString()
                              : 'Unknown'}
                          </p>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => navigate(`/book/${book.id}`)}
                              className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                              title="View Book"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setBookToUnhide(book)}
                              disabled={actionInProgress === book.id}
                              className="p-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50"
                              title="Unhide Book"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setBookToDelete(book)}
                              disabled={actionInProgress === book.id}
                              className="p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
                              title="Permanently Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-6 flex items-center justify-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-gray-400">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}

        {/* Modals */}
        {bookToUnhide && (
          <UnhideBookModal
            isOpen={!!bookToUnhide}
            onClose={() => setBookToUnhide(null)}
            book={bookToUnhide}
            onUnhide={handleUnhide}
          />
        )}

        {bookToDelete && (
          <PermanentDeleteBookModal
            isOpen={!!bookToDelete}
            onClose={() => setBookToDelete(null)}
            book={bookToDelete}
            onDelete={handlePermanentDelete}
          />
        )}
      </div>
    </AdminLayoutTabs>
  );
}
