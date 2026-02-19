/**
 * My Books Page.
 *
 * Author dashboard to view and manage uploaded books.
 * Shows book list with status, allows editing and deletion.
 */

import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  BookOpen,
  Plus,
  Edit2,
  Trash2,
  Eye,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader,
  Search,
  Filter,
  MoreVertical,
  X,
  Settings,
  Play,
  Calendar,
  Tag,
  Share2,
  RefreshCw,
  FileText,
  Lock,
  Link2,
  Globe,
} from 'lucide-react';
import { api } from '../lib/api';
import toast from 'react-hot-toast';
import { DeleteConfirmationModal } from '../components/DeleteConfirmationModal';
import { generatePlaceholderCover, getBookCoverUrl } from '../lib/bookCoverUtils';
import BookVoiceSettingsModal from '../components/BookVoiceSettingsModal';
import { BookInvitationModal } from '../components/BookInvitationModal';
import BookVisibilityModal from '../components/BookVisibilityModal';
import { useProfile } from '../hooks/useProfile';
import type { BookVisibility } from '../types/book';

interface Book {
  id: string;
  title: string;
  author: string;
  description?: string;
  cover_url?: string;
  processing_status: string;
  created_at?: string;
  genre?: string[];
  visibility?: string;
  visibility_badge?: string;
}

interface EditModalProps {
  book: Book;
  onClose: () => void;
  onSave: (data: { title: string; author: string; description: string; genre: string; cover_url: string }) => Promise<void>;
}

