/**
 * HomePage
 * Netflix-style home page with hero banner and horizontal book shelves
 */

import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import HeroBanner from '../components/HeroBanner';
import BookShelf from '../components/BookShelf';
import PullToRefreshIndicator from '../components/PullToRefreshIndicator';
import { usePullToRefresh } from '../hooks/usePullToRefresh';
import { api } from '../lib/api';
import { getBookCoverUrl } from '../lib/bookCoverUtils';

// Spiritual category icons and colors
const CATEGORY_STYLES: Record<string, { icon: string; color: string }> = {
  prayer: { icon: '🙏', color: 'from-purple-600 to-purple-800' },
  faith: { icon: '✝️', color: 'from-blue-600 to-blue-800' },
  deliverance: { icon: '⚔️', color: 'from-red-600 to-red-800' },
  prosperity: { icon: '💎', color: 'from-green-600 to-green-800' },
  healing: { icon: '🕊️', color: 'from-teal-600 to-teal-800' },
  leadership: { icon: '👑', color: 'from-yellow-600 to-yellow-800' },
  family: { icon: '👨‍👩‍👧‍👦', color: 'from-pink-600 to-pink-800' },
  youth: { icon: '🌟', color: 'from-indigo-600 to-indigo-800' },
  praise: { icon: '🎵', color: 'from-orange-600 to-orange-800' },
  prophecy: { icon: '🔮', color: 'from-violet-600 to-violet-800' },
};

// Featured book from database - actual book that exists
const MOCK_FEATURED = {
  id: 'book_h18rkyrf0r', // Strategic Declarations and Prayers
  title: 'Strategic Declarations and Prayers',
  author: 'Archbishop Nicholas Duncan-Williams',
  description:
    "A powerful collection of strategic prayers and declarations for spiritual warfare and breakthrough. This book provides biblical declarations to strengthen faith and overcome life's challenges.",
  coverUrl: 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1675937624i/107526921.jpg',
  backgroundUrl: 'https://books.google.com/books/content?id=rOWKjgEACAAJ&printsec=frontcover&img=1&zoom=1&source=gbs_api',
  duration: 72,
  genre: 'Prayer & Spiritual Warfare',
};

const MOCK_CONTINUE_READING = [
  {
    id: 'book_5bb65ca24e10', // Enforcing Prophetic Decrees - actual book ID from DB
    title: 'Enforcing Prophetic Decrees',
    author: 'Archbishop Nicholas Duncan-Williams',
    coverUrl: 'https://ndwministries.org/wp-content/uploads/2022/06/K9A6922-Papa-photo-rosa-approved-min-scaled.jpg',
    duration: 180,
    progress: 15,
  },
  {
    id: 'book_g8v8sja2luh', // Binding the Strongman - actual book ID from DB
    title: 'Binding the Strongman',
    author: 'Archbishop Nicholas Duncan-Williams',
    coverUrl: 'https://images.squarespace-cdn.com/content/v1/5d3482a50544c00001cd8325/1621364181290-XH1SYSTALROSE8GNDZI5/Duncan-Williams,+Nicholas+(Archbishop).png',
    duration: 180,
    progress: 45,
  },
  {
    id: 'book_715b1932bece', // Turning Pain to Power - actual book ID from DB
    title: 'Turning Pain to Power',
    author: 'Archbishop Nicholas Duncan-Williams',
    coverUrl: 'https://pbs.twimg.com/media/FdMPCv8XEAAqWe3.jpg',
    duration: 150,
    progress: 72,
  },
];

