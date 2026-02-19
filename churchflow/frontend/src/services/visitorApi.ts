/**
 * Visitor Tracking API Service
 *
 * Handles all API calls for visitor capture, journey management,
 * cell groups, enrichment, and communications.
 */

import axios from '../lib/axios-config';
import { getApiUrl } from '../config/api-config';

// Use the globally configured axios instance with automatic token refresh
const apiClient = axios;

// ============================================
// TypeScript Types
// ============================================

export interface Visitor {
  id: string;
  phone: string;
  name: string;
  full_name?: string;
  email?: string;
  member_status: 'visitor' | 'active_member' | 'inactive_member' | 'alumni';
  current_spiritual_stage?: string;
  current_cell_stage?: string;
  current_ministry_stage?: string;

  // Visit tracking
  first_visit_date?: string;
  visit_count: number;
  last_visit_date?: string;
  first_visit_source?: string;

  // Assignments
  cell_group_id?: string;
  assigned_cell_leader_id?: string;
  zone_id?: string;

  // Journey history
  stage_history?: StageTransition[];
  enrichment_history?: DataEnrichment[];
  life_events?: LifeEvent[];

  // Extended profile
  occupation?: string;
  marital_status?: string;
  address?: string;
  date_of_birth?: string;
  gender?: string;

  created_at: string;
  updated_at: string;
}

export interface StageTransition {
  previous_stage?: string;
  new_stage: string;
  journey_type: 'spiritual' | 'cell' | 'ministry';
  transitioned_at: string;
  transitioned_by_user_id?: string;
  notes?: string;
}

export interface DataEnrichment {
  field_name: string;
  previous_value?: any;
  new_value: any;
  enriched_by_user_id: string;
  enriched_by_role: string;
  enriched_at: string;
  notes?: string;
}

export interface LifeEvent {
  event_type: 'birth' | 'death' | 'marriage' | 'job_change' | 'relocation' | 'illness' | 'celebration' | 'other';
  event_date: string;
  description: string;
  recorded_by_user_id: string;
  recorded_at: string;
  requires_followup: boolean;
  followup_completed: boolean;
}

export interface CellGroup {
  id: string;
  organization_id: string;
  zone_id?: string;
  name: string;
  description?: string;
  meeting_day?: string;
  meeting_time?: string;
  meeting_location?: string;
  cell_leader_id?: string;
  cell_leader_name?: string;
  current_member_count: number;
  target_size: number;
  is_full: boolean;
  is_active: boolean;
  created_at: string;
}

export interface Zone {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  geographic_area?: string;
  zone_leader_id?: string;
  zone_leader_name?: string;
  cell_group_count: number;
  is_active: boolean;
  created_at: string;
}

export interface Department {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  department_type: string;
  department_head_id?: string;
  department_head_name?: string;
  volunteer_count: number;
  is_active: boolean;
  created_at: string;
}

export interface JourneyStage {
  id: string;
  organization_id: string;
  stage_name: string;
  stage_display_name: string;
  journey_type: 'spiritual' | 'cell' | 'ministry';
  stage_order: number;
  is_custom: boolean;
  is_active: boolean;
  auto_send_welcome: boolean;
  welcome_delay_minutes: number;
  welcome_message_template?: string;
  welcome_channels: string[];
  scheduled_followups: ScheduledFollowup[];
  description?: string;
}

export interface ScheduledFollowup {
  delay_days: number;
  message_template: string;
  communication_channels: string[];
}

export interface JourneyAnalytics {
  journey_type: string;
  total_members: number;
  funnel: {
    stage_name: string;
    stage_display_name: string;
    count: number;
    percentage: number;
  }[];
  conversion_rates?: Record<string, number>;
  date_range: {
    start: string;
    end: string;
  };
}

export interface ScheduledCommunication {
  id: string;
  user_id: string;
  followup_type: string;
  scheduled_for: string;
  channels: string[];
  message_template: string;
  status: 'pending' | 'sent' | 'failed' | 'cancelled';
  sent_at?: string;
  error_message?: string;
}

// ============================================
// Visitor API
// ============================================

export interface VisitorStats {
  total_users: number;
  active_members: number;
  visitors: number;
  inactive_members: number;
  alumni: number;
}

