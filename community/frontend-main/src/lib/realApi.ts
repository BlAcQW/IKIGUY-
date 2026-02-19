import { supabase, Database } from './supabase';

// Types from the existing API
export * from './api';

type Profile = Database['public']['Tables']['profiles']['Row'];
type Submission = Database['public']['Tables']['submissions']['Row'];
type Language = Database['public']['Tables']['languages']['Row'];
type Validation = Database['public']['Tables']['validations']['Row'];

// Real API client with Supabase integration
class RealApiClient {
  private baseURL = '/api/v1';

  private async getAuthHeaders() {
    const { data: { session } } = await supabase.auth.getSession();
    return {
      'Content-Type': 'application/json',
      'Authorization': session?.access_token ? `Bearer ${session.access_token}` : '',
    };
  }

  private async fetchApi(endpoint: string, options?: RequestInit) {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      headers: {
        ...headers,
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  // Languages
  async getLanguages(): Promise<Language[]> {
    try {
      const response = await this.fetchApi('/languages');
      return response.items || response || [];
    } catch (error) {
      console.error('Error fetching languages from API:', error);
      // Return mock data instead of failing Supabase call
      return [
        {
          code: "twi",
          name: "Twi",
          native_name: "Twi",
          family: "Niger-Congo",
          iso639_1: "tw",
          iso639_2: "twi",
          iso639_3: "twi",
          speakers: 9000000,
          countries: ["Ghana"],
          regions: ["West Africa"],
          writing_systems: ["Latin"],
          status: "active",
          description: "Twi is a dialect of the Akan language spoken in Ghana",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          code: "yor",
          name: "Yoruba",
          native_name: "Yorùbá",
          family: "Niger-Congo",
          iso639_1: "yo",
          iso639_2: "yor",
          iso639_3: "yor",
          speakers: 47000000,
          countries: ["Nigeria", "Benin", "Togo"],
          regions: ["West Africa"],
          writing_systems: ["Latin", "Arabic"],
          status: "active",
          description: "Yoruba is a language spoken in West Africa",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];
    }
  }

  async getLanguageDetail(code: string): Promise<Language | null> {
    const { data, error } = await supabase
      .from('languages')
      .select('*')
      .eq('code', code)
      .single();

    if (error) {
      console.error('Error fetching language detail:', error);
      return null;
    }

    return data;
  }

  async getLanguageFamilies() {
    try {
      return await this.fetchApi('/languages/families');
    } catch (error) {
      console.error('Error fetching language families:', error);
      // Return mock data as fallback
      return [];
    }
  }

  async getLanguageStats() {
    try {
      return await this.fetchApi('/languages/stats');
    } catch (error) {
      console.error('Error fetching language stats:', error);
      return {
        total_languages: 0,
        total_families: 0,
        most_contributed: '',
        total_hours: 0
      };
    }
  }

  // Submissions
  async submitText(submission: any): Promise<Submission> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { data, error } = await supabase
      .from('submissions')
      .insert({
        user_id: user.id,
        language_code: submission.language_code,
        type: 'text',
        title: submission.title,
        description: submission.description,
        text_content: submission.text_content,
        status: 'pending',
        validation_status: 'pending'
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  }

  async submitLink(submission: any): Promise<Submission> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { data, error } = await supabase
      .from('submissions')
      .insert({
        user_id: user.id,
        language_code: submission.language_code,
        type: 'link',
        title: submission.title,
        description: submission.description,
        external_url: submission.external_url,
        status: 'pending',
        validation_status: 'pending'
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  }

  async submitAudio(submission: any): Promise<Submission> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { data, error } = await supabase
      .from('submissions')
      .insert({
        user_id: user.id,
        language_code: submission.language_code,
        type: 'audio',
        title: submission.title,
        description: submission.description,
        audio_url: submission.audio_url,
        status: 'pending',
        validation_status: 'pending'
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  }

  async getSubmissions(filters?: any) {
    let query = supabase
      .from('submissions')
      .select(`
        *,
        profiles!submissions_user_id_fkey (username, full_name)
      `)
      .order('created_at', { ascending: false });

    if (filters?.status) {
      query = query.eq('status', filters.status);
    }

    if (filters?.language_code) {
      query = query.eq('language_code', filters.language_code);
    }

    if (filters?.type) {
      query = query.eq('type', filters.type);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data || [];
  }

  async getSubmissionStats() {
    try {
      const { data, error } = await supabase
        .from('submissions')
        .select('type, status, validation_status');

      if (error) throw error;

      const stats = {
        total_submissions: data?.length || 0,
        by_type: {
          text: data?.filter(s => s.type === 'text').length || 0,
          audio: data?.filter(s => s.type === 'audio').length || 0,
          link: data?.filter(s => s.type === 'link').length || 0,
        },
        by_status: {
          pending: data?.filter(s => s.status === 'pending').length || 0,
          approved: data?.filter(s => s.status === 'approved').length || 0,
          rejected: data?.filter(s => s.status === 'rejected').length || 0,
          validated: data?.filter(s => s.validation_status === 'validated').length || 0,
        }
      };

      return stats;
    } catch (error) {
      console.error('Error fetching submission stats:', error);
      return {
        total_submissions: 0,
        by_type: { text: 0, audio: 0, link: 0 },
        by_status: { pending: 0, approved: 0, rejected: 0, validated: 0 }
      };
    }
  }

  // Validations
  async submitValidation(validation: any): Promise<Validation> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { data, error } = await supabase
      .from('validations')
      .insert({
        submission_id: validation.submission_id,
        validator_id: user.id,
        action: validation.action,
        quality_rating: validation.quality_rating,
        confidence_level: validation.confidence_level,
        comments: validation.comments,
        specific_issues: validation.specific_issues || [],
        suggested_corrections: validation.suggested_corrections
      })
      .select()
      .single();

    if (error) throw error;

    // Also update the submission status
    await supabase
      .from('submissions')
      .update({
        status: validation.action === 'approve' ? 'approved' : 'rejected',
        validation_status: 'validated',
        quality_score: validation.quality_rating
      })
      .eq('id', validation.submission_id);

    return data;
  }

  async getValidationHistory(userId: string) {
    const { data, error } = await supabase
      .from('validations')
      .select(`
        *,
        submissions!validations_submission_id_fkey (title, type, language_code)
      `)
      .eq('validator_id', userId)
      .order('created_at', { ascending: false })
      .limit(10);

    if (error) throw error;
    return data || [];
  }

  // User Profiles
  async getUserProfile(userId: string): Promise<Profile | null> {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single();

    if (error) {
      console.error('Error fetching user profile:', error);
      return null;
    }

    return data;
  }

  async updateUserProfile(userId: string, updates: Partial<Profile>): Promise<Profile> {
    const { data, error } = await supabase
      .from('profiles')
      .update(updates)
      .eq('id', userId)
      .select()
      .single();

    if (error) throw error;
    return data;
  }

  async getUserStatistics(userId: string) {
    try {
      // Get user's submissions count
      const { data: submissions } = await supabase
        .from('submissions')
        .select('id, type, status, quality_score')
        .eq('user_id', userId);

      // Get user's validations count
      const { data: validations } = await supabase
        .from('validations')
        .select('id, quality_rating')
        .eq('validator_id', userId);

      const stats = {
        submissions_count: submissions?.length || 0,
        validations_count: validations?.length || 0,
        approved_submissions: submissions?.filter(s => s.status === 'approved').length || 0,
        average_quality: submissions?.length ?
          submissions.reduce((acc, s) => acc + (s.quality_score || 0), 0) / submissions.length : 0,
        weekly_goals: {
          submissions: 5,
          validations: 10,
          current_submissions: 0,
          current_validations: 0
        },
        streak_days: 0
      };

      return stats;
    } catch (error) {
      console.error('Error fetching user statistics:', error);
      return {
        submissions_count: 0,
        validations_count: 0,
        approved_submissions: 0,
        average_quality: 0,
        weekly_goals: {
          submissions: 5,
          validations: 10,
          current_submissions: 0,
          current_validations: 0
        },
        streak_days: 0
      };
    }
  }

  async getUserActivities(userId: string) {
    try {
      // Get recent submissions
      const { data: submissions } = await supabase
        .from('submissions')
        .select('id, title, type, status, created_at')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(5);

      // Get recent validations
      const { data: validations } = await supabase
        .from('validations')
        .select(`
          id, action, created_at,
          submissions!validations_submission_id_fkey (title, type)
        `)
        .eq('validator_id', userId)
        .order('created_at', { ascending: false })
        .limit(5);

      const activities = [
        ...(submissions || []).map(s => ({
          id: s.id,
          activity_type: 'submission',
          title: s.title,
          details: `${s.type} submission`,
          status: s.status,
          timestamp: s.created_at
        })),
        ...(validations || []).map(v => ({
          id: v.id,
          activity_type: 'validation',
          title: (v.submissions as any)?.title || 'Validation',
          details: `${v.action} validation`,
          status: v.action,
          timestamp: v.created_at
        }))
      ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
       .slice(0, 10);

      return activities;
    } catch (error) {
      console.error('Error fetching user activities:', error);
      return [];
    }
  }

  async getUserAchievements(userId: string) {
    try {
      // For now, return mock achievements
      // In real implementation, this would query an achievements table
      return [
        {
          id: 'first_submission',
          achievement_type: 'milestone',
          title: 'First Submission',
          description: 'Submit your first contribution',
          icon: '🎯',
          progress: 100,
          unlocked: true,
          unlocked_at: new Date().toISOString()
        }
      ];
    } catch (error) {
      console.error('Error fetching user achievements:', error);
      return [];
    }
  }

  // Community features
  async getCommunityStats() {
    try {
      return await this.fetchApi('/community/stats');
    } catch (error) {
      console.error('Error fetching community stats:', error);
      return {
        total_members: 0,
        active_contributors: 0,
        this_month_contributions: 0,
        growth_rate: 0
      };
    }
  }

  async getLeaderboard() {
    try {
      return await this.fetchApi('/community/leaderboard');
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
      return [];
    }
  }

  async getCommunityActivities() {
    try {
      return await this.fetchApi('/community/activities');
    } catch (error) {
      console.error('Error fetching community activities:', error);
      return [];
    }
  }

  // File upload
  async uploadFile(file: File, folder: string = 'submissions'): Promise<string> {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const fileExt = file.name.split('.').pop();
    const fileName = `${user.id}/${Date.now()}.${fileExt}`;
    const filePath = `${folder}/${fileName}`;

    const { data, error } = await supabase.storage
      .from('uploads')
      .upload(filePath, file);

    if (error) throw error;

    // Get public URL
    const { data: { publicUrl } } = supabase.storage
      .from('uploads')
      .getPublicUrl(filePath);

    return publicUrl;
  }

  // Search functionality
  async searchLanguages(query: string, options?: { limit?: number }) {
    try {
      const response = await this.fetchApi(`/languages/search?q=${encodeURIComponent(query)}&limit=${options?.limit || 10}`);
      return response || [];
    } catch (error) {
      console.error('Error searching languages:', error);
      // Return mock search results
      return [
        {
          code: "twi",
          name: "Twi",
          native_name: "Twi",
          speakers: 9000000,
          family: "Niger-Congo",
          tier: "tier-1"
        }
      ].filter(lang =>
        lang.name.toLowerCase().includes(query.toLowerCase()) ||
        lang.native_name.toLowerCase().includes(query.toLowerCase()) ||
        lang.code.toLowerCase().includes(query.toLowerCase())
      );
    }
  }

  async searchSubmissions(query: string, filters?: any) {
    try {
      // For now, return mock submission results since we don't have a submissions search endpoint yet
      console.log('Searching submissions for:', query, filters);
      return [
        {
          id: "sub1",
          title: `Twi: ${query}`,
          type: "text",
          language_code: "twi",
          description: "Sample Twi submission matching your search",
          status: "approved",
          created_at: new Date().toISOString(),
          profiles: { username: "contributor", full_name: "Sample User" }
        }
      ].filter(sub =>
        sub.title.toLowerCase().includes(query.toLowerCase()) ||
        sub.description.toLowerCase().includes(query.toLowerCase())
      );
    } catch (error) {
      console.error('Error searching submissions:', error);
      return [];
    }
  }

  async searchUsers(query: string, options?: { limit?: number }) {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .or(`username.ilike.%${query}%, full_name.ilike.%${query}%, bio.ilike.%${query}%`)
      .order('username')
      .limit(options?.limit || 10);

    if (error) throw error;
    return data || [];
  }

  async getSearchSuggestions(query: string) {
    if (!query || query.length < 2) return [];

    try {
      // Get quick suggestions from multiple sources
      const [languages, submissions] = await Promise.all([
        this.searchLanguages(query, { limit: 5 }),
        this.searchSubmissions(query, { limit: 5 })
      ]);

      const suggestions = [];

      // Add language suggestions
      languages.forEach(lang => {
        suggestions.push({
          type: 'language',
          text: lang.name,
          subtitle: lang.native_name,
          url: `/languages/${lang.code}`
        });
      });

      // Add submission suggestions
      submissions.forEach(sub => {
        suggestions.push({
          type: 'submission',
          text: sub.title,
          subtitle: `${sub.type} • ${sub.language_code}`,
          url: `/submissions/${sub.id}`
        });
      });

      return suggestions.slice(0, 10);
    } catch (error) {
      console.error('Error getting search suggestions:', error);
      return [];
    }
  }

  async performGlobalSearch(query: string, filters?: {
    types?: string[];
    language?: string;
    dateRange?: string;
    limit?: number;
  }) {
    const results = [];
    const limit = filters?.limit || 50;

    try {
      const searchPromises = [];

      // Search languages if included
      if (!filters?.types || filters.types.includes('language')) {
        searchPromises.push(
          this.searchLanguages(query, { limit: Math.ceil(limit / 4) })
            .then(data => data.map(item => ({ ...item, _type: 'language' })))
        );
      }

      // Search submissions if included
      if (!filters?.types || filters.types.includes('submission')) {
        searchPromises.push(
          this.searchSubmissions(query, {
            language_code: filters?.language,
            limit: Math.ceil(limit / 2)
          }).then(data => data.map(item => ({ ...item, _type: 'submission' })))
        );
      }

      // Search users if included
      if (!filters?.types || filters.types.includes('user')) {
        searchPromises.push(
          this.searchUsers(query, { limit: Math.ceil(limit / 4) })
            .then(data => data.map(item => ({ ...item, _type: 'user' })))
        );
      }

      const searchResults = await Promise.all(searchPromises);
      return searchResults.flat().slice(0, limit);
    } catch (error) {
      console.error('Global search failed:', error);
      return [];
    }
  }

  // Draft management
  async saveDraft(draftData: any) {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not authenticated');

    const { data, error } = await supabase
      .from('submissions')
      .insert({
        ...draftData,
        user_id: user.id,
        status: 'draft'
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  }

  async getDrafts(userId: string) {
    const { data, error } = await supabase
      .from('submissions')
      .select('*')
      .eq('user_id', userId)
      .eq('status', 'draft')
      .order('updated_at', { ascending: false });

    if (error) throw error;
    return data || [];
  }

  async deleteDraft(draftId: string) {
    const { error } = await supabase
      .from('submissions')
      .delete()
      .eq('id', draftId)
      .eq('status', 'draft');

    if (error) throw error;
    return true;
  }
}

export const realApiClient = new RealApiClient();
export default realApiClient;