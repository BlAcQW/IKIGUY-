/**
 * BrowsePage
 * Browse sermons by spiritual categories and series
 */

import { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api } from '../lib/api';
import { getBookCoverUrl } from '../lib/bookCoverUtils';
import BookCard from '../components/BookCard';
import PullToRefreshIndicator from '../components/PullToRefreshIndicator';
import { usePullToRefresh } from '../hooks/usePullToRefresh';

interface Category {
  key: string;
  name: string;
  icon?: string;
  color?: string;
}

interface Sermon {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
  duration: number;
  genre?: string[];
}

interface Series {
  series_name: string;
  sermon_count: number;
  topics: string[];
  representative_sermon: Sermon;
}

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

export default function BrowsePage() {
	useEffect(() => {
		document.title = 'Browse Books - InkWave';
	}, []);

  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [sermons, setSermons] = useState<Sermon[]>([]);
  const [series, setSeries] = useState<Series[]>([]);
  const [newAdditions, setNewAdditions] = useState<Sermon[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'categories' | 'sermons' | 'series' | 'new-additions'>('categories');

  useEffect(() => {
    fetchCategories();
    const category = searchParams.get('category');
    const view = searchParams.get('view');

    if (category) {
      setSelectedCategory(category);
      setViewMode('sermons');
      fetchSermonsByCategory(category);
    } else if (view === 'series') {
      setViewMode('series');
      fetchSeries();
    } else if (view === 'new-additions') {
      setViewMode('new-additions');
      fetchNewAdditions();
    }
  }, [searchParams]);

  const fetchCategories = async () => {
    try {
      const response = await api.recommendations.getCategories();
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  const fetchSermonsByCategory = async (category: string) => {
    try {
      setLoading(true);
      const response = await api.recommendations.getByCategory(category, 50);
      const sermonData = response.data.sermons || [];
      const mappedSermons = sermonData.map((sermon: any) => ({
        id: sermon.id,
        title: sermon.title,
        author: sermon.author,
        coverUrl: getBookCoverUrl(sermon.cover_url, sermon.title, sermon.author),
        duration: sermon.duration || 0,
        genre: sermon.genre || []
      }));
      setSermons(mappedSermons);
    } catch (error) {
      console.error('Failed to fetch sermons:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSeries = async () => {
    try {
      setLoading(true);
      const response = await api.recommendations.getSeriesDetailed(20);
      setSeries(response.data.series || []);
    } catch (error) {
      console.error('Failed to fetch series:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchNewAdditions = async () => {
    try {
      setLoading(true);
      const response = await api.recommendations.getLatest(50);
      const sermonData = response.data.sermons || [];
      const mappedSermons = sermonData.map((sermon: any) => ({
        id: sermon.id,
        title: sermon.title,
        author: sermon.author,
        coverUrl: getBookCoverUrl(sermon.cover_url, sermon.title, sermon.author),
        duration: sermon.duration || 0,
        genre: sermon.genre || []
      }));
      setNewAdditions(mappedSermons);
    } catch (error) {
      console.error('Failed to fetch new additions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryClick = (categoryKey: string) => {
    navigate(`/browse?category=${categoryKey}`);
  };

  const handleSeriesClick = () => {
    navigate('/browse?view=series');
  };

  const handleNewAdditionsClick = () => {
    navigate('/browse?view=new-additions');
  };

  const handleBackToCategories = () => {
    navigate('/browse');
    setViewMode('categories');
    setSelectedCategory(null);
    setLoading(false);
  };

  // Refresh handler based on current view mode
  const handleRefresh = useCallback(async () => {
    if (viewMode === 'categories') {
      await fetchCategories();
    } else if (viewMode === 'sermons' && selectedCategory) {
      await fetchSermonsByCategory(selectedCategory);
    } else if (viewMode === 'series') {
      await fetchSeries();
    } else if (viewMode === 'new-additions') {
      await fetchNewAdditions();
    }
  }, [viewMode, selectedCategory]);

  // Pull-to-refresh for mobile
  const { handlers, state: pullState } = usePullToRefresh({
    onRefresh: handleRefresh,
    disabled: loading,
  });

  if (loading && viewMode !== 'categories') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading sermons...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-gray-950 text-white pt-16 md:pt-20 pb-16 md:pb-20"
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

      <div className="container mx-auto px-3 md:px-4 lg:px-6">
        {/* Header */}
        <div className="mb-6 md:mb-8">
          {viewMode !== 'categories' && (
            <button
              onClick={handleBackToCategories}
              className="mb-3 md:mb-4 text-gray-400 hover:text-white transition-colors flex items-center gap-2 text-sm md:text-base"
            >
              ← Back to Browse
            </button>
          )}
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-2">
            {viewMode === 'categories' && 'Browse Sermons'}
            {viewMode === 'sermons' && `${categories.find(c => c.key === selectedCategory)?.name || 'Sermons'}`}
            {viewMode === 'series' && 'Sermon Series'}
            {viewMode === 'new-additions' && 'New Additions'}
          </h1>
          <p className="text-gray-400 text-sm md:text-base">
            {viewMode === 'categories' && 'Explore messages by spiritual topics'}
            {viewMode === 'sermons' && `Messages from Archbishop Duncan-Williams on ${categories.find(c => c.key === selectedCategory)?.name}`}
            {viewMode === 'series' && 'Collections of related messages'}
            {viewMode === 'new-additions' && 'Recently added sermons from Archbishop Duncan-Williams'}
          </p>
        </div>

        {/* Categories View */}
        {viewMode === 'categories' && (
          <div>
            {/* Quick Access Buttons */}
            <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={handleNewAdditionsClick}
                className="bg-gradient-to-r from-emerald-600 to-emerald-800 text-white px-6 py-4 rounded-lg hover:from-emerald-700 hover:to-emerald-900 transition-all shadow-lg flex items-center justify-center gap-3"
              >
                <span className="text-2xl">✨</span>
                <div className="text-left">
                  <div className="font-bold">New Additions</div>
                  <div className="text-sm text-emerald-200">Recently added sermons</div>
                </div>
              </button>

              <button
                onClick={handleSeriesClick}
                className="bg-gradient-to-r from-purple-600 to-purple-800 text-white px-6 py-4 rounded-lg hover:from-purple-700 hover:to-purple-900 transition-all shadow-lg flex items-center justify-center gap-3"
              >
                <span className="text-2xl">📚</span>
                <div className="text-left">
                  <div className="font-bold">Browse by Series</div>
                  <div className="text-sm text-purple-200">Collections of related messages</div>
                </div>
              </button>
            </div>

            {/* Category Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
              {categories.map((category) => {
                const style = CATEGORY_STYLES[category.key] || { icon: '📖', color: 'from-gray-600 to-gray-800' };
                return (
                  <motion.button
                    key={category.key}
                    onClick={() => handleCategoryClick(category.key)}
                    className={`bg-gradient-to-br ${style.color} p-4 md:p-6 rounded-xl shadow-lg hover:shadow-2xl transition-all hover:scale-105`}
                    whileHover={{ y: -5 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className="text-4xl md:text-5xl mb-2 md:mb-3">{style.icon}</div>
                    <h3 className="text-base md:text-xl font-bold">{category.name}</h3>
                  </motion.button>
                );
              })}
            </div>
          </div>
        )}

        {/* Sermons Grid View */}
        {viewMode === 'sermons' && (
          <div>
            {sermons.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg">No sermons found in this category yet.</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 md:gap-4">
                {sermons.map((sermon) => (
                  <BookCard
                    key={sermon.id}
                    id={sermon.id}
                    title={sermon.title}
                    author={sermon.author}
                    coverUrl={sermon.coverUrl}
                    duration={sermon.duration}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Series View */}
        {viewMode === 'series' && (
          <div>
            {series.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg">No sermon series available yet.</p>
              </div>
            ) : (
              <div className="space-y-6 md:space-y-8">
                {series.map((seriesItem, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-gray-900 rounded-xl p-4 md:p-6 shadow-lg hover:shadow-2xl transition-all"
                  >
                    <div className="flex flex-col sm:flex-row items-start gap-4 md:gap-6">
                      {/* Representative Sermon Image */}
                      <div className="flex-shrink-0 w-full sm:w-auto">
                        <img
                          src={seriesItem.representative_sermon.coverUrl || 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&h=600&fit=crop'}
                          alt={seriesItem.series_name}
                          className="w-full sm:w-24 md:w-32 h-36 sm:h-36 md:h-48 object-cover rounded-lg shadow-md"
                        />
                      </div>

                      {/* Series Info */}
                      <div className="flex-1">
                        <h3 className="text-xl md:text-2xl font-bold mb-2">{seriesItem.series_name}</h3>
                        <p className="text-gray-400 mb-4 text-sm md:text-base">
                          {seriesItem.sermon_count} {seriesItem.sermon_count === 1 ? 'sermon' : 'sermons'}
                        </p>

                        {/* Topics */}
                        <div className="flex flex-wrap gap-2 mb-4">
                          {seriesItem.topics.slice(0, 5).map((topic, i) => (
                            <span
                              key={i}
                              className="bg-gray-800 text-purple-300 px-2 md:px-3 py-1 rounded-full text-xs md:text-sm"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>

                        {/* View Series Button */}
                        <button
                          onClick={() => handleCategoryClick(seriesItem.topics[0])}
                          className="bg-purple-600 hover:bg-purple-700 text-white px-4 md:px-6 py-2 rounded-lg transition-colors text-sm md:text-base"
                        >
                          View Series
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* New Additions View */}
        {viewMode === 'new-additions' && (
          <div>
            {newAdditions.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg">No new sermons added yet.</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 md:gap-4">
                {newAdditions.map((sermon) => (
                  <BookCard
                    key={sermon.id}
                    id={sermon.id}
                    title={sermon.title}
                    author={sermon.author}
                    coverUrl={sermon.coverUrl}
                    duration={sermon.duration}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
