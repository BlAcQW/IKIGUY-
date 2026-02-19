/**
 * Book Moderation Page
 *
 * Comprehensive admin page for book moderation with three tabs:
 * - All Books: Search and hide any book
 * - Hidden Books: View and manage hidden books
 * - Audit Log: View all moderation actions
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Shield,
  Search,
  EyeOff,
  Eye,
  Trash2,
  Loader,
  FileText,
  Calendar,
  User,
  Book as BookIcon,
} from 'lucide-react';
import { api } from '../../lib/api';
import toast from 'react-hot-toast';
import AdminLayoutTabs from '../../components/admin/AdminLayoutTabs';
import HideBookModal from '../../components/HideBookModal';
import UnhideBookModal from '../../components/UnhideBookModal';
import PermanentDeleteBookModal from '../../components/PermanentDeleteBookModal';
import AuditLogViewer from '../../components/admin/AuditLogViewer';
import { useAuthStore } from '../../store/authStore';
import { generatePlaceholderCover, getBookCoverUrl } from '../../lib/bookCoverUtils';
import type { Book, HiddenBook } from '../../types/book';

type TabType = 'all' | 'hidden' | 'audit';

export default function BookModerationPage() {
  useEffect(() => {
    document.title = 'Book Moderation - InkWave';
  }, []);

  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [searchParams, setSearchParams] = useSearchParams();

  const [activeTab, setActiveTab] = useState<TabType>(
    (searchParams.get('tab') as TabType) || 'all'
  );

  // All Books Tab State
  const [allBooks, setAllBooks] = useState<Book[]>([]);
  const [allBooksLoading, setAllBooksLoading] = useState(false);
  const [allBooksSearch, setAllBooksSearch] = useState('');
  const [allBooksPage, setAllBooksPage] = useState(1);
  const [allBooksTotal, setAllBooksTotal] = useState(0);

  // Hidden Books Tab State
  const [hiddenBooks, setHiddenBooks] = useState<HiddenBook[]>([]);
  const [hiddenBooksLoading, setHiddenBooksLoading] = useState(false);
  const [hiddenBooksSearch, setHiddenBooksSearch] = useState('');
  const [hiddenBooksPage, setHiddenBooksPage] = useState(1);
  const [hiddenBooksTotal, setHiddenBooksTotal] = useState(0);

  // Modals
  const [bookToHide, setBookToHide] = useState<Book | null>(null);
  const [bookToUnhide, setBookToUnhide] = useState<HiddenBook | null>(null);
  const [bookToDelete, setBookToDelete] = useState<HiddenBook | null>(null);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const perPage = 20;

  useEffect(() => {
    if (activeTab === 'all') {
      loadAllBooks();
    } else if (activeTab === 'hidden') {
      loadHiddenBooks();
    }
  }, [activeTab, allBooksPage, hiddenBooksPage]);

  useEffect(() => {
    setSearchParams({ tab: activeTab });
  }, [activeTab, setSearchParams]);

  const loadAllBooks = async () => {
    try {
      setAllBooksLoading(true);
      const response = await api.books.getAllBooks({
        page: allBooksPage,
        per_page: perPage,
      });
      setAllBooks(response.data.books || []);
      setAllBooksTotal(response.data.total || 0);
    } catch (error: any) {
      console.error('Failed to load all books:', error);
      toast.error('Failed to load books');
    } finally {
      setAllBooksLoading(false);
    }
  };

  const loadHiddenBooks = async () => {
    try {
      setHiddenBooksLoading(true);
      const response = await api.admin.listHiddenBooks({
        page: hiddenBooksPage,
        per_page: perPage,
      });
      setHiddenBooks(response.data.books || []);
      setHiddenBooksTotal(response.data.total || 0);
    } catch (error: any) {
      console.error('Failed to load hidden books:', error);
      toast.error('Failed to load hidden books');
    } finally {
      setHiddenBooksLoading(false);
    }
  };

  const handleHideBook = async (reason: string) => {
    if (!bookToHide) return;

    setActionInProgress(bookToHide.id);
    try {
      await api.admin.hideBook(bookToHide.id, reason);
      toast.success(`"${bookToHide.title}" has been hidden`);
      await loadAllBooks();
      setBookToHide(null);
    } catch (error: any) {
      console.error('Failed to hide book:', error);
      toast.error(error.response?.data?.detail || 'Failed to hide book');
    } finally {
      setActionInProgress(null);
    }
  };

  const handleUnhideBook = async (reason?: string) => {
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

  const filteredAllBooks = allBooks.filter(
    (book) =>
      book.title.toLowerCase().includes(allBooksSearch.toLowerCase()) ||
      book.author.toLowerCase().includes(allBooksSearch.toLowerCase())
  );

  const filteredHiddenBooks = hiddenBooks.filter(
    (book) =>
      book.title.toLowerCase().includes(hiddenBooksSearch.toLowerCase()) ||
      book.author.toLowerCase().includes(hiddenBooksSearch.toLowerCase()) ||
      book.hidden_reason?.toLowerCase().includes(hiddenBooksSearch.toLowerCase())
  );

  const allBooksPages = Math.ceil(allBooksTotal / perPage);
  const hiddenBooksPages = Math.ceil(hiddenBooksTotal / perPage);

  const tabs = [
    { id: 'all' as TabType, label: 'All Books', icon: BookIcon },
    { id: 'hidden' as TabType, label: 'Hidden Books', icon: EyeOff },
    { id: 'audit' as TabType, label: 'Audit Log', icon: FileText },
  ];

  return (
    <AdminLayoutTabs
      currentPage="/admin/books/moderation"
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
              <Shield className="w-6 h-6 text-red-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Book Moderation</h1>
              <p className="text-sm text-gray-400">
                Manage book visibility and view moderation audit logs
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-gray-700">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-3 font-semibold transition-colors relative ${
                  activeTab === tab.id
                    ? 'text-purple-400 border-b-2 border-purple-400'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="min-h-[600px]">
          {/* All Books Tab */}
          {activeTab === 'all' && (
            <div className="space-y-6">
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={allBooksSearch}
                  onChange={(e) => setAllBooksSearch(e.target.value)}
                  placeholder="Search by title or author..."
                  className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>

              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Total Books</p>
                      <p className="text-2xl font-bold text-white">{allBooksTotal}</p>
                    </div>
                    <BookIcon className="w-8 h-8 text-purple-400" />
                  </div>
                </div>
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Current Page</p>
                      <p className="text-2xl font-bold text-white">
                        {allBooksPage} / {allBooksPages || 1}
                      </p>
                    </div>
                    <Calendar className="w-8 h-8 text-blue-400" />
                  </div>
                </div>
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Showing</p>
                      <p className="text-2xl font-bold text-white">{filteredAllBooks.length}</p>
                    </div>
                    <Eye className="w-8 h-8 text-green-400" />
                  </div>
                </div>
              </div>

              {/* Books Table */}
              {allBooksLoading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader className="w-8 h-8 text-purple-400 animate-spin" />
                </div>
              ) : filteredAllBooks.length === 0 ? (
                <div className="text-center py-20 bg-gray-800/50 border border-gray-700 rounded-lg">
                  <BookIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-white mb-2">No books found</h2>
                  <p className="text-gray-400">
                    {allBooksSearch ? 'No books match your search' : 'No books available'}
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
                              Author
                            </th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                              Status
                            </th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                              Visibility
                            </th>
                            <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700">
                          {filteredAllBooks.map((book) => (
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
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <p className="text-gray-300">{book.author}</p>
                              </td>
                              <td className="px-6 py-4">
                                <span
                                  className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                                    book.processing_status === 'completed'
                                      ? 'bg-green-500/20 text-green-400'
                                      : book.processing_status === 'processing'
                                      ? 'bg-blue-500/20 text-blue-400'
                                      : 'bg-yellow-500/20 text-yellow-400'
                                  }`}
                                >
                                  {book.processing_status}
                                </span>
                              </td>
                              <td className="px-6 py-4">
                                <span
                                  className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                                    book.visibility === 'public'
                                      ? 'bg-green-500/20 text-green-400'
                                      : book.visibility === 'unlisted'
                                      ? 'bg-blue-500/20 text-blue-400'
                                      : book.visibility === 'private'
                                      ? 'bg-red-500/20 text-red-400'
                                      : 'bg-yellow-500/20 text-yellow-400'
                                  }`}
                                >
                                  {book.visibility || 'public'}
                                </span>
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
                                    onClick={() => setBookToHide(book)}
                                    disabled={actionInProgress === book.id || book.is_hidden}
                                    className="p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
                                    title="Hide Book"
                                  >
                                    <EyeOff className="w-4 h-4" />
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
                  {allBooksPages > 1 && (
                    <div className="mt-6 flex items-center justify-center gap-2">
                      <button
                        onClick={() => setAllBooksPage((p) => Math.max(1, p - 1))}
                        disabled={allBooksPage === 1}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <span className="text-gray-400">
                        Page {allBooksPage} of {allBooksPages}
                      </span>
                      <button
                        onClick={() => setAllBooksPage((p) => Math.min(allBooksPages, p + 1))}
                        disabled={allBooksPage === allBooksPages}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Hidden Books Tab */}
          {activeTab === 'hidden' && (
            <div className="space-y-6">
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={hiddenBooksSearch}
                  onChange={(e) => setHiddenBooksSearch(e.target.value)}
                  placeholder="Search by title, author, or reason..."
                  className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>

              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Total Hidden</p>
                      <p className="text-2xl font-bold text-white">{hiddenBooksTotal}</p>
                    </div>
                    <EyeOff className="w-8 h-8 text-red-400" />
                  </div>
                </div>
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Current Page</p>
                      <p className="text-2xl font-bold text-white">
                        {hiddenBooksPage} / {hiddenBooksPages || 1}
                      </p>
                    </div>
                    <Calendar className="w-8 h-8 text-blue-400" />
                  </div>
                </div>
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Showing</p>
                      <p className="text-2xl font-bold text-white">
                        {filteredHiddenBooks.length}
                      </p>
                    </div>
                    <User className="w-8 h-8 text-green-400" />
                  </div>
                </div>
              </div>

              {/* Hidden Books Table */}
              {hiddenBooksLoading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader className="w-8 h-8 text-purple-400 animate-spin" />
                </div>
              ) : filteredHiddenBooks.length === 0 ? (
                <div className="text-center py-20 bg-gray-800/50 border border-gray-700 rounded-lg">
                  <EyeOff className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-white mb-2">No hidden books</h2>
                  <p className="text-gray-400">
                    {hiddenBooksSearch
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
                          {filteredHiddenBooks.map((book) => (
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
                                <p className="text-gray-300">
                                  {book.hidden_by_email || 'Unknown'}
                                </p>
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
                  {hiddenBooksPages > 1 && (
                    <div className="mt-6 flex items-center justify-center gap-2">
                      <button
                        onClick={() => setHiddenBooksPage((p) => Math.max(1, p - 1))}
                        disabled={hiddenBooksPage === 1}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <span className="text-gray-400">
                        Page {hiddenBooksPage} of {hiddenBooksPages}
                      </span>
                      <button
                        onClick={() =>
                          setHiddenBooksPage((p) => Math.min(hiddenBooksPages, p + 1))
                        }
                        disabled={hiddenBooksPage === hiddenBooksPages}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Audit Log Tab */}
          {activeTab === 'audit' && (
            <div>
              <AuditLogViewer limit={100} />
            </div>
          )}
        </div>

        {/* Modals */}
        {bookToHide && (
          <HideBookModal
            isOpen={!!bookToHide}
            onClose={() => setBookToHide(null)}
            book={bookToHide}
            onHide={handleHideBook}
          />
        )}

        {bookToUnhide && (
          <UnhideBookModal
            isOpen={!!bookToUnhide}
            onClose={() => setBookToUnhide(null)}
            book={bookToUnhide}
            onUnhide={handleUnhideBook}
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
