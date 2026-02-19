/**
 * AllBooksPage
 * View all books with pagination and filtering
 */

import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api } from '../lib/api';
import { getBookCoverUrl } from '../lib/bookCoverUtils';
import BookCard from '../components/BookCard';

interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
  duration: number;
  genre?: string[];
  description?: string;
}

export default function AllBooksPage() {
	useEffect(() => {
		document.title = 'All Books - InkWave';
	}, []);

  const [searchParams, setSearchParams] = useSearchParams();
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [genreFilter, setGenreFilter] = useState(searchParams.get('genre') || '');
  const perPage = 24; // 4x6 grid

  useEffect(() => {
    fetchBooks();
  }, [currentPage, searchQuery, genreFilter]);

  const fetchBooks = async () => {
    try {
      setLoading(true);

      let response;
      if (searchQuery) {
        // Use search endpoint
        response = await api.books.search(searchQuery, undefined, currentPage, perPage);
      } else {
        // Use list endpoint
        response = await api.books.list({
          page: currentPage,
          limit: perPage,
          genre: genreFilter || undefined
        });
      }

      const booksData = response.data.books || [];
      const mappedBooks = booksData.map((book: any) => ({
        id: book.id,
        title: book.title,
        author: book.author,
        coverUrl: getBookCoverUrl(book.cover_url, book.title, book.author),
        duration: book.duration || 0,
        genre: book.genre || [],
        description: book.description || ''
      }));

      setBooks(mappedBooks);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to fetch books:', error);
      setBooks([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    setSearchParams({ search: searchQuery, genre: genreFilter });
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setGenreFilter('');
    setCurrentPage(1);
    setSearchParams({});
  };

  const totalPages = Math.ceil(total / perPage);

  if (loading && currentPage === 1) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading books...</p>
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
    >
      <div className="container mx-auto px-3 md:px-4 lg:px-6">
        {/* Header */}
        <div className="mb-6 md:mb-8">
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-2">
            All Books
          </h1>
          <p className="text-gray-400 text-sm md:text-base">
            Browse {total} books from Archbishop Nicholas Duncan-Williams
          </p>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 md:mb-8 bg-gray-900 rounded-xl p-4 md:p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search Input */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Search Books
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search by title or author..."
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            {/* Genre Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Filter by Genre
              </label>
              <select
                value={genreFilter}
                onChange={(e) => {
                  setGenreFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">All Genres</option>
                <option value="Christian">Christian</option>
                <option value="Prayer">Prayer</option>
                <option value="Faith">Faith</option>
                <option value="Leadership">Leadership</option>
                <option value="Spiritual Warfare">Spiritual Warfare</option>
                <option value="Deliverance">Deliverance</option>
                <option value="Healing">Healing</option>
                <option value="Prosperity">Prosperity</option>
                <option value="Family">Family</option>
                <option value="Youth">Youth</option>
              </select>
            </div>
          </div>

          {/* Filter Actions */}
          <div className="flex gap-3 mt-4">
            <button
              onClick={handleSearch}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium transition-colors"
            >
              Search
            </button>
            {(searchQuery || genreFilter) && (
              <button
                onClick={handleClearFilters}
                className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {/* Books Grid */}
        {books.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">
              {searchQuery || genreFilter
                ? 'No books found matching your criteria.'
                : 'No books available yet.'}
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 md:gap-4">
              {books.map((book) => (
                <BookCard
                  key={book.id}
                  id={book.id}
                  title={book.title}
                  author={book.author}
                  coverUrl={book.coverUrl}
                  duration={book.duration}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 flex justify-center items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentPage === 1
                      ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      : 'bg-gray-700 hover:bg-gray-600 text-white'
                  }`}
                >
                  Previous
                </button>

                <div className="flex gap-2">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }

                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                          currentPage === pageNum
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-700 hover:bg-gray-600 text-white'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    currentPage === totalPages
                      ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      : 'bg-gray-700 hover:bg-gray-600 text-white'
                  }`}
                >
                  Next
                </button>
              </div>
            )}

            {/* Page Info */}
            <div className="mt-4 text-center text-gray-400 text-sm">
              Showing {(currentPage - 1) * perPage + 1} - {Math.min(currentPage * perPage, total)} of {total} books
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}
