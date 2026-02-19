// Vapi API Integration
const VAPI_BASE_URL = import.meta.env.VAPI_BASE_URL || 'https://api.vapi.ai';
const VAPI_PRIVATE_KEY = import.meta.env.VAPI_PRIVATE_KEY;

export interface VapiCall {
  id: string;
  assistantId: string;
  status: string;
  startTime: string;
  endTime?: string;
  duration?: number;
  cost?: number;
  transcript?: string;
  summary?: string;
  metadata?: Record<string, any>;
}

export interface VapiAssistant {
  id: string;
  name: string;
  status: string;
  type: string;
  voiceId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface VapiCallHistoryParams {
  assistantId?: string;
  limit?: number;
  offset?: number;
  startDate?: string;
  endDate?: string;
  status?: string;
}

/**
 * Make authenticated request to Vapi API
 */
const makeVapiRequest = async (endpoint: string, options: RequestInit = {}) => {
  if (!VAPI_PRIVATE_KEY) {
    throw new Error('Vapi API key not configured');
  }

  const url = `${VAPI_BASE_URL}${endpoint}`;
  const headers = {
    'Authorization': `Bearer ${VAPI_PRIVATE_KEY}`,
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Vapi API error: ${response.status} - ${errorText}`);
  }

  return response.json();
};

/**
 * Get call history from Vapi
 */
export const getVapiCallHistory = async (params: VapiCallHistoryParams = {}): Promise<VapiCall[]> => {
  try {
    const queryParams = new URLSearchParams();
    
    if (params.assistantId) queryParams.append('assistantId', params.assistantId);
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.offset) queryParams.append('offset', params.offset.toString());
    if (params.startDate) queryParams.append('startDate', params.startDate);
    if (params.endDate) queryParams.append('endDate', params.endDate);
    if (params.status) queryParams.append('status', params.status);

    const endpoint = `/call${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await makeVapiRequest(endpoint);
    
    return response.data || [];
  } catch (error) {
    console.error('Error fetching Vapi call history:', error);
    throw error;
  }
};

/**
 * Get specific call details from Vapi
 */
export const getVapiCallDetails = async (callId: string): Promise<VapiCall> => {
  try {
    const response = await makeVapiRequest(`/call/${callId}`);
    return response;
  } catch (error) {
    console.error('Error fetching Vapi call details:', error);
    throw error;
  }
};

/**
 * Get assistant details from Vapi
 */
export const getVapiAssistant = async (assistantId: string): Promise<VapiAssistant> => {
  try {
    const response = await makeVapiRequest(`/assistant/${assistantId}`);
    return response;
  } catch (error) {
    console.error('Error fetching Vapi assistant:', error);
    throw error;
  }
};

/**
 * Get all assistants from Vapi
 */
export const getVapiAssistants = async (): Promise<VapiAssistant[]> => {
  try {
    const response = await makeVapiRequest('/assistant');
    return response.data || [];
  } catch (error) {
    console.error('Error fetching Vapi assistants:', error);
    throw error;
  }
};

/**
 * Update assistant status in Vapi
 */
export const updateVapiAssistantStatus = async (assistantId: string, status: 'active' | 'inactive'): Promise<void> => {
  try {
    await makeVapiRequest(`/assistant/${assistantId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  } catch (error) {
    console.error('Error updating Vapi assistant status:', error);
    throw error;
  }
};

/**
 * Delete assistant from Vapi
 */
export const deleteVapiAssistant = async (assistantId: string): Promise<void> => {
  try {
    await makeVapiRequest(`/assistant/${assistantId}`, {
      method: 'DELETE',
    });
  } catch (error) {
    console.error('Error deleting Vapi assistant:', error);
    throw error;
  }
};

/**
 * Get call analytics from Vapi
 */
export const getVapiCallAnalytics = async (assistantId?: string, timeRange?: string): Promise<any> => {
  try {
    const queryParams = new URLSearchParams();
    
    if (assistantId) queryParams.append('assistantId', assistantId);
    if (timeRange) queryParams.append('timeRange', timeRange);

    const endpoint = `/analytics/calls${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await makeVapiRequest(endpoint);
    
    return response;
  } catch (error) {
    console.error('Error fetching Vapi call analytics:', error);
    throw error;
  }
};

/**
 * Test Vapi API connection
 */
export const testVapiConnection = async (): Promise<boolean> => {
  try {
    await makeVapiRequest('/assistant');
    return true;
  } catch (error) {
    console.error('Vapi connection test failed:', error);
    return false;
  }
};