export default function HomePage() {
	useEffect(() => {
		document.title = 'Home - InkWave';
	}, []);

  const navigate = useNavigate();
  const [featured, setFeatured] = useState(MOCK_FEATURED);
  const [continueReading, setContinueReading] = useState(MOCK_CONTINUE_READING);
  const [recommended, setRecommended] = useState([]);
  const [latestSermons, setLatestSermons] = useState([]);
  const [popularSeries, setPopularSeries] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchContent = useCallback(async () => {
    try {
      setLoading(true);

      // Fetch spiritual categories
      try {
        const categoriesResponse = await api.recommendations.getCategories();
        setCategories(categoriesResponse.data.categories || []);
      } catch (err) {
        console.log('Could not fetch categories');
      }

      // Fetch featured sermon
      try {
        const featuredResponse = await api.recommendations.getFeatured();
        if (featuredResponse.data.featured) {
          const sermon = featuredResponse.data.featured;
          const author = sermon.author || 'Archbishop Nicholas Duncan-Williams';
          setFeatured({
            id: sermon.id,
            title: sermon.title,
            author,
            description: sermon.description || 'Powerful message from Archbishop Duncan-Williams',
            coverUrl: getBookCoverUrl(sermon.cover_url, sermon.title, author),
            backgroundUrl: getBookCoverUrl(sermon.cover_url, sermon.title, author),
            duration: sermon.duration || 0,
            genre: sermon.genre?.[0] || 'Sermon',
          });
        }
      } catch (err) {
        console.log('Could not fetch featured sermon, using default');
      }

      // Fetch personalized recommendations
      try {
        const recommendedResponse = await api.recommendations.getPersonalized(10);
        const recommendations = recommendedResponse.data.recommendations || [];
        const mappedRecommendations = recommendations.map((sermon: any) => ({
          id: sermon.id,
          title: sermon.title,
          author: sermon.author,
          coverUrl: getBookCoverUrl(sermon.cover_url, sermon.title, sermon.author),
          duration: sermon.duration || 0,
        }));
        setRecommended(mappedRecommendations);
      } catch (err) {
        console.log('Could not fetch recommendations');
      }

      // Fetch latest sermons
      try {
        const latestResponse = await api.recommendations.getLatest(10);
        const latest = latestResponse.data.sermons || [];
        const mappedLatest = latest.map((sermon: any) => ({
          id: sermon.id,
          title: sermon.title,
          author: sermon.author,
          coverUrl: getBookCoverUrl(sermon.cover_url, sermon.title, sermon.author),
          duration: sermon.duration || 0,
        }));
        setLatestSermons(mappedLatest);
      } catch (err) {
        console.log('Could not fetch latest sermons');
      }

      // Fetch popular series
      try {
        const seriesResponse = await api.recommendations.getSeries(5);
        const series = seriesResponse.data.series || [];
        const mappedSeries = series.map((sermon: any) => ({
          id: sermon.id,
          title: sermon.title,
          author: sermon.author,
          coverUrl: getBookCoverUrl(sermon.cover_url, sermon.title, sermon.author),
          duration: sermon.duration || 0,
        }));
        setPopularSeries(mappedSeries);
      } catch (err) {
        console.log('Could not fetch popular series');
      }

      // Fetch continue listening (from reading sessions)
      try {
        const continueResponse = await api.books.continueReading(10);
        const continueBooks = continueResponse.data.books || [];
        if (continueBooks.length > 0) {
          const mappedContinue = continueBooks.map((book: any) => ({
            id: book.id,
            title: book.title,
            author: book.author,
            coverUrl: getBookCoverUrl(book.cover_url, book.title, book.author),
            duration: book.duration || 0,
            progress: book.progress || 0,
          }));
          setContinueReading(mappedContinue);
        }
        // Keep mock data if API returns empty
      } catch (err) {
        console.log('Could not fetch continue listening - keeping mock data');
        // Keep MOCK_CONTINUE_READING as fallback
      }

    } catch (error) {
      console.error('Error fetching content:', error);
      // Keep mock data on error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContent();
  }, [fetchContent]);

  // Pull-to-refresh for mobile
  const { handlers, state: pullState } = usePullToRefresh({
    onRefresh: fetchContent,
    disabled: loading,
  });

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

      {/* Hero Banner */}
      <HeroBanner
        id={featured.id}
        title={featured.title}
        author={featured.author}
        description={featured.description}
        coverUrl={featured.coverUrl}
        backgroundUrl={featured.backgroundUrl}
        duration={featured.duration}
        genre={featured.genre}
      />

      {/* Spiritual Topics Grid */}
      {categories.length > 0 && (
        <div className="mb-12 px-4">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Browse by Spiritual Topic</h2>
            <button
              onClick={() => navigate('/browse')}
              className="text-purple-400 hover:text-purple-300 transition-colors"
            >
              View All →
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {categories.slice(0, 5).map((category: any) => {
              const style = CATEGORY_STYLES[category.key] || { icon: '📖', color: 'from-gray-600 to-gray-800' };
              return (
                <motion.button
                  key={category.key}
                  onClick={() => navigate(`/browse?category=${category.key}`)}
                  className={`bg-gradient-to-br ${style.color} p-4 rounded-xl shadow-lg hover:shadow-2xl transition-all hover:scale-105`}
                  whileHover={{ y: -3 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <div className="text-4xl mb-2">{style.icon}</div>
                  <h3 className="text-sm font-bold">{category.name}</h3>
                </motion.button>
              );
            })}
          </div>
        </div>
      )}

      {/* Sermon Shelves */}
      <div className="space-y-8">
        {/* Continue Listening */}
        {continueReading.length > 0 && (
          <BookShelf
            title="Continue Listening"
            books={continueReading}
            showProgress={true}
          />
        )}

        {/* Recommended for You */}
        {recommended.length > 0 && (
          <BookShelf title="Recommended for You" books={recommended} />
        )}

        {/* Latest Messages */}
        {latestSermons.length > 0 && (
          <BookShelf title="Latest Messages from Archbishop Duncan-Williams" books={latestSermons} />
        )}

        {/* Popular Series */}
        {popularSeries.length > 0 && (
          <BookShelf title="Popular Sermon Series" books={popularSeries} />
        )}
      </div>
    </motion.div>
  );
}