function EditBookModal({ book, onClose, onSave }: EditModalProps) {
  const [title, setTitle] = useState(book.title);
  const [author, setAuthor] = useState(book.author);
  const [description, setDescription] = useState(book.description || '');
  const [genre, setGenre] = useState(Array.isArray(book.genre) ? book.genre.join(', ') : '');
  const [coverUrl, setCoverUrl] = useState(book.cover_url || '');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({ title, author, description, genre, cover_url: coverUrl });
      onClose();
    } catch (error) {
      // Error handled by parent
    } finally {
      setSaving(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-gray-800 border border-gray-700 rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Edit Book</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-700 rounded">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Cover Image Preview and URL */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Cover Image</label>
            <div className="flex gap-4">
              {/* Preview */}
              <div className="w-20 h-28 flex-shrink-0 rounded-lg overflow-hidden bg-gray-900 border border-gray-700">
                {coverUrl ? (
                  <img
                    src={coverUrl}
                    alt="Cover preview"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '';
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-600">
                    <BookOpen className="w-8 h-8" />
                  </div>
                )}
              </div>
              {/* URL Input */}
              <div className="flex-1">
                <input
                  type="url"
                  value={coverUrl}
                  onChange={(e) => setCoverUrl(e.target.value)}
                  placeholder="Enter cover image URL"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Paste a URL to an image (JPG, PNG, WebP)
                </p>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Author</label>
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 resize-none"
              placeholder="Enter a description for this book..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Genre (comma-separated)</label>
            <input
              type="text"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              placeholder="Fiction, Science, etc."
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}

export default function MyBooksPage() {
	useEffect(() => {
		document.title = 'My Books - InkWave';
	}, []);

  const navigate = useNavigate();
  const { data: profile } = useProfile();
  const isAdmin = profile?.is_admin ?? false;

  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [deletingBookId, setDeletingBookId] = useState<string | null>(null);
  const [bookToDelete, setBookToDelete] = useState<Book | null>(null);
  const [bookForVoiceSettings, setBookForVoiceSettings] = useState<Book | null>(null);
  const [bookToShare, setBookToShare] = useState<Book | null>(null);
  const [bookForVisibility, setBookForVisibility] = useState<Book | null>(null);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [reprocessingBookId, setReprocessingBookId] = useState<string | null>(null);
  const [changingVisibility, setChangingVisibility] = useState<string | null>(null);

  // Ref for intersection observer
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Load initial books
  useEffect(() => {
    loadBooks(true);
  }, [statusFilter]);

  // Infinite scroll observer
  useEffect(() => {
    if (!loadMoreRef.current || !hasMore || loadingMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          loadMoreBooks();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);

    return () => observer.disconnect();
  }, [hasMore, loadingMore, page]);

  const loadBooks = async (reset: boolean = false) => {
    try {
      if (reset) {
        setLoading(true);
        setPage(1);
        setBooks([]);
      }

      const response = await api.books.myBooks({
        page: reset ? 1 : page,
        per_page: 24,
        status: statusFilter || undefined,
      });

      const newBooks = response.data.books || [];

      if (reset) {
        setBooks(newBooks);
      } else {
        setBooks(prev => [...prev, ...newBooks]);
      }

      // Check if there are more books to load
      const currentPage = reset ? 1 : page;
      const totalPages = response.data.total_pages || 1;
      setHasMore(currentPage < totalPages);
    } catch (error: any) {
      console.error('Failed to load books:', error);
      toast.error('Failed to load your books');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const loadMoreBooks = async () => {
    if (loadingMore || !hasMore) return;

    setLoadingMore(true);
    setPage(prev => prev + 1);

    // Wait for page state to update, then load
    setTimeout(() => loadBooks(false), 0);
  };

  const handleEdit = async (bookId: string, data: { title: string; author: string; description: string; genre: string; cover_url: string }) => {
    try {
      await api.books.update(bookId, {
        title: data.title,
        author: data.author,
        description: data.description,
        genre: data.genre,
        cover_url: data.cover_url,
      });
      toast.success('Book updated successfully');
      loadBooks(true);
    } catch (error: any) {
      console.error('Failed to update book:', error);
      toast.error(error.response?.data?.detail || 'Failed to update book');
      throw error;
    }
  };

  const handleDeleteClick = (book: Book) => {
    setBookToDelete(book);
  };

  const handleDeleteConfirm = async () => {
    if (!bookToDelete) return;

    setDeletingBookId(bookToDelete.id);
    try {
      await api.books.delete(bookToDelete.id);
      toast.success('Book deleted successfully');
      loadBooks(true);
      setBookToDelete(null);
    } catch (error: any) {
      console.error('Failed to delete book:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete book');
    } finally {
      setDeletingBookId(null);
    }
  };

  const handleReprocess = async (book: Book) => {
    if (!isAdmin) {
      toast.error('Admin access required');
      return;
    }

    setReprocessingBookId(book.id);
    try {
      await api.books.reprocess(book.id);
      toast.success(`Reprocessing started for "${book.title}"`);
      loadBooks(true);
    } catch (error: any) {
      console.error('Failed to reprocess book:', error);
      toast.error(error.response?.data?.detail || 'Failed to reprocess book');
    } finally {
      setReprocessingBookId(null);
    }
  };

  const handleChangeVisibility = async (bookId: string, newVisibility: BookVisibility) => {
    setChangingVisibility(bookId);
    try {
      await api.books.updateVisibility(bookId, newVisibility);
      toast.success(`Book visibility changed to ${newVisibility}`);
      loadBooks(true); // Refresh list
    } catch (error: any) {
      console.error('Failed to change visibility:', error);
      toast.error(error.response?.data?.detail || 'Failed to change visibility');
    } finally {
      setChangingVisibility(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'processing':
        return <Loader className="w-4 h-4 text-yellow-400 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      ready: 'bg-green-500/20 text-green-400 border-green-500/30',
      processing: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      error: 'bg-red-500/20 text-red-400 border-red-500/30',
      pending: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    };
    return styles[status] || styles.pending;
  };

  const filteredBooks = books.filter(book =>
    book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    book.author.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-6 h-6 text-gray-400" />
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                  <BookOpen className="w-8 h-8 text-purple-400" />
                  My Books
                </h1>
                <p className="text-gray-400 mt-1">
                  Manage your uploaded books
                </p>
              </div>
            </div>

            <Link
              to="/author/upload"
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg font-semibold transition-all"
            >
              <Plus className="w-5 h-5" />
              Upload New Book
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-8">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search your books..."
              className="w-full pl-10 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
            />
          </div>

          {/* Status Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="pl-10 pr-8 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 appearance-none cursor-pointer"
            >
              <option value="">All Status</option>
              <option value="ready">Ready</option>
              <option value="processing">Processing</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>

        {/* Books Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader className="w-8 h-8 text-purple-400 animate-spin" />
          </div>
        ) : filteredBooks.length === 0 ? (
          <div className="text-center py-20">
            <BookOpen className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">No books found</h2>
            <p className="text-gray-400 mb-6">
              {searchQuery || statusFilter
                ? 'Try adjusting your filters'
                : "You haven't uploaded any books yet"}
            </p>
            {!searchQuery && !statusFilter && (
              <Link
                to="/author/upload"
                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors"
              >
                <Plus className="w-5 h-5" />
                Upload Your First Book
              </Link>
            )}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {filteredBooks.map((book, index) => (
              <motion.div
                key={book.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 border border-gray-700/50 rounded-xl overflow-hidden hover:border-purple-500/50 hover:shadow-xl hover:shadow-purple-500/10 transition-all duration-300 group cursor-pointer"
                onClick={() => navigate(`/book/${book.id}`)}
              >
                {/* Cover Image with Overlay */}
                <div className="relative aspect-[3/4] bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 overflow-hidden p-1">
                  <img
                    src={getBookCoverUrl(book.cover_url, book.title, book.author)}
                    alt={book.title}
                    className="w-full h-full object-contain rounded-sm group-hover:scale-105 transition-transform duration-500"
                    onError={(e) => {
                      e.currentTarget.src = generatePlaceholderCover(book.title, book.author);
                      e.currentTarget.onerror = null; // Prevent infinite loop
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                  {/* Status Badge */}
                  <div className={`absolute top-2 left-2 flex items-center gap-1 px-2 py-1 rounded-full border backdrop-blur-md text-xs font-semibold shadow-lg ${getStatusBadge(book.processing_status)}`}>
                    {getStatusIcon(book.processing_status)}
                    <span className="capitalize hidden sm:inline">{book.processing_status}</span>
                  </div>

                  {/* Visibility Badge (if not public) */}
                  {book.visibility && book.visibility !== 'public' && (
                    <div className={`absolute top-12 left-2 flex items-center gap-1 px-2 py-1 rounded-full border backdrop-blur-md text-xs font-semibold shadow-lg ${
                      book.visibility === 'draft' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
                      book.visibility === 'unlisted' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
                      'bg-red-500/20 text-red-400 border-red-500/30'
                    }`}>
                      {book.visibility === 'draft' && <FileText className="w-3 h-3" />}
                      {book.visibility === 'unlisted' && <Link2 className="w-3 h-3" />}
                      {book.visibility === 'private' && <Lock className="w-3 h-3" />}
                      <span className="capitalize hidden sm:inline">{book.visibility}</span>
                    </div>
                  )}

                  {/* Quick Actions on Hover */}
                  <div className="absolute inset-0 flex items-center justify-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                    <motion.button
                      initial={{ scale: 0.8, opacity: 0 }}
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/player/${book.id}`);
                      }}
                      className="p-3 bg-purple-600 hover:bg-purple-700 rounded-full text-white shadow-xl pointer-events-auto transition-colors"
                    >
                      <Play className="w-5 h-5 fill-white" />
                    </motion.button>
                  </div>

                  {/* Actions Menu Button */}
                  <div className="absolute top-2 right-2" onClick={(e) => e.stopPropagation()}>
                    <button
                      id={`menu-btn-${book.id}`}
                      onClick={() => setOpenMenuId(openMenuId === book.id ? null : book.id)}
                      className="p-1.5 bg-gray-900/90 backdrop-blur-md hover:bg-gray-800 rounded-lg text-gray-300 hover:text-white transition-all shadow-lg"
                    >
                      <MoreVertical className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Book Info */}
                <div className="p-3 space-y-2">
                  <div>
                    <h3 className="font-bold text-white mb-1 line-clamp-2 text-sm leading-tight group-hover:text-purple-300 transition-colors">
                      {book.title}
                    </h3>
                    <p className="text-xs text-gray-400 flex items-center gap-1.5">
                      <span className="text-gray-500">by</span>
                      <span className="font-medium">{book.author}</span>
                    </p>
                  </div>

                  {/* Description Preview */}
                  {book.description && (
                    <p className="text-xs text-gray-500 line-clamp-1 leading-relaxed">
                      {book.description}
                    </p>
                  )}

                  {/* Genre Tags */}
                  {book.genre && Array.isArray(book.genre) && book.genre.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {book.genre.slice(0, 2).map((g, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-md text-xs font-medium"
                        >
                          <Tag className="w-3 h-3" />
                          {g}
                        </span>
                      ))}
                      {book.genre.length > 2 && (
                        <span className="text-xs text-gray-500">+{book.genre.length - 2}</span>
                      )}
                    </div>
                  )}

                  {/* Metadata Footer */}
                  <div className="flex items-center justify-between pt-1.5 border-t border-gray-700/50">
                    {book.created_at && (
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Calendar className="w-3 h-3" />
                        <span className="hidden sm:inline">{new Date(book.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      <span className="capitalize hidden sm:inline">{book.processing_status}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
              ))}
            </div>

            {/* Infinite Scroll Trigger */}
            {hasMore && (
              <div
                ref={loadMoreRef}
                className="flex items-center justify-center py-8 mt-8"
              >
                {loadingMore && (
                  <div className="flex items-center gap-3 text-purple-400">
                    <Loader className="w-5 h-5 animate-spin" />
                    <span className="text-sm font-medium">Loading more books...</span>
                  </div>
                )}
              </div>
            )}

            {/* End of Results Message */}
            {!hasMore && filteredBooks.length > 0 && (
              <div className="text-center py-8 mt-8">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-full text-gray-400 text-sm">
                  <CheckCircle className="w-4 h-4" />
                  <span>You've reached the end of your library</span>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Edit Modal */}
      <AnimatePresence>
        {editingBook && (
          <EditBookModal
            book={editingBook}
            onClose={() => setEditingBook(null)}
            onSave={(data) => handleEdit(editingBook.id, data)}
          />
        )}
      </AnimatePresence>

      {/* Dropdown Menu Portal - renders outside overflow-hidden containers */}
      <AnimatePresence>
        {openMenuId && (
          <>
            {/* Backdrop to close menu */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setOpenMenuId(null)}
            />
            {/* Menu positioned near the button */}
            {(() => {
              const btn = document.getElementById(`menu-btn-${openMenuId}`);
              const rect = btn?.getBoundingClientRect();
              const book = filteredBooks.find(b => b.id === openMenuId);
              if (!rect || !book) return null;

              return (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: -10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: -10 }}
                  style={{
                    position: 'fixed',
                    top: rect.bottom + 8,
                    right: window.innerWidth - rect.right,
                    zIndex: 50,
                  }}
                  className="w-48 bg-gray-800/95 backdrop-blur-md border border-gray-700 rounded-xl shadow-2xl overflow-hidden"
                >
                  <button
                    onClick={() => {
                      navigate(`/book/${book.id}`);
                      setOpenMenuId(null);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-gray-700/50 hover:text-white transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                    View Details
                  </button>
                  <button
                    onClick={() => {
                      navigate(`/player/${book.id}`);
                      setOpenMenuId(null);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-purple-400 hover:bg-purple-500/20 transition-colors"
                  >
                    <Play className="w-4 h-4" />
                    Play Book
                  </button>
                  <button
                    onClick={() => {
                      setEditingBook(book);
                      setOpenMenuId(null);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-gray-700/50 hover:text-white transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => {
                      setBookForVoiceSettings(book);
                      setOpenMenuId(null);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-purple-400 hover:bg-purple-500/20 transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                    Voice Settings
                  </button>
                  <button
                    onClick={() => {
                      setBookForVisibility(book);
                      setOpenMenuId(null);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-blue-400 hover:bg-blue-500/20 transition-colors"
                  >
                    <Globe className="w-4 h-4" />
                    Change Visibility
                  </button>
                  <button
                    onClick={() => {
                      setBookToShare(book);
                      setOpenMenuId(null);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-green-400 hover:bg-green-500/20 transition-colors"
                  >
                    <Share2 className="w-4 h-4" />
                    Share Access
                  </button>
                  {/* Admin-only: Reprocess book */}
                  {isAdmin && (
                    <button
                      onClick={() => {
                        handleReprocess(book);
                        setOpenMenuId(null);
                      }}
                      disabled={reprocessingBookId === book.id}
                      className="w-full flex items-center gap-3 px-4 py-3 text-orange-400 hover:bg-orange-500/20 transition-colors disabled:opacity-50"
                    >
                      <RefreshCw className={`w-4 h-4 ${reprocessingBookId === book.id ? 'animate-spin' : ''}`} />
                      {reprocessingBookId === book.id ? 'Reprocessing...' : 'Reprocess'}
                    </button>
                  )}
                  <div className="border-t border-gray-700 my-1" />
                  <button
                    onClick={() => {
                      handleDeleteClick(book);
                      setOpenMenuId(null);
                    }}
                    disabled={deletingBookId === book.id}
                    className="w-full flex items-center gap-3 px-4 py-3 text-red-400 hover:bg-red-500/20 transition-colors disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </motion.div>
              );
            })()}
          </>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={!!bookToDelete}
        onClose={() => setBookToDelete(null)}
        onConfirm={handleDeleteConfirm}
        itemName={bookToDelete?.title}
        itemType="book"
        consequences={[
          'All book content and embeddings will be permanently deleted',
          'All reading sessions and interactions will be lost',
          'This action cannot be undone'
        ]}
        variant="destructive"
        isDeleting={!!deletingBookId}
        warningMessage="This will permanently remove the book from your library and all associated data."
      />

      {/* Book Voice Settings Modal */}
      {bookForVoiceSettings && (
        <BookVoiceSettingsModal
          isOpen={!!bookForVoiceSettings}
          onClose={() => setBookForVoiceSettings(null)}
          bookId={bookForVoiceSettings.id}
          bookTitle={bookForVoiceSettings.title}
        />
      )}

      {/* Book Invitation Modal */}
      {bookToShare && (
        <BookInvitationModal
          isOpen={!!bookToShare}
          onClose={() => setBookToShare(null)}
          book={{
            id: bookToShare.id,
            title: bookToShare.title,
            cover_url: bookToShare.cover_url,
          }}
        />
      )}

      {/* Book Visibility Modal */}
      {bookForVisibility && (
        <BookVisibilityModal
          isOpen={!!bookForVisibility}
          onClose={() => setBookForVisibility(null)}
          book={{
            id: bookForVisibility.id,
            title: bookForVisibility.title,
            visibility: bookForVisibility.visibility,
          }}
          onVisibilityChange={handleChangeVisibility}
        />
      )}
    </div>
  );
}
