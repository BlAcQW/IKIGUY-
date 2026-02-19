/**
 * DiscoverPage Component
 * User discovery with search and follow suggestions
 * Route: /discover
 */

import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search,
  Users,
  TrendingUp,
  Loader,
  ArrowLeft,
  UserPlus,
  Sparkles,
} from 'lucide-react';
import { useUserSearch } from '../hooks/useUserProfile';
import { useFollowSuggestions } from '../hooks/useSocial';
import { useAuthStore } from '../store/authStore';
import UserCard from '../components/UserCard';
import { useDebounce } from '../hooks/useDebounce';

export default function DiscoverPage() {
	useEffect(() => {
		document.title = 'Discover Users - InkWave';
	}, []);

  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  // Debounce search query (300ms)
  const debouncedQuery = useDebounce(searchQuery, 300);

  // Fetch search results (only if query is 2+ chars)
  const shouldSearch = debouncedQuery.length >= 2;
  const {
    data: searchData,
    isLoading: searchLoading,
    isFetching: searchFetching,
  } = useUserSearch(shouldSearch ? debouncedQuery : '', page, 20, {
    enabled: shouldSearch,
  });

  // Fetch follow suggestions
  const { data: suggestionsData, isLoading: suggestionsLoading } =
    useFollowSuggestions(50);

  const searchResults = searchData?.users || [];
  const suggestions = suggestionsData?.suggestions || [];
  const hasSearchResults = shouldSearch && searchResults.length > 0;
  const showSuggestions = !shouldSearch || searchResults.length === 0;

  // Reset page when query changes
  useEffect(() => {
    setPage(1);
  }, [debouncedQuery]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Header */}
      <div className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3 mb-4">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <ArrowLeft size={20} className="text-gray-400" />
            </button>
            <div className="flex items-center gap-2">
              <Users size={24} className="text-blue-500" />
              <h1 className="text-xl font-bold text-white">Discover</h1>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search
              size={20}
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              placeholder="Search users by name or username..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
            />
            {searchFetching && (
              <Loader
                size={20}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 animate-spin"
              />
            )}
          </div>

          {/* Search Hint */}
          {searchQuery.length > 0 && searchQuery.length < 2 && (
            <p className="text-gray-500 text-sm mt-2">
              Type at least 2 characters to search
            </p>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Search Results */}
        {hasSearchResults && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Search size={20} className="text-gray-400" />
              <h2 className="text-lg font-semibold text-white">
                Search Results
              </h2>
              <span className="text-gray-500 text-sm">
                ({searchResults.length} {searchResults.length === 1 ? 'user' : 'users'})
              </span>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {searchResults.map((userResult, index) => (
                <motion.div
                  key={userResult.user_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <UserCard user={userResult} variant="default" />
                </motion.div>
              ))}
            </div>

            {/* Load More */}
            {searchData?.has_more && (
              <div className="text-center mt-6">
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={searchFetching}
                  className="bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {searchFetching ? (
                    <span className="flex items-center gap-2">
                      <Loader size={16} className="animate-spin" />
                      Loading...
                    </span>
                  ) : (
                    'Load More'
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* No Search Results */}
        {shouldSearch && !searchLoading && searchResults.length === 0 && (
          <div className="text-center py-20">
            <Search size={48} className="text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">No users found</p>
            <p className="text-gray-500 text-sm mt-2">
              Try searching with a different name or username
            </p>
          </div>
        )}

        {/* Follow Suggestions */}
        {showSuggestions && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Sparkles size={20} className="text-yellow-500" />
              <h2 className="text-lg font-semibold text-white">
                Suggested for You
              </h2>
            </div>

            {suggestionsLoading && (
              <div className="flex items-center justify-center py-20">
                <Loader className="animate-spin text-blue-500" size={32} />
              </div>
            )}

            {!suggestionsLoading && suggestions.length === 0 && (
              <div className="text-center py-20">
                <UserPlus size={48} className="text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">No suggestions available</p>
                <p className="text-gray-500 text-sm mt-2">
                  Check back later for personalized recommendations
                </p>
              </div>
            )}

            {!suggestionsLoading && suggestions.length > 0 && (
              <>
                {/* Popular Users (Top 10 with large cards) */}
                <div className="mb-8">
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp size={18} className="text-blue-500" />
                    <h3 className="text-md font-medium text-gray-300">
                      Popular Listeners
                    </h3>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    {suggestions.slice(0, 10).map((suggestion, index) => (
                      <motion.div
                        key={suggestion.user_id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <UserCard user={suggestion} variant="default" />
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* More Suggestions (Compact) */}
                {suggestions.length > 10 && (
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <Users size={18} className="text-gray-500" />
                      <h3 className="text-md font-medium text-gray-300">
                        More Suggestions
                      </h3>
                    </div>
                    <div className="grid gap-3 md:grid-cols-3">
                      {suggestions.slice(10).map((suggestion, index) => (
                        <motion.div
                          key={suggestion.user_id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: (index + 10) * 0.03 }}
                        >
                          <UserCard user={suggestion} variant="compact" />
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Empty State (Not logged in) */}
        {!user && showSuggestions && !suggestionsLoading && (
          <div className="text-center py-20">
            <Users size={48} className="text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-2">
              Discover fellow listeners
            </p>
            <p className="text-gray-500 text-sm mb-6">
              Sign in to see personalized recommendations and connect with others
            </p>
            <button
              onClick={() => navigate('/login')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium transition-colors"
            >
              Sign In
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
