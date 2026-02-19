const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://language-community-api.ailabsafrica.com/api/v1';

export interface Language {
  id: string;
  code: string;
  name: string;
  family: string;
  status: string;
  speakers_count: number;
}

export interface LanguageBasic {
  code: string;
  name: string;
  native_name: string;
  speakers: number;
  progress: number;
  tier: string;
}

export interface LanguageFamily {
  id: string;
  name: string;
  description: string;
  total_speakers: string;
  countries: number;
  total_contributions: number;
  active_contributors: number;
  color: string;
  featured_languages: string[];
  priority_level: string;
  top_languages: LanguageBasic[];
}

export interface LanguageDetail {
  code: string;
  name: string;
  native_name: string;
  family: string;
  subfamily: string;
  speakers: number;
  countries: string[];
  regions: string[];
  tier: string;
  priority_level: string;
  progress: number;
  total_contributions: number;
  active_contributors: number;
  is_featured: boolean;
  development_status: string;
  data_sources_count: number;
}

export interface Notebook {
  id: string;
  name: string;
  type: 'data_acquisition' | 'data_processing' | 'training' | 'inference';
  language_code: string;
  version: string;
  model_type?: string;
  description: string;
  file_url: string;
  created_at: string;
  updated_at: string;
}

export interface ModelType {
  id: string;
  name: string;
  category: 'asr' | 'tts' | 'llm';
  description: string;
  supported_languages: string[];
}

export interface LanguageStats {
  total_languages: number;
  total_speakers: number;
  total_countries: number;
  featured_languages: number;
  family_distribution: Array<{
    _id: string;
    count: number;
  }>;
}

export interface Submission {
  id: string;
  language_code: string;
  type: 'text' | 'audio' | 'link' | 'image' | 'video';
  title: string;
  description?: string;
  category?: string;
  dialect?: string;
  cultural_context?: string;
  usage_context?: string;
  tier: 'tier-1-validated' | 'tier-2-reviewed' | 'tier-3-submitted';
  status: 'pending' | 'in_review' | 'validated' | 'rejected' | 'needs_improvement';
  contributor_id: string;
  quality_score?: number;
  points_awarded?: number;
  created_at: string;
  updated_at: string;
}

export interface SubmissionCreate {
  language_code: string;
  type: 'text' | 'audio' | 'link' | 'image' | 'video';
  title: string;
  description?: string;
  category?: string;
  dialect?: string;
  cultural_context?: string;
  usage_context?: string;
  text_content?: string;
  external_url?: string;
}

export interface SubmissionStats {
  total_submissions: number;
  by_type: Record<string, number>;
  by_tier: Record<string, number>;
  by_status: Record<string, number>;
}

export interface PendingValidation {
  id: string;
  title: string;
  type: 'text' | 'audio' | 'link' | 'image' | 'video';
  language: string;
  language_code: string;
  contributor: string;
  contributor_id: string;
  submittedAt: string;
  ai_quality_score: number;
  priority: 'high' | 'medium' | 'low';
  validations_needed: number;
  current_validations: number;
  description?: string;
}

export interface ValidationCreate {
  submission_id: string;
  submission_type: string;
  action: 'approve' | 'reject' | 'flag' | 'request_changes';
  category: 'content_quality' | 'linguistic_accuracy' | 'cultural_appropriateness' | 'technical_quality' | 'audio_clarity' | 'pronunciation';
  quality_rating: number; // 1-5
  confidence_level: number; // 0.0-1.0
  comments?: string;
  specific_issues?: string[];
  suggested_corrections?: string;
  audio_quality?: number; // 1-5
  pronunciation_accuracy?: number; // 1-5
  cultural_accuracy?: number; // 1-5
  time_spent_seconds?: number;
}

export interface ValidationHistory {
  id: string;
  submission_title: string;
  status: 'approved' | 'rejected' | 'disputed';
  my_score: number;
  consensus_score: number;
  points_awarded: number;
  accuracy_bonus?: number;
  language_code: string;
  submission_type: string;
  reviewed_at: string;
}

export interface ValidationStats {
  total_pending: number;
  total_validated: number;
  total_points: number;
  accuracy_rate: number;
  validations_this_week: number;
  streak_days: number;
  rank_percentile: number;
}

export interface LeaderboardUser {
  rank: number;
  user_id: string;
  username: string;
  full_name: string;
  primary_language: string;
  specialization: string;
  total_points: number;
  total_contributions: number;
  total_validations: number;
  accuracy_rate: number;
  badge: string;
  level: string;
  location: string;
  avatar_url?: string;
}

export interface CommunityActivity {
  id: string;
  user_id: string;
  user_name: string;
  username: string;
  action: string;
  item: string;
  item_type: string;
  points_awarded: number;
  language_code: string;
  language_name: string;
  timestamp: string;
  activity_type: 'contribution' | 'achievement';
}

export interface Achievement {
  id: string;
  type: string;
  title: string;
  description: string;
  icon: string;
  points_required: number;
  requirements: Record<string, any>;
  tier: string;
}

export interface UserAchievement {
  achievement_id: string;
  achievement_type: string;
  title: string;
  description: string;
  icon: string;
  progress: number;
  unlocked: boolean;
  unlocked_at?: string;
}

export interface LanguageChannel {
  id: string;
  name: string;
  language_code: string;
  language_family: string;
  description: string;
  member_count: number;
  active_members: number;
  is_active: boolean;
  moderators: string[];
  last_activity: string;
}

