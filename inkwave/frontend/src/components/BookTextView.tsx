/**
 * BookTextView Component
 * 
 * Displays the book text with a moving highlighter that follows the audio playback.
 * Shows chunks of text and highlights the currently playing chunk/word.
 */

import { useEffect, useRef, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, BookOpen } from 'lucide-react';

interface BookChunk {
  chunk_index: number;
  text: string;
  chapter_title?: string;
  word_count?: number;
}

interface BookTextViewProps {
  isOpen: boolean;
  onClose: () => void;
  bookId: string;
  currentChunkIndex: number;
  currentPositionInChunk: number; // Position in seconds within current chunk
  chunkDuration?: number; // Duration of current chunk in seconds
  totalChunks: number;
}

export default function BookTextView({
  isOpen,
  onClose,
  bookId,
  currentChunkIndex,
  currentPositionInChunk,
  chunkDuration,
  totalChunks,
}: BookTextViewProps) {
  const [chunks, setChunks] = useState<BookChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const highlightRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load chunks when opened
  useEffect(() => {
    if (isOpen && bookId) {
      loadChunks();
    }
  }, [isOpen, bookId]);

  // Scroll to highlight when chunk changes
  useEffect(() => {
    if (isOpen && highlightRef.current && containerRef.current) {
      const highlightElement = highlightRef.current;
      const container = containerRef.current;
      
      // Calculate position
      const highlightTop = highlightElement.offsetTop;
      const containerHeight = container.clientHeight;
      const scrollPosition = highlightTop - containerHeight / 2 + highlightElement.offsetHeight / 2;
      
      // Smooth scroll to keep highlight in view
      container.scrollTo({
        top: Math.max(0, scrollPosition),
        behavior: 'smooth',
      });
    }
  }, [currentChunkIndex, isOpen]);

  const loadChunks = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load chunks around current position (current chunk ± 5 chunks for context)
      const startChunk = Math.max(0, currentChunkIndex - 5);
      const endChunk = Math.min(totalChunks - 1, currentChunkIndex + 10);
      
      const { api } = await import('../lib/api');
      const chunksData: BookChunk[] = [];
      
      // Fetch chunks sequentially (or batch if API supports it)
      for (let i = startChunk; i <= endChunk; i++) {
        try {
          const response = await api.reading.getChunk(bookId, i);
          chunksData.push({
            chunk_index: i,
            text: response.data.text || response.data.content || '',
            chapter_title: response.data.chapter_title,
            word_count: response.data.word_count,
          });
        } catch (err) {
          console.warn(`Failed to load chunk ${i}:`, err);
        }
      }
      
      setChunks(chunksData);
    } catch (err: any) {
      console.error('Failed to load book chunks:', err);
      setError(err.response?.data?.detail || 'Failed to load book text');
    } finally {
      setLoading(false);
    }
  };

  // Calculate word position within current chunk for word-level highlighting
  const getCurrentWordIndex = useMemo(() => {
    if (!chunkDuration || currentPositionInChunk < 0) return -1;
    
    const currentChunk = chunks.find(c => c.chunk_index === currentChunkIndex);
    if (!currentChunk) return -1;
    
    const words = currentChunk.text.trim().split(/\s+/);
    if (words.length === 0) return -1;
    
    const progress = Math.min(1, Math.max(0, currentPositionInChunk / chunkDuration));
    const wordIndex = Math.floor(progress * words.length);
    
    return Math.min(wordIndex, words.length - 1);
  }, [currentChunkIndex, currentPositionInChunk, chunkDuration, chunks]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="absolute right-0 top-0 h-full w-full max-w-2xl bg-gray-900 border-l border-gray-800 flex flex-col shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900/95 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <BookOpen className="w-5 h-5 text-purple-400" />
              <h2 className="text-lg font-semibold text-white">Book Text</h2>
              <span className="text-sm text-gray-500">
                Chunk {currentChunkIndex + 1} of {totalChunks}
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Content */}
          <div
            ref={containerRef}
            className="flex-1 overflow-y-auto p-6 space-y-6"
          >
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-red-400 mb-4">{error}</p>
                <button
                  onClick={loadChunks}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
                >
                  Retry
                </button>
              </div>
            ) : chunks.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p>No text available for this book.</p>
              </div>
            ) : (
              chunks.map((chunk, idx) => {
                const isCurrentChunk = chunk.chunk_index === currentChunkIndex;
                const words = chunk.text.split(/(\s+)/);
                
                return (
                  <div
                    key={chunk.chunk_index}
                    className={`relative ${
                      isCurrentChunk ? 'bg-purple-500/10 border-l-4 border-purple-500' : 'opacity-60'
                    } rounded-lg p-4 transition-all`}
                  >
                    {/* Chapter Title */}
                    {chunk.chapter_title && idx === 0 && (
                      <h3 className="text-lg font-semibold text-purple-400 mb-3">
                        {chunk.chapter_title}
                      </h3>
                    )}
                    
                    {/* Chunk Text with Word-level Highlighting */}
                    <div
                      ref={isCurrentChunk ? highlightRef : null}
                      className={`text-gray-200 leading-relaxed ${
                        isCurrentChunk ? 'text-white' : ''
                      }`}
                    >
                      {isCurrentChunk && getCurrentWordIndex >= 0 ? (
                        // Word-level highlighting for current chunk
                        (() => {
                          const words = chunk.text.trim().split(/\s+/);
                          return words.map((word, wordIdx) => {
                            const isCurrentWord = wordIdx === getCurrentWordIndex;
                            const isPastWord = wordIdx < getCurrentWordIndex;
                            
                            return (
                              <span
                                key={wordIdx}
                                className={
                                  isCurrentWord
                                    ? 'bg-yellow-500/40 text-yellow-100 px-1.5 py-0.5 rounded font-medium'
                                    : isPastWord
                                    ? 'text-gray-300'
                                    : 'text-gray-500'
                                }
                              >
                                {word}
                                {wordIdx < words.length - 1 && ' '}
                              </span>
                            );
                          });
                        })()
                      ) : (
                        // Simple text for non-current chunks
                        <span>{chunk.text}</span>
                      )}
                    </div>
                    
                    {/* Chunk Index Badge */}
                    <div className="mt-2 text-xs text-gray-500">
                      Chunk {chunk.chunk_index + 1}
                      {chunk.word_count && ` • ${chunk.word_count} words`}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer Info */}
          <div className="p-4 border-t border-gray-800 bg-gray-900/95 backdrop-blur-sm">
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>
                {currentChunkIndex + 1} / {totalChunks} chunks
              </span>
              {chunkDuration && (
                <span>
                  {Math.floor(currentPositionInChunk)}s / {Math.floor(chunkDuration)}s
                </span>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