export const visitorApi = {
  /**
   * Get overall visitor and member statistics
   */
  getStats: async (): Promise<VisitorStats> => {
    const response = await apiClient.get(getApiUrl('visitors/stats'));
    return response.data;
  },

  /**
   * Capture a new visitor or update existing
   */
  captureVisitor: async (data: {
    phone: string;
    name?: string;
    email?: string;
    first_visit_source?: string;
    send_immediate_welcome?: boolean;
  }): Promise<Visitor> => {
    const response = await apiClient.post(getApiUrl('visitors'), data);
    return response.data;
  },

  /**
   * Get list of recent visitors
   */
  getRecentVisitors: async (params: {
    days?: number;
    limit?: number;
    skip?: number;
  } = {}): Promise<{ visitors: Visitor[]; total: number }> => {
    const response = await apiClient.get(getApiUrl('visitors'), { params });
    return response.data;
  },

  /**
   * Get visitor details by ID
   */
  getVisitorById: async (userId: string): Promise<Visitor> => {
    const response = await apiClient.get(getApiUrl(`visitors/${userId}`));
    return response.data;
  },

  /**
   * Update visitor information
   */
  updateVisitor: async (userId: string, data: Partial<Visitor>): Promise<Visitor> => {
    const response = await apiClient.put(getApiUrl(`visitors/${userId}`), data);
    return response.data;
  },

  /**
   * Resend welcome communication
   */
  resendWelcome: async (userId: string): Promise<{ message: string }> => {
    const response = await apiClient.post(getApiUrl(`visitors/${userId}/resend-welcome`));
    return response.data;
  },

  /**
   * Delete a single visitor/user
   */
  deleteVisitor: async (userId: string): Promise<{ message: string; deleted_count: number }> => {
    const response = await apiClient.delete(getApiUrl(`visitors/${userId}`));
    return response.data;
  },

  /**
   * Bulk delete multiple visitors/users
   */
  bulkDeleteVisitors: async (userIds: string[]): Promise<{ message: string; deleted_count: number; requested_count: number }> => {
    const response = await apiClient.post(getApiUrl('visitors/bulk-delete'), { user_ids: userIds });
    return response.data;
  },
};

// ============================================
// Journey API
// ============================================

export const journeyApi = {
  /**
   * Get all journey stages
   */
  getStages: async (params: {
    journey_type?: 'spiritual' | 'cell' | 'ministry';
  } = {}): Promise<{ stages: JourneyStage[] }> => {
    const response = await apiClient.get(getApiUrl('journey/stages'), { params });
    return response.data;
  },

  /**
   * Create custom journey stage
   */
  createStage: async (data: Partial<JourneyStage>): Promise<JourneyStage> => {
    const response = await apiClient.post(getApiUrl('journey/stages'), data);
    return response.data;
  },

  /**
   * Advance member to new stage
   */
  advanceStage: async (data: {
    user_id: string;
    journey_type: 'spiritual' | 'cell' | 'ministry';
    new_stage: string;
    notes?: string;
  }): Promise<{ message: string; current_stage: string }> => {
    const response = await apiClient.post(getApiUrl('journey/advance'), data);
    return response.data;
  },

  /**
   * Get journey history for member
   */
  getJourneyHistory: async (userId: string): Promise<{
    user_id: string;
    stage_history: StageTransition[];
  }> => {
    const response = await apiClient.get(getApiUrl(`journey/history/${userId}`));
    return response.data;
  },

  /**
   * Get journey analytics
   */
  getAnalytics: async (params: {
    journey_type: 'spiritual' | 'cell' | 'ministry';
    start_date?: string;
  }): Promise<JourneyAnalytics> => {
    const response = await apiClient.get(getApiUrl('journey/analytics/funnel'), { params });
    return response.data;
  },

  /**
   * Get members at specific stage
   */
  getMembersByStage: async (params: {
    journey_type: 'spiritual' | 'cell' | 'ministry';
    stage: string;
    limit?: number;
  }): Promise<{ members: Visitor[] }> => {
    const response = await apiClient.get(getApiUrl('journey/members'), { params });
    return response.data;
  },
};

// ============================================
// Cell Groups API
// ============================================

export const cellGroupApi = {
  /**
   * Get all cell groups
   */
  getCellGroups: async (params: {
    zone_id?: string;
    is_active?: boolean;
  } = {}): Promise<{ cell_groups: CellGroup[] }> => {
    const response = await apiClient.get(getApiUrl('cell-groups'), { params });
    return response.data;
  },

  /**
   * Create new cell group
   */
  createCellGroup: async (data: {
    name: string;
    zone_id?: string;
    description?: string;
    meeting_day?: string;
    meeting_time?: string;
    meeting_location?: string;
  }): Promise<CellGroup> => {
    const response = await apiClient.post(getApiUrl('cell-groups'), data);
    return response.data;
  },

  /**
   * Update cell group
   */
  updateCellGroup: async (cellGroupId: string, data: Partial<CellGroup>): Promise<CellGroup> => {
    const response = await apiClient.put(getApiUrl(`cell-groups/${cellGroupId}`), data);
    return response.data;
  },

  /**
   * Get cell group members
   */
  getCellMembers: async (cellGroupId: string, includeVisitors = true): Promise<{
    cell_group: CellGroup;
    members: Visitor[];
  }> => {
    const response = await apiClient.get(`/cell-groups/${cellGroupId}/members`, {
      params: { include_visitors: includeVisitors }
    });
    return response.data;
  },

  /**
   * Assign member to cell group
   */
  assignMember: async (cellGroupId: string, userId: string): Promise<{ message: string }> => {
    const response = await apiClient.post(getApiUrl(`cell-groups/${cellGroupId}/assign-member`), {
      user_id: userId
    });
    return response.data;
  },

  /**
   * Assign cell leader
   */
  assignLeader: async (cellGroupId: string, userId: string): Promise<CellGroup> => {
    const response = await apiClient.post(getApiUrl(`cell-groups/${cellGroupId}/assign-leader`), {
      user_id: userId
    });
    return response.data;
  },
};