export interface CommunityStats {
  active_members: number;
  total_contributions: number;
  total_languages: number;
  average_quality_score: number;
  daily_active_users: number;
  weekly_active_users: number;
  monthly_active_users: number;
}

export interface ExternalDataset {
  id: string;
  name: string;
  source: string;
  dataset_type: string;
  language_code: string;
  language_family?: string;
  processing_status: string;
  total_files?: number;
  total_size_mb?: number;
  total_duration_hours?: number;
  total_words?: number;
  quality_score?: number;
  files_processed: number;
  files_integrated: number;
  files_rejected: number;
  duplicate_files: number;
  created_at: string;
  created_by: string;
  description?: string;
  tags: string[];
  source_url?: string;
  license_type: string;
  commercial_use_allowed: boolean;
  processing_started_at?: string;
  processing_completed_at?: string;
  processing_error?: string;
  auto_process: boolean;
  priority: number;
  hosting_type?: 'local' | 'external' | 'hybrid';
  download_url?: string;
  storage_path?: string;
}

export interface DatasetStats {
  total_datasets: number;
  datasets_by_source: Record<string, number>;
  datasets_by_language: Record<string, number>;
  datasets_by_status: Record<string, number>;
  total_files_integrated: number;
  total_size_gb: number;
  total_audio_hours: number;
  average_quality_score: number;
  processing_queue_length: number;
}

export interface DatasetCreate {
  name: string;
  source: string;
  dataset_type: string;
  language_code: string;
  source_url: string;
  license_type: string;
  description: string;
  tags: string[];
  auto_process?: boolean;
  quality_threshold?: number;
  priority?: number;
}

export interface UserProfile {
  id: string;
  username?: string;
  full_name?: string;
  email: string;
  avatar_url?: string;
  bio?: string;
  location?: string;
  languages_spoken: string[];
  level: string;
  total_points: number;
  level_points: number;
  achievements: string[];
  badges: string[];
  language_expertise: LanguageExpertise[];
  verified_languages: string[];
  contributions_count: number;
  validations_count: number;
  quality_rating: number;
  reputation_score: number;
  created_at: string;
  last_activity?: string;
  can_validate: boolean;
  can_moderate: boolean;
}

export interface LanguageExpertise {
  language_code: string;
  language_name: string;
  proficiency: string;
  specialization: string;
  verification_status: string;
}

export interface UserStatistics {
  user_id: string;
  total_submissions: number;
  validated_submissions: number;
  rejected_submissions: number;
  pending_submissions: number;
  audio_submissions: number;
  text_submissions: number;
  translation_submissions: number;
  validations_performed: number;
  validation_accuracy_rate: number;
  avg_quality_score: number;
  streak_days: number;
  max_streak_days: number;
  weekly_goals: WeeklyGoals;
  achievement_progress: Record<string, AchievementProgress>;
  this_week: TimePeriodStats;
  this_month: TimePeriodStats;
  all_time: TimePeriodStats;
  languages_contributed: Record<string, LanguageContribution>;
  quality_metrics: QualityMetrics;
  last_updated: string;
}

export interface WeeklyGoals {
  audio_submissions: GoalProgress;
  validations: GoalProgress;
  daily_streak: GoalProgress;
}

export interface GoalProgress {
  current: number;
  target: number;
  week_start: string;
}

export interface AchievementProgress {
  current: number;
  target: number;
  progress: number;
}

export interface TimePeriodStats {
  submissions: number;
  validations: number;
  points_earned: number;
  achievements_unlocked?: number;
  streak_maintained?: boolean;
}

export interface LanguageContribution {
  submissions: number;
  validations: number;
  points: number;
}

export interface QualityMetrics {
  submission_approval_rate: number;
  validation_accuracy: number;
  cultural_accuracy: number;
  technical_quality: number;
  community_rating: number;
}

export interface UserActivity {
  id: string;
  user_id: string;
  activity_type: string;
  title: string;
  description: string;
  status: string;
  points_awarded: number;
  language_code: string;
  language_name: string;
  submission_type?: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface UserAchievementDetailed {
  id: string;
  user_id: string;
  achievement_type: string;
  achievement_id: string;
  title: string;
  description: string;
  icon: string;
  rarity: string;
  points_awarded: number;
  metadata: Record<string, any>;
  awarded_at: string;
  unlocked: boolean;
  progress?: number;
}

class ApiClient {
  private async getAuthHeaders(): Promise<HeadersInit> {
    // Get JWT token from localStorage (set by BackendAuthContext)
    try {
      const accessToken = localStorage.getItem('auth_access_token');

      if (accessToken) {
        return {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        };
      }
    } catch (error) {
      console.warn('No auth token found:', error);
    }

    return {
      'Content-Type': 'application/json',
    };
  }

  private async fetchApi(endpoint: string, options?: RequestInit) {
    const authHeaders = await this.getAuthHeaders();

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        ...authHeaders,
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const json = await response.json();

    // Backend wraps responses in {success, message, data} format
    // Extract the data field if present
    if (json && typeof json === 'object' && 'data' in json) {
      return json.data;
    }

    return json;
  }

  // Languages
  async getLanguages(): Promise<Language[]> {
    return this.fetchApi('/languages/'); // Trailing slash needed for languages router
  }

  async getLanguage(code: string): Promise<Language> {
    return this.fetchApi(`/languages/${code}`);
  }

  async getLanguageStats(): Promise<LanguageStats> {
    return this.fetchApi('/languages/stats/overview');
  }

  // New enhanced language endpoints
  async getLanguageFamilies(): Promise<LanguageFamily[]> {
    return this.fetchApi('/languages/families');
  }

