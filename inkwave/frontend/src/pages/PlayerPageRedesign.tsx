/**
 * PlayerPage - Redesigned
 * Modern, elegant audiobook player with clean centered layout
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
	ChevronLeft,
	Play,
	Pause,
	RotateCcw,
	RotateCw,
	SkipBack,
	SkipForward,
	Volume2,
	Mic,
	Share2,
	Settings,
	Clock,
	TrendingUp,
	BookOpen,
	Library,
} from 'lucide-react';
import ChapterNav from '../components/ChapterNav';
import SeamlessConversation from '../components/SeamlessConversation';
import AIResponse from '../components/AIResponse';
import ConversationDrawer, {
	Conversation,
} from '../components/ConversationDrawer';
import SleepTimer from '../components/SleepTimer';
import BookmarkManager, { BookmarkItem } from '../components/BookmarkManager';
import VoiceSettingsDropdown from '../components/VoiceSettingsDropdown';
import BookTextView from '../components/BookTextView';
import SocialShareButtons from '../components/SocialShareButtons';
import BuyCreditsButton from '../components/BuyCreditsButton';
import { useAudioPlayer } from '../hooks/useAudioPlayer';
import { useChunkPlayer, VoiceSettings as ChunkVoiceSettings, ChapterBoundary } from '../hooks/useChunkPlayer';
import { useConsumptionTracking } from '../hooks/useConsumptionTracking';
import { api } from '../lib/api';
import { getBookCoverUrl } from '../lib/bookCoverUtils';
import { useProfile } from '../hooks/useProfile';
import { useWalletStore } from '../store/walletStore';
import { PRICING } from '../config/constants';
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

interface VoiceSettings {
	tts: {
		default_provider: string;
		default_voice: string | null;
		speed: number;
		pitch: number;
	};
	asr: {
		default_provider: string;
		language: string;
	};
}

export default function PlayerPageRedesign() {
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
	const [showSeamlessChat, setShowSeamlessChat] = useState(false);
	const [interactionId, setInteractionId] = useState<string | null>(null);
	const [conversations, setConversations] = useState<Conversation[]>([]);
	const [latestResponse, setLatestResponse] = useState<Conversation | null>(null);
	const [isProcessing, setIsProcessing] = useState(false);
	const [voiceSettings, setVoiceSettings] = useState<VoiceSettings | null>(null);
	const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
	const [showVolumeSlider, setShowVolumeSlider] = useState(false);
	const [isLoadingBook, setIsLoadingBook] = useState(true);
	const [bookLoadError, setBookLoadError] = useState<string | null>(null);
	const [sessionId, setSessionId] = useState<string | null>(null);
	const [sessionTotalTime, setSessionTotalTime] = useState<number>(0);
	const [bookmarks, setBookmarks] = useState<BookmarkItem[]>([]);
	const [useChunkMode, setUseChunkMode] = useState(false);  // Toggle between legacy and chunk mode
	const [shouldAutoPlayChunk, setShouldAutoPlayChunk] = useState(false);  // Auto-play when chunk mode starts
	const [shouldNavigateToChapter, setShouldNavigateToChapter] = useState<number | null>(null);  // Chapter to navigate to when chunk mode starts
	const [showTextView, setShowTextView] = useState(false);  // Toggle text view
	const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null);  // Swipe feedback
	const [seekFeedback, setSeekFeedback] = useState<{ show: boolean; seconds: number } | null>(null);  // Visual feedback for seeking
	const [chunkVoiceSettings, setChunkVoiceSettings] = useState<ChunkVoiceSettings>({
		provider_id: 'kokoro',
		voice_id: 'am_michael',
		speed: 1.0,
	});
	const [audioGenStatus, setAudioGenStatus] = useState<{
		status?: string;
		progress?: number;
		message?: string;
		generated_count?: number;
		total_chunks?: number;
	} | null>(null);
	const [isPreloading, setIsPreloading] = useState(false);

	const bookRef = useRef<BookPlayerData | null>(book);
	const currentChapterRef = useRef(currentChapter);
	const touchStartX = useRef<number | null>(null);
	const touchStartY = useRef<number | null>(null);

	useEffect(() => {
		bookRef.current = book;
		currentChapterRef.current = currentChapter;
	}, [book, currentChapter]);

	const handleTimeUpdate = useCallback((time: number) => {
		// Chapter tracking
	}, []);

	// Legacy audio player (for single audio URL mode)
	const legacyPlayer = useAudioPlayer({
		src: !useChunkMode ? book?.audioUrl : undefined,
		onTimeUpdate: handleTimeUpdate,
	});

	// Chunk-based audio player (for full book TTS)
	// waitForVoiceSettings=true ensures we don't load audio until voice settings are loaded
	const chunkPlayer = useChunkPlayer({
		bookId: bookId || '',
		sessionId: sessionId || undefined,
		initialChunkIndex: 0,
		initialPositionSeconds: 0,
		initialTotalTimeMinutes: sessionTotalTime,
		voiceSettings: chunkVoiceSettings,
		waitForVoiceSettings: true, // Wait for voice settings to be loaded before fetching audio
		onChunkChange: (chunkIndex) => {
			console.log('Chunk changed to:', chunkIndex);
		},
		onProgressUpdate: (chunkIndex, positionSeconds, totalTimeMinutes) => {
			if (sessionId) {
				api.reading.updateProgress(sessionId, chunkIndex, positionSeconds, totalTimeMinutes).catch(console.error);
			}
		},
	});

	// Use chunk player when in chunk mode, otherwise legacy
	const {
		isPlaying,
		currentTime,
		duration,
		playbackRate,
		isLoading,
		error,
		togglePlay,
		pause,
		skipForward,
		skipBackward,
		changePlaybackRate,
	} = useChunkMode ? {
		isPlaying: chunkPlayer.isPlaying,
		currentTime: chunkPlayer.globalPosition,
		duration: chunkPlayer.totalDuration,
		playbackRate: chunkPlayer.playbackRate,
		isLoading: chunkPlayer.isLoading,
		error: chunkPlayer.error,
		togglePlay: chunkPlayer.togglePlay,
		pause: chunkPlayer.pause,
		skipForward: () => chunkPlayer.skipForward(15),
		skipBackward: () => chunkPlayer.skipBackward(15),
		changePlaybackRate: chunkPlayer.changePlaybackRate,
	} : {
			isPlaying: legacyPlayer.isPlaying,
			currentTime: legacyPlayer.currentTime,
			duration: legacyPlayer.duration,
			playbackRate: legacyPlayer.playbackRate,
			isLoading: legacyPlayer.isLoading,
			error: legacyPlayer.error,
			togglePlay: legacyPlayer.togglePlay,
			pause: legacyPlayer.pause,
			skipForward: () => legacyPlayer.skipForward(15),
			skipBackward: () => legacyPlayer.skipBackward(15),
			changePlaybackRate: legacyPlayer.changePlaybackRate,
		};

	// Seek function based on mode
	const seek = useChunkMode ? chunkPlayer.seekToGlobalPosition : legacyPlayer.seek;
	const enableAutoPlay = legacyPlayer.enableAutoPlay;

	// Calculate listening statistics
	const percentageListened = duration > 0 ? (currentTime / duration) * 100 : 0;
	const minutesListened = Math.floor(currentTime / 60);
	const minutesRemaining = Math.floor((duration - currentTime) / 60);

	// Wallet balance for real-time cost display
	const { balance, refreshBalance } = useWalletStore();

	// Consumption tracking with real-time billing
	const {
		sessionCostCredits,
		lastBillingSuccess,
	} = useConsumptionTracking({
		sessionId,
		bookId: bookId || '',
		bookTitle: book?.title,
		bookAuthor: book?.author,
		totalChunks: chunkPlayer.totalChunks,
		isPlaying,
		currentChunkIndex: chunkPlayer.currentChunkIndex,
		currentPosition: chunkPlayer.currentTime,
		consumptionMode: 'audio_playback',
		enabled: useChunkMode && !!sessionId,
	});

	// Refresh balance when billing happens
	useEffect(() => {
		if (sessionCostCredits > 0) {
			// Refresh balance every 30 seconds during playback to show updated balance
			refreshBalance();
		}
	}, [sessionCostCredits, refreshBalance]);

	// Convert credits to currency for display
	const sessionCostCurrency = (sessionCostCredits / PRICING.CREDITS_PER_DOLLAR).toFixed(2);
	const balanceCurrency = (balance / PRICING.CREDITS_PER_DOLLAR).toFixed(2);

	// 15-second skip functions
	const skip15Forward = () => skipForward();
	const skip15Backward = () => skipBackward();

	// Chapter navigation functions
	const goToPreviousChapter = useCallback(() => {
		if (!book?.chapters || !Array.isArray(book.chapters) || book.chapters.length === 0) return;

		const currentIdx = book.chapters.findIndex((ch) => ch.order === currentChapter);
		if (currentIdx > 0) {
			const prevChapter = book.chapters[currentIdx - 1];
			handleSelectChapter(prevChapter);
			toast.success(`Playing: ${prevChapter.title}`);
		} else {
			// Already at first chapter, restart it
			seek(0);
			toast.success('Restarting chapter');
		}
	}, [book?.chapters, currentChapter, seek]);

	const goToNextChapter = useCallback(() => {
		if (!book?.chapters || !Array.isArray(book.chapters) || book.chapters.length === 0) return;

		const currentIdx = book.chapters.findIndex((ch) => ch.order === currentChapter);
		if (currentIdx < book.chapters.length - 1) {
			const nextChapter = book.chapters[currentIdx + 1];
			handleSelectChapter(nextChapter);
			toast.success(`Playing: ${nextChapter.title}`);
		} else {
			toast.success('Already at last chapter');
		}
	}, [book?.chapters, currentChapter]);

	// Swipe gesture handlers for seeking (Libby-style)
	const handleTouchStart = useCallback((e: React.TouchEvent) => {
		touchStartX.current = e.touches[0].clientX;
		touchStartY.current = e.touches[0].clientY;
	}, []);

	const handleTouchEnd = useCallback((e: React.TouchEvent) => {
		if (touchStartX.current === null || touchStartY.current === null) return;

		const touchEndX = e.changedTouches[0].clientX;
		const touchEndY = e.changedTouches[0].clientY;
		const deltaX = touchEndX - touchStartX.current;
		const deltaY = touchEndY - touchStartY.current;

		// Only trigger if horizontal swipe is dominant and significant
		const minSwipeDistance = 50;
		if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > minSwipeDistance) {
			// Calculate seek amount based on swipe distance (Libby-style)
			// More swipe = more seek. Max 60 seconds per swipe
			const swipeRatio = Math.min(Math.abs(deltaX) / 300, 1); // Normalize to 0-1
			const seekSeconds = Math.ceil(15 + (swipeRatio * 45)); // 15-60 seconds based on swipe distance

			if (deltaX > 0) {
				// Swiped right -> skip backward
				setSwipeDirection('right');
				skipBackward(seekSeconds);
				setSeekFeedback({ show: true, seconds: -seekSeconds });
			} else {
				// Swiped left -> skip forward
				setSwipeDirection('left');
				skipForward(seekSeconds);
				setSeekFeedback({ show: true, seconds: seekSeconds });
			}

			// Clear swipe indicator after animation
			setTimeout(() => setSwipeDirection(null), 300);
			setTimeout(() => setSeekFeedback(null), 1500);
		}

		touchStartX.current = null;
		touchStartY.current = null;
	}, [skipForward, skipBackward]);

	// Keyboard shortcuts for seeking (Libby-style)
	useEffect(() => {
		const handleKeyDown = (e: KeyboardEvent) => {
			// Ignore if user is typing in an input
			if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
				return;
			}

			switch (e.key) {
				case 'ArrowRight':
					e.preventDefault();
					skip15Forward();
					setSeekFeedback({ show: true, seconds: 15 });
					setTimeout(() => setSeekFeedback(null), 1500);
					break;
				case 'ArrowLeft':
					e.preventDefault();
					skip15Backward();
					setSeekFeedback({ show: true, seconds: -15 });
					setTimeout(() => setSeekFeedback(null), 1500);
					break;
				case ' ':
					e.preventDefault();
					togglePlay();
					break;
			}
		};

		window.addEventListener('keydown', handleKeyDown);
		return () => window.removeEventListener('keydown', handleKeyDown);
	}, [skip15Forward, skip15Backward, togglePlay]);

	// Check if at first/last chapter
	const isFirstChapter = currentChapter === 1;
	const isLastChapter = book?.chapters ? currentChapter === book.chapters.length : true;

	useEffect(() => {
		if (book?.chapters && Array.isArray(book.chapters) && book.chapters.length > 0 && duration > 0) {
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
		initializeSession();
		loadAudioGenerationStatus();
	}, [bookId]);

	// Load audio generation status periodically
	const loadAudioGenerationStatus = async () => {
		if (!bookId) return;
		try {
			const response = await api.audiobook.getBookAudioStatus(bookId);
			const status = response.data;
			setAudioGenStatus({
				status: status.is_complete ? 'completed' : 'generating',
				generated_count: status.generated_chunks,
				total_chunks: status.total_chunks,
				progress: status.total_chunks > 0
					? Math.round((status.generated_chunks / status.total_chunks) * 100)
					: 0,
				message: status.is_complete
					? 'All audio ready'
					: `Preparing ${status.generated_chunks}/${status.total_chunks} sections`
			});
		} catch (error) {
			console.error('Failed to load audio generation status:', error);
		}
	};

	// Preload first playable chunks when voice settings are ready and chunk player is initialized
	useEffect(() => {
		const preloadFirstChunks = async () => {
			if (!bookId || !useChunkMode || !chunkVoiceSettings.provider_id) return;
			if (chunkPlayer.totalChunks === 0) return; // Wait for chunks to load
			if (isPreloading) return; // Already preloading

			try {
				setIsPreloading(true);

				// Find first playable chunk (skip TOC, etc.)
				const skipChunks = chunkPlayer.skipChunks || [];
				let firstPlayable = 0;
				for (let i = 0; i < chunkPlayer.totalChunks; i++) {
					if (!skipChunks.includes(i)) {
						firstPlayable = i;
						break;
					}
				}

				// Preload first playable chunk + next 2 chunks (3 total)
				console.log(`[Player] Preloading chunks starting from ${firstPlayable}`);
				await api.audiobook.preload(bookId, {
					start_chunk: firstPlayable,
					num_chunks: 3,
					provider_id: chunkVoiceSettings.provider_id,
					voice_id: chunkVoiceSettings.voice_id,
					speed: chunkVoiceSettings.speed || 1.0,
				});
				console.log(`[Player] Preload complete for chunks ${firstPlayable}-${firstPlayable + 2}`);
			} catch (error) {
				console.error('[Player] Preload failed (non-critical):', error);
			} finally {
				setIsPreloading(false);
			}
		};

		// Trigger preload when chunk player is ready and voice settings are loaded
		if (chunkPlayer.totalChunks > 0 && chunkVoiceSettings.provider_id && !chunkPlayer.isLoading) {
			preloadFirstChunks();
		}
	}, [bookId, useChunkMode, chunkVoiceSettings, chunkPlayer.totalChunks, chunkPlayer.skipChunks, chunkPlayer.isLoading]);

	// Navigate to selected chapter when chunk mode initializes
	useEffect(() => {
		if (shouldNavigateToChapter && useChunkMode && chunkPlayer.chapterBoundaries && chunkPlayer.chapterBoundaries.length > 0 && !chunkPlayer.isLoading) {
			const chapterToNavigate = book?.chapters?.find(ch => ch.order === shouldNavigateToChapter);
			if (chapterToNavigate) {
				const chapterIndex = chunkPlayer.chapterBoundaries.findIndex(
					(boundary) => boundary.chapter_title === chapterToNavigate.title
				);
				if (chapterIndex >= 0) {
					chunkPlayer.goToChapter(chapterIndex);
					toast.success(`Starting from: ${chapterToNavigate.title}`);
					// After navigating to chapter, trigger auto-play if needed
					// Use a small delay to ensure chapter navigation completes
					setTimeout(() => {
						if (shouldAutoPlayChunk) {
							chunkPlayer.togglePlay();
							setShouldAutoPlayChunk(false);
						}
					}, 300);
				}
			}
			setShouldNavigateToChapter(null);
		}
	}, [shouldNavigateToChapter, useChunkMode, chunkPlayer.chapterBoundaries, chunkPlayer.isLoading, chunkPlayer.goToChapter, chunkPlayer.togglePlay, book?.chapters, shouldAutoPlayChunk]);

	// Auto-play when chunk mode is enabled and audio is ready (only if no chapter navigation is pending)
	useEffect(() => {
		if (shouldAutoPlayChunk && useChunkMode && !chunkPlayer.isLoading && !chunkPlayer.error && !shouldNavigateToChapter) {
			// Immediately clear flag to prevent multiple calls
			setShouldAutoPlayChunk(false);
			// Then trigger play
			chunkPlayer.togglePlay();
		}
	}, [shouldAutoPlayChunk, useChunkMode, chunkPlayer.isLoading, chunkPlayer.error, shouldNavigateToChapter, chunkPlayer.togglePlay]);

	// Initialize reading session and load bookmarks
	const initializeSession = async () => {
		try {
			const response = await api.reading.startSession(bookId!);
			const session = response.data;
			setSessionId(session.session_id);

			// Initialize total time from session for accurate tracking
			setSessionTotalTime(session.total_time_spent_minutes || 0);

			// Load bookmarks from session
			if (session.bookmarks) {
				const mappedBookmarks: BookmarkItem[] = session.bookmarks.map((b: any) => ({
					id: b.bookmark_id,
					position: b.position_seconds,
					note: b.note,
					chapterTitle: b.chapter_title,
					createdAt: b.created_at,
				}));
				setBookmarks(mappedBookmarks);
			}
		} catch (error) {
			console.error('Failed to initialize session:', error);
		}
	};

	// Bookmark handlers
	const handleAddBookmark = async (bookmark: Omit<BookmarkItem, 'id' | 'createdAt'>) => {
		if (!sessionId) return;

		try {
			const response = await api.reading.addBookmark(sessionId, {
				chunk_index: 0, // We'll use position_seconds for audio-based bookmarks
				position_seconds: bookmark.position,
				note: bookmark.note,
				chapter_title: bookmark.chapterTitle,
			});

			// Update local bookmarks from response
			if (response.data.bookmarks) {
				const mappedBookmarks: BookmarkItem[] = response.data.bookmarks.map((b: any) => ({
					id: b.bookmark_id,
					position: b.position_seconds,
					note: b.note,
					chapterTitle: b.chapter_title,
					createdAt: b.created_at,
				}));
				setBookmarks(mappedBookmarks);
			}
		} catch (error) {
			console.error('Failed to add bookmark:', error);
			toast.error('Failed to add bookmark');
		}
	};

	const handleUpdateBookmark = async (id: string, note: string) => {
		if (!sessionId) return;

		try {
			const response = await api.reading.updateBookmark(sessionId, id, note);

			if (response.data.bookmarks) {
				const mappedBookmarks: BookmarkItem[] = response.data.bookmarks.map((b: any) => ({
					id: b.bookmark_id,
					position: b.position_seconds,
					note: b.note,
					chapterTitle: b.chapter_title,
					createdAt: b.created_at,
				}));
				setBookmarks(mappedBookmarks);
			}
		} catch (error) {
			console.error('Failed to update bookmark:', error);
			toast.error('Failed to update bookmark');
		}
	};

	const handleDeleteBookmark = async (id: string) => {
		if (!sessionId) return;

		try {
			const response = await api.reading.deleteBookmark(sessionId, id);

			if (response.data.bookmarks) {
				const mappedBookmarks: BookmarkItem[] = response.data.bookmarks.map((b: any) => ({
					id: b.bookmark_id,
					position: b.position_seconds,
					note: b.note,
					chapterTitle: b.chapter_title,
					createdAt: b.created_at,
				}));
				setBookmarks(mappedBookmarks);
			}
		} catch (error) {
			console.error('Failed to delete bookmark:', error);
			toast.error('Failed to delete bookmark');
		}
	};

	const handleSeekToBookmark = (position: number) => {
		seek(position);
		toast.success('Jumped to bookmark');
	};

	// Get current chapter end time for sleep timer
	const getCurrentChapterEndTime = (): number | undefined => {
		if (!book?.chapters || !Array.isArray(book.chapters) || book.chapters.length === 0) return undefined;

		const currentChapterData = book.chapters.find(ch => ch.order === currentChapter);
		if (!currentChapterData) return undefined;

		const nextChapter = book.chapters.find(ch => ch.order === currentChapter + 1);
		return nextChapter?.startTime || duration;
	};

	const generateAudioOnDemand = async () => {
		if (!book || isGeneratingAudio) return;

		try {
			setIsGeneratingAudio(true);
			toast.loading('Generating audio narration...', { id: 'audio-gen' });

			const response = await api.books.generateAudio(book.id, {
				provider_id: voiceSettings?.tts?.default_provider || 'f5tts',
				voice_id: voiceSettings?.tts?.default_voice || 'archbishop_1',
				speed: voiceSettings?.tts?.speed || 1.0,
				pitch: voiceSettings?.tts?.pitch || 0,
				language: voiceSettings?.asr?.language || 'en'
			});

			const audioData = response.data;

			if (!audioData.audio_url || audioData.audio_url.length < 100) {
				throw new Error('Invalid audio URL received from server');
			}

			enableAutoPlay();

			const updatedBook = {
				...book,
				audioUrl: audioData.audio_url
			};

			setBook(updatedBook);

			toast.success(`Audio generated! Duration: ${Math.round(audioData.duration)}s`, { id: 'audio-gen' });

		} catch (error: any) {
			console.error('Failed to generate audio:', error);
			toast.error(error.response?.data?.detail || 'Failed to generate audio', { id: 'audio-gen' });
		} finally {
			setIsGeneratingAudio(false);
		}
	};

	const loadVoiceSettings = async () => {
		try {
			// Load user's global voice settings
			const response = await api.voiceSettings.getMySettings();
			setVoiceSettings(response.data);

			// Apply user's global TTS settings as defaults
			let appliedSettings: ChunkVoiceSettings = {
				provider_id: response.data?.tts?.default_provider || 'kokoro',
				voice_id: response.data?.tts?.default_voice || 'am_michael',
				speed: response.data?.tts?.speed || 1.0,
				language: 'en',
			};

			if (response.data?.tts?.speed) {
				changePlaybackRate(response.data.tts.speed);
			}

			// Load book-specific voice settings (these override global settings)
			try {
				const bookVoiceResponse = await api.books.getVoiceSettings(bookId!);
				const bookVoice = bookVoiceResponse.data?.voice_settings;

				if (bookVoice) {
					console.log('Loaded book voice settings:', bookVoice);

					// Apply book-specific TTS settings (override global)
					appliedSettings = {
						provider_id: bookVoice.tts_provider || appliedSettings.provider_id,
						voice_id: bookVoice.tts_voice || appliedSettings.voice_id,
						speed: bookVoice.tts_speed || appliedSettings.speed,
						language: bookVoice.asr_language || appliedSettings.language,
					};

					// Also update playback rate if specified
					if (bookVoice.tts_speed) {
						changePlaybackRate(bookVoice.tts_speed);
					}
				}
			} catch (bookError: any) {
				// Book voice settings not found is fine - just use user's global settings
				if (bookError.response?.status !== 404) {
					console.error('Failed to load book voice settings:', bookError);
				}
				console.log('No book-specific voice settings, using global:', appliedSettings);
			}

			// Apply the final settings to both state and chunk player
			console.log('Applying voice settings to chunk player:', appliedSettings);
			setChunkVoiceSettings(appliedSettings);
			chunkPlayer.setVoiceSettings(appliedSettings);

		} catch (error) {
			console.error('Failed to load voice settings:', error);
		}
	};

	const fetchBook = async () => {
		try {
			setIsLoadingBook(true);
			setBookLoadError(null);

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

			const mappedBook: BookPlayerData = {
				id: bookData.id,
				title: bookData.title,
				author: bookData.author,
				coverUrl: getBookCoverUrl(bookData.cover_url, bookData.title, bookData.author),
				chapters: bookData.chapters || [],
				audioUrl: audioUrl,
			};

			setBook(mappedBook);
			// Set loading to false immediately - don't wait for image to load
			// The image will show its own loading spinner if needed
			setIsLoadingBook(false);

			const chapterId = searchParams.get('chapter');
			if (chapterId && Array.isArray(mappedBook.chapters) && mappedBook.chapters.length > 0) {
				const chapter = mappedBook.chapters.find((ch) => ch.id === chapterId);
				if (chapter) {
					setCurrentChapter(chapter.order);
					if (chapter.startTime) {
						seek(chapter.startTime);
					}
				}
			}
		} catch (error: any) {
			console.error('Error fetching book:', error);
			const errorMessage = error.response?.status === 404
				? 'Book not found. It may have been removed or the link is incorrect.'
				: 'Failed to load book. Please try again.';

			setBookLoadError(errorMessage);
			setIsLoadingBook(false);
			toast.error(errorMessage);
		}
	};

	// Save chapter position to localStorage
	const saveChapterPosition = useCallback((chapterOrder: number, position: number) => {
		if (!bookId) return;
		try {
			const key = `inkwave_chapter_positions_${bookId}`;
			const positions = JSON.parse(localStorage.getItem(key) || '{}');
			positions[chapterOrder] = position;
			localStorage.setItem(key, JSON.stringify(positions));
		} catch (e) {
			console.error('Failed to save chapter position:', e);
		}
	}, [bookId]);

	// Get saved chapter position from localStorage
	const getSavedChapterPosition = useCallback((chapterOrder: number): number | null => {
		if (!bookId) return null;
		try {
			const key = `inkwave_chapter_positions_${bookId}`;
			const positions = JSON.parse(localStorage.getItem(key) || '{}');
			return positions[chapterOrder] || null;
		} catch (e) {
			return null;
		}
	}, [bookId]);

	// Save position periodically while playing
	useEffect(() => {
		if (isPlaying && currentChapter && currentTime > 0) {
			const timer = setTimeout(() => {
				saveChapterPosition(currentChapter, currentTime);
			}, 5000); // Save every 5 seconds
			return () => clearTimeout(timer);
		}
	}, [isPlaying, currentChapter, currentTime, saveChapterPosition]);

	const handleSelectChapter = (chapter: Chapter) => {
		// Save current chapter position before switching
		if (currentChapter && currentTime > 0) {
			saveChapterPosition(currentChapter, currentTime);
		}

		setCurrentChapter(chapter.order);

		// Check for saved position in this chapter
		const savedPosition = getSavedChapterPosition(chapter.order);
		const chapterStartTime = chapter.startTime || 0;

		// If not in chunk mode and no legacy audio URL, switch to chunk mode first
		if (!useChunkMode && !book?.audioUrl) {
			setUseChunkMode(true);
			// After switching to chunk mode, navigate to the chapter
			// Use a timeout to let chunk player initialize
			setTimeout(() => {
				const chapterIndex = chunkPlayer.chapterBoundaries.findIndex(
					(boundary) => boundary.chapter_title === chapter.title
				);
				if (chapterIndex >= 0) {
					chunkPlayer.goToChapter(chapterIndex);
				}
			}, 500);
			return;
		}

		// If using chunk mode, use chunk player's goToChapter
		if (useChunkMode && chunkPlayer.goToChapter) {
			// Find chapter index from chapter boundaries
			const chapterIndex = chunkPlayer.chapterBoundaries.findIndex(
				(boundary) => boundary.chapter_title === chapter.title
			);
			if (chapterIndex >= 0) {
				chunkPlayer.goToChapter(chapterIndex);
				// If there's a saved position, seek to it after a short delay
				if (savedPosition && savedPosition > chapterStartTime) {
					setTimeout(() => {
						seek(savedPosition);
						toast.success('Resumed from last position');
					}, 500);
				}
			} else {
				// Fallback: try to find by chunk index if chapter has startChunk
				const startChunk = (chapter as any).startChunk;
				if (startChunk !== undefined && chunkPlayer.goToChunk) {
					chunkPlayer.goToChunk(startChunk);
				}
			}
		} else if (chapter.startTime !== undefined) {
			// Legacy mode: use time-based seeking
			// Resume from saved position if available, otherwise start at chapter beginning
			if (savedPosition && savedPosition > chapterStartTime) {
				seek(savedPosition);
				toast.success('Resumed from last position');
			} else {
				seek(chapter.startTime);
			}
		}
	};

	// Quick bookmark a chapter start
	const handleBookmarkChapter = useCallback((chapter: Chapter) => {
		const position = chapter.startTime || 0;
		const note = `Chapter ${chapter.order}: ${chapter.title}`;
		handleAddBookmark({
			position,
			note,
			chapterTitle: chapter.title,
		});
		toast.success(`Bookmarked: ${chapter.title}`);
	}, [handleAddBookmark]);

	const handleShare = async () => {
		try {
			if (!bookId) {
				toast.error('Book ID not found');
				return;
			}

			const shareUrl = `${window.location.origin}/player/${bookId}`;
			console.log('Sharing URL:', shareUrl);

			// Try using the Web Share API if available (mobile)
			if (navigator.share) {
				try {
					await navigator.share({
						title: book?.title || 'InkWave Book',
						text: `Check out "${book?.title}" by ${book?.author} on InkWave`,
						url: shareUrl,
					});
					toast.success('Shared successfully!');
					return;
				} catch (err: any) {
					// User cancelled or share failed, fall through to clipboard
					if (err.name !== 'AbortError') {
						console.error('Share failed:', err);
					} else {
						// User cancelled, don't show error
						return;
					}
				}
			}

			// Fallback to clipboard API
			if (navigator.clipboard && navigator.clipboard.writeText) {
				await navigator.clipboard.writeText(shareUrl);
				toast.success('Link copied to clipboard!');
			} else {
				// Fallback for browsers without clipboard API
				const textArea = document.createElement('textarea');
				textArea.value = shareUrl;
				textArea.style.position = 'fixed';
				textArea.style.opacity = '0';
				document.body.appendChild(textArea);
				textArea.select();
				try {
					document.execCommand('copy');
					toast.success('Link copied to clipboard!');
				} catch (fallbackErr) {
					console.error('Fallback copy failed:', fallbackErr);
					toast.error('Failed to copy link. Please copy manually: ' + shareUrl);
				}
				document.body.removeChild(textArea);
			}
		} catch (error) {
			console.error('Failed to share:', error);
			toast.error('Failed to copy link. Please try again.');
		}
	};

	const handleVoiceQA = async () => {
		try {
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

	const handleClearConversations = () => {
		if (window.confirm('Are you sure you want to clear all conversations?')) {
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

	const formatTime = (seconds: number) => {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	};

	const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

	// Loading state
	if (isLoadingBook) {
		return (
			<div className="flex items-center justify-center min-h-screen bg-gray-950">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
					<p className="text-gray-400">Loading player...</p>
				</div>
			</div>
		);
	}

	// Error state
	if (bookLoadError || !book) {
		return (
			<div className="flex items-center justify-center min-h-screen bg-gray-950">
				<div className="text-center max-w-md px-4">
					<div className="mb-6">
						<svg
							className="w-16 h-16 mx-auto text-red-500 mb-4"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth={2}
								d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
						<h2 className="text-2xl font-bold text-white mb-2">Failed to Load Book</h2>
						<p className="text-gray-400 mb-6">
							{bookLoadError || 'The book you\'re looking for could not be found.'}
						</p>
					</div>
					<div className="space-y-3">
						<button
							onClick={() => navigate('/all-books')}
							className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
						>
							Browse All Books
						</button>
						<button
							onClick={() => navigate(-1)}
							className="w-full px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
						>
							Go Back
						</button>
					</div>
				</div>
			</div>
		);
	}

	const currentChapterData = Array.isArray(book.chapters)
		? book.chapters.find((ch) => ch.order === currentChapter)
		: undefined;

	return (
		<div className="min-h-screen bg-gradient-to-br from-gray-950 via-purple-950/20 to-gray-950 flex flex-col">
			{/* Top Header - Minimal */}
			<div className="absolute top-0 left-0 right-0 z-20 p-6">
				<div className="flex items-center justify-between max-w-6xl mx-auto">
					<button
						onClick={() => navigate(-1)}
						className="p-2 bg-gray-900/60 backdrop-blur-md hover:bg-gray-800/80 rounded-full text-gray-300 hover:text-white transition-all"
					>
						<ChevronLeft className="h-6 w-6" />
					</button>

					<div className="flex items-center gap-2">
						{/* Desktop only controls */}
						<div className="hidden sm:flex items-center gap-2">
							<ConversationDrawer
								conversations={conversations}
								onClear={handleClearConversations}
								onExport={handleExportConversations}
							/>
							{/* Sleep Timer - Libby-inspired */}
							{(book?.audioUrl || useChunkMode) && !error && (
								<SleepTimer
									isPlaying={isPlaying}
									onPause={pause}
									currentTime={currentTime}
									duration={duration}
									chapterEndTime={getCurrentChapterEndTime()}
								/>
							)}
							{/* Bookmark Manager - Libby-inspired */}
							<BookmarkManager
								bookId={bookId!}
								currentTime={currentTime}
								currentChapterTitle={currentChapterData?.title}
								bookmarks={bookmarks}
								onAddBookmark={handleAddBookmark}
								onUpdateBookmark={handleUpdateBookmark}
								onDeleteBookmark={handleDeleteBookmark}
								onSeekToBookmark={handleSeekToBookmark}
							/>
						</div>
						{/* Always visible controls */}
						<div className="flex items-center gap-2">
							{/* Chapter Navigation - visible on all screens */}
							<ChapterNav
								chapters={book.chapters}
								currentChapter={currentChapter}
								currentTime={currentTime}
								totalDuration={duration}
								onSelectChapter={handleSelectChapter}
								onBookmarkChapter={handleBookmarkChapter}
							/>
							{/* Add to Library button */}
							<button
								onClick={async () => {
									try {
										// TODO: Implement add to library API call
										toast.success('Added to your library!');
									} catch (error) {
										toast.error('Failed to add to library');
									}
								}}
								className="p-2 bg-gray-900/60 backdrop-blur-md hover:bg-gray-800/80 rounded-full text-gray-300 hover:text-white transition-all"
								title="Add to Library"
							>
								<Library className="h-5 w-5" />
							</button>
							{/* Share button with social media options */}
							<div className="relative">
								<SocialShareButtons
									bookTitle={book?.title || ''}
									bookAuthor={book?.author || ''}
									bookId={bookId || ''}
									bookCover={book?.coverUrl}
								/>
							</div>
							{/* Buy Credits button */}
							<BuyCreditsButton compact />
							{/* Settings button */}
							<button
								onClick={() => navigate('/voice-settings')}
								className="p-2 bg-gray-900/60 backdrop-blur-md hover:bg-gray-800/80 rounded-full text-gray-300 hover:text-white transition-all"
							>
								<Settings className="h-5 w-5" />
							</button>
						</div>
					</div>
				</div>
			</div>

			{/* Main Content - Centered */}
			<div className="flex-1 flex items-center justify-center px-6 py-20">
				<div className="w-full max-w-2xl">
					<motion.div
						initial={{ opacity: 0, y: 30 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ duration: 0.6, ease: "easeOut" }}
						className="space-y-8"
					>

						{/* Book Cover - Large and Centered with Swipe Support */}
						<div className="flex justify-center">
							<motion.div
								className="relative group"
								whileHover={{ scale: 1.02 }}
								transition={{ duration: 0.3 }}
								onTouchStart={handleTouchStart}
								onTouchEnd={handleTouchEnd}
								animate={{
									x: swipeDirection === 'left' ? -20 : swipeDirection === 'right' ? 20 : 0,
								}}
							>
								<div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-pink-500/20 blur-3xl rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
								<div className="relative w-80 h-80 sm:w-96 sm:h-96 rounded-3xl shadow-2xl ring-1 ring-white/10 overflow-hidden bg-gray-900/50">
									<img
										src={book.coverUrl}
										alt={book.title}
										className="w-full h-full object-cover select-none"
										draggable={false}
									/>

									{/* Seek feedback overlay */}
									<AnimatePresence>
										{seekFeedback?.show && (
											<motion.div
												initial={{ opacity: 0, scale: 0.8 }}
												animate={{ opacity: 1, scale: 1 }}
												exit={{ opacity: 0, scale: 0.8 }}
												transition={{ duration: 0.2 }}
												className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-3xl pointer-events-none"
											>
												<div className="text-center">
													<div className={`text-6xl font-bold mb-2 ${seekFeedback.seconds > 0 ? 'text-green-400' : 'text-orange-400'}`}>
														{seekFeedback.seconds > 0 ? '+' : ''}{seekFeedback.seconds}s
													</div>
													<div className="text-sm text-white/80">
														{seekFeedback.seconds > 0 ? 'Forward' : 'Backward'}
													</div>
												</div>
											</motion.div>
										)}
									</AnimatePresence>

									{/* Swipe hint overlay (shows on first load or idle) */}
									{!seekFeedback?.show && (
										<div className="absolute bottom-3 left-1/2 -translate-x-1/2 text-xs text-white/50 bg-black/30 px-3 py-1 rounded-full backdrop-blur-sm pointer-events-none sm:hidden">
											← Swipe to seek →
										</div>
									)}
								</div>
								{/* Loading Spinner Overlay on Cover */}
								{isLoading && (
									<div className="absolute inset-0 bg-black/60 rounded-3xl flex items-center justify-center">
										<div className="animate-spin rounded-full h-16 w-16 border-4 border-purple-500 border-t-transparent" />
									</div>
								)}
								{/* Playback indicator overlay */}
								{isPlaying && !isLoading && (
									<motion.div
										initial={{ opacity: 0 }}
										animate={{ opacity: 1 }}
										className="absolute inset-0 bg-gradient-to-t from-purple-900/40 to-transparent rounded-3xl flex items-end justify-center pb-6 pointer-events-none"
									>
										<div className="flex gap-1">
											{[...Array(5)].map((_, i) => (
												<motion.div
													key={i}
													className="w-1 bg-white rounded-full"
													animate={{
														height: ['8px', '24px', '8px'],
													}}
													transition={{
														duration: 0.8,
														repeat: Infinity,
														delay: i * 0.1,
													}}
												/>
											))}
										</div>
									</motion.div>
								)}
							</motion.div>
						</div>

						{/* Book Info */}
						<div className="text-center space-y-2 px-4">
							<h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
								{book.title}
							</h1>
							<p className="text-lg text-gray-400">
								{book.author}
							</p>
							{/* Enhanced Chapter Display */}
							{currentChapterData && book.chapters && Array.isArray(book.chapters) && book.chapters.length > 0 && (
								<div className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 border border-purple-500/20 rounded-full">
									<span className="text-xs font-medium text-purple-300 bg-purple-500/20 px-2 py-0.5 rounded-full">
										{currentChapter} / {book.chapters.length}
									</span>
									<span className="text-sm font-medium text-purple-300 truncate max-w-[200px] sm:max-w-[300px]">
										{currentChapterData.title}
									</span>
								</div>
							)}
						</div>

						{/* Progress Bar - Elegant with Chapter Markers */}
						{(book?.audioUrl || useChunkMode) && !error && duration > 0 && (
							<div className="space-y-3 px-4">
								<div className="relative">
									{/* Background track */}
									<div className="h-1.5 bg-gray-800/50 rounded-full overflow-hidden backdrop-blur-sm">
										{/* Progress fill with gradient */}
										<motion.div
											className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-purple-500 rounded-full relative"
											style={{ width: `${progress}%` }}
											initial={{ width: 0 }}
											animate={{ width: `${progress}%` }}
										>
											{/* Glow effect */}
											<div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg shadow-purple-500/50" />
										</motion.div>
									</div>

									{/* Chapter markers */}
									{book.chapters && Array.isArray(book.chapters) && book.chapters.length > 1 && (
										<div className="absolute inset-0 pointer-events-none">
											{book.chapters.slice(1).map((chapter) => {
												const markerPosition = chapter.startTime
													? (chapter.startTime / duration) * 100
													: 0;
												if (markerPosition <= 0 || markerPosition >= 100) return null;
												return (
													<div
														key={chapter.id}
														className="absolute top-1/2 -translate-y-1/2 w-0.5 h-3 bg-white/30 rounded-full"
														style={{ left: `${markerPosition}%` }}
														title={chapter.title}
													/>
												);
											})}
										</div>
									)}

									{/* Clickable seek overlay */}
									<div
										className="absolute inset-0 cursor-pointer z-10"
										onClick={async (e) => {
											e.stopPropagation();
											const rect = e.currentTarget.getBoundingClientRect();
											const x = e.clientX - rect.left;
											const percentage = Math.max(0, Math.min(1, x / rect.width));
											const targetTime = percentage * duration;
											console.log('[ProgressBar] Seeking to:', { percentage, targetTime, duration });
											await seek(targetTime);
										}}
										onMouseMove={(e) => {
											// Optional: Add hover effect or preview
											const rect = e.currentTarget.getBoundingClientRect();
											const x = e.clientX - rect.left;
											const percentage = Math.max(0, Math.min(1, x / rect.width));
											// Could add a tooltip showing the target time here
										}}
									/>
								</div>

								{/* Time labels */}
								<div className="flex items-center justify-between text-xs text-gray-500">
									<span>{formatTime(currentTime)}</span>
									<span>{formatTime(duration)}</span>
								</div>

								{/* Session Cost Display - Real-time billing */}
								{useChunkMode && sessionId && (
									<div className="flex items-center justify-between text-xs mt-2 px-1">
										<div className="flex items-center gap-1.5">
											<span className={`inline-block w-1.5 h-1.5 rounded-full ${lastBillingSuccess ? 'bg-green-500' : 'bg-red-500'}`} />
											<span className="text-purple-400">
												Session: {sessionCostCredits.toFixed(1)} credits
												<span className="text-gray-500"> (~GH₵{sessionCostCurrency})</span>
											</span>
										</div>
										<span className="text-gray-400">
											Balance: GH₵{balanceCurrency}
										</span>
									</div>
								)}
							</div>
						)}

						{/* Playback Controls */}
						{!book?.audioUrl && !useChunkMode && !isGeneratingAudio ? (
							<div className="space-y-4 px-4">
								{/* Button Container - Centered */}
								<div className="flex items-center justify-center">
									<motion.button
										whileHover={{ scale: 1.05 }}
										whileTap={{ scale: 0.95 }}
										onClick={() => {
											setUseChunkMode(true);
											setShouldAutoPlayChunk(true);

											// If a chapter is selected (not default chapter 1), navigate to it
											if (book?.chapters && currentChapter > 1) {
												setShouldNavigateToChapter(currentChapter);
											}
										}}
										className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-full text-white font-semibold shadow-lg shadow-green-500/30 transition-all"
									>
										Start Listening
									</motion.button>
								</div>
							</div>
						) : isGeneratingAudio ? (
							<div className="text-center space-y-4 px-4">
								<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto" />
								<p className="text-gray-400">Generating narration...</p>
							</div>
						) : error ? (
							<div className="text-center space-y-4 px-4">
								<p className="text-red-400">{error}</p>
								<motion.button
									whileHover={{ scale: 1.05 }}
									whileTap={{ scale: 0.95 }}
									onClick={generateAudioOnDemand}
									className="px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full text-white font-semibold"
								>
									Regenerate Audio
								</motion.button>
							</div>
						) : (
							<div className="space-y-6 px-4">
								{/* Main Controls */}
								<div className="flex items-center justify-center gap-2 sm:gap-4">
									{/* Previous Chapter */}
									{book.chapters && Array.isArray(book.chapters) && book.chapters.length > 1 && (
										<motion.button
											whileHover={{ scale: 1.1 }}
											whileTap={{ scale: 0.9 }}
											onClick={goToPreviousChapter}
											disabled={isFirstChapter}
											className="p-2 sm:p-3 bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
											title="Previous Chapter"
										>
											<SkipBack className="h-5 w-5 sm:h-6 sm:w-6" />
										</motion.button>
									)}

									{/* 15 Second Rewind */}
									<motion.button
										whileHover={{ scale: 1.1 }}
										whileTap={{ scale: 0.9 }}
										onClick={skip15Backward}
										className="relative p-3 bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-white transition-all group"
									>
										<RotateCcw className="h-6 w-6" />
										<span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs text-gray-500 group-hover:text-purple-400 transition-colors">
											15
										</span>
									</motion.button>

									{/* Play/Pause - Large - Always Enabled */}
									<motion.button
										whileHover={{ scale: 1.05 }}
										whileTap={{ scale: 0.95 }}
										onClick={togglePlay}
										className="p-6 bg-gradient-to-br from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-full text-white shadow-2xl shadow-purple-500/40 transition-all"
									>
										{isPlaying ? (
											<Pause className="h-8 w-8 fill-white" />
										) : (
											<Play className="h-8 w-8 fill-white ml-0.5" />
										)}
									</motion.button>

									{/* 15 Second Forward */}
									<motion.button
										whileHover={{ scale: 1.1 }}
										whileTap={{ scale: 0.9 }}
										onClick={skip15Forward}
										className="relative p-3 bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-white transition-all group"
									>
										<RotateCw className="h-6 w-6" />
										<span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs text-gray-500 group-hover:text-purple-400 transition-colors">
											15
										</span>
									</motion.button>

									{/* Next Chapter */}
									{book.chapters && Array.isArray(book.chapters) && book.chapters.length > 1 && (
										<motion.button
											whileHover={{ scale: 1.1 }}
											whileTap={{ scale: 0.9 }}
											onClick={goToNextChapter}
											disabled={isLastChapter}
											className="p-2 sm:p-3 bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
											title="Next Chapter"
										>
											<SkipForward className="h-5 w-5 sm:h-6 sm:w-6" />
										</motion.button>
									)}
								</div>

								{/* Secondary Controls */}
								<div className="flex items-center justify-between">
									{/* Playback Speed */}
									<div className="flex items-center gap-2">
										<button
											onClick={() => {
												const speeds = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];
												const currentIndex = speeds.indexOf(playbackRate);
												const nextIndex = (currentIndex + 1) % speeds.length;
												changePlaybackRate(speeds[nextIndex]);
											}}
											className="px-3 py-1.5 bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 rounded-full text-sm text-gray-300 hover:text-white transition-all"
										>
											{playbackRate}x
										</button>
									</div>

									{/* Voice Settings (only in chunk mode) */}
									{useChunkMode && (
										<VoiceSettingsDropdown
											settings={chunkVoiceSettings}
											onChange={(newSettings) => {
												setChunkVoiceSettings(newSettings);
												chunkPlayer.setVoiceSettings(newSettings);
											}}
											className="bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80"
										/>
									)}

									{/* Text View Toggle (only in chunk mode) */}
									{useChunkMode && (
										<button
											onClick={() => setShowTextView(!showTextView)}
											className={`p-2 rounded-full transition-all ${showTextView
												? 'bg-purple-600 text-white'
												: 'bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 text-gray-300 hover:text-white'
												}`}
											title="Show/Hide Text"
										>
											<BookOpen className="h-5 w-5" />
										</button>
									)}

									{/* Volume */}
									<div className="relative">
										<button
											onClick={() => setShowVolumeSlider(!showVolumeSlider)}
											className="p-2 bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-white transition-all"
										>
											<Volume2 className="h-5 w-5" />
										</button>

										{/* Volume Slider */}
										{showVolumeSlider && (
											<>
												{/* Backdrop to close on click outside */}
												<div
													className="fixed inset-0 z-40"
													onClick={() => setShowVolumeSlider(false)}
												/>
												<div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800/95 backdrop-blur-md rounded-xl p-4 shadow-2xl border border-gray-700/50 z-50">
													<div className="flex flex-col items-center gap-3">
														<span className="text-xs text-gray-400 font-medium">Volume</span>
														<div className="relative h-28 flex items-center">
															<input
																type="range"
																min="0"
																max="1"
																step="0.01"
																value={chunkPlayer.volume}
																onChange={(e) => chunkPlayer.changeVolume(parseFloat(e.target.value))}
																orient="vertical"
																className="volume-slider w-2 h-24 appearance-none bg-gray-700 rounded-full cursor-pointer"
																style={{
																	writingMode: 'vertical-lr',
																	direction: 'rtl',
																}}
															/>
														</div>
														<span className="text-sm text-white font-semibold">
															{Math.round(chunkPlayer.volume * 100)}%
														</span>
													</div>
												</div>
											</>
										)}
									</div>

									{/* Share - Hidden on mobile (moved to header) */}
									<button
										onClick={handleShare}
										className="hidden sm:block p-2 bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-white transition-all"
									>
										<Share2 className="h-5 w-5" />
									</button>
								</div>

								{/* Chunk Mode Indicator */}
								{useChunkMode && (
									<div className="flex items-center justify-center gap-2 text-xs text-gray-500">
										<span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
										<span>
											Chunk {chunkPlayer.currentChunkIndex + 1} of {chunkPlayer.totalChunks}
											{chunkPlayer.currentChapter && ` • ${chunkPlayer.currentChapter.title}`}
										</span>
									</div>
								)}
							</div>
						)}

						{/* Voice Q&A Button - Only show for admin users */}
						{canAccessVoiceQA && !isProcessing && (book?.audioUrl || useChunkMode) && !error && (
							<div className="flex justify-center pt-4 px-4">
								<motion.button
									whileHover={{ scale: 1.05 }}
									whileTap={{ scale: 0.95 }}
									onClick={handleVoiceQA}
									className="flex items-center gap-3 px-6 py-3 bg-gray-800/60 backdrop-blur-md hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-white border border-purple-500/20 hover:border-purple-500/40 transition-all"
								>
									<Mic className="h-5 w-5" />
									<span>Ask About This Book</span>
								</motion.button>
							</div>
						)}

						{/* Latest AI Response */}
						<AnimatePresence>
							{latestResponse && (
								<motion.div
									initial={{ opacity: 0, y: 20 }}
									animate={{ opacity: 1, y: 0 }}
									exit={{ opacity: 0, y: -20 }}
									className="px-4"
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
								className="text-center space-y-4 px-4"
							>
								<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto" />
								<p className="text-gray-400">Processing your question...</p>
							</motion.div>
						)}

						{/* Book Text View */}
						{useChunkMode && bookId && (
							<BookTextView
								isOpen={showTextView}
								onClose={() => setShowTextView(false)}
								bookId={bookId}
								currentChunkIndex={chunkPlayer.currentChunkIndex}
								currentPositionInChunk={chunkPlayer.currentTime}
								chunkDuration={chunkPlayer.chunkDurations[chunkPlayer.currentChunkIndex]}
								totalChunks={chunkPlayer.totalChunks}
							/>
						)}

						{/* Featured Book - Archbishop Duncan-Williams */}
						<motion.div
							initial={{ opacity: 0, y: 20 }}
							animate={{ opacity: 1, y: 0 }}
							transition={{ delay: 0.5 }}
							className="mt-12 px-4"
						>
							<div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-md rounded-2xl p-6 border border-purple-500/20 shadow-xl">
								<h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
									<span className="text-purple-400">✨</span>
									Featured Book
								</h3>

								<div className="flex gap-4">
									{/* Book Cover Thumbnail */}
									<div className="flex-shrink-0">
										<div className="w-24 h-32 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg shadow-lg flex items-center justify-center text-white text-xs font-bold p-2 text-center">
											Archbishop Duncan-Williams
										</div>
									</div>

									{/* Book Details */}
									<div className="flex-1 space-y-2">
										<h4 className="text-xl font-bold text-white">
											You Are Destined to Succeed
										</h4>
										<p className="text-sm text-purple-400">
											by Archbishop Nicholas Duncan-Williams
										</p>
										<p className="text-sm text-gray-400 line-clamp-3">
											A powerful message of hope and destiny from one of Africa's most influential spiritual leaders.
											Discover how to unlock your God-given potential and walk in your divine purpose.
											This transformative teaching will inspire you to rise above limitations and embrace the success that awaits you.
										</p>
										<div className="flex items-center gap-4 pt-2">
											<span className="text-xs text-gray-500 bg-gray-800/50 px-3 py-1 rounded-full">
												Inspirational
											</span>
											<span className="text-xs text-gray-500 bg-gray-800/50 px-3 py-1 rounded-full">
												Leadership
											</span>
										</div>
									</div>
								</div>

								{/* Note about Sample */}
								<div className="mt-4 pt-4 border-t border-gray-700/50">
									<p className="text-xs text-gray-500 text-center">
										📖 Sample book for demonstration purposes. Full ebook content is not included.
									</p>
								</div>
							</div>
						</motion.div>
					</motion.div>
				</div>
			</div>

			{/* Seamless Conversation Modal */}
			<AnimatePresence>
				{showSeamlessChat && interactionId && (
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
							<SeamlessConversation
								bookId={bookId!}
								interactionId={interactionId}
								onClose={() => setShowSeamlessChat(false)}
							/>
						</motion.div>
					</motion.div>
				)}
			</AnimatePresence>
		</div>
	);
}
