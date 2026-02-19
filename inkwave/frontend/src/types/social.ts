/**
 * TypeScript types for social functionality
 * Matches backend Pydantic models from social.py and leaderboard.py
 */

// ============================================================================
// USER TYPES
// ============================================================================

export interface SocialUser {
  user_id: string;
  username?: string;
  display_name?: string;
  avatar_url?: string;
  bio?: string;
  followers_count: number;
  following_count: number;
  listening_stats?: {
    total_listening_hours: number;
    books_completed: number;
  };
  is_following: boolean;
}

export interface UserListResponse {
  users: SocialUser[];
  total: number;
  page: number;
  per_page: number;
}

// ============================================================================
// FOLLOW/UNFOLLOW TYPES
// ============================================================================

export interface FollowResponse {
  success: boolean;
  message: string;
  following_user_id: string;
}

export interface UnfollowResponse {
  message: string;
}

// ============================================================================
// LEADERBOARD TYPES
// ============================================================================

export type LeaderboardPeriod = 'week' | 'month' | 'all_time';

export type DisplayMode = 'full_profile' | 'anonymous' | 'opt_out';

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string | null;
  display_name: string | null;
  avatar_url: string | null;
  listening_hours: number;
  display_mode: DisplayMode;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  period: LeaderboardPeriod;
  total: number;
}

export interface UserRankResponse {
  rank: number | null;
  period: LeaderboardPeriod;
  on_leaderboard: boolean;
}

// ============================================================================
// ACTIVITY FEED TYPES
// ============================================================================

export type ActivityType = 'started_book' | 'completed_book' | 'milestone' | 'new_follower';

export interface ReadingActivity {
  activity_id: string;
  user_id: string;
  user_display_name: string | null;
  user_avatar_url: string | null;
  activity_type: ActivityType;
  book_id?: string;
  book_title?: string;
  book_cover_url?: string;
  progress?: number;
  created_at: string;
}

export interface ActivityFeedResponse {
  activities: ReadingActivity[];
  count: number;
}

// ============================================================================
// BLOCKING & REPORTING TYPES
// ============================================================================

export type ReportType =
  | 'spam'
  | 'harassment'
  | 'inappropriate_content'
  | 'impersonation'
  | 'other';

export interface ReportUserRequest {
  report_type: ReportType;
  description: string;
  evidence_urls?: string[];
}

export interface ReportUserResponse {
  success: boolean;
  message: string;
  report_id: string;
}

export interface BlockResponse {
  success: boolean;
  message: string;
}

// ============================================================================
// FOLLOW SUGGESTIONS TYPES
// ============================================================================

export interface FollowSuggestion {
  user_id: string;
  username?: string;
  display_name?: string;
  avatar_url?: string;
  reason: string; // e.g., "Reads similar books", "Popular listener"
  followers_count: number;
  listening_hours: number;
}

export interface FollowSuggestionsResponse {
  suggestions: FollowSuggestion[];
}

// ============================================================================
// NOTIFICATION TYPES (for future implementation)
// ============================================================================

export type NotificationType =
  | 'follow'
  | 'comment'
  | 'reply'
  | 'milestone'
  | 'system';

export interface Notification {
  id: string;
  type: NotificationType;
  user_id?: string;
  user_name?: string;
  user_avatar?: string;
  message: string;
  link?: string;
  read: boolean;
  created_at: string;
}

export interface NotificationsResponse {
  notifications: Notification[];
  unread_count: number;
}

// ============================================================================
// PUBLIC PROFILE TYPES (from /users/{user_id}/profile)
// ============================================================================

export interface PublicProfile {
  user_id: string;
  username?: string;
  display_name?: string;
  avatar_url?: string;
  bio?: string;
  created_at?: string;
  followers_count?: number;
  following_count?: number;
  listening_stats?: {
    total_listening_hours: number;
    books_completed: number;
  };
  is_following?: boolean;
  is_follower?: boolean;
}

export interface PublicProfileResponse extends PublicProfile {}

// Currently reading books
export interface CurrentlyReadingBook {
  book_id: string;
  title: string;
  author: string;
  cover_url?: string;
  progress: number; // 0-100
  last_read_at: string;
}

export interface CurrentlyReadingResponse {
  books: CurrentlyReadingBook[];
}

// User activity
export type ActivityType =
  | 'started_book'
  | 'completed_book'
  | 'milestone'
  | 'comment';

export interface UserActivity {
  id: string;
  type: ActivityType;
  user_id: string;
  username?: string;
  display_name?: string;
  avatar_url?: string;
  book_id?: string;
  book_title?: string;
  book_cover_url?: string;
  message: string;
  metadata?: {
    progress?: number;
    listening_hours?: number;
    milestone?: string;
    comment_text?: string;
  };
  created_at: string;
}

export interface ActivityResponse {
  activities: UserActivity[];
  count: number;
}

// User search
export interface UserSearchResult {
  user_id: string;
  username?: string;
  display_name?: string;
  avatar_url?: string;
  bio?: string;
  followers_count: number;
  is_following: boolean;
}

export interface UserSearchResponse {
  users: UserSearchResult[];
  total: number;
  page: number;
  per_page: number;
}

// ============================================================================
// FULL PROFILE TYPES (for own profile /profile endpoint)
// ============================================================================

export interface UserProfile {
  user_id: string;
  email: string;
  username?: string;
  display_name?: string;
  avatar_url?: string;
  bio?: string;
  created_at: string;
  last_active: string;
  social_stats: {
    followers_count: number;
    following_count: number;
    listening_hours: number;
    books_completed: number;
  };
  privacy_settings: {
    show_followers_list: boolean;
    show_following_list: boolean;
    show_activity: boolean;
    show_on_leaderboard: boolean;
  };
}

// ============================================================================
// API ERROR TYPES
// ============================================================================

export interface ApiError {
  detail: string;
  status_code: number;
}