// ============================================
// Zones API
// ============================================

export const zoneApi = {
  /**
   * Get all zones
   */
  getZones: async (): Promise<{ zones: Zone[] }> => {
    const response = await apiClient.get(getApiUrl('zones'));
    return response.data;
  },

  /**
   * Create new zone
   */
  createZone: async (data: {
    name: string;
    description?: string;
    geographic_area?: string;
  }): Promise<Zone> => {
    const response = await apiClient.post(getApiUrl('zones'), data);
    return response.data;
  },

  /**
   * Assign zone leader
   */
  assignZoneLeader: async (zoneId: string, userId: string): Promise<Zone> => {
    const response = await apiClient.post(getApiUrl(`zones/${zoneId}/assign-leader`), {
      user_id: userId
    });
    return response.data;
  },

  /**
   * Get all members in zone
   */
  getZoneMembers: async (zoneId: string): Promise<{ members: Visitor[] }> => {
    const response = await apiClient.get(getApiUrl(`zones/${zoneId}/members`));
    return response.data;
  },
};

// ============================================
// Enrichment API
// ============================================

export const enrichmentApi = {
  /**
   * Enrich member data
   */
  enrichMemberData: async (userId: string, data: {
    field_updates: Record<string, any>;
    notes?: string;
  }): Promise<{
    id: string;
    updated_fields: string[];
    enriched_by: { user_id: string; role: string };
    message: string;
  }> => {
    const response = await apiClient.put(getApiUrl(`members/${userId}/enrich`), data);
    return response.data;
  },

  /**
   * Record life event
   */
  recordLifeEvent: async (userId: string, data: {
    event_type: string;
    event_date: string;
    description: string;
    requires_followup?: boolean;
  }): Promise<{ message: string }> => {
    const response = await apiClient.post(getApiUrl(`members/${userId}/life-events`), data);
    return response.data;
  },

  /**
   * Get pending follow-ups
   */
  getPendingFollowups: async (params: {
    assigned_to_me?: boolean;
    limit?: number;
  } = {}): Promise<{
    followups: any[];
    total: number;
  }> => {
    const response = await apiClient.get(getApiUrl('members/life-events/pending-followups'), { params });
    return response.data;
  },

  /**
   * Mark follow-up completed
   */
  markFollowupCompleted: async (userId: string, eventIndex: number): Promise<{ message: string }> => {
    const response = await apiClient.post(getApiUrl(`members/${userId}/life-events/mark-completed`), {
      event_index: eventIndex
    });
    return response.data;
  },

  /**
   * Get enrichment history
   */
  getEnrichmentHistory: async (userId: string): Promise<{
    enrichment_history: DataEnrichment[];
  }> => {
    const response = await apiClient.get(getApiUrl(`members/${userId}/enrichment-history`));
    return response.data;
  },

  /**
   * Get life events
   */
  getLifeEvents: async (userId: string, eventType?: string): Promise<{
    life_events: LifeEvent[];
  }> => {
    const response = await apiClient.get(`/members/${userId}/life-events`, {
      params: { event_type: eventType }
    });
    return response.data;
  },
};

// ============================================
// Communications API
// ============================================

export const communicationApi = {
  /**
   * Send manual communication
   */
  sendCommunication: async (data: {
    user_ids: string[];
    message_template: string;
    channels: string[];
    template_variables?: Record<string, string>;
  }): Promise<{
    total: number;
    success: number;
    failure: number;
  }> => {
    const response = await apiClient.post(getApiUrl('journey/communications/send'), data);
    return response.data;
  },

  /**
   * Get scheduled communications
   */
  getScheduledCommunications: async (params: {
    status_filter?: 'pending' | 'sent' | 'failed' | 'cancelled';
    user_id?: string;
    limit?: number;
  } = {}): Promise<{
    scheduled_communications: ScheduledCommunication[];
    total: number;
  }> => {
    const response = await apiClient.get(getApiUrl('journey/communications/scheduled'), { params });
    return response.data;
  },

  /**
   * Cancel scheduled communication
   */
  cancelScheduledCommunication: async (scheduledCommId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(getApiUrl(`journey/communications/scheduled/${scheduledCommId}`));
    return response.data;
  },

  /**
   * Create stage campaign
   */
  createStageCampaign: async (data: {
    journey_type: 'spiritual' | 'cell' | 'ministry';
    stage_name: string;
    message_template: string;
    channels: string[];
    template_variables?: Record<string, string>;
  }): Promise<{
    total: number;
    success: number;
    failure: number;
  }> => {
    const response = await apiClient.post(getApiUrl('journey/communications/campaign'), data);
    return response.data;
  },

  /**
   * Get communication stats
   */
  getCommunicationStats: async (days = 30): Promise<{
    total_communications: number;
    by_status: Record<string, number>;
    by_channel: Record<string, number>;
    success_rate: number;
  }> => {
    const response = await apiClient.get(getApiUrl('journey/communications/stats'), {
      params: { days }
    });
    return response.data;
  },
};
