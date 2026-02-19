/**
 * BookDetailPage
 * Detailed view of a book with play button, description, and chapters
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Clock,
  Calendar,
  Star,
  Bookmark,
  Share2,
  ChevronLeft,
  Settings,
  MessageSquare,
  Wallet,
  Heart,
  Coins,
  Headphones,
  ListMusic,
  AlertCircle,
} from 'lucide-react';
import { api } from '../lib/api';
import { getBookCoverUrl, generatePlaceholderCover } from '../lib/bookCoverUtils';
import SocialShareButtons from '../components/SocialShareButtons';
import BookComments from '../components/BookComments';
import VoiceBookChat from '../components/VoiceBookChat';
import PaymentOptionsModal from '../components/PaymentOptionsModal';
import toast from 'react-hot-toast';
import BookVoiceSettingsModal from '../components/BookVoiceSettingsModal';
import { useProfile } from '../hooks/useProfile';
import { useWalletStore } from '../store/walletStore';
import { PRICING } from '../config/constants';

interface Chapter {
  id: string;
  title: string;
  duration: number;
  order: number;
}

interface BookDetail {
  id: string;
  title: string;
  author: string;
  authorImageUrl?: string;  // Dynamic author photo from web search
  description: string;
  coverUrl: string;
  backgroundUrl?: string;
  duration: number;
  genre: string;
  releaseDate: string;
  rating: number;
  narrator?: string;
  chapters: Chapter[];
  progress?: number;
  visibility?: string;
  is_in_library?: boolean;
}

// Mock data for development - uses real book from database
const MOCK_BOOK: BookDetail = {
  id: 'demo_the_power_of_faith',
  title: 'The Power of Faith: A Journey to Spiritual Victory',
  author: 'Dr. Samuel Blessing',
  description:
    "An inspiring journey through the transformative power of faith. Discover how faith can move mountains, change circumstances, and bring victory in every area of life. Through practical examples, biblical teachings, and real-life testimonies, experience God's supernatural power in action.\n\nThis book will guide you through understanding the nature of faith, building unshakeable trust in God's promises, and activating your faith for breakthrough in health, finances, relationships, and purpose.",
  coverUrl: 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&h=600&fit=crop',
  backgroundUrl: 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=1920&h=1080&fit=crop',
  duration: 180, // 3 hours
  genre: 'Faith & Inspiration',
  releaseDate: '2024-01-15',
  rating: 4.8,
  narrator: 'Archbishop Duncan-Williams',
  chapters: [
    { id: 'ch1', title: 'The Foundation of Faith', duration: 18, order: 1 },
    { id: 'ch2', title: 'Faith That Moves Mountains', duration: 22, order: 2 },
    { id: 'ch3', title: 'Walking by Faith, Not by Sight', duration: 20, order: 3 },
    { id: 'ch4', title: 'The Shield of Faith', duration: 25, order: 4 },
    { id: 'ch5', title: 'Faith in Action', duration: 30, order: 5 },
    { id: 'ch6', title: 'Overcoming Through Faith', duration: 28, order: 6 },
    { id: 'ch7', title: 'Living a Faith-Filled Life', duration: 37, order: 7 },
  ],
  progress: 0,
};

export default function BookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: profileData } = useProfile();
  const { balance } = useWalletStore();

  // Check if user is admin
  const canAccessVoiceQA = profileData ? (profileData.is_admin || profileData.role === 'admin' || profileData.role === 'superadmin') : false;

  const [book, setBook] = useState<BookDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [addingToLibrary, setAddingToLibrary] = useState(false);
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);
  const [showSeamlessChat, setShowSeamlessChat] = useState(false);
  const [interactionId, setInteractionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'chapters' | 'reviews' | 'share'>('chapters');
  const [showBuyCreditsModal, setShowBuyCreditsModal] = useState(false);

  // Calculate estimated credits for this book based on duration
  const estimatedCredits = book ? Math.ceil(book.duration * PRICING.NARRATION_PER_MINUTE * PRICING.CREDITS_PER_DOLLAR) : 0;
  const hasEnoughCredits = balance >= estimatedCredits;
  const balanceInCurrency = (balance / PRICING.CREDITS_PER_DOLLAR).toFixed(2);

  // Update page title when book data loads
  useEffect(() => {
    if (book) {
      document.title = `${book.title} - InkWave`;
    } else {
      document.title = 'Book Details - InkWave';
    }
  }, [book]);

  useEffect(() => {
    fetchBook();
  }, [id]);

  const fetchBook = async () => {
    try {
      setLoading(true);
      const response = await api.books.get(id!);
      const bookData = response.data;

      // Map API response to BookDetail format
      const coverUrl = getBookCoverUrl(bookData.cover_url, bookData.title, bookData.author);
      const mappedBook: BookDetail = {
        id: bookData.id,
        title: bookData.title,
        author: bookData.author,
        authorImageUrl: bookData.author_image_url || undefined,  // Dynamic author photo
        description: bookData.description || 'No description available.',
        coverUrl: coverUrl,
        backgroundUrl: bookData.background_url || coverUrl,
        duration: bookData.duration || 0,
        genre: Array.isArray(bookData.genre) ? bookData.genre[0] : (bookData.genre || 'Book'),
        releaseDate: bookData.created_at || new Date().toISOString(),
        rating: bookData.rating || 4.5,
        narrator: bookData.narrator || 'Archbishop Duncan-Williams',
        chapters: bookData.chapters || [],
        progress: bookData.progress || 0,
        visibility: bookData.visibility || 'public',
        is_in_library: bookData.is_in_library || false,
      };

      setBook(mappedBook);

      // Check if book is bookmarked
      try {
        const bookmarkStatus = await api.bookmarks.getStatus(id!);
        setIsBookmarked(bookmarkStatus.data.bookmarked || false);
      } catch (err) {
        console.log('Could not fetch bookmark status');
        setIsBookmarked(false);
      }
    } catch (error) {
      console.error('Error fetching book:', error);
      toast.error('Failed to load book details');
      // Fallback to mock data on error
      setBook(MOCK_BOOK);
    } finally {
      setLoading(false);
    }
  };

  const handlePlay = async () => {
    try {
      // Create a reading session when user starts listening
      const sessionResponse = await api.reading.startSession(id!);
      console.log('Started reading session:', sessionResponse.data);
      navigate(`/player/${id}`);
    } catch (error) {
      console.error('Error starting reading session:', error);
      // Navigate anyway, will use mock data if backend unavailable
      navigate(`/player/${id}`);
    }
  };

  const handleBookmark = async () => {
    if (!book) return;

    // Only allow bookmarking public books
    if (book.visibility !== 'public' && !isBookmarked) {
      toast.error('Only public books can be bookmarked');
      return;
    }

    setAddingToLibrary(true);
    try {
      if (!isBookmarked) {
        await api.bookmarks.add(book.id);
        setIsBookmarked(true);
        toast.success('Bookmarked for later');
      } else {
        await api.bookmarks.remove(book.id);
        setIsBookmarked(false);
        toast.success('Removed from bookmarks');
      }
    } catch (error: any) {
      console.error('Failed to update bookmarks:', error);
      toast.error(error.response?.data?.detail || 'Failed to update bookmarks');
    } finally {
      setAddingToLibrary(false);
    }
  };

  const handleVoiceQA = async () => {
    try {
      // Create or get interaction session
      if (!interactionId) {
        const response = await api.interactions.create(
          `session_${id}`,
          id!
        );
        setInteractionId(response.data.interaction_id);
      }
      setShowSeamlessChat(true);
    } catch (error) {
      console.error('Failed to create interaction:', error);
      toast.error('Failed to start conversation');
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading book details...</p>
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950">
        <div className="text-center">
          <p className="text-gray-400 mb-4">Book not found</p>
          <button
            onClick={() => navigate('/')}
            className="text-purple-400 hover:text-purple-300"
          >
            Go back home
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-gray-950"
    >
      {/* Background with gradient overlay */}
      <div className="absolute inset-0 h-[60vh]">
        <img
          src={book.backgroundUrl || book.coverUrl}
          alt={book.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src = generatePlaceholderCover(book.title, book.author);
            e.currentTarget.onerror = null;
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-gray-950/50 via-gray-950/80 to-gray-950" />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-4 sm:py-6 md:py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center space-x-2 text-gray-400 hover:text-white transition mb-6 sm:mb-8"
        >
          <ChevronLeft className="h-4 w-4 sm:h-5 sm:w-5" />
          <span className="text-sm sm:text-base">Back</span>
        </button>

        {/* Book Header */}
        <div className="flex flex-col md:flex-row gap-6 sm:gap-8 mb-8 sm:mb-12">
          {/* Book Cover */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="flex-shrink-0 mx-auto md:mx-0"
          >
            <img
              src={book.coverUrl}
              alt={book.title}
              className="w-48 h-72 sm:w-56 sm:h-84 md:w-64 md:h-96 object-cover rounded-lg shadow-2xl"
              onError={(e) => {
                e.currentTarget.src = generatePlaceholderCover(book.title, book.author);
                e.currentTarget.onerror = null;
              }}
            />
          </motion.div>

          {/* Book Info */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex-1 space-y-6"
          >
            {/* Genre Badge */}
            <div className="inline-block px-4 py-1 rounded-full bg-purple-500/20 border border-purple-500/50">
              <span className="text-sm font-semibold text-purple-300">
                {book.genre}
              </span>
            </div>

            {/* Title & Author */}
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-2">
                {book.title}
              </h1>
              <div className="flex items-center gap-3">
                {/* Author Image (if available) */}
                {book.authorImageUrl && (
                  <img
                    src={book.authorImageUrl}
                    alt={book.author}
                    className="w-10 h-10 sm:w-12 sm:h-12 rounded-full object-cover border-2 border-purple-500/50"
                    onError={(e) => {
                      // Hide image on error
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                )}
                <p className="text-base sm:text-lg md:text-xl text-gray-300">
                  by{' '}
                  <span className="text-purple-400 font-semibold">
                    {book.author}
                  </span>
                </p>
              </div>
            </div>

            {/* Metadata */}
            <div className="flex flex-wrap gap-6 text-sm text-gray-400">
              <div className="flex items-center space-x-2">
                <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                <span className="text-white font-semibold">{book.rating}</span>
                <span>/ 5.0</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4" />
                <span>{formatDuration(book.duration)}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4" />
                <span>{formatDate(book.releaseDate)}</span>
              </div>
            </div>

            {/* Narrator */}
            {book.narrator && (
              <p className="text-gray-400">
                Narrated by{' '}
                <span className="text-gray-200">{book.narrator}</span>
              </p>
            )}

            {/* Progress Bar (if started) */}
            {book.progress && book.progress > 0 && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-400">
                  <span>{book.progress}% complete</span>
                  <span>
                    {formatDuration(
                      Math.floor((book.duration * book.progress) / 100)
                    )}{' '}
                    listened
                  </span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                    style={{ width: `${book.progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Credits & Pricing Card - Prominent Display */}
            <div className="p-4 sm:p-5 rounded-2xl border-2 bg-gradient-to-r from-purple-900/30 to-pink-900/30 border-purple-500/30">
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                {/* Cost Info */}
                <div className="flex items-center gap-3 flex-1">
                  <div className="p-3 rounded-xl bg-purple-500/20">
                    <Headphones className="h-6 w-6 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Listening Cost</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-bold text-purple-400">
                        {estimatedCredits}
                      </span>
                      <span className="text-gray-400">credits</span>
                      <span className="text-sm text-gray-500">
                        (~GH₵{(estimatedCredits / PRICING.CREDITS_PER_DOLLAR).toFixed(2)})
                      </span>
                    </div>
                  </div>
                </div>

                {/* Balance & Action */}
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-xs text-gray-400 mb-1">Your Balance</p>
                    <p className="text-xl font-bold text-pink-400">
                      GH₵{balanceInCurrency}
                    </p>
                  </div>
                  {!hasEnoughCredits && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-pink-500/20 rounded-full">
                      <AlertCircle className="h-4 w-4 text-pink-400" />
                      <span className="text-xs text-pink-300 font-medium">Low Balance</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Primary Action Buttons */}
            <div className="flex flex-wrap items-center gap-3 sm:gap-4">
              {/* Play Button - always shows Listen, opens buy modal if no credits */}
              <button
                onClick={hasEnoughCredits ? handlePlay : () => setShowBuyCreditsModal(true)}
                className="flex items-center space-x-2 sm:space-x-3 px-6 sm:px-8 py-3 sm:py-4 rounded-full font-semibold text-base sm:text-lg transition transform hover:scale-105 shadow-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
              >
                <Play className="h-5 w-5 sm:h-6 sm:w-6 fill-white" />
                <span>{book.progress && book.progress > 0 ? 'Continue' : 'Start'} Listening</span>
              </button>

              {/* Bookmark Button */}
              <button
                onClick={handleBookmark}
                disabled={addingToLibrary}
                className={`flex items-center space-x-2 px-4 sm:px-6 py-3 sm:py-4 rounded-full font-semibold text-sm sm:text-base transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
                  isBookmarked
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                <Bookmark
                  className={`h-4 w-4 sm:h-5 sm:w-5 ${isBookmarked ? 'fill-white' : ''}`}
                />
                <span className="hidden sm:inline">
                  {addingToLibrary ? 'Updating...' : isBookmarked ? 'Bookmarked' : 'Bookmark'}
                </span>
              </button>

              {/* Wishlist Button */}
              <button
                onClick={() => {
                  setIsWishlisted(!isWishlisted);
                  toast.success(isWishlisted ? 'Removed from wishlist' : 'Added to wishlist');
                }}
                className={`flex items-center space-x-2 px-4 sm:px-6 py-3 sm:py-4 rounded-full font-semibold text-sm sm:text-base transition transform hover:scale-105 ${
                  isWishlisted
                    ? 'bg-pink-500 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
                title={isWishlisted ? 'Remove from Wishlist' : 'Add to Wishlist'}
              >
                <Heart
                  className={`h-4 w-4 sm:h-5 sm:w-5 ${isWishlisted ? 'fill-white' : ''}`}
                />
                <span className="hidden sm:inline">
                  {isWishlisted ? 'Wishlisted' : 'Wishlist'}
                </span>
              </button>

              {/* Voice Q&A Button (Admin Only) */}
              {canAccessVoiceQA && (
                <button
                  onClick={handleVoiceQA}
                  className="flex items-center space-x-2 px-4 sm:px-6 py-3 sm:py-4 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 rounded-full text-white font-semibold text-sm sm:text-base transition transform hover:scale-105 shadow-lg"
                  title="Ask questions about this book"
                >
                  <MessageSquare className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span className="hidden sm:inline">Ask AI</span>
                </button>
              )}
            </div>

            {/* Audible-Style Tab Navigation */}
            <div className="border-b border-gray-700">
              <div className="flex gap-1 -mb-px">
                <button
                  onClick={() => setActiveTab('chapters')}
                  className={`flex items-center gap-2 px-4 sm:px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'chapters'
                      ? 'border-purple-500 text-purple-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
                  }`}
                >
                  <ListMusic className="h-4 w-4" />
                  <span>Chapters</span>
                  {book.chapters && book.chapters.length > 0 && (
                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                      activeTab === 'chapters' ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700 text-gray-400'
                    }`}>
                      {book.chapters.length}
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('reviews')}
                  className={`flex items-center gap-2 px-4 sm:px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'reviews'
                      ? 'border-purple-500 text-purple-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
                  }`}
                >
                  <Star className="h-4 w-4" />
                  <span>Reviews</span>
                </button>
                <button
                  onClick={() => setActiveTab('share')}
                  className={`flex items-center gap-2 px-4 sm:px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'share'
                      ? 'border-purple-500 text-purple-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
                  }`}
                >
                  <Share2 className="h-4 w-4" />
                  <span>Share</span>
                </button>
                <button
                  onClick={() => setShowVoiceSettings(true)}
                  className="flex items-center gap-2 px-4 sm:px-6 py-3 text-sm font-medium border-b-2 border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600 transition-colors"
                >
                  <Settings className="h-4 w-4" />
                  <span className="hidden sm:inline">Voice Settings</span>
                </button>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Description - Always visible */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mb-8 sm:mb-12"
        >
          <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">About this book</h2>
          <p className="text-gray-300 text-sm sm:text-base md:text-lg leading-relaxed whitespace-pre-line max-w-4xl">
            {book.description}
          </p>
        </motion.div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {/* Chapters Tab */}
          {activeTab === 'chapters' && book.chapters && book.chapters.length > 0 && (
            <motion.div
              key="chapters"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-4 sm:mb-6">
                Chapters ({book.chapters.length})
              </h2>
              <div className="space-y-2">
                {book.chapters.map((chapter, index) => (
                  <div
                    key={chapter.id}
                    className="flex items-center justify-between p-3 sm:p-4 bg-gray-800/50 hover:bg-gray-800 rounded-lg transition cursor-pointer group"
                    onClick={() => navigate(`/player/${book.id}?chapter=${chapter.id}`)}
                  >
                    <div className="flex items-center space-x-3 sm:space-x-4 flex-1 min-w-0">
                      <span className="text-gray-500 font-mono text-xs sm:text-sm w-6 sm:w-8 flex-shrink-0">
                        {index + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm sm:text-base text-white font-medium group-hover:text-purple-400 transition truncate">
                          {chapter.title}
                        </p>
                        <p className="text-xs sm:text-sm text-gray-500">
                          {formatDuration(chapter.duration)}
                        </p>
                      </div>
                    </div>
                    <Play className="h-4 w-4 sm:h-5 sm:w-5 text-gray-500 group-hover:text-purple-400 transition flex-shrink-0" />
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Reviews Tab */}
          {activeTab === 'reviews' && book && (
            <motion.div
              key="reviews"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <BookComments bookId={book.id} />
            </motion.div>
          )}

          {/* Share Tab */}
          {activeTab === 'share' && (
            <motion.div
              key="share"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="py-6"
            >
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-4 sm:mb-6">Share this book</h2>
              <div className="bg-gray-800/50 rounded-xl p-6">
                <p className="text-gray-400 mb-4">Share "{book.title}" with friends and family</p>
                <SocialShareButtons
                  bookTitle={book.title}
                  bookAuthor={book.author}
                  bookId={book.id}
                  bookCover={book.coverUrl}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Book Voice Settings Modal */}
      {book && (
        <BookVoiceSettingsModal
          isOpen={showVoiceSettings}
          onClose={() => setShowVoiceSettings(false)}
          bookId={book.id}
          bookTitle={book.title}
        />
      )}

      {/* Voice Book Chat Modal (Real-time WebSocket/WebRTC) */}
      <AnimatePresence>
        {showSeamlessChat && book && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setShowSeamlessChat(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-2xl h-[600px]"
              onClick={(e) => e.stopPropagation()}
            >
              <VoiceBookChat
                bookId={book.id}
                bookTitle={book.title}
                onClose={() => setShowSeamlessChat(false)}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Buy Credits Modal - For "Buy to Listen" flow */}
      <PaymentOptionsModal
        isOpen={showBuyCreditsModal}
        onClose={() => setShowBuyCreditsModal(false)}
        amount={Math.ceil((estimatedCredits - balance) / PRICING.CREDITS_PER_DOLLAR)}
        onSuccess={() => {
          setShowBuyCreditsModal(false);
          toast.success('Credits added! You can now start listening.');
        }}
      />
    </motion.div>
  );
}