  async getFeaturedLanguages(limit: number = 6): Promise<LanguageDetail[]> {
    return this.fetchApi(`/languages/featured?limit=${limit}`);
  }

  async searchLanguages(query: string, limit: number = 20): Promise<LanguageBasic[]> {
    const encodedQuery = encodeURIComponent(query);
    return this.fetchApi(`/languages/search?q=${encodedQuery}&limit=${limit}`);
  }

  async getLanguageDetail(code: string): Promise<LanguageDetail> {
    return this.fetchApi(`/languages/${code}`);
  }

  // Notebooks
  async getNotebooks(languageCode?: string, type?: string): Promise<Notebook[]> {
    if (languageCode) {
      return this.fetchApi(`/languages/${languageCode}/notebooks`);
    }

    const params = new URLSearchParams();
    if (type) params.append('type', type);

    const query = params.toString() ? `?${params}` : '';
    return this.fetchApi(`/notebooks${query}`);
  }

  async getNotebook(id: string): Promise<Notebook> {
    return this.fetchApi(`/notebooks/${id}`);
  }

  async getNotebooksByLanguageAndModel(languageCode: string, modelType: string): Promise<Notebook[]> {
    return this.fetchApi(`/notebooks/language/${languageCode}/model/${modelType}`);
  }

  async getNotebookComments(notebookId: string): Promise<any[]> {
    return this.fetchApi(`/notebooks/${notebookId}/comments`);
  }

  async addNotebookComment(notebookId: string, comment: string): Promise<any> {
    return this.fetchApi(`/notebooks/${notebookId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ content: comment }),
    });
  }

  // Model Types
  async getModelTypes(): Promise<ModelType[]> {
    return this.fetchApi('/model-types');
  }

  async getModelType(id: string): Promise<ModelType> {
    return this.fetchApi(`/model-types/${id}`);
  }

  // Submissions
  async getSubmissionStats(): Promise<SubmissionStats> {
    return this.fetchApi('/submit/stats/overview');
  }

  async getUserSubmissions(page: number = 1, pageSize: number = 20): Promise<Submission[]> {
    return this.fetchApi(`/submit/history?page=${page}&page_size=${pageSize}`);
  }

  async getSubmission(id: string): Promise<Submission> {
    return this.fetchApi(`/submit/${id}`);
  }

  async submitText(data: SubmissionCreate): Promise<Submission> {
    return this.fetchApi('/submit/text', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async submitLink(data: SubmissionCreate): Promise<Submission> {
    return this.fetchApi('/submit/link', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async submitAudio(formData: FormData): Promise<Submission> {
    // For FormData, we need to handle headers differently
    const authHeaders = await this.getAuthHeaders();
    delete (authHeaders as any)['Content-Type']; // Let browser set it for FormData

    const response = await fetch(`${API_BASE_URL}/submit/audio`, {
      method: 'POST',
      headers: authHeaders,
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const json = await response.json();

    // Backend wraps responses in {success, message, data} format
    if (json && typeof json === 'object' && 'data' in json) {
      return json.data;
    }

    return json;
  }

  async updateSubmission(id: string, updates: Partial<SubmissionCreate>): Promise<Submission> {
    return this.fetchApi(`/submit/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteSubmission(id: string): Promise<{ deleted: boolean }> {
    return this.fetchApi(`/submit/${id}`, {
      method: 'DELETE',
    });
  }

  async browseLanguageSubmissions(
    languageCode: string,
    page: number = 1,
    pageSize: number = 20,
    filters: Record<string, string> = {}
  ): Promise<Submission[]> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...filters,
    });
    return this.fetchApi(`/submit/language/${languageCode}/browse?${params}`);
  }

  // Validations
  async getPendingValidations(
    page: number = 1,
    pageSize: number = 20,
    languageCode?: string,
    submissionType?: string
  ): Promise<PendingValidation[]> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (languageCode) params.append('language_code', languageCode);
    if (submissionType) params.append('submission_type', submissionType);

