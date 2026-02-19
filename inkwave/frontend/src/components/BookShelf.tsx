/**
 * BookShelf Component
 * Horizontal scrolling shelf for books (Netflix-style)
 * Enhanced with swipe gestures for mobile
 */

import { useRef, useState, useCallback } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import BookCard from './BookCard';

interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
  duration?: number;
  progress?: number;
}

interface BookShelfProps {
  title: string;
  books: Book[];
  showProgress?: boolean;
}

export default function BookShelf({
  title,
  books,
  showProgress = false,
}: BookShelfProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(true);

  // Swipe gesture state
  const touchStartX = useRef<number>(0);
  const touchStartScrollLeft = useRef<number>(0);
  const isSwiping = useRef<boolean>(false);

  const scroll = (direction: 'left' | 'right') => {
    if (scrollContainerRef.current) {
      const scrollAmount = 800; // Scroll ~4 books at a time
      const newScrollLeft =
        direction === 'left'
          ? scrollContainerRef.current.scrollLeft - scrollAmount
          : scrollContainerRef.current.scrollLeft + scrollAmount;

      scrollContainerRef.current.scrollTo({
        left: newScrollLeft,
        behavior: 'smooth',
      });
    }
  };

  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } =
        scrollContainerRef.current;

      setShowLeftArrow(scrollLeft > 0);
      setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  // Touch handlers for swipe gestures
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (!scrollContainerRef.current) return;
    touchStartX.current = e.touches[0].clientX;
    touchStartScrollLeft.current = scrollContainerRef.current.scrollLeft;
    isSwiping.current = true;
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isSwiping.current || !scrollContainerRef.current) return;
    const touchX = e.touches[0].clientX;
    const diff = touchStartX.current - touchX;
    scrollContainerRef.current.scrollLeft = touchStartScrollLeft.current + diff;
  }, []);

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    if (!isSwiping.current || !scrollContainerRef.current) return;
    isSwiping.current = false;

    // Calculate swipe velocity for momentum
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchStartX.current - touchEndX;
    const velocity = Math.abs(diff);

    // If swipe was fast enough, scroll to next/prev "page"
    if (velocity > 50) {
      const cardWidth = 180; // Approximate book card width
      const cardsToScroll = Math.max(1, Math.floor(velocity / 100));
      const scrollAmount = cardWidth * cardsToScroll;

      scrollContainerRef.current.scrollTo({
        left: scrollContainerRef.current.scrollLeft + (diff > 0 ? scrollAmount : -scrollAmount),
        behavior: 'smooth',
      });
    }
  }, []);

  if (books.length === 0) {
    return null;
  }

  return (
    <div className="mb-8">
      {/* Shelf Title */}
      <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-white mb-4 px-4 sm:px-6 md:px-8">{title}</h2>

      {/* Scrollable Container */}
      <div className="relative group">
        {/* Left Arrow */}
        <AnimatePresence>
          {showLeftArrow && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => scroll('left')}
              className="absolute left-0 top-0 bottom-0 z-10 w-12 sm:w-16 bg-gradient-to-r from-gray-950 to-transparent flex items-center justify-start pl-1 sm:pl-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity"
            >
              <div className="p-1.5 sm:p-2 rounded-full bg-gray-800/90 hover:bg-gray-700/90 transition">
                <ChevronLeft className="h-4 w-4 sm:h-6 sm:w-6 text-white" />
              </div>
            </motion.button>
          )}
        </AnimatePresence>

        {/* Right Arrow */}
        <AnimatePresence>
          {showRightArrow && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => scroll('right')}
              className="absolute right-0 top-0 bottom-0 z-10 w-12 sm:w-16 bg-gradient-to-l from-gray-950 to-transparent flex items-center justify-end pr-1 sm:pr-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity"
            >
              <div className="p-1.5 sm:p-2 rounded-full bg-gray-800/90 hover:bg-gray-700/90 transition">
                <ChevronRight className="h-4 w-4 sm:h-6 sm:w-6 text-white" />
              </div>
            </motion.button>
          )}
        </AnimatePresence>

        {/* Books Container */}
        <div
          ref={scrollContainerRef}
          onScroll={handleScroll}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          className="flex space-x-3 sm:space-x-4 overflow-x-auto scrollbar-hide px-4 sm:px-6 md:px-8 py-2 touch-pan-x"
          style={{
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
          }}
        >
          {books.map((book) => (
            <BookCard
              key={book.id}
              id={book.id}
              title={book.title}
              author={book.author}
              coverUrl={book.coverUrl}
              duration={book.duration}
              progress={book.progress}
              showProgress={showProgress}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
