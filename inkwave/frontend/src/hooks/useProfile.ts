/**
 * useProfile Hook
 *
 * React Query hooks for user profile management.
 * Handles profile fetching, updates, avatar upload, preferences, and statistics.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { toast } from 'react-hot-toast';

// Profile types
export interface VoicePreferences {
	provider_id: string;
	voice_id: string;
	speed: number;
	language: string;
	voice_clone_reference?: string | null;
}

export interface InteractionPreferences {
	explanation_depth: string;
	discussion_topics: string[];
}

export interface UserProfile {
	preferred_voice: string;
	playback_speed: number;
	voice_preferences: VoicePreferences;
	reading_level: string;
	interaction_preferences: InteractionPreferences;
}

export interface Profile {
	user_id: string;
	email: string;
	display_name?: string;
	avatar_url?: string;
	profile: UserProfile;
	wallet_id?: string;
	credits: number;
	is_admin: boolean;
	role?: string; // 'user' | 'author' | 'admin' | 'superadmin'
	created_at: string;
	last_active: string;
}

export interface ProfileStats {
	books_started: number;
	questions_asked: number;
	listening_time_minutes: number;
}

// Query keys
const PROFILE_KEYS = {
	profile: ['profile'] as const,
	stats: ['profile', 'stats'] as const,
};

/**
 * Fetch user profile
 */
export function useProfile() {
	return useQuery<Profile>({
		queryKey: PROFILE_KEYS.profile,
		queryFn: async () => {
			const response = await api.profile.get();
			return response.data;
		},
		staleTime: 1000 * 60 * 5, // 5 minutes
		retry: 1,
	});
}

/**
 * Update basic profile (name, avatar URL)
 */
export function useUpdateProfile() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (data: {
			display_name?: string;
			avatar_url?: string;
		}) => {
			const response = await api.profile.update(data);
			return response.data;
		},
		onSuccess: (data) => {
			// Update cache with new profile data
			queryClient.setQueryData(PROFILE_KEYS.profile, data);
			toast.success('Profile updated successfully');
		},
		onError: (error: any) => {
			const message = error?.response?.data?.detail || 'Failed to update profile';
			toast.error(message);
			console.error('Profile update error:', error);
		},
	});
}

/**
 * Upload avatar file
 */
export function useUploadAvatar() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (file: File) => {
			const response = await api.profile.uploadAvatar(file);
			return response.data;
		},
		onSuccess: (data) => {
			// Update cached profile with new avatar URL
			queryClient.setQueryData<Profile>(PROFILE_KEYS.profile, (old) => {
				if (!old) return old;
				return { ...old, avatar_url: data.avatar_url };
			});
			toast.success(data.message || 'Avatar uploaded successfully');
		},
		onError: (error: any) => {
			const message = error?.response?.data?.detail || 'Failed to upload avatar';
			toast.error(message);
			console.error('Avatar upload error:', error);
		},
	});
}

/**
 * Set avatar from URL
 */
export function useUpdateAvatarUrl() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (avatarUrl: string) => {
			const response = await api.profile.updateAvatarUrl(avatarUrl);
			return response.data;
		},
		onSuccess: (data) => {
			// Update cached profile with new avatar URL
			queryClient.setQueryData<Profile>(PROFILE_KEYS.profile, (old) => {
				if (!old) return old;
				return { ...old, avatar_url: data.avatar_url };
			});
			toast.success(data.message || 'Avatar updated successfully');
		},
		onError: (error: any) => {
			const message = error?.response?.data?.detail || 'Failed to update avatar URL';
			toast.error(message);
			console.error('Avatar URL update error:', error);
		},
	});
}

/**
 * Update voice preferences
 */
export function useUpdateVoicePreferences() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (preferences: {
			provider_id?: string;
			voice_id?: string;
			speed?: number;
			language?: string;
			voice_clone_reference?: string;
		}) => {
			const response = await api.profile.updateVoicePreferences(preferences);
			return response.data;
		},
		onSuccess: (data) => {
			// Update cached profile with new voice preferences
			queryClient.setQueryData<Profile>(PROFILE_KEYS.profile, (old) => {
				if (!old) return old;
				return {
					...old,
					profile: {
						...old.profile,
						voice_preferences: data,
					},
				};
			});
			toast.success('Voice preferences updated');
		},
		onError: (error: any) => {
			const message = error?.response?.data?.detail || 'Failed to update voice preferences';
			toast.error(message);
			console.error('Voice preferences update error:', error);
		},
	});
}

/**
 * Update interaction preferences
 */
export function useUpdateInteractionPreferences() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (preferences: {
			explanation_depth?: string;
			discussion_topics?: string[];
		}) => {
			const response = await api.profile.updateInteractionPreferences(preferences);
			return response.data;
		},
		onSuccess: (data) => {
			// Update cached profile with new interaction preferences
			queryClient.setQueryData<Profile>(PROFILE_KEYS.profile, (old) => {
				if (!old) return old;
				return {
					...old,
					profile: {
						...old.profile,
						interaction_preferences: data,
					},
				};
			});
			toast.success('Interaction preferences updated');
		},
		onError: (error: any) => {
			const message = error?.response?.data?.detail || 'Failed to update interaction preferences';
			toast.error(message);
			console.error('Interaction preferences update error:', error);
		},
	});
}

/**
 * Update reading level
 */
export function useUpdateReadingLevel() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: async (level: string) => {
			const response = await api.profile.updateReadingLevel(level);
			return response.data;
		},
		onSuccess: (data) => {
			// Update cached profile with new reading level
			queryClient.setQueryData<Profile>(PROFILE_KEYS.profile, (old) => {
				if (!old) return old;
				return {
					...old,
					profile: {
						...old.profile,
						reading_level: data.reading_level,
					},
				};
			});
			toast.success('Reading level updated');
		},
		onError: (error: any) => {
			const message = error?.response?.data?.detail || 'Failed to update reading level';
			toast.error(message);
			console.error('Reading level update error:', error);
		},
	});
}

/**
 * Fetch user statistics
 */
export function useProfileStats() {
	return useQuery<ProfileStats>({
		queryKey: PROFILE_KEYS.stats,
		queryFn: async () => {
			const response = await api.profile.getStats();
			return response.data;
		},
		staleTime: 1000 * 60 * 5, // 5 minutes
		retry: 1,
	});
}