    return this.fetchApi(`/validate/pending?${params}`);
  }

  async submitValidation(validationData: ValidationCreate): Promise<any> {
    return this.fetchApi(`/validate/${validationData.submission_id}`, {
      method: 'POST',
      body: JSON.stringify(validationData),
    });
  }

  async getValidationHistory(page: number = 1, pageSize: number = 20): Promise<ValidationHistory[]> {
    return this.fetchApi(`/validate/my-reviews?page=${page}&page_size=${pageSize}`);
  }

  async getValidationStats(): Promise<ValidationStats> {
    return this.fetchApi('/validate/stats/validator');
  }

  async getValidationQueueSummary(): Promise<any> {
    return this.fetchApi('/validate/queue/summary');
  }

  async getValidationConsensus(submissionId: string): Promise<any> {
    return this.fetchApi(`/validate/consensus/${submissionId}`);
  }

  async getValidatorLeaderboard(
    timeframe: string = 'monthly',
    page: number = 1,
    pageSize: number = 50
  ): Promise<any[]> {
    const params = new URLSearchParams({
      timeframe,
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    return this.fetchApi(`/validate/leaderboard?${params}`);
  }

  async promoteSubmission(submissionId: string): Promise<any> {
    return this.fetchApi(`/validate/promote/${submissionId}`, {
      method: 'POST',
    });
  }

  async disputeValidation(validationId: string, reason: string): Promise<any> {
    return this.fetchApi(`/validate/dispute/${validationId}`, {
      method: 'POST',
      body: JSON.stringify({ dispute_reason: reason }),
    });
  }

  // Content Reporting
  async submitReport(reportData: {
    entity_type: string;
    entity_id: string;
    reason: string;
    description?: string;
  }): Promise<any> {
    return this.fetchApi('/governance/reports', {
      method: 'POST',
      body: JSON.stringify(reportData),
    });
  }

  // External Resources & Links
  async submitResourceLink(linkData: {
    title: string;
    url: string;
    description: string;
    language_code: string;
    resource_type: string;
    category?: string;
    tags?: string[];
  }): Promise<any> {
    return this.fetchApi('/resources', {
      method: 'POST',
      body: JSON.stringify(linkData),
    });
  }

  async getResourceLinks(
    page: number = 1,
    pageSize: number = 20,
    languageCode?: string,
    resourceType?: string,
    category?: string,
    verifiedOnly: boolean = false
  ): Promise<any[]> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (languageCode) params.append('language_code', languageCode);
    if (resourceType) params.append('resource_type', resourceType);
    if (category) params.append('category', category);
    if (verifiedOnly) params.append('verified_only', 'true');

    return this.fetchApi(`/resources/links?${params}`);
  }

  async getResourceLink(linkUuid: string): Promise<any> {
    return this.fetchApi(`/resources/links/${linkUuid}`);
  }

  async updateResourceLink(linkUuid: string, updates: {
    title?: string;
    description?: string;
    tags?: string[];
    category?: string;
  }): Promise<any> {
    return this.fetchApi(`/resources/links/${linkUuid}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async verifyResourceLink(linkUuid: string, verificationData: {
    is_valid: boolean;
    notes?: string;
    quality_score?: number;
  }): Promise<any> {
    return this.fetchApi(`/resources/links/${linkUuid}/verify`, {
      method: 'POST',
      body: JSON.stringify(verificationData),
    });
  }

  async voteOnResource(linkUuid: string, voteData: {
    vote_type: 'upvote' | 'downvote';
  }): Promise<any> {
    return this.fetchApi(`/resources/links/${linkUuid}/vote`, {
      method: 'POST',
      body: JSON.stringify(voteData),
    });
  }

  async trackResourceClick(linkUuid: string): Promise<any> {
    return this.fetchApi(`/resources/links/${linkUuid}/click`, {
      method: 'POST',
    });
  }

  async uploadResourceFile(formData: FormData): Promise<any> {
    const authHeaders = await this.getAuthHeaders();
    delete (authHeaders as any)['Content-Type']; // Let browser set it for FormData

    const response = await fetch(`${API_BASE_URL}/resources/upload`, {
      method: 'POST',
      headers: authHeaders,
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const json = await response.json();
    if (json && typeof json === 'object' && 'data' in json) {
      return json.data;
    }
    return json;
  }

  async getUploadStatus(uploadUuid: string): Promise<any> {
    return this.fetchApi(`/resources/uploads/${uploadUuid}`);
  }

  async listUserUploads(
    page: number = 1,
    pageSize: number = 20,
    status?: string
  ): Promise<any[]> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (status) params.append('status', status);

    return this.fetchApi(`/resources/uploads?${params}`);
  }

  async getResourceStats(): Promise<{
    total_links: number;
    total_uploads: number;
    verified_links: number;
    by_type: Record<string, number>;
    by_language: Record<string, number>;
    top_contributors: any[];
  }> {
    return this.fetchApi('/resources/stats');
  }

  // ML Models Management
  async createModel(modelData: {
    name: string;
    model_type: string;
    architecture: string;
    languages: string[];
    description: string;
    primary_language?: string;
    storage_path?: string;
    checkpoint_path?: string;
    training_config?: any;
    performance_metrics?: any;
    license?: string;
    tags?: string[];
  }): Promise<any> {
    return this.fetchApi('/mlops/models', {
      method: 'POST',
      body: JSON.stringify(modelData),
    });
  }

  async getModels(
    page: number = 1,
    pageSize: number = 20,
    modelType?: string,
    languageCode?: string,
    architecture?: string
  ): Promise<{ items: any[]; total_count: number; page: number; page_size: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (modelType) params.append('model_type', modelType);
    if (languageCode) params.append('language_code', languageCode);
    if (architecture) params.append('architecture', architecture);

    return this.fetchApi(`/mlops/models?${params}`);
  }

  async searchModels(
    query: string,
    page: number = 1,
    pageSize: number = 20,
    modelType?: string
  ): Promise<{ items: any[]; total_count: number; page: number; page_size: number }> {
    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (modelType) params.append('model_type', modelType);

    return this.fetchApi(`/mlops/models/search?${params}`);
  }

  async getModel(modelUuid: string): Promise<any> {
    return this.fetchApi(`/mlops/models/${modelUuid}`);
  }

  async updateModel(modelUuid: string, updates: {
    name?: string;
    description?: string;
    tags?: string[];
    license?: string;
    performance_metrics?: any;
  }): Promise<any> {
    return this.fetchApi(`/mlops/models/${modelUuid}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteModel(modelUuid: string): Promise<{ deleted: boolean }> {
    return this.fetchApi(`/mlops/models/${modelUuid}`, {
      method: 'DELETE',
    });
  }

  async downloadModel(modelUuid: string, versionNumber?: string): Promise<any> {
    const params = versionNumber ? `?version_number=${versionNumber}` : '';
    return this.fetchApi(`/mlops/models/${modelUuid}/download${params}`);
  }

  async reportModelIssue(modelUuid: string, issueData: {
    title: string;
    description: string;
    severity: string;
    category: string;
  }): Promise<any> {
    return this.fetchApi(`/mlops/models/${modelUuid}/issues`, {
      method: 'POST',
      body: JSON.stringify(issueData),
    });
  }

  async getModelStats(): Promise<any> {
    return this.fetchApi('/mlops/models/stats');
  }

  // Model Versions
  async getModelVersions(modelId: string): Promise<any[]> {
    return this.fetchApi(`/mlops/models/${modelId}/versions`);
  }

  async createModelVersion(modelId: string, versionData: {
    version_number: string;
    changelog: string;
    architecture_changes?: string;
    training_config?: any;
    performance_metrics?: any;
    file_path?: string;
  }): Promise<any> {
    return this.fetchApi(`/mlops/models/${modelId}/versions`, {
      method: 'POST',
      body: JSON.stringify(versionData),
    });
  }

  async getModelVersionDetails(modelId: string, versionNumber: string): Promise<any> {
    return this.fetchApi(`/mlops/models/${modelId}/versions/${versionNumber}`);
  }

  async compareModelVersions(modelId: string, version1: string, version2: string): Promise<any> {
    return this.fetchApi(`/mlops/models/${modelId}/versions/compare?v1=${version1}&v2=${version2}`);
  }

  // Community
  async getLeaderboard(
    timeframe: string = 'monthly',
    languageFamily?: string,
    page: number = 1,
    pageSize: number = 50
  ): Promise<LeaderboardUser[]> {
    const params = new URLSearchParams({
      timeframe,
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (languageFamily) params.append('language_family', languageFamily);

    return this.fetchApi(`/community/leaderboard?${params}`);
  }

  async getCommunityStats(): Promise<CommunityStats> {
    return this.fetchApi('/community/stats/engagement');
  }

  async getCommunityActivityFeed(
    languageFamily?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<CommunityActivity[]> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (languageFamily) params.append('language_family', languageFamily);

    return this.fetchApi(`/community/activity/feed?${params}`);
  }

  async getAllAchievements(): Promise<Achievement[]> {
    return this.fetchApi('/community/achievements');
  }


  async getLanguageChannels(): Promise<LanguageChannel[]> {
    return this.fetchApi('/community/channels');
  }

  async createCommunityProposal(proposalData: any): Promise<any> {
    return this.fetchApi('/community/proposals', {
      method: 'POST',
      body: JSON.stringify(proposalData),
    });
  }

  async getCommunityProposals(
    statusFilter: string = 'active',
    page: number = 1,
    pageSize: number = 20
  ): Promise<any[]> {
    return this.fetchApi(`/community/proposals?status=${statusFilter}&page=${page}&page_size=${pageSize}`);
  }

  async voteOnProposal(proposalId: string, voteData: any): Promise<any> {
    return this.fetchApi(`/community/proposals/${proposalId}/vote`, {
      method: 'POST',
      body: JSON.stringify(voteData),
    });
  }

  async getProposalDetails(proposalId: string): Promise<any> {
    return this.fetchApi(`/community/proposals/${proposalId}`);
  }

  async getLanguageContributors(
    languageCode: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<{
    items: any[];
    total_count: number;
    page: number;
    page_size: number;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    return this.fetchApi(`/community/languages/${languageCode}/contributors?${params}`);
  }

  // Datasets
  async getDatasets(
    source?: string,
    datasetType?: string,
    languageCode?: string,
    status?: string,
    search?: string,
    page: number = 1,
    limit: number = 20
  ): Promise<{ datasets: ExternalDataset[]; total_count: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (source) params.append('source', source);
    if (datasetType) params.append('dataset_type', datasetType);
    if (languageCode) params.append('language_code', languageCode);
    if (status) params.append('status', status);
    if (search) params.append('search', search);

    return this.fetchApi(`/datasets?${params}`);
  }

  async getDataset(datasetId: string): Promise<ExternalDataset> {
    return this.fetchApi(`/datasets/${datasetId}`);
  }

  async createDataset(datasetData: DatasetCreate): Promise<ExternalDataset> {
    return this.fetchApi('/datasets', {
      method: 'POST',
      body: JSON.stringify(datasetData),
    });
  }

  async startDatasetProcessing(datasetId: string): Promise<{ message: string; dataset_id: string }> {
    return this.fetchApi(`/datasets/${datasetId}/process`, {
      method: 'POST',
    });
  }

  async pauseDatasetProcessing(datasetId: string): Promise<{ message: string; dataset_id: string }> {
    return this.fetchApi(`/datasets/${datasetId}/pause`, {
      method: 'POST',
    });
  }

  async deleteDataset(datasetId: string): Promise<{ message: string; dataset_id: string }> {
    return this.fetchApi(`/datasets/${datasetId}`, {
      method: 'DELETE',
    });
  }

  async getDatasetStats(): Promise<DatasetStats> {
    return this.fetchApi('/datasets/stats/overview');
  }

  async exportDatasetManifest(datasetId: string): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/download`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.blob();
  }

  // Dataset Versions
  async createDatasetVersion(datasetId: string, versionData: any): Promise<any> {
    return this.fetchApi(`/datasets/${datasetId}/versions`, {
      method: 'POST',
      body: JSON.stringify(versionData),
    });
  }

  async getDatasetVersions(
    datasetId: string,
    includeDeprecated: boolean = false,
    includePrerelease: boolean = false
  ): Promise<{
    versions: any[];
    total: number;
    latest_version: string;
    stable_version: string;
  }> {
    const params = new URLSearchParams();
    if (includeDeprecated) params.append('include_deprecated', 'true');
    if (includePrerelease) params.append('include_prerelease', 'true');
    return this.fetchApi(`/datasets/${datasetId}/versions?${params}`);
  }

  async getDatasetVersion(datasetId: string, version: string): Promise<any> {
    return this.fetchApi(`/datasets/${datasetId}/versions/${version}`);
  }

  async updateDatasetVersion(datasetId: string, version: string, updateData: any): Promise<any> {
    return this.fetchApi(`/datasets/${datasetId}/versions/${version}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async downloadDatasetVersion(datasetId: string, version: string): Promise<any> {
    return this.fetchApi(`/datasets/${datasetId}/versions/${version}/download`);
  }

  async compareDatasetVersions(
    datasetId: string,
    versionA: string,
    versionB: string
  ): Promise<any> {
    const params = new URLSearchParams({
      version_a: versionA,
      version_b: versionB,
    });
    return this.fetchApi(`/datasets/${datasetId}/versions/compare?${params}`);
  }

  async suggestNextVersion(
    datasetId: string,
    currentVersion: string,
    bumpType: 'major' | 'minor' | 'patch'
  ): Promise<{
    current_version: string;
    suggested_version: string;
    bump_type: string;
    already_exists: boolean;
  }> {
    const params = new URLSearchParams({
      bump_type: bumpType,
    });
    return this.fetchApi(`/datasets/${datasetId}/versions/${currentVersion}/increment?${params}`, {
      method: 'POST',
    });
  }

  async checkVersionCompatibility(
    datasetId: string,
    version: string,
    compareWith: string
  ): Promise<{
    version_a: string;
    version_b: string;
    compatible: boolean;
    explanation: string;
  }> {
    const params = new URLSearchParams({
      compare_with: compareWith,
    });
    return this.fetchApi(`/datasets/${datasetId}/versions/${version}/compatible?${params}`);
  }

  // Discovery & Exploration
  async discoverByLanguage(
    languageCode: string,
    includeDatasets: boolean = true,
    includeModels: boolean = true,
    includeResources: boolean = true,
    includePipelines: boolean = false
  ): Promise<{
    language: any;
    statistics: any;
    resources: any;
  }> {
    const params = new URLSearchParams();
    if (!includeDatasets) params.append('include_datasets', 'false');
    if (!includeModels) params.append('include_models', 'false');
    if (!includeResources) params.append('include_resources', 'false');
    if (includePipelines) params.append('include_pipelines', 'true');

    const query = params.toString() ? `?${params}` : '';
    return this.fetchApi(`/discovery/languages/${languageCode}${query}`);
  }

  async discoverDatasetsByLanguage(
    languageCode: string,
    page: number = 1,
    limit: number = 20
  ): Promise<{ items: any[]; total_count: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    return this.fetchApi(`/discovery/languages/${languageCode}/datasets?${params}`);
  }

  async discoverModelsByLanguage(
    languageCode: string,
    modelType?: string,
    page: number = 1,
    limit: number = 20
  ): Promise<{ items: any[]; total_count: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (modelType) params.append('model_type', modelType);

    return this.fetchApi(`/discovery/languages/${languageCode}/models?${params}`);
  }

  async discoverResourcesByLanguage(
    languageCode: string,
    resourceType?: string,
    page: number = 1,
    limit: number = 20
  ): Promise<{ items: any[]; total_count: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (resourceType) params.append('resource_type', resourceType);

    return this.fetchApi(`/discovery/languages/${languageCode}/resources?${params}`);
  }

  async discoverByTask(
    taskType: string,
    languageCode?: string,
    page: number = 1,
    limit: number = 20
  ): Promise<{ items: any[]; total_count: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (languageCode) params.append('language_code', languageCode);

    return this.fetchApi(`/discovery/tasks/${taskType}?${params}`);
  }

  async getTrendingModels(limit: number = 10, days: number = 7): Promise<any[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      days: days.toString(),
    });
    return this.fetchApi(`/discovery/trending/models?${params}`);
  }

  async getTrendingDatasets(limit: number = 10, days: number = 7): Promise<any[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      days: days.toString(),
    });
    return this.fetchApi(`/discovery/trending/datasets?${params}`);
  }

  async getTrendingResources(limit: number = 10, days: number = 7): Promise<any[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      days: days.toString(),
    });
    return this.fetchApi(`/discovery/trending/resources?${params}`);
  }

  async getSimilarModels(modelUuid: string, limit: number = 5): Promise<any[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    return this.fetchApi(`/discovery/recommendations/models/${modelUuid}/similar?${params}`);
  }

  async getCompatibleModels(datasetUuid: string, limit: number = 5): Promise<any[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    return this.fetchApi(`/discovery/recommendations/datasets/${datasetUuid}/compatible-models?${params}`);
  }

  async getPlatformOverview(): Promise<{
    total_languages: number;
    total_datasets: number;
    total_models: number;
    total_resources: number;
    featured_languages: any[];
    trending_models: any[];
    trending_datasets: any[];
    recent_activity: any[];
  }> {
    return this.fetchApi('/discovery/overview');
  }

  async globalSearch(
    query: string,
    searchType?: string,
    languageCode?: string,
    page: number = 1,
    limit: number = 20
  ): Promise<{
    datasets: any[];
    models: any[];
    resources: any[];
    languages: any[];
    total_results: number;
  }> {
    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      limit: limit.toString(),
    });
    if (searchType) params.append('type', searchType);
    if (languageCode) params.append('language_code', languageCode);

    return this.fetchApi(`/discovery/search?${params}`);
  }

  // Dashboard and User Profile
  async getCurrentUser(): Promise<UserProfile> {
    return this.fetchApi('/auth/me');
  }

  async getUserProfile(userId: string): Promise<UserProfile> {
    return this.fetchApi(`/users/${userId}/profile`);
  }

  async updateUserProfile(updates: Partial<UserProfile>): Promise<UserProfile> {
    return this.fetchApi('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async getUserStatistics(userId?: string): Promise<UserStatistics> {
    const endpoint = userId ? `/users/${userId}/statistics` : '/auth/statistics';
    return this.fetchApi(endpoint);
  }

  async getUserActivities(
    userId?: string,
    page: number = 1,
    limit: number = 20
  ): Promise<UserActivity[]> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    const endpoint = userId
      ? `/users/${userId}/activities?${params}`
      : `/auth/activities?${params}`;
    return this.fetchApi(endpoint);
  }

  async getUserAchievements(userId?: string): Promise<UserAchievementDetailed[]> {
    const endpoint = userId ? `/users/${userId}/achievements` : '/auth/achievements';
    return this.fetchApi(endpoint);
  }

  async updateWeeklyGoals(goals: WeeklyGoals): Promise<WeeklyGoals> {
    return this.fetchApi('/auth/goals', {
      method: 'PUT',
      body: JSON.stringify(goals),
    });
  }

  async getDashboardOverview(): Promise<{
    user: UserProfile;
    statistics: UserStatistics;
    recent_activities: UserActivity[];
    achievements: UserAchievementDetailed[];
  }> {
    return this.fetchApi('/auth/dashboard');
  }

  // ML Training Pipelines
  async createPipeline(pipelineData: {
    name: string;
    description: string;
    model_type: string;
    language_code: string;
    task_type: string;
    base_model_id?: string;
    dataset_ids?: string[];
    training_config?: any;
    priority?: string;
  }): Promise<any> {
    return this.fetchApi('/mlops/pipelines', {
      method: 'POST',
      body: JSON.stringify(pipelineData),
    });
  }

  async getPipelines(
    page: number = 1,
    pageSize: number = 20,
    status?: string,
    modelType?: string,
    languageCode?: string
  ): Promise<{ items: any[]; total_count: number; page: number; page_size: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (status) params.append('status', status);
    if (modelType) params.append('model_type', modelType);
    if (languageCode) params.append('language_code', languageCode);

    return this.fetchApi(`/mlops/pipelines?${params}`);
  }

  async getPipeline(pipelineId: string): Promise<any> {
    return this.fetchApi(`/mlops/pipelines/${pipelineId}`);
  }

  async updatePipeline(pipelineId: string, updates: {
    name?: string;
    description?: string;
    status?: string;
    notes?: string;
    training_config?: any;
  }): Promise<any> {
    return this.fetchApi(`/mlops/pipelines/${pipelineId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async updatePipelineStage(pipelineId: string, stageName: string, stageData: {
    status: string;
    progress?: number;
    start_time?: string;
    end_time?: string;
    error_message?: string;
    metrics?: any;
    notes?: string;
  }): Promise<any> {
    return this.fetchApi(`/mlops/pipelines/${pipelineId}/stages/${stageName}`, {
      method: 'PUT',
      body: JSON.stringify(stageData),
    });
  }

  async getPipelineMetrics(pipelineId: string, stageName?: string): Promise<any> {
    const params = stageName ? `?stage_name=${stageName}` : '';
    return this.fetchApi(`/mlops/pipelines/${pipelineId}/metrics${params}`);
  }

  async completePipeline(pipelineId: string, completionData: {
    final_model_path?: string;
    final_metrics?: any;
    notes?: string;
  }): Promise<any> {
    return this.fetchApi(`/mlops/pipelines/${pipelineId}/complete`, {
      method: 'POST',
      body: JSON.stringify(completionData),
    });
  }

  async getPipelineStats(): Promise<any> {
    return this.fetchApi('/mlops/pipelines/stats');
  }

  // Pipeline Artifacts
  async uploadPipelineArtifact(
    pipelineId: string,
    file: File,
    metadata: {
      name: string;
      description?: string;
      type: string;
      version?: string;
    }
  ): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    const authHeaders = await this.getAuthHeaders();
    delete (authHeaders as any)['Content-Type']; // Let browser set it for FormData

    const response = await fetch(`${API_BASE_URL}/mlops/pipelines/${pipelineId}/artifacts`, {
      method: 'POST',
      headers: authHeaders,
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    return response.json();
  }

  async getPipelineArtifacts(pipelineId: string): Promise<any[]> {
    return this.fetchApi(`/mlops/pipelines/${pipelineId}/artifacts`);
  }

  async deletePipelineArtifact(pipelineId: string, artifactId: string): Promise<any> {
    return this.fetchApi(`/mlops/pipelines/${pipelineId}/artifacts/${artifactId}`, {
      method: 'DELETE',
    });
  }

  async downloadPipelineArtifact(pipelineId: string, artifactId: string): Promise<Blob> {
    const authHeaders = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/mlops/pipelines/${pipelineId}/artifacts/${artifactId}/download`, {
      method: 'GET',
      headers: authHeaders,
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status} ${response.statusText}`);
    }

    return response.blob();
  }
}

  // ==================== Community Drive API ====================

  // Drive Item Types
  async getDriveFolderContents(params: {
    folder_id?: string | null;
    language_code?: string;
    category?: string;
    skip?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }): Promise<DriveListResponse> {
    const searchParams = new URLSearchParams();
    if (params.folder_id) searchParams.append('folder_id', params.folder_id);
    if (params.language_code) searchParams.append('language_code', params.language_code);
    if (params.category) searchParams.append('category', params.category);
    if (params.skip) searchParams.append('skip', params.skip.toString());
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.sort_by) searchParams.append('sort_by', params.sort_by);
    if (params.sort_order) searchParams.append('sort_order', params.sort_order);

    return this.fetchApi(`/drive/folders?${searchParams}`);
  }

  async getDriveBreadcrumbs(folderId?: string | null, languageCode?: string): Promise<BreadcrumbItem[]> {
    const params = new URLSearchParams();
    if (folderId) params.append('folder_id', folderId);
    if (languageCode) params.append('language_code', languageCode);

    return this.fetchApi(`/drive/breadcrumbs?${params}`);
  }

  async createDriveFolder(data: {
    name: string;
    language_code: string;
    category?: string;
    parent_id?: string | null;
    description?: string;
  }): Promise<DriveItem> {
    return this.fetchApi('/drive/folders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async uploadDriveFile(formData: FormData): Promise<DriveItem> {
    const authHeaders = await this.getAuthHeaders();
    delete (authHeaders as any)['Content-Type']; // Let browser set it for FormData

    const response = await fetch(`${API_BASE_URL}/drive/upload`, {
      method: 'POST',
      headers: authHeaders,
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const json = await response.json();
    if (json && typeof json === 'object' && 'data' in json) {
      return json.data;
    }
    return json;
  }

  async getDriveFileInfo(fileId: string): Promise<DriveItem> {
    return this.fetchApi(`/drive/files/${fileId}`);
  }

  async downloadDriveFile(fileId: string): Promise<Blob> {
    const authHeaders = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/drive/files/${fileId}/download`, {
      method: 'GET',
      headers: authHeaders,
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status} ${response.statusText}`);
    }

    return response.blob();
  }

  async deleteDriveFile(fileId: string, permanent: boolean = false): Promise<{ status: string; file_id: string }> {
    const params = permanent ? '?permanent=true' : '';
    return this.fetchApi(`/drive/files/${fileId}${params}`, {
      method: 'DELETE',
    });
  }

  async renameDriveFile(fileId: string, newName: string): Promise<DriveItem> {
    return this.fetchApi(`/drive/files/${fileId}/rename`, {
      method: 'PATCH',
      body: JSON.stringify({ new_name: newName }),
    });
  }

  async toggleDriveFileStar(fileId: string): Promise<DriveItem> {
    return this.fetchApi(`/drive/files/${fileId}/star`, {
      method: 'POST',
    });
  }

  async toggleDriveFilePublic(fileId: string): Promise<DriveItem> {
    return this.fetchApi(`/drive/files/${fileId}/public`, {
      method: 'POST',
    });
  }

  async searchDriveFiles(params: {
    q: string;
    language_code?: string;
    category?: string;
    file_type?: 'file' | 'folder';
    tags?: string;
    skip?: number;
    limit?: number;
  }): Promise<DriveSearchResponse> {
    const searchParams = new URLSearchParams();
    searchParams.append('q', params.q);
    if (params.language_code) searchParams.append('language_code', params.language_code);
    if (params.category) searchParams.append('category', params.category);
    if (params.file_type) searchParams.append('file_type', params.file_type);
    if (params.tags) searchParams.append('tags', params.tags);
    if (params.skip) searchParams.append('skip', params.skip.toString());
    if (params.limit) searchParams.append('limit', params.limit.toString());

    return this.fetchApi(`/drive/search?${searchParams}`);
  }

  async getMyDriveFiles(skip: number = 0, limit: number = 50): Promise<DriveListResponse> {
    return this.fetchApi(`/drive/my-files?skip=${skip}&limit=${limit}`);
  }

  async getRecentDriveFiles(limit: number = 20): Promise<DriveItem[]> {
    return this.fetchApi(`/drive/recent?limit=${limit}`);
  }

  async getDriveLanguageFiles(
    languageCode: string,
    category?: string,
    limit: number = 50
  ): Promise<DriveItem[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (category) params.append('category', category);

    return this.fetchApi(`/drive/languages/${languageCode}/files?${params}`);
  }

  async getDriveStats(languageCode?: string): Promise<DriveStatsResponse> {
    const params = languageCode ? `?language_code=${languageCode}` : '';
    return this.fetchApi(`/drive/stats${params}`);
  }

  async getGlobalDriveStats(languageCode?: string): Promise<DriveStatsResponse> {
    const params = languageCode ? `?language_code=${languageCode}` : '';
    return this.fetchApi(`/drive/stats/global${params}`);
  }
}

// ==================== Drive Types ====================

export interface DriveItem {
  id: string;
  name: string;
  type: 'file' | 'folder';
  path?: string;
  parent_id?: string | null;
  language_code?: string;
  category?: string;
  size: number;
  mime_type?: string;
  description: string;
  tags: string[];
  license?: string;
  download_count: number;
  view_count: number;
  created_at?: string;
  modified_at?: string;
  owner_id?: string;
  is_starred: boolean;
  is_public: boolean;
  is_deleted: boolean;
}

export interface DriveListResponse {
  items: DriveItem[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface DriveSearchResponse {
  items: DriveItem[];
  total: number;
  skip: number;
  limit: number;
  query: string;
}

export interface BreadcrumbItem {
  id: string | null;
  name: string;
}

export interface DriveStatsResponse {
  total_files: number;
  total_size_bytes: number;
  total_size_mb: number;
  total_downloads: number;
  by_category: Record<string, { count: number; size_bytes: number; downloads: number }>;
}

export const apiClient = new ApiClient();