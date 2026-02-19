/**
 * AudiobookPlayerPage
 *
 * New Libby-inspired audiobook player page with:
 * - OpenAI TTS voices (alloy, echo, fable, onyx, nova, shimmer)
 * - Book-level progress bar
 * - Chunk scrubber visualization
 * - Progressive audio caching
 * - Voice Q&A integration
 */

import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
	ChevronLeft,
	Mic,
	Bookmark,
	BookOpen,
	MessageCircle,
	Moon,
	Settings,
	X,
	Wallet,
} from 'lucide-react';
import { LibbyPlayer } from '../components/audiobook';
import TableOfContents from '../components/TableOfContents';
import SeamlessConversation from '../components/SeamlessConversation';
import ConversationDrawer, { Conversation } from '../components/ConversationDrawer';
import SleepTimer from '../components/SleepTimer';
import BookmarkManager from '../components/BookmarkManager';
import BuyCreditsButton from '../components/BuyCreditsButton';
import { api } from '../lib/api';
import { audioCache } from '../lib/audioCache';
import { generatePlaceholderCover } from '../lib/bookCoverUtils';
import toast from 'react-hot-toast';

interface BookData {
	id: string;
	title: string;
	author: string;
	coverUrl: string;
	totalChunks: number;
	contentStartChunk?: number; // First chunk with actual content (skips TOC/copyright)
	chapters: Array<{
		id: string;
		title: string;
		startChunk: number;
		endChunk: number;
	}>;
}

interface UserPreferences {
	provider: string;
	voiceId: string;
	speed: number;
	lastChunk: number;
	lastPosition: number;
}

