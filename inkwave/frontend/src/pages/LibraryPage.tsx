/**
 * LibraryPage
 * Shows user's personal library: books being read, completed, and bookmarked
 */

import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  BookOpen,
  Play,
  CheckCircle,
  Bookmark,
  Clock,
  TrendingUp,
  Gift,
} from 'lucide-react';
import { api } from '../lib/api';
import { getBookCoverUrl, generatePlaceholderCover } from '../lib/bookCoverUtils';
import toast from 'react-hot-toast';
import PullToRefreshIndicator from '../components/PullToRefreshIndicator';
import { usePullToRefresh } from '../hooks/usePullToRefresh';

interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
  duration: number;
  progress?: number;
  lastAccessed?: string;
  completed?: boolean;
}

interface LibraryBook {
  id: string;
  title: string;
  author?: string;
  cover_url?: string;
  description?: string;
  access_type: string;
  granted_at?: string;
  processing_status: string;
}

export default function LibraryPage() {
	useEffect(() => {
		document.title = 'My Library - InkWave';
	}, []);

  const navigate = useNavigate();
  const [myBooks, setMyBooks] = useState<LibraryBook[]>([]);
  const [continueReading, setContinueReading] = useState<Book[]>([]);
  const [completed, setCompleted] = useState<Book[]>([]);
  const [bookmarked, setBookmarked] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'mybooks' | 'continue' | 'completed' | 'bookmarked'>('mybooks');

  const fetchLibrary = useCallback(async () => {
    try {
      setLoading(true);

      // Fetch user's granted books (from invitations)
      try {
        const libraryResponse = await api.bookInvitations.getMyLibrary();
        const libraryBooks = libraryResponse.data.books || [];
        setMyBooks(libraryBooks);
      } catch (err) {
        console.log('Could not fetch my books');
        setMyBooks([]);
      }

      // Fetch continue reading/listening books
      try {
        const continueResponse = await api.books.continueReading(50);
        const continueBooks = continueResponse.data.books || [];
        const mappedContinue = continueBooks.map((book: any) => ({
          id: book.id,
          title: book.title,
          author: book.author,
          coverUrl: getBookCoverUrl(book.cover_url, book.title, book.author),
          duration: book.duration || 0,
          progress: book.progress || 0,
          lastAccessed: book.last_accessed,
          completed: book.progress >= 100,
        }));

        // Separate into continue reading and completed
        const inProgress = mappedContinue.filter((book: Book) => book.progress && book.progress < 100 && book.progress > 0);
        const done = mappedContinue.filter((book: Book) => book.progress && book.progress >= 100);

        setContinueReading(inProgress);
        setCompleted(done);
      } catch (err) {
        console.log('Could not fetch library books');
        setContinueReading([]);
        setCompleted([]);
      }

      // Fetch bookmarked books
      try {
        const bookmarksResponse = await api.bookmarks.list();
        const bookmarkedBooks = bookmarksResponse.data.books || [];
        const mappedBookmarks = bookmarkedBooks.map((book: any) => ({
          id: book.id,
          title: book.title,
          author: book.author,
          coverUrl: book.cover_url || '',
          duration: book.duration || 0,
          bookmarked_at: book.bookmarked_at,
        }));
        setBookmarked(mappedBookmarks);
      } catch (err) {
        console.log('Could not fetch bookmarked books');
        setBookmarked([]);
      }

    } catch (error) {
      console.error('Error fetching library:', error);
      toast.error('Failed to load library');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLibrary();
  }, [fetchLibrary]);

  // Pull-to-refresh for mobile
  const { handlers, state: pullState } = usePullToRefresh({
    onRefresh: fetchLibrary,
    disabled: loading,
  });

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  const formatLastAccessed = (dateString?: string) => {
    if (!dateString) return 'Recently';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  const BookCard = ({ book }: { book: Book }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => navigate(`/book/${book.id}`)}
      className="bg-gray-800 rounded-lg overflow-hidden cursor-pointer hover:bg-gray-750 transition group"
    >
      <div className="relative aspect-[2/3]">
        <img
          src={book.coverUrl}
          alt={book.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src = generatePlaceholderCover(book.title, book.author);
            e.currentTarget.onerror = null;
          }}
        />
        {book.progress !== undefined && book.progress > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-900">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
              style={{ width: `${book.progress}%` }}
            />
          </div>
        )}
        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
          <Play className="w-12 h-12 text-white fill-white" />
        </div>
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-white mb-1 truncate">{book.title}</h3>
        <p className="text-sm text-gray-400 mb-2 truncate">{book.author}</p>
        {book.progress !== undefined && book.progress > 0 && (
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{book.progress}% complete</span>
            {book.lastAccessed && (
              <span>{formatLastAccessed(book.lastAccessed)}</span>
            )}
          </div>
        )}
        {book.duration > 0 && (
          <div className="flex items-center space-x-1 text-xs text-gray-500 mt-1">
            <Clock className="w-3 h-3" />
            <span>{formatDuration(book.duration)}</span>
          </div>
        )}
      </div>
    </motion.div>
  );

  const EmptyState = ({ icon: Icon, title, description }: { icon: any, title: string, description: string }) => (
    <div className="text-center py-16">
      <Icon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
      <h3 className="text-xl font-semibold text-gray-300 mb-2">{title}</h3>
      <p className="text-gray-500 mb-6">{description}</p>
      <button
        onClick={() => navigate('/browse')}
        className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-full text-white font-semibold transition"
      >
        Browse Books
      </button>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading your library...</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'mybooks' as const, label: 'My Books', count: myBooks.length, icon: Gift },
    { id: 'continue' as const, label: 'Continue Listening', count: continueReading.length, icon: TrendingUp },
    { id: 'completed' as const, label: 'Completed', count: completed.length, icon: CheckCircle },
    { id: 'bookmarked' as const, label: 'Bookmarked', count: bookmarked.length, icon: Bookmark },
  ];

  const currentBooks = activeTab === 'continue' ? continueReading : activeTab === 'completed' ? completed : activeTab === 'bookmarked' ? bookmarked : [];

  // Card for library books (from invitations)
  const LibraryBookCard = ({ book }: { book: LibraryBook }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => navigate(`/book/${book.id}`)}
      className="bg-gray-800 rounded-lg overflow-hidden cursor-pointer hover:bg-gray-750 transition group"
    >
      <div className="relative aspect-[2/3]">
        <img
          src={getBookCoverUrl(book.cover_url, book.title, book.author)}
          alt={book.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src = generatePlaceholderCover(book.title, book.author || '');
            e.currentTarget.onerror = null;
          }}
        />
        <div className="absolute top-2 right-2">
          <span className="px-2 py-1 bg-purple-500/80 text-white text-xs rounded-full">
            <Gift className="w-3 h-3 inline mr-1" />
            Shared
          </span>
        </div>
        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
          <Play className="w-12 h-12 text-white fill-white" />
        </div>
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-white mb-1 truncate">{book.title}</h3>
        <p className="text-sm text-gray-400 mb-2 truncate">{book.author || 'Unknown Author'}</p>
        {book.processing_status && book.processing_status !== 'ready' && (
          <span className="text-xs text-yellow-400">Processing: {book.processing_status}</span>
        )}
      </div>
    </motion.div>
  );

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-gray-950 pb-16"
      {...handlers}
    >
      {/* Pull-to-refresh indicator */}
      <PullToRefreshIndicator
        pullDistance={pullState.pullDistance}
        progress={pullState.progress}
        canRelease={pullState.canRelease}
        isRefreshing={pullState.isRefreshing}
        isPulling={pullState.isPulling}
      />

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">My Library</h1>
          <p className="text-gray-400">Your personal collection of books and listening progress</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gradient-to-br from-indigo-500/10 to-indigo-600/10 border border-indigo-500/20 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <Gift className="w-8 h-8 text-indigo-400" />
              <span className="text-3xl font-bold text-white">{myBooks.length}</span>
            </div>
            <p className="text-gray-300 font-medium">My Books</p>
            <p className="text-sm text-gray-500">Books shared with you</p>
          </div>

          <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-8 h-8 text-purple-400" />
              <span className="text-3xl font-bold text-white">{continueReading.length}</span>
            </div>
            <p className="text-gray-300 font-medium">In Progress</p>
            <p className="text-sm text-gray-500">Currently listening</p>
          </div>

          <div className="bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle className="w-8 h-8 text-green-400" />
              <span className="text-3xl font-bold text-white">{completed.length}</span>
            </div>
            <p className="text-gray-300 font-medium">Completed</p>
            <p className="text-sm text-gray-500">Books finished</p>
          </div>

          <div className="bg-gradient-to-br from-pink-500/10 to-pink-600/10 border border-pink-500/20 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <Bookmark className="w-8 h-8 text-pink-400" />
              <span className="text-3xl font-bold text-white">{bookmarked.length}</span>
            </div>
            <p className="text-gray-300 font-medium">Bookmarked</p>
            <p className="text-sm text-gray-500">Saved for later</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-6 border-b border-gray-800">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-6 py-3 font-semibold transition border-b-2 ${
                  activeTab === tab.id
                    ? 'text-purple-400 border-purple-400'
                    : 'text-gray-400 border-transparent hover:text-gray-300'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{tab.label}</span>
                <span className="px-2 py-0.5 bg-gray-800 rounded-full text-xs">
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Books Grid */}
        {activeTab === 'mybooks' ? (
          // My Books tab - shows books from invitations
          myBooks.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {myBooks.map((book) => (
                <LibraryBookCard key={book.id} book={book} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Gift}
              title="No shared books yet"
              description="Books shared with you will appear here"
            />
          )
        ) : currentBooks.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {currentBooks.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={activeTab === 'continue' ? BookOpen : activeTab === 'completed' ? CheckCircle : Bookmark}
            title={
              activeTab === 'continue'
                ? 'No books in progress'
                : activeTab === 'completed'
                ? 'No completed books yet'
                : 'No bookmarked books'
            }
            description={
              activeTab === 'continue'
                ? 'Start listening to a book to see it here'
                : activeTab === 'completed'
                ? 'Complete a book to see it here'
                : 'Bookmark books to save them for later'
            }
          />
        )}
      </div>
    </motion.div>
  );
}
