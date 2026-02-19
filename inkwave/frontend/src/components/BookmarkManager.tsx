/**
 * BookmarkManager Component
 * Libby-inspired bookmark management with notes support
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bookmark, Plus, Trash2, Edit2, X, Clock, MessageSquare } from 'lucide-react';
import toast from 'react-hot-toast';

export interface BookmarkItem {
  id: string;
  position: number; // seconds
  note?: string;
  chapterTitle?: string;
  createdAt: string;
}

interface BookmarkManagerProps {
  bookId: string;
  currentTime: number;
  currentChapterTitle?: string;
  bookmarks: BookmarkItem[];
  onAddBookmark: (bookmark: Omit<BookmarkItem, 'id' | 'createdAt'>) => void;
  onUpdateBookmark: (id: string, note: string) => void;
  onDeleteBookmark: (id: string) => void;
  onSeekToBookmark: (position: number) => void;
}

export default function BookmarkManager({
  bookId,
  currentTime,
  currentChapterTitle,
  bookmarks,
  onAddBookmark,
  onUpdateBookmark,
  onDeleteBookmark,
  onSeekToBookmark,
}: BookmarkManagerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editNote, setEditNote] = useState('');
  const [newNote, setNewNote] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  const formatTime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const handleQuickBookmark = () => {
    onAddBookmark({
      position: currentTime,
      chapterTitle: currentChapterTitle,
    });
    toast.success('Bookmark added', { icon: '🔖' });
  };

  const handleAddWithNote = () => {
    if (!newNote.trim()) {
      // Add without note
      handleQuickBookmark();
      setShowAddForm(false);
      return;
    }

    onAddBookmark({
      position: currentTime,
      note: newNote.trim(),
      chapterTitle: currentChapterTitle,
    });
    setNewNote('');
    setShowAddForm(false);
    toast.success('Bookmark with note added', { icon: '📝' });
  };

  const handleStartEdit = (bookmark: BookmarkItem) => {
    setEditingId(bookmark.id);
    setEditNote(bookmark.note || '');
  };

  const handleSaveEdit = (id: string) => {
    onUpdateBookmark(id, editNote.trim());
    setEditingId(null);
    setEditNote('');
    toast.success('Bookmark updated');
  };

  const handleDelete = (id: string) => {
    if (window.confirm('Delete this bookmark?')) {
      onDeleteBookmark(id);
      toast.success('Bookmark deleted');
    }
  };

  // Sort bookmarks by position
  const sortedBookmarks = [...bookmarks].sort((a, b) => a.position - b.position);

  return (
    <div className="relative">
      {/* Quick Bookmark Button */}
      <div className="flex items-center gap-1">
        <button
          onClick={handleQuickBookmark}
          className="p-2 bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-yellow-400 transition-all"
          title="Quick bookmark"
        >
          <Plus className="h-4 w-4" />
        </button>

        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`relative p-2 backdrop-blur-md rounded-full transition-all ${
            bookmarks.length > 0
              ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
              : 'bg-gray-800/60 text-gray-300 hover:text-white hover:bg-gray-700/80'
          }`}
          title="View bookmarks"
        >
          <Bookmark className={`h-5 w-5 ${bookmarks.length > 0 ? 'fill-current' : ''}`} />

          {/* Bookmark count badge */}
          {bookmarks.length > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-500 text-gray-900 text-xs font-bold rounded-full flex items-center justify-center">
              {bookmarks.length}
            </span>
          )}
        </button>
      </div>

      {/* Bookmarks Panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Panel */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="fixed sm:absolute bottom-4 sm:bottom-full left-4 right-4 sm:left-auto sm:right-0 sm:mb-3 w-auto sm:w-80 max-h-[70vh] sm:max-h-96 bg-gray-900/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl z-50 overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-700/50 flex-shrink-0">
                <div className="flex items-center gap-2">
                  <Bookmark className="h-5 w-5 text-yellow-400 fill-current" />
                  <h3 className="font-semibold text-white">Bookmarks</h3>
                  <span className="text-xs text-gray-500">({bookmarks.length})</span>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 text-gray-400 hover:text-white transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Add Bookmark Form */}
              <div className="p-3 border-b border-gray-700/50 flex-shrink-0">
                {showAddForm ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-gray-400">
                      <Clock className="h-4 w-4" />
                      <span>At {formatTime(currentTime)}</span>
                      {currentChapterTitle && (
                        <span className="text-purple-400 truncate">• {currentChapterTitle}</span>
                      )}
                    </div>
                    <textarea
                      value={newNote}
                      onChange={(e) => setNewNote(e.target.value)}
                      placeholder="Add a note (optional)..."
                      className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm resize-none focus:outline-none focus:border-purple-500/50"
                      rows={2}
                      autoFocus
                    />
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleAddWithNote}
                        className="flex-1 px-3 py-1.5 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-medium text-sm rounded-lg transition-colors"
                      >
                        Save Bookmark
                      </button>
                      <button
                        onClick={() => {
                          setShowAddForm(false);
                          setNewNote('');
                        }}
                        className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowAddForm(true)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded-lg transition-colors"
                  >
                    <Plus className="h-4 w-4" />
                    <span className="text-sm font-medium">Bookmark at {formatTime(currentTime)}</span>
                  </button>
                )}
              </div>

              {/* Bookmarks List */}
              <div className="flex-1 overflow-y-auto">
                {sortedBookmarks.length === 0 ? (
                  <div className="p-6 text-center">
                    <Bookmark className="h-10 w-10 text-gray-700 mx-auto mb-3" />
                    <p className="text-gray-500 text-sm">No bookmarks yet</p>
                    <p className="text-gray-600 text-xs mt-1">
                      Tap + to add your first bookmark
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-800/50">
                    {sortedBookmarks.map((bookmark) => (
                      <div
                        key={bookmark.id}
                        className="p-3 hover:bg-gray-800/30 transition-colors"
                      >
                        {editingId === bookmark.id ? (
                          // Edit Mode
                          <div className="space-y-2">
                            <textarea
                              value={editNote}
                              onChange={(e) => setEditNote(e.target.value)}
                              placeholder="Add a note..."
                              className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm resize-none focus:outline-none focus:border-purple-500/50"
                              rows={2}
                              autoFocus
                            />
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleSaveEdit(bookmark.id)}
                                className="px-3 py-1 bg-purple-500 hover:bg-purple-600 text-white text-xs rounded transition-colors"
                              >
                                Save
                              </button>
                              <button
                                onClick={() => {
                                  setEditingId(null);
                                  setEditNote('');
                                }}
                                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs rounded transition-colors"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          // View Mode
                          <div className="flex items-start gap-3">
                            <button
                              onClick={() => onSeekToBookmark(bookmark.position)}
                              className="flex-shrink-0 w-10 h-10 bg-yellow-500/20 rounded-lg flex items-center justify-center text-yellow-400 hover:bg-yellow-500/30 transition-colors"
                            >
                              <Bookmark className="h-4 w-4 fill-current" />
                            </button>

                            <div className="flex-1 min-w-0">
                              <button
                                onClick={() => onSeekToBookmark(bookmark.position)}
                                className="text-left w-full"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-mono text-white">
                                    {formatTime(bookmark.position)}
                                  </span>
                                  {bookmark.chapterTitle && (
                                    <span className="text-xs text-purple-400 truncate">
                                      {bookmark.chapterTitle}
                                    </span>
                                  )}
                                </div>

                                {bookmark.note && (
                                  <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                                    {bookmark.note}
                                  </p>
                                )}

                                <p className="text-xs text-gray-600 mt-1">
                                  {formatDate(bookmark.createdAt)}
                                </p>
                              </button>
                            </div>

                            <div className="flex-shrink-0 flex items-center gap-1">
                              <button
                                onClick={() => handleStartEdit(bookmark)}
                                className="p-1.5 text-gray-500 hover:text-purple-400 transition-colors"
                                title="Edit note"
                              >
                                <Edit2 className="h-3.5 w-3.5" />
                              </button>
                              <button
                                onClick={() => handleDelete(bookmark.id)}
                                className="p-1.5 text-gray-500 hover:text-red-400 transition-colors"
                                title="Delete"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              {bookmarks.length > 0 && (
                <div className="p-3 border-t border-gray-700/50 flex-shrink-0">
                  <p className="text-xs text-gray-500 text-center">
                    Tap a bookmark to jump to that position
                  </p>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
