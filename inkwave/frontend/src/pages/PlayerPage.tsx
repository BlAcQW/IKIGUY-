/**
 * PlayerPage
 * Full-screen immersive audio player with voice Q&A
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronLeft,
  Mic,
  Bookmark,
  Share2,
  MoreHorizontal,
  Settings,
} from 'lucide-react';
import AudioPlayer from '../components/AudioPlayer';
import ProgressBar from '../components/ProgressBar';
import WaveformVisualization from '../components/WaveformVisualization';
import TableOfContents from '../components/TableOfContents';
import ChapterNav from '../components/ChapterNav';
import VoiceRecorder from '../components/VoiceRecorder';
import VoiceBookChat from '../components/VoiceBookChat';
import AIResponse from '../components/AIResponse';
import ConversationDrawer, {
  Conversation,
} from '../components/ConversationDrawer';
import { useAudioPlayer } from '../hooks/useAudioPlayer';
import { api } from '../lib/api';
import { getBookCoverUrl, generatePlaceholderCover } from '../lib/bookCoverUtils';
import { useProfile } from '../hooks/useProfile';
import toast from 'react-hot-toast';

interface Chapter {
  id: string;
  title: string;
  duration: number;
  order: number;
  startTime?: number;
}

interface BookPlayerData {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
  chapters: Chapter[];
  audioUrl?: string;
}

// Mock data for development
const MOCK_BOOK: BookPlayerData = {
  id: '1',
  title: 'The Power of Forgiveness',
  author: 'Archbishop Nicholas Duncan-Williams',
  coverUrl: 'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400&h=600&fit=crop',
  chapters: [
    { id: 'ch1', title: 'Introduction: The Journey to Freedom', duration: 12, order: 1, startTime: 0 },
    { id: 'ch2', title: 'Understanding Unforgiveness', duration: 15, order: 2, startTime: 720 },
    { id: 'ch3', title: 'The Cost of Holding Grudges', duration: 18, order: 3, startTime: 1620 },
    { id: 'ch4', title: 'Biblical Foundation of Forgiveness', duration: 20, order: 4, startTime: 2700 },
    { id: 'ch5', title: 'Forgiving Yourself', duration: 22, order: 5, startTime: 3900 },
    { id: 'ch6', title: 'Forgiving Others', duration: 25, order: 6, startTime: 5220 },
    { id: 'ch7', title: 'Breaking Generational Curses', duration: 28, order: 7, startTime: 6720 },
    { id: 'ch8', title: 'Walking in Freedom', duration: 24, order: 8, startTime: 8400 },
    { id: 'ch9', title: 'Maintaining Your Deliverance', duration: 20, order: 9, startTime: 9840 },
    { id: 'ch10', title: 'Living a Life of Grace', duration: 18, order: 10, startTime: 11040 },
  ],
  // audioUrl: 'https://example.com/audio.mp3', // Will be fetched from backend
};

interface VoiceSettings {
  tts: {
    default_provider: string;
    speed: number;
    pitch: number;
  };
  asr: {
    default_provider: string;
    language: string;
  };
}

export default function PlayerPage() {
  useEffect(() => {
    document.title = 'Player - InkWave';
  }, []);

  const { bookId } = useParams<{ bookId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { data: profileData } = useProfile();

  // Check if user is admin
  const canAccessVoiceQA = profileData ? (profileData.is_admin || profileData.role === 'admin' || profileData.role === 'superadmin') : false;

  const [book, setBook] = useState<BookPlayerData | null>(null);
  const [currentChapter, setCurrentChapter] = useState(1);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const [showSeamlessChat, setShowSeamlessChat] = useState(false);
  const [interactionId, setInteractionId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [latestResponse, setLatestResponse] = useState<Conversation | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings | null>(null);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);

  // Use refs to avoid recreating callback and audio element
  const bookRef = useRef<BookPlayerData | null>(book);
  const currentChapterRef = useRef(currentChapter);

  // Update refs when values change
  useEffect(() => {
    bookRef.current = book;
    currentChapterRef.current = currentChapter;
  }, [book, currentChapter]);

  // Create stable callback that doesn't change on re-renders
  // This prevents the audio element from being recreated
  const handleTimeUpdate = useCallback((time: number) => {
    // Chapter tracking - we'll implement this properly later
    // For now, we just want to prevent audio element recreation
  }, []); // Empty dependencies = callback never changes

  // Audio player hook
  const {
    isPlaying,
    currentTime,
    duration,
    playbackRate,
    isLoading,
    error,
    togglePlay,
    seek,
    skipForward,
    skipBackward,
    changePlaybackRate,
    enableAutoPlay,
  } = useAudioPlayer({
    src: book?.audioUrl,
    onTimeUpdate: handleTimeUpdate,
  });

  // Track chapter changes based on currentTime from audio player
  useEffect(() => {
    if (book?.chapters && duration > 0) {
      const chapter = book.chapters.find((ch, idx) => {
        const nextChapter = book.chapters[idx + 1];
        const chStart = ch.startTime || 0;
        const chEnd = nextChapter?.startTime || duration;
        return currentTime >= chStart && currentTime < chEnd;
      });
      if (chapter && chapter.order !== currentChapter) {
        setCurrentChapter(chapter.order);
      }
    }
  }, [currentTime, book?.chapters, duration, currentChapter]);

  useEffect(() => {
    fetchBook();
    loadVoiceSettings();
  }, [bookId]);

  // Generate audio on-demand when user first clicks play
  const generateAudioOnDemand = async () => {
    if (!book || isGeneratingAudio) return;

    try {
      setIsGeneratingAudio(true);
      toast.loading('Generating audio narration...', { id: 'audio-gen' });

      // Call generate-audio endpoint with voice settings
      const response = await api.books.generateAudio(book.id, {
        provider_id: voiceSettings?.tts?.default_provider || 'f5tts',  // F5-TTS with voice cloning
        voice_id: 'archbishop_1',  // Archbishop Duncan-Williams' voice
        speed: voiceSettings?.tts?.speed || 1.0,
        language: 'en'
      });

      const audioData = response.data;
      console.log('🎵 Audio generation response:', {
        provider: audioData.provider_used,
        duration: audioData.duration,
        audioUrlType: audioData.audio_url?.startsWith('data:') ? 'data URL' : 'regular URL',
        audioUrlLength: audioData.audio_url?.length,
        audioUrlStart: audioData.audio_url?.substring(0, 100)
      });

      // Validate audio URL
      if (!audioData.audio_url || audioData.audio_url.length < 100) {
        throw new Error('Invalid audio URL received from server');
      }

      // Enable auto-play BEFORE setting the src
      console.log('✅ Calling enableAutoPlay()');
      enableAutoPlay();

      // Update book with generated audio URL (data URL for immediate playback)
      console.log('📝 Setting book.audioUrl...');
      const updatedBook = {
        ...book,
        audioUrl: audioData.audio_url
      };

      setBook(updatedBook);
      console.log('✅ Book state updated with audioUrl');

      toast.success(`Audio generated! Duration: ${Math.round(audioData.duration)}s`, { id: 'audio-gen' });

    } catch (error: any) {
      console.error('Failed to generate audio:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate audio', { id: 'audio-gen' });
    } finally {
      setIsGeneratingAudio(false);
    }
  };

  // Load user's voice settings and apply default playback speed
  const loadVoiceSettings = async () => {
    try {
      const response = await api.voiceSettings.getMySettings();
      setVoiceSettings(response.data);

      // Apply default speed from voice settings to audio player
      if (response.data?.tts?.speed) {
        changePlaybackRate(response.data.tts.speed);
      }
    } catch (error) {
      console.error('Failed to load voice settings:', error);
      // Continue without settings (use defaults)
    }
  };

  const fetchBook = async () => {
    try {
      // Fetch real book data from API
      const response = await api.books.get(bookId!);
      const bookData = response.data;

      // Validate audio URL - don't use PDF files as audio sources
      let audioUrl: string | undefined = undefined;
      if (bookData.audio_url) {
        const url = bookData.audio_url.toLowerCase();
        // Only use if it's not a PDF file
        if (!url.endsWith('.pdf') && !url.includes('.pdf?')) {
          audioUrl = bookData.audio_url;
        } else {
          console.warn('Ignoring PDF URL as audio source:', bookData.audio_url);
        }
      }

      // Map API response to BookPlayerData format
      const mappedBook: BookPlayerData = {
        id: bookData.id,
        title: bookData.title,
        author: bookData.author,
        coverUrl: getBookCoverUrl(bookData.cover_url, bookData.title, bookData.author),
        chapters: bookData.chapters || [],
        audioUrl: audioUrl,
      };

      setBook(mappedBook);

      // Check if starting from specific chapter
      const chapterId = searchParams.get('chapter');
      if (chapterId && mappedBook.chapters) {
        const chapter = mappedBook.chapters.find((ch) => ch.id === chapterId);
        if (chapter) {
          setCurrentChapter(chapter.order);
          if (chapter.startTime) {
            seek(chapter.startTime);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching book:', error);
      toast.error('Failed to load book. Please try again.');

      // Fallback to mock data for development
      setBook(MOCK_BOOK);
    }
  };

  const handleSelectChapter = (chapter: Chapter) => {
    setCurrentChapter(chapter.order);
    if (chapter.startTime !== undefined) {
      seek(chapter.startTime);
    }
  };

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked);
    toast.success(isBookmarked ? 'Bookmark removed' : 'Bookmark added');
  };

  const handleShare = () => {
    toast.success('Link copied to clipboard!');
  };

  const handleVoiceQA = async () => {
    try {
      // Create or get interaction session
      if (!interactionId) {
        const response = await api.interactions.create(
          `session_${bookId}`,
          bookId!
        );
        setInteractionId(response.data.interaction_id);
      }
      setShowSeamlessChat(true);
    } catch (error) {
      console.error('Failed to create interaction:', error);
      toast.error('Failed to start conversation');
    }
  };

  const handleRecordingComplete = async (
    audioBlob: Blob,
    transcript: string
  ) => {
    setShowVoiceRecorder(false);
    setIsProcessing(true);

    try {
      // Step 1: Create or get interaction session
      let interactionId = conversations[0]?.id; // Reuse existing interaction

      if (!interactionId) {
        // Create new interaction
        const interactionResponse = await api.interactions.create(
          'session_' + bookId, // session_id (we can use bookId as session for now)
          bookId!
        );
        interactionId = interactionResponse.data.interaction_id;
      }

      // Step 2: Send message and get AI response
      const messageResponse = await api.interactions.sendMessage(
        interactionId,
        transcript || 'Your voice question'
      );

      const aiMessage = messageResponse.data.message;
      const conversation: Conversation = {
        id: interactionId,
        question: transcript || 'Your voice question',
        answer: aiMessage?.content || 'Sorry, I could not generate a response.',
        timestamp: new Date(),
      };

      // Step 3: Optionally synthesize TTS audio for the answer
      // const ttsResponse = await api.voice.synthesize(aiMessage.content);
      // conversation.audioUrl = URL.createObjectURL(ttsResponse.data);

      setConversations((prev) => [conversation, ...prev]);
      setLatestResponse(conversation);

      toast.success('Answer ready!');
    } catch (error: any) {
      console.error('Error processing question:', error);

      // Fallback to mock response on error
      const mockAnswer = `I'm having trouble connecting to the AI service. Error: ${error?.response?.data?.detail || error.message}`;

      const conversation: Conversation = {
        id: Date.now().toString(),
        question: transcript || 'Your voice question',
        answer: mockAnswer,
        timestamp: new Date(),
      };

      setConversations((prev) => [conversation, ...prev]);
      setLatestResponse(conversation);

      toast.error('Failed to process your question, showing fallback response');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRecordingCancel = () => {
    setShowVoiceRecorder(false);
  };

  const handleClearConversations = () => {
    if (
      window.confirm('Are you sure you want to clear all conversations?')
    ) {
      setConversations([]);
      setLatestResponse(null);
      toast.success('Conversations cleared');
    }
  };

  const handleExportConversations = () => {
    const dataStr = JSON.stringify(conversations, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `inkwave-qa-${bookId}-${Date.now()}.json`;
    link.click();
    toast.success('Conversations exported');
  };

  if (!book) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading player...</p>
        </div>
      </div>
    );
  }

  const currentChapterData = book.chapters.find(
    (ch) => ch.order === currentChapter
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-gray-900/95 backdrop-blur-md border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          {/* Back Button */}
          <button
            onClick={() => navigate(-1)}
            className="flex items-center space-x-2 text-gray-400 hover:text-white transition"
          >
            <ChevronLeft className="h-5 w-5" />
            <span className="hidden sm:inline">Back</span>
          </button>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <ConversationDrawer
              conversations={conversations}
              onClear={handleClearConversations}
              onExport={handleExportConversations}
            />
            <button
              onClick={() => navigate('/voice-settings')}
              className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition"
              title="Voice Settings"
            >
              <Settings className="h-5 w-5" />
            </button>
            <button
              onClick={handleBookmark}
              className={`p-2 rounded-lg transition ${
                isBookmarked
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              <Bookmark className={`h-5 w-5 ${isBookmarked ? 'fill-white' : ''}`} />
            </button>
            <button
              onClick={handleShare}
              className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition"
            >
              <Share2 className="h-5 w-5" />
            </button>
            <button className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition">
              <MoreHorizontal className="h-5 w-5" />
            </button>
            <ChapterNav
              chapters={book.chapters}
              currentChapter={currentChapter}
              onSelectChapter={handleSelectChapter}
            />
          </div>
        </div>
      </div>

      {/* Main Player Area */}
      <div className="flex-1 flex flex-col items-center px-4 py-8 overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-2xl space-y-8"
        >
          {/* Book Cover - Large and Centered */}
          <div className="flex justify-center pt-4 sm:pt-8">
            <motion.img
              src={book.coverUrl}
              alt={book.title}
              className="w-48 sm:w-64 md:w-80 h-auto aspect-[2/3] object-cover rounded-xl sm:rounded-2xl shadow-2xl"
              whileHover={{ scale: 1.02 }}
              transition={{ duration: 0.2 }}
              onError={(e) => {
                e.currentTarget.src = generatePlaceholderCover(book.title, book.author);
                e.currentTarget.onerror = null;
              }}
            />
          </div>

          {/* Book Info - Centered */}
          <div className="text-center space-y-3">
            <h1 className="text-3xl sm:text-4xl font-bold text-white">
              {book.title}
            </h1>
            <p className="text-xl text-gray-400">by {book.author}</p>
            {currentChapterData && (
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/20 border border-purple-500/30 rounded-full">
                <span className="text-sm text-purple-400 font-medium">
                  {currentChapterData.title}
                </span>
              </div>
            )}
          </div>

          {/* Progress Bar with Time Display */}
          {book?.audioUrl && !error && !isGeneratingAudio ? (
            <div className="space-y-2 pt-4">
              <ProgressBar
                currentTime={currentTime}
                duration={duration}
                onSeek={seek}
              />
            </div>
          ) : null}

          {/* Waveform Visualization */}
          {book?.audioUrl && !error && !isGeneratingAudio ? (
            <WaveformVisualization
              isPlaying={isPlaying}
              currentTime={currentTime}
              duration={duration}
              barCount={50}
              height={60}
            />
          ) : null}

          {/* Audio Player Controls */}
          {!book?.audioUrl && !isGeneratingAudio ? (
            <div className="text-center space-y-4 py-8">
              <p className="text-gray-400">No audio generated yet</p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={generateAudioOnDemand}
                className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-full text-white font-semibold shadow-lg"
              >
                🎧 Generate Audio Narration
              </motion.button>
              <p className="text-xs text-gray-500">
                Uses your selected voice @ {voiceSettings?.tts?.speed || 1.0}x speed
              </p>
            </div>
          ) : isGeneratingAudio ? (
            <div className="text-center space-y-4 py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto" />
              <p className="text-gray-400">Generating audio narration...</p>
              <p className="text-sm text-gray-500">This may take a few moments</p>
            </div>
          ) : error ? (
            <div className="text-center space-y-4 py-8">
              <p className="text-red-400 mb-2">{error}</p>
              <p className="text-gray-500 text-sm mb-4">
                Unable to load audio. Try generating it again.
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={generateAudioOnDemand}
                className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-full text-white font-semibold shadow-lg"
              >
                🔄 Regenerate Audio
              </motion.button>
            </div>
          ) : (
            <AudioPlayer
              isPlaying={isPlaying}
              isLoading={isLoading}
              onTogglePlay={togglePlay}
              onSkipForward={skipForward}
              onSkipBackward={skipBackward}
              playbackRate={playbackRate}
              onChangePlaybackRate={changePlaybackRate}
            />
          )}

          {/* Table of Contents */}
          {book?.audioUrl && !error && !isGeneratingAudio && book.chapters.length > 0 && (
            <div className="pt-8">
              <TableOfContents
                chapters={book.chapters.map(ch => ({
                  id: ch.id,
                  title: ch.title,
                  startTime: ch.startTime || 0,
                  duration: ch.duration * 60, // Convert minutes to seconds
                }))}
                currentChapterId={currentChapterData?.id || null}
                currentTime={currentTime}
                onChapterClick={(chapter) => {
                  seek(chapter.startTime);
                  toast.success(`Jumped to: ${chapter.title}`);
                }}
                isExpanded={true}
              />
            </div>
          )}

          {/* Latest AI Response */}
          <AnimatePresence>
            {latestResponse && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <AIResponse
                  question={latestResponse.question}
                  answer={latestResponse.answer}
                  audioUrl={latestResponse.audioUrl}
                  timestamp={latestResponse.timestamp}
                  onClose={() => setLatestResponse(null)}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Processing State */}
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center space-y-4"
            >
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto" />
              <p className="text-gray-400">Processing your question...</p>
              <p className="text-sm text-gray-500">
                AI is analyzing the book content
              </p>
            </motion.div>
          )}

          {/* Voice Q&A Button - Only show for admin users */}
          {canAccessVoiceQA && !isProcessing && (
            <div className="flex justify-center pt-8">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleVoiceQA}
                className="flex items-center space-x-3 px-8 py-4 bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 rounded-full text-white font-semibold shadow-lg"
              >
                <Mic className="h-6 w-6" />
                <span>Ask a Question</span>
              </motion.button>
            </div>
          )}
        </motion.div>
      </div>

      {/* Voice Recorder Modal (Legacy) */}
      <AnimatePresence>
        {showVoiceRecorder && (
          <VoiceRecorder
            onComplete={handleRecordingComplete}
            onCancel={handleRecordingCancel}
            maxDuration={60}
          />
        )}
      </AnimatePresence>

      {/* Voice Book Chat Modal (Real-time WebSocket/WebRTC) */}
      <AnimatePresence>
        {showSeamlessChat && bookId && (
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
                bookId={bookId}
                bookTitle={bookData?.title}
                onClose={() => setShowSeamlessChat(false)}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