export default function AudiobookPlayerPage() {
	useEffect(() => {
		document.title = 'Audiobook Player - InkWave';
	}, []);

	const { bookId } = useParams<{ bookId: string }>();
	const navigate = useNavigate();

	// Book data
	const [book, setBook] = useState<BookData | null>(null);
	const [isLoading, setIsLoading] = useState(true);

	// User preferences
	const [preferences, setPreferences] = useState<UserPreferences>({
		provider: 'openai_tts',
		voiceId: 'alloy',
		speed: 1.0,
		lastChunk: 0,
		lastPosition: 0,
	});

	// UI state
	const [showTOC, setShowTOC] = useState(false);
	const [showChat, setShowChat] = useState(false);
	const [showSleepTimer, setShowSleepTimer] = useState(false);
	const [showBookmarks, setShowBookmarks] = useState(false);
	const [isBookmarked, setIsBookmarked] = useState(false);

	// Q&A state
	const [conversations, setConversations] = useState<Conversation[]>([]);
	const [interactionId, setInteractionId] = useState<string | null>(null);

	// Fetch book data on mount
	useEffect(() => {
		if (bookId) {
			fetchBookData();
			fetchUserPreferences();
			initAudioCache();
		}
	}, [bookId]);

	const initAudioCache = async () => {
		try {
			await audioCache.init();
			const stats = await audioCache.getStats();
			console.log('Audio cache initialized:', stats);
		} catch (error) {
			console.error('Failed to initialize audio cache:', error);
		}
	};

	const fetchBookData = async () => {
		setIsLoading(true);
		try {
			const response = await api.get(`/books/${bookId}`);
			const bookData = {
				id: response.data.book_id,
				title: response.data.title,
				author: response.data.author,
				coverUrl: response.data.cover_url,
				totalChunks: response.data.total_chunks || 0,
				contentStartChunk: response.data.content_start_chunk || 0,
				chapters: (response.data.chapters || []).map((ch: any) => ({
					id: ch.id,
					title: ch.title,
					startChunk: ch.start_chunk,
					endChunk: ch.end_chunk,
				})),
			};
			setBook(bookData);

			// If this is a new book (no saved preferences), start from content_start_chunk
			const stored = localStorage.getItem(`inkwave_prefs_${bookId}`);
			if (!stored && bookData.contentStartChunk > 0) {
				setPreferences(prev => ({
					...prev,
					lastChunk: bookData.contentStartChunk,
					lastPosition: 0,
				}));
			}
		} catch (error) {
			console.error('Failed to fetch book:', error);
			toast.error('Failed to load book');
		} finally {
			setIsLoading(false);
		}
	};

	const fetchUserPreferences = async () => {
		try {
			// Try to get from localStorage first
			const stored = localStorage.getItem(`inkwave_prefs_${bookId}`);
			if (stored) {
				setPreferences(JSON.parse(stored));
				return;
			}

			// Otherwise fetch from API
			const response = await api.get(`/voice-settings`);
			const settings = response.data;

			setPreferences({
				provider: settings?.tts?.default_provider || 'openai_tts',
				voiceId: settings?.tts?.voice_id || 'alloy',
				speed: settings?.tts?.speed || 1.0,
				lastChunk: 0,
				lastPosition: 0,
			});
		} catch (error) {
			console.log('Using default preferences');
		}
	};

	const savePreferences = useCallback(
		(updates: Partial<UserPreferences>) => {
			const newPrefs = { ...preferences, ...updates };
			setPreferences(newPrefs);
			localStorage.setItem(`inkwave_prefs_${bookId}`, JSON.stringify(newPrefs));
		},
		[preferences, bookId]
	);

	const handleProviderChange = useCallback(
		(provider: string) => {
			savePreferences({ provider });
		},
		[savePreferences]
	);

	const handleVoiceChange = useCallback(
		(voiceId: string) => {
			savePreferences({ voiceId });
		},
		[savePreferences]
	);

	const handleSpeedChange = useCallback(
		(speed: number) => {
			savePreferences({ speed });
		},
		[savePreferences]
	);

	const handleProgressUpdate = useCallback(
		async (chunk: number, position: number, totalTimeMinutes: number) => {
			savePreferences({ lastChunk: chunk, lastPosition: position });

			// Also save to backend with time tracking
			try {
				await api.post(`/audiobook/books/${bookId}/progress`, {
					current_chunk: chunk,
					current_position: position,
					total_time_minutes: totalTimeMinutes
				});
			} catch (error) {
				// Log error for debugging but don't interrupt playback
				console.error('Failed to update progress:', error);
			}
		},
		[bookId, savePreferences]
	);

	const toggleBookmark = async () => {
		setIsBookmarked(!isBookmarked);
		toast.success(isBookmarked ? 'Bookmark removed' : 'Bookmark added');
	};

	const handleChapterSelect = (chapterIndex: number) => {
		// Find the starting chunk for this chapter
		if (book?.chapters && book.chapters[chapterIndex]) {
			const chapter = book.chapters[chapterIndex];
			savePreferences({
				lastChunk: chapter.startChunk,
				lastPosition: 0,
			});
		}
		setShowTOC(false);
	};

	if (isLoading) {
		return (
			<div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-black flex items-center justify-center">
				<div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500" />
			</div>
		);
	}

	if (!book) {
		return (
			<div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-black flex flex-col items-center justify-center text-white">
				<p className="text-xl mb-4">Book not found</p>
				<button
					onClick={() => navigate('/library')}
					className="px-4 py-2 bg-purple-500 rounded-lg hover:bg-purple-600 transition"
				>
					Back to Library
				</button>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-black text-white">
			{/* Header */}
			<header className="fixed top-0 left-0 right-0 z-40 bg-gray-900/90 backdrop-blur-sm border-b border-gray-800">
				<div className="flex items-center justify-between px-4 py-3">
					<button
						onClick={() => navigate(-1)}
						className="p-2 hover:bg-gray-800 rounded-full transition"
					>
						<ChevronLeft className="w-6 h-6" />
					</button>

					<h1 className="text-lg font-semibold truncate max-w-[200px]">
						{book.title}
					</h1>

					<div className="flex items-center gap-2">
						<button
							onClick={toggleBookmark}
							className={`p-2 rounded-full transition ${isBookmarked
									? 'bg-purple-500/20 text-purple-400'
									: 'hover:bg-gray-800'
								}`}
						>
							<Bookmark
								className={`w-5 h-5 ${isBookmarked ? 'fill-current' : ''}`}
							/>
						</button>
						<button
							onClick={() => setShowTOC(true)}
							className="p-2 hover:bg-gray-800 rounded-full transition"
						>
							<BookOpen className="w-5 h-5" />
						</button>
					</div>
				</div>
			</header>

			{/* Main Content */}
			<main className="pt-16 pb-24 px-4">
				{/* Cover Art */}
				<div className="flex justify-center my-6 sm:my-8">
					{book.coverUrl && (
						<motion.img
							src={book.coverUrl}
							alt={book.title}
							className="w-36 sm:w-44 md:w-48 h-auto aspect-[2/3] object-cover rounded-xl shadow-2xl shadow-purple-500/20"
							initial={{ opacity: 0, y: 20 }}
							animate={{ opacity: 1, y: 0 }}
							transition={{ duration: 0.5 }}
							onError={(e) => {
								e.currentTarget.src = generatePlaceholderCover(book.title, book.author);
								e.currentTarget.onerror = null;
							}}
						/>
					)}
				</div>

				{/* Book Info */}
				<div className="text-center mb-6 sm:mb-8">
					<h2 className="text-xl sm:text-2xl font-bold mb-2">{book.title}</h2>
					<p className="text-sm sm:text-base text-gray-400">{book.author}</p>
				</div>

				{/* Libby Player */}
				<LibbyPlayer
					bookId={book.id}
					bookTitle={book.title}
					coverUrl={book.coverUrl}
					provider={preferences.provider}
					voiceId={preferences.voiceId}
					speed={preferences.speed}
					onProviderChange={handleProviderChange}
					onVoiceChange={handleVoiceChange}
					onSpeedChange={handleSpeedChange}
					onProgressUpdate={handleProgressUpdate}
					initialChunk={preferences.lastChunk}
					initialPosition={preferences.lastPosition}
					chapters={book.chapters.map((ch, idx) => ({
						id: ch.id,
						title: ch.title,
						duration: Math.ceil((ch.endChunk - ch.startChunk) * 30 / 60), // Estimate minutes
						order: idx + 1,
						startTime: 0, // Will be calculated by player
						startChunk: ch.startChunk,
						endChunk: ch.endChunk,
					}))}
					onChapterSelect={handleChapterSelect}
				/>
			</main>

			{/* Bottom Action Bar */}
			<div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-gray-800 px-4 py-3 pb-safe">
				<div className="flex items-center justify-around">
					<button
						onClick={() => setShowSleepTimer(true)}
						className="flex flex-col items-center gap-1 text-gray-400 hover:text-white transition"
					>
						<Moon className="w-5 h-5" />
						<span className="text-[10px]">Sleep Timer</span>
					</button>

					<button
						onClick={() => setShowBookmarks(true)}
						className="flex flex-col items-center gap-1 text-gray-400 hover:text-white transition"
					>
						<Bookmark className="w-5 h-5" />
						<span className="text-[10px]">Bookmarks</span>
					</button>

					{/* Buy Credits Button */}
					<BuyCreditsButton iconOnly className="flex flex-col items-center gap-1" />

					<button
						onClick={() => setShowChat(true)}
						className="flex flex-col items-center gap-1 text-purple-400 hover:text-purple-300 transition"
					>
						<div className="relative">
							<MessageCircle className="w-6 h-6" />
							<Mic className="w-3 h-3 absolute -bottom-1 -right-1 bg-purple-500 rounded-full p-0.5" />
						</div>
						<span className="text-[10px]">Ask AI</span>
					</button>

					<button
						onClick={() => setShowTOC(true)}
						className="flex flex-col items-center gap-1 text-gray-400 hover:text-white transition"
					>
						<BookOpen className="w-5 h-5" />
						<span className="text-[10px]">Chapters</span>
					</button>
				</div>
			</div>

			{/* Table of Contents Drawer */}
			<AnimatePresence>
				{showTOC && (
					<motion.div
						initial={{ opacity: 0 }}
						animate={{ opacity: 1 }}
						exit={{ opacity: 0 }}
						className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
						onClick={() => setShowTOC(false)}
					>
						<motion.div
							initial={{ x: '100%' }}
							animate={{ x: 0 }}
							exit={{ x: '100%' }}
							transition={{ type: 'spring', damping: 25 }}
							className="absolute right-0 top-0 bottom-0 w-full max-w-xs sm:max-w-sm bg-gray-900 border-l border-gray-800"
							onClick={(e) => e.stopPropagation()}
						>
							<div className="flex items-center justify-between p-4 border-b border-gray-800">
								<h3 className="text-lg font-semibold">Chapters</h3>
								<button
									onClick={() => setShowTOC(false)}
									className="p-2 hover:bg-gray-800 rounded-full"
								>
									<X className="w-5 h-5" />
								</button>
							</div>
							<div className="p-4 overflow-y-auto max-h-[calc(100vh-80px)]">
								{book.chapters?.map((chapter, index) => (
									<button
										key={chapter.id}
										onClick={() => handleChapterSelect(index)}
										className="w-full text-left px-4 py-3 hover:bg-gray-800 rounded-lg transition mb-2"
									>
										<div className="text-sm font-medium text-white">
											{chapter.title}
										</div>
										<div className="text-xs text-gray-500">
											Chunks {chapter.startChunk + 1} - {chapter.endChunk + 1}
										</div>
									</button>
								))}
							</div>
						</motion.div>
					</motion.div>
				)}
			</AnimatePresence>

			{/* Voice Chat Drawer */}
			<AnimatePresence>
				{showChat && (
					<motion.div
						initial={{ opacity: 0 }}
						animate={{ opacity: 1 }}
						exit={{ opacity: 0 }}
						className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
						onClick={() => setShowChat(false)}
					>
						<motion.div
							initial={{ y: '100%' }}
							animate={{ y: 0 }}
							exit={{ y: '100%' }}
							transition={{ type: 'spring', damping: 25 }}
							className="absolute bottom-0 left-0 right-0 h-[70vh] bg-gray-900 rounded-t-3xl"
							onClick={(e) => e.stopPropagation()}
						>
							<div className="flex justify-center pt-3 pb-2">
								<div className="w-12 h-1 bg-gray-700 rounded-full" />
							</div>
							<div className="p-4">
								<SeamlessConversation
									bookId={book.id}
									currentChunkIndex={preferences.lastChunk}
									onClose={() => setShowChat(false)}
								/>
							</div>
						</motion.div>
					</motion.div>
				)}
			</AnimatePresence>

			{/* Sleep Timer Modal */}
			<AnimatePresence>
				{showSleepTimer && (
					<SleepTimer onClose={() => setShowSleepTimer(false)} />
				)}
			</AnimatePresence>

			{/* Bookmarks Modal */}
			<AnimatePresence>
				{showBookmarks && (
					<BookmarkManager
						bookId={book.id}
						onClose={() => setShowBookmarks(false)}
						onSelectBookmark={(chunk, position) => {
							savePreferences({ lastChunk: chunk, lastPosition: position });
							setShowBookmarks(false);
						}}
					/>
				)}
			</AnimatePresence>
		</div>
	);
}
