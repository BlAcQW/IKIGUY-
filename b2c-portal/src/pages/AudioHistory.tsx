/**
 * Audio History Page
 *
 * Displays user's TTS synthesis history with search, filters, and playback.
 *
 * Created: 2025-10-27
 * Sprint 2: User Experience Enhancements (Phase 8)
 */

import React, { useState, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { useAudioHistory } from '@/hooks/useAudioHistory';
import {
  Search,
  Play,
  Download,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Filter,
  Clock,
  DollarSign,
  FileText,
  Volume2,
  X,
  AlertCircle,
} from 'lucide-react';

interface AudioHistoryProps {}

const AudioHistory: React.FC<AudioHistoryProps> = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [isPlayingId, setIsPlayingId] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const {
    items,
    total,
    page,
    hasMore,
    isLoading,
    error,
    fetchHistory,
    getHistoryItem,
    deleteHistoryItem,
  } = useAudioHistory();

  // Available providers (can be fetched dynamically)
  const providers = [
    'coqui_xtts',
    'melotts',
    'kokoro',
    'f5tts',
    'styletts2',
    'openvoice',
    'akan_mms',
  ];

  // Load history on mount and when filters change
  useEffect(() => {
    fetchHistory(currentPage, 20, searchTerm || undefined, selectedProvider || undefined);
  }, [currentPage, searchTerm, selectedProvider, fetchHistory]);

  /**
   * Handle audio playback for a history item.
   */
  const handlePlayAudio = async (itemId: string) => {
    try {
      // Stop currently playing audio
      if (audioElement) {
        audioElement.pause();
        audioElement.currentTime = 0;
      }

      // If clicking the same item, just stop
      if (isPlayingId === itemId) {
        setIsPlayingId(null);
        setAudioElement(null);
        return;
      }

      setIsPlayingId(itemId);

      // Fetch the full history item with audio
      const item = await getHistoryItem(itemId);

      if (!item || !item.audio_base64) {
        throw new Error('Audio data not available');
      }

      // Convert base64 to audio blob
      const audioBytes = Uint8Array.from(atob(item.audio_base64), c => c.charCodeAt(0));
      const blob = new Blob([audioBytes], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(blob);

      // Create and play audio
      const audio = new Audio(audioUrl);
      audio.onended = () => {
        setIsPlayingId(null);
        setAudioElement(null);
        URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = () => {
        console.error('Audio playback error');
        setIsPlayingId(null);
        setAudioElement(null);
      };

      setAudioElement(audio);
      await audio.play();
    } catch (err) {
      console.error('Error playing audio:', err);
      setIsPlayingId(null);
      setAudioElement(null);
    }
  };

  /**
   * Handle downloading audio for a history item.
   */
  const handleDownloadAudio = async (itemId: string, text: string) => {
    try {
      const item = await getHistoryItem(itemId);

      if (!item || !item.audio_base64) {
        throw new Error('Audio data not available');
      }

      // Convert base64 to blob
      const audioBytes = Uint8Array.from(atob(item.audio_base64), c => c.charCodeAt(0));
      const blob = new Blob([audioBytes], { type: 'audio/wav' });
      const url = URL.createObjectURL(blob);

      // Create download link
      const a = document.createElement('a');
      a.href = url;
      a.download = `tts_${text.slice(0, 30).replace(/\s+/g, '_')}_${Date.now()}.wav`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading audio:', err);
    }
  };

  /**
   * Handle delete confirmation.
   */
  const handleDeleteClick = (itemId: string) => {
    setDeleteConfirmId(itemId);
  };

  /**
   * Confirm and execute delete.
   */
  const confirmDelete = async () => {
    if (!deleteConfirmId) return;

    const success = await deleteHistoryItem(deleteConfirmId);

    if (success) {
      // Stop audio if this item is playing
      if (isPlayingId === deleteConfirmId) {
        if (audioElement) {
          audioElement.pause();
          audioElement.currentTime = 0;
        }
        setIsPlayingId(null);
        setAudioElement(null);
      }
    }

    setDeleteConfirmId(null);
  };

  /**
   * Cancel delete.
   */
  const cancelDelete = () => {
    setDeleteConfirmId(null);
  };

  /**
   * Format duration (seconds to MM:SS).
   */
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  /**
   * Format date.
   */
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  /**
   * Handle pagination.
   */
  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (hasMore) {
      setCurrentPage(currentPage + 1);
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      <DashboardSidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <div className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Volume2 className="h-6 w-6 text-indigo-600" />
              <h1 className="text-2xl font-bold text-foreground">Audio History</h1>
            </div>

            <div className="text-center">
              <div className="text-sm text-gray-600">Total Syntheses</div>
              <div className="text-lg font-semibold">{total}</div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 max-w-7xl mx-auto px-6 py-8 w-full">
          {/* Filters */}
          <div className="bg-card rounded-lg p-4 mb-6 border border-border">
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by text..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-md text-foreground placeholder-gray-400 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="px-4 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Providers</option>
                {providers.map((provider) => (
                  <option key={provider} value={provider}>
                    {provider.toUpperCase()}
                  </option>
                ))}
              </select>

              {(searchTerm || selectedProvider) && (
                <button
                  onClick={() => {
                    setSearchTerm('');
                    setSelectedProvider('');
                  }}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-900 rounded-md text-sm font-medium transition-colors"
                >
                  Clear Filters
                </button>
              )}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          {/* Loading State */}
          {isLoading && items.length === 0 && (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && items.length === 0 && (
            <div className="flex items-center justify-center py-20">
              <div className="text-center max-w-md">
                <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <FileText className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">No History Yet</h3>
                <p className="text-gray-600 mb-6">
                  Your TTS synthesis history will appear here. Start creating some audio to see your history!
                </p>
              </div>
            </div>
          )}

          {/* History Table */}
          {!isLoading && items.length > 0 && (
            <div className="bg-card rounded-lg border border-border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-muted border-b border-border">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Text
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Provider
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Duration
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Cost
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {items.map((item) => (
                      <tr key={item._id} className="hover:bg-muted/50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="text-sm text-foreground max-w-md truncate" title={item.text}>
                            {item.text}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {item.character_count} characters
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-indigo-100 text-indigo-800 text-xs rounded font-medium">
                            {item.provider_id.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-foreground">
                          {formatDuration(item.duration_seconds)}
                        </td>
                        <td className="px-4 py-3 text-sm text-foreground">
                          ${item.cost.toFixed(4)}
                        </td>
                        <td className="px-4 py-3 text-sm text-muted-foreground">
                          {formatDate(item.created_at)}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handlePlayAudio(item._id)}
                              className={`p-2 rounded-md transition-colors ${
                                isPlayingId === item._id
                                  ? 'bg-indigo-600 text-white'
                                  : 'bg-indigo-100 text-indigo-600 hover:bg-indigo-200'
                              }`}
                              title="Play audio"
                            >
                              {isPlayingId === item._id ? (
                                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                              ) : (
                                <Play className="w-4 h-4" />
                              )}
                            </button>
                            <button
                              onClick={() => handleDownloadAudio(item._id, item.text)}
                              className="p-2 bg-green-100 text-green-600 rounded-md hover:bg-green-200 transition-colors"
                              title="Download audio"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteClick(item._id)}
                              className="p-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200 transition-colors"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="bg-muted px-4 py-3 border-t border-border flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  Page {page} • Total: {total} items
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handlePreviousPage}
                    disabled={currentPage === 1}
                    className="px-3 py-1 bg-background border border-border rounded-md hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleNextPage}
                    disabled={!hasMore}
                    className="px-3 py-1 bg-background border border-border rounded-md hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Delete Confirmation Modal */}
        {deleteConfirmId && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                  <Trash2 className="w-5 h-5 text-red-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Delete History Item?
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    This will permanently delete this audio synthesis from your history. This action cannot be undone.
                  </p>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={cancelDelete}
                  className="px-4 py-2 text-sm font-medium text-foreground bg-muted hover:bg-muted/80 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AudioHistory;
