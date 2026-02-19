/**
 * LibbyPlayer Component
 *
 * Libby-inspired audiobook player with:
 * - Book-level progress bar
 * - Chunk scrubber visualization
 * - Voice selection
 * - Auto-advance to next chunk
 * - Preloading next chunks
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, RotateCcw, RotateCw, Volume2, VolumeX, Settings } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ChunkScrubber from './ChunkScrubber';
import BookProgressBar from './BookProgressBar';
import VoiceSelector from './VoiceSelector';
import ChapterNav from '../ChapterNav';

/**
 * Convert a data URL to a blob URL for reliable audio playback.
 * Browsers handle blob URLs more efficiently than large base64 data URLs.
 */
function dataUrlToBlobUrl(dataUrl: string): string {
  try {
    const matches = dataUrl.match(/^data:([^;]+);base64,(.+)$/);
    if (!matches) {
      console.error('Invalid data URL format, returning original');
      return dataUrl;
    }

    const mimeType = matches[1];
    const base64Data = matches[2];

    const binaryString = atob(base64Data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    const blob = new Blob([bytes], { type: mimeType });
    const blobUrl = URL.createObjectURL(blob);

    console.log(`Converted data URL (${dataUrl.length} chars) to blob URL: ${blobUrl}`);
    return blobUrl;
  } catch (err) {
    console.error('Failed to convert data URL to blob URL:', err);
    return dataUrl;
  }
}

interface ChunkData {
  chunkIndex: number;
  chunkId: string;
  audioUrl: string;
  duration: number;
}

interface BookProgress {
  totalChunks: number;
  totalDuration: number;
  currentChunk: number;
  currentPosition: number;
  overallProgress: number;
  chunkDurations: number[];
}

interface Chapter {
  id: string;
  title: string;
  duration: number;
  order: number;
  startTime?: number;
  startChunk?: number;
  endChunk?: number;
}

interface LibbyPlayerProps {
  bookId: string;
  bookTitle: string;
  coverUrl?: string;
  provider: string;
  voiceId: string;
  speed: number;
  onProviderChange: (provider: string) => void;
  onVoiceChange: (voice: string) => void;
  onSpeedChange: (speed: number) => void;
  onProgressUpdate?: (chunk: number, position: number, totalTimeMinutes: number) => void;
  initialChunk?: number;
  initialPosition?: number;
  chapters?: Chapter[];
  onChapterSelect?: (chapterIndex: number) => void;
}

const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];

