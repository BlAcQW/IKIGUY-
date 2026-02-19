/**
 * Application Constants
 */

export const APP_NAME = import.meta.env.VITE_APP_NAME || 'Inkwave';
export const FREE_TRIAL_CREDITS = Number(import.meta.env.VITE_FREE_TRIAL_CREDITS) || 200;

// Pricing
export const PRICING = {
  NARRATION_PER_MINUTE: 0.02, // $0.02 per minute
  VOICE_QA_AVERAGE: 0.04, // ~$0.04 per voice Q&A
  CREDITS_PER_DOLLAR: 100, // 100 credits = $1
};

// Top-up packages
export const TOPUP_PACKAGES = [
  { amount: 5, credits: 500, bonus: 0, popular: false },
  { amount: 10, credits: 1000, bonus: 0, popular: true },
  { amount: 25, credits: 2500, bonus: 100, popular: false },
  { amount: 50, credits: 5000, bonus: 300, popular: false },
];

// Playback speeds
export const PLAYBACK_SPEEDS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0];

// Reading levels
export const READING_LEVELS = ['beginner', 'intermediate', 'advanced'] as const;
export type ReadingLevel = typeof READING_LEVELS[number];

// Genres
export const GENRES = [
  'Fiction',
  'Non-Fiction',
  'Self-Help',
  'Business',
  'Biography',
  'Science',
  'History',
  'Philosophy',
  'Psychology',
  'Technology',
];

// Audio player settings
export const AUDIO = {
  SKIP_SECONDS: 15, // Skip forward/backward by 15 seconds
  AUTO_SAVE_INTERVAL: 30000, // Auto-save position every 30 seconds
  BUFFER_CHUNKS: 3, // Pre-load 3 chunks ahead
};

// Voice settings
export const VOICE = {
  MAX_RECORDING_DURATION: 60000, // 60 seconds max recording
  SILENCE_THRESHOLD: 3000, // 3 seconds of silence auto-stops recording
  MIN_RECORDING_DURATION: 500, // 500ms minimum recording
};

// Wallet settings
export const WALLET = {
  LOW_BALANCE_THRESHOLD: 100, // 100 credits = $1
  MIN_TOPUP: 5,
  MAX_TOPUP: 500,
};

// API endpoints (for reference)
export const ENDPOINTS = {
  SUPABASE: import.meta.env.VITE_SUPABASE_URL,
  API: import.meta.env.VITE_API_URL,
};