export default function LibbyPlayer({
  bookId,
  bookTitle,
  coverUrl,
  provider,
  voiceId,
  speed,
  onProviderChange,
  onVoiceChange,
  onSpeedChange,
  onProgressUpdate,
  initialChunk = 0,
  initialPosition = 0,
  chapters = [],
  onChapterSelect,
}: LibbyPlayerProps) {
  // Audio state
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1.0); // Volume from 0.0 to 1.0
  const [showVolumeSlider, setShowVolumeSlider] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [skipDuration, setSkipDuration] = useState(15); // Configurable skip: 10, 15, 30, 60 seconds

  const SKIP_DURATIONS = [10, 15, 30, 60]; // Available skip durations

  // Chunk state
  const [currentChunkIndex, setCurrentChunkIndex] = useState(initialChunk);
  const [currentPosition, setCurrentPosition] = useState(initialPosition);
  const [chunkDuration, setChunkDuration] = useState(0);

  // Time tracking state
  const [totalListeningTimeMinutes, setTotalListeningTimeMinutes] = useState(0);
  const lastPlayTimeRef = useRef<number>(Date.now());
  const accumulatedSecondsRef = useRef<number>(0);

  // Book progress
  const [bookProgress, setBookProgress] = useState<BookProgress | null>(null);

  // Preloaded chunks
  const [preloadedChunks, setPreloadedChunks] = useState<Map<number, ChunkData>>(new Map());

  // Audio element ref
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Track current blob URL for cleanup
  const currentBlobUrl = useRef<string | null>(null);

  // Volume control ref for click-outside detection
  const volumeControlRef = useRef<HTMLDivElement | null>(null);

  // Close volume slider when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (volumeControlRef.current && !volumeControlRef.current.contains(event.target as Node)) {
        setShowVolumeSlider(false);
      }
    };

    if (showVolumeSlider) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showVolumeSlider]);

  // Fetch book progress on mount
  useEffect(() => {
    fetchBookProgress();
  }, [bookId]);

  // Preload chunks when current chunk changes
  useEffect(() => {
    preloadNextChunks(currentChunkIndex);
  }, [currentChunkIndex, provider, voiceId]);

  // Track listening time during playback
  useEffect(() => {
    if (isPlaying) {
      lastPlayTimeRef.current = Date.now();

      const interval = setInterval(() => {
        const now = Date.now();
        const elapsedSeconds = (now - lastPlayTimeRef.current) / 1000;
        lastPlayTimeRef.current = now;

        // Accumulate seconds
        accumulatedSecondsRef.current += elapsedSeconds;

        // Convert to minutes when we reach 60 seconds
        if (accumulatedSecondsRef.current >= 60) {
          const minutesToAdd = Math.floor(accumulatedSecondsRef.current / 60);
          accumulatedSecondsRef.current = accumulatedSecondsRef.current % 60;
          setTotalListeningTimeMinutes(prev => prev + minutesToAdd);
        }
      }, 1000); // Update every second

      return () => clearInterval(interval);
    }
  }, [isPlaying]);

  // Auto-save progress periodically
  useEffect(() => {
    if (isPlaying && onProgressUpdate) {
      const interval = setInterval(() => {
        onProgressUpdate(currentChunkIndex, currentPosition, totalListeningTimeMinutes);
      }, 5000); // Save every 5 seconds
      return () => clearInterval(interval);
    }
  }, [isPlaying, currentChunkIndex, currentPosition, totalListeningTimeMinutes, onProgressUpdate]);

  const fetchBookProgress = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `/api/v1/audiobook/books/${bookId}/progress`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setBookProgress(data);
        if (data.currentChunk !== undefined) {
          setCurrentChunkIndex(data.currentChunk);
          setCurrentPosition(data.currentPosition || 0);
        }
      }
    } catch (error) {
      console.error('Failed to fetch book progress:', error);
    }
  };

  const preloadNextChunks = async (startChunk: number) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `/api/v1/audiobook/books/${bookId}/preload`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            start_chunk: startChunk,
            num_chunks: 3,
            provider_id: provider,
            voice_id: voiceId,
            speed: speed,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        const newPreloaded = new Map(preloadedChunks);
        data.preloaded_chunks.forEach((chunk: any) => {
          newPreloaded.set(chunk.chunk_index, {
            chunkIndex: chunk.chunk_index,
            chunkId: chunk.chunk_id,
            audioUrl: chunk.audio_url,
            duration: chunk.duration,
          });
        });
        setPreloadedChunks(newPreloaded);
      }
    } catch (error) {
      console.error('Failed to preload chunks:', error);
    }
  };

  const loadChunk = useCallback(async (chunkIndex: number) => {
    setIsLoading(true);

    try {
      // Check if already preloaded
      let chunkData = preloadedChunks.get(chunkIndex);

      if (!chunkData) {
        // Fetch from API
        const token = localStorage.getItem('access_token');
        const response = await fetch(
          `/api/v1/audiobook/books/${bookId}/chunks/${chunkIndex}/audio?` +
            new URLSearchParams({
              provider_id: provider,
              voice_id: voiceId,
              speed: speed.toString(),
            }),
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to load chunk audio');
        }

        const data = await response.json();
        chunkData = {
          chunkIndex: data.chunk_index,
          chunkId: data.chunk_id,
          audioUrl: data.audio_url,
          duration: data.duration,
        };
      }

      // Create/update audio element
      if (!audioRef.current) {
        audioRef.current = new Audio();
      }

      const audio = audioRef.current;

      // Revoke previous blob URL to prevent memory leak
      if (currentBlobUrl.current) {
        URL.revokeObjectURL(currentBlobUrl.current);
        currentBlobUrl.current = null;
      }

      // Convert data URL to blob URL for reliable playback
      const blobUrl = dataUrlToBlobUrl(chunkData.audioUrl);
      currentBlobUrl.current = blobUrl;

      audio.src = blobUrl;
      audio.playbackRate = speed;
      audio.muted = isMuted;
      audio.volume = volume;

      // Setup event listeners
      audio.onloadedmetadata = () => {
        setChunkDuration(audio.duration || chunkData!.duration);
        setIsLoading(false);
      };

      audio.ontimeupdate = () => {
        setCurrentPosition(audio.currentTime);
      };

      audio.onended = () => {
        // Auto-advance to next chunk
        if (bookProgress && chunkIndex < bookProgress.totalChunks - 1) {
          setCurrentChunkIndex(chunkIndex + 1);
          loadChunk(chunkIndex + 1).then(() => {
            if (isPlaying) {
              audioRef.current?.play();
            }
          });
        } else {
          setIsPlaying(false);
        }
      };

      audio.onerror = () => {
        console.error('Audio playback error');
        setIsLoading(false);
      };

      await audio.load();

      // Preload next chunks
      preloadNextChunks(chunkIndex + 1);

    } catch (error) {
      console.error('Failed to load chunk:', error);
      setIsLoading(false);
    }
  }, [bookId, provider, voiceId, speed, preloadedChunks, bookProgress, isMuted, volume, isPlaying]);

  // Load initial chunk
  useEffect(() => {
    loadChunk(currentChunkIndex);
    return () => {
      audioRef.current?.pause();
      // Clean up blob URL on unmount
      if (currentBlobUrl.current) {
        URL.revokeObjectURL(currentBlobUrl.current);
        currentBlobUrl.current = null;
      }
    };
  }, []);

  // Track the last processed initialChunk to avoid re-processing
  const lastProcessedChunkRef = useRef<number>(initialChunk);

  // Listen for changes in initialChunk prop (chapter navigation)
  // This allows chapter navigation to work correctly
  useEffect(() => {
    // Only update if initialChunk has actually changed from what we last processed
    // Don't check currentPosition as it updates constantly during playback
    if (initialChunk !== lastProcessedChunkRef.current) {
      console.log(`Chapter changed: ${lastProcessedChunkRef.current} -> ${initialChunk}`);
      lastProcessedChunkRef.current = initialChunk;

      const wasPlaying = isPlaying;

      // Pause if playing
      if (wasPlaying && audioRef.current) {
        audioRef.current.pause();
        setIsPlaying(false);
      }

      // Update state
      setCurrentChunkIndex(initialChunk);

      // Load new chunk
      loadChunk(initialChunk)
        .then(() => {
          // Seek to the specified position if provided
          if (audioRef.current && initialPosition > 0) {
            audioRef.current.currentTime = initialPosition;
          }
        })
        .catch((error) => {
          console.error('Failed to load chapter:', error);
          setIsLoading(false);
        });
    }
  }, [initialChunk, initialPosition, loadChunk, isPlaying]);

  const togglePlay = async () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      try {
        await audioRef.current.play();
        setIsPlaying(true);
      } catch (error) {
        console.error('Playback failed:', error);
      }
    }
  };

  const skipForward = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.min(
        chunkDuration,
        audioRef.current.currentTime + skipDuration
      );
    }
  };

  const skipBackward = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(
        0,
        audioRef.current.currentTime - skipDuration
      );
    }
  };

  const cycleSkipDuration = () => {
    const currentIndex = SKIP_DURATIONS.indexOf(skipDuration);
    const nextIndex = (currentIndex + 1) % SKIP_DURATIONS.length;
    setSkipDuration(SKIP_DURATIONS[nextIndex]);
  };

  const seekToPosition = (position: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = position;
      setCurrentPosition(position);
    }
  };

  const seekToChunk = async (chunkIndex: number, positionInChunk: number = 0) => {
    const wasPlaying = isPlaying;
    if (isPlaying) {
      audioRef.current?.pause();
      setIsPlaying(false);
    }

    setCurrentChunkIndex(chunkIndex);
    await loadChunk(chunkIndex);

    if (audioRef.current && positionInChunk > 0) {
      audioRef.current.currentTime = positionInChunk;
    }

    if (wasPlaying) {
      await audioRef.current?.play();
      setIsPlaying(true);
    }
  };

  const seekToBookProgress = (progress: number) => {
    if (!bookProgress) return;

    const targetSeconds = progress * bookProgress.totalDuration;
    let accumulated = 0;

    for (let i = 0; i < bookProgress.chunkDurations.length; i++) {
      const chunkDur = bookProgress.chunkDurations[i];
      if (accumulated + chunkDur >= targetSeconds) {
        const positionInChunk = targetSeconds - accumulated;
        seekToChunk(i, positionInChunk);
        return;
      }
      accumulated += chunkDur;
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
    // Auto-unmute if volume is increased
    if (newVolume > 0 && isMuted) {
      setIsMuted(false);
      if (audioRef.current) {
        audioRef.current.muted = false;
      }
    }
  };

  const getVolumeIcon = () => {
    if (isMuted || volume === 0) return <VolumeX className="w-5 h-5" />;
    return <Volume2 className="w-5 h-5" />;
  };

  const cyclePlaybackRate = () => {
    const currentIndex = PLAYBACK_RATES.indexOf(speed);
    const nextIndex = (currentIndex + 1) % PLAYBACK_RATES.length;
    const newSpeed = PLAYBACK_RATES[nextIndex];
    onSpeedChange(newSpeed);
    if (audioRef.current) {
      audioRef.current.playbackRate = newSpeed;
    }
  };

  // Calculate overall progress
  const calculateOverallProgress = (): number => {
    if (!bookProgress) return 0;
    const elapsed = bookProgress.chunkDurations
      .slice(0, currentChunkIndex)
      .reduce((a, b) => a + b, 0) + currentPosition;
    return elapsed / bookProgress.totalDuration;
  };

  const formatTime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate current chapter based on chunk index
  const getCurrentChapter = (): number => {
    if (!chapters || chapters.length === 0) return 1;

    for (let i = 0; i < chapters.length; i++) {
      const chapter = chapters[i];
      const nextChapter = chapters[i + 1];

      if (chapter.startChunk !== undefined) {
        const chapterStart = chapter.startChunk;
        const chapterEnd = nextChapter?.startChunk ?? Infinity;

        if (currentChunkIndex >= chapterStart && currentChunkIndex < chapterEnd) {
          return chapter.order;
        }
      }
    }

    return 1;
  };

  // Calculate current playback time in seconds
  const calculateCurrentTime = (): number => {
    if (!bookProgress) return 0;
    return (bookProgress.chunkDurations || [])
      .slice(0, currentChunkIndex)
      .reduce((a, b) => a + b, 0) + currentPosition;
  };

  // Handle chapter selection from ChapterNav
  const handleChapterSelect = (chapter: Chapter) => {
    if (chapter.startChunk !== undefined && onChapterSelect) {
      // Find the index of this chapter
      const chapterIndex = chapters.findIndex(ch => ch.id === chapter.id);
      if (chapterIndex !== -1) {
        onChapterSelect(chapterIndex);
      }
    }
  };

  return (
    <div className="w-full flex flex-col items-center bg-gradient-to-b from-gray-900 to-black p-6 rounded-2xl">
      {/* Book Info */}
      <div className="flex items-center gap-4 mb-6 w-full">
        {coverUrl && (
          <div className="relative w-16 h-24">
            <img
              src={coverUrl}
              alt={bookTitle}
              className="w-16 h-24 object-cover rounded-lg shadow-lg"
            />
            {/* Loading Spinner Overlay on Cover */}
            {isLoading && (
              <div className="absolute inset-0 bg-black/60 rounded-lg flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-500 border-t-transparent" />
              </div>
            )}
          </div>
        )}
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-white line-clamp-2">
            {bookTitle}
          </h2>
          <p className="text-sm text-gray-400">
            Chapter {currentChunkIndex + 1} of {bookProgress?.totalChunks || '...'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Chapter Navigation */}
          {chapters && chapters.length > 0 && (
            <ChapterNav
              chapters={chapters}
              currentChapter={getCurrentChapter()}
              currentTime={calculateCurrentTime()}
              totalDuration={bookProgress?.totalDuration || 0}
              onSelectChapter={handleChapterSelect}
            />
          )}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 rounded-full hover:bg-gray-800 transition"
          >
            <Settings className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="w-full mb-4 overflow-hidden"
          >
            <VoiceSelector
              currentProvider={provider}
              currentVoice={voiceId}
              onProviderChange={onProviderChange}
              onVoiceChange={onVoiceChange}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Book-Level Progress Bar */}
      <BookProgressBar
        progress={calculateOverallProgress()}
        totalDuration={bookProgress?.totalDuration || 0}
        currentTime={
          (bookProgress?.chunkDurations || [])
            .slice(0, currentChunkIndex)
            .reduce((a, b) => a + b, 0) + currentPosition
        }
        onSeek={seekToBookProgress}
      />

      {/* Chunk Scrubber */}
      <ChunkScrubber
        totalChunks={bookProgress?.totalChunks || 0}
        currentChunk={currentChunkIndex}
        chunkDurations={bookProgress?.chunkDurations || []}
        listenedChunks={currentChunkIndex}
        onChunkSelect={seekToChunk}
      />

      {/* Chunk Progress - Clickable Seek Bar */}
      <div className="w-full flex items-center gap-2 text-xs text-gray-400 mt-2 mb-4">
        <span>{formatTime(currentPosition)}</span>
        <div
          className="flex-1 h-3 bg-gray-700 rounded-full overflow-hidden cursor-pointer relative group"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const percentage = clickX / rect.width;
            const newPosition = percentage * chunkDuration;
            seekToPosition(newPosition);
          }}
        >
          {/* Progress fill */}
          <div
            className="h-full bg-purple-500 transition-all duration-100"
            style={{ width: `${(currentPosition / chunkDuration) * 100}%` }}
          />
          {/* Seek indicator on hover */}
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-[10px] text-white/70">Click to seek</span>
            </div>
          </div>
        </div>
        <span>-{formatTime(Math.max(0, chunkDuration - currentPosition))}</span>
      </div>

      {/* Main Playback Controls */}
      <div className="flex items-center justify-center gap-4 mb-4">
        {/* Volume Control */}
        <div className="relative" ref={volumeControlRef}>
          <button
            onClick={() => setShowVolumeSlider(!showVolumeSlider)}
            className="p-3 rounded-full hover:bg-gray-800 transition text-gray-400 hover:text-white"
            aria-label="Volume control"
          >
            {getVolumeIcon()}
          </button>

          {/* Volume Slider */}
          <AnimatePresence>
            {showVolumeSlider && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-gray-800 rounded-lg p-3 shadow-xl z-50"
              >
                <div className="flex flex-col items-center gap-2">
                  {/* Vertical slider for better mobile UX */}
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={volume}
                    onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                    className="w-32 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer
                      [&::-webkit-slider-thumb]:appearance-none
                      [&::-webkit-slider-thumb]:w-4
                      [&::-webkit-slider-thumb]:h-4
                      [&::-webkit-slider-thumb]:rounded-full
                      [&::-webkit-slider-thumb]:bg-purple-500
                      [&::-webkit-slider-thumb]:cursor-pointer
                      [&::-webkit-slider-thumb]:shadow-lg
                      [&::-moz-range-thumb]:w-4
                      [&::-moz-range-thumb]:h-4
                      [&::-moz-range-thumb]:rounded-full
                      [&::-moz-range-thumb]:bg-purple-500
                      [&::-moz-range-thumb]:border-0
                      [&::-moz-range-thumb]:cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, rgb(168, 85, 247) 0%, rgb(168, 85, 247) ${volume * 100}%, rgb(55, 65, 81) ${volume * 100}%, rgb(55, 65, 81) 100%)`
                    }}
                  />
                  <div className="text-xs font-semibold text-white">
                    {Math.round(volume * 100)}%
                  </div>
                  <button
                    onClick={toggleMute}
                    className="text-xs text-purple-400 hover:text-purple-300 transition"
                  >
                    {isMuted ? 'Unmute' : 'Mute'}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Skip Backward - Click to skip, Double-click to change duration */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={skipBackward}
          onDoubleClick={cycleSkipDuration}
          className="relative w-14 h-14 rounded-full bg-gray-800/80 hover:bg-gray-700 border border-gray-700 text-white transition-all flex items-center justify-center group"
          title={`Skip back ${skipDuration}s (double-click to change)`}
        >
          <div className="flex flex-col items-center">
            <RotateCcw className="h-4 w-4 mb-[-2px]" />
            <span className="text-[9px] font-bold">{skipDuration}</span>
          </div>
          {/* Tooltip on hover */}
          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 hidden group-hover:block bg-gray-900 text-[10px] px-2 py-1 rounded whitespace-nowrap">
            Double-click to change
          </div>
        </motion.button>

        {/* Play/Pause - Always Enabled */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={togglePlay}
          className="relative w-18 h-18 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-2xl transition-all flex items-center justify-center"
          style={{ width: 72, height: 72 }}
        >
          {isPlaying ? (
            <Pause className="h-7 w-7 fill-white" />
          ) : (
            <Play className="h-7 w-7 fill-white ml-1" />
          )}
        </motion.button>

        {/* Skip Forward - Click to skip, Double-click to change duration */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={skipForward}
          onDoubleClick={cycleSkipDuration}
          className="relative w-14 h-14 rounded-full bg-gray-800/80 hover:bg-gray-700 border border-gray-700 text-white transition-all flex items-center justify-center group"
          title={`Skip forward ${skipDuration}s (double-click to change)`}
        >
          <div className="flex flex-col items-center">
            <RotateCw className="h-4 w-4 mb-[-2px]" />
            <span className="text-[9px] font-bold">{skipDuration}</span>
          </div>
          {/* Tooltip on hover */}
          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 hidden group-hover:block bg-gray-900 text-[10px] px-2 py-1 rounded whitespace-nowrap">
            Double-click to change
          </div>
        </motion.button>

        {/* Speed */}
        <button
          onClick={cyclePlaybackRate}
          className="px-3 py-2 bg-gray-800/60 hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-white transition text-sm font-semibold border border-gray-700"
        >
          {speed}x
        </button>
      </div>
    </div>
  );
}
