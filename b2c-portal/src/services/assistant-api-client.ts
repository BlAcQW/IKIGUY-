/**
 * Assistant API Client
 *
 * Centralized service for managing voice assistants via the backend API.
 * Handles CRUD operations, publishing, and assistant lifecycle management.
 *
 * Usage:
 * ```typescript
 * const client = new AssistantApiClient();
 * const assistants = await client.fetchAssistants({ activeOnly: false });
 * await client.updateAssistant(id, { name: 'New Name' });
 * ```
 */

import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL } from '@/config/api-config';
import type {
  Assistant,
  FetchAssistantsOptions,
  CreateAssistantData,
  AssistantApiError,
} from '@/types/voice-lab';

// ============================================================================
// Assistant API Client Class
// ============================================================================

export class AssistantApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Get authenticated request headers
   */
  private async getHeaders(): Promise<Record<string, string>> {
    const authHeaders = await getAuthHeaders();
    return {
      ...authHeaders,
      'Content-Type': 'application/json',
    };
  }

  /**
   * Handle API errors consistently
   */
  private handleError(error: any, context: string): never {
    const apiError = new Error(
      `${context}: ${error.message || 'Unknown error'}`
    ) as AssistantApiError;
    apiError.statusCode = error.statusCode || 500;
    apiError.details = error.details;
    throw apiError;
  }

  /**
   * Fetch all assistants
   *
   * @param options - Filter options
   * @returns Array of assistants
   *
   * @example
   * const assistants = await client.fetchAssistants({ activeOnly: false });
   */
  async fetchAssistants(options: FetchAssistantsOptions = {}): Promise<Assistant[]> {
    try {
      const params = new URLSearchParams();
      if (options.userId) {
        params.append('user_id', options.userId);
      }
      params.append('active_only', String(options.activeOnly ?? true));

      const url = `${this.baseUrl}/voice/assistants/?${params.toString()}`;
      const headers = await this.getHeaders();

      const response = await fetch(url, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Handle both wrapped and direct array responses
      if (Array.isArray(data)) {
        return data;
      } else if (data.success && Array.isArray(data.assistants)) {
        return data.assistants;
      } else if (data.assistants && Array.isArray(data.assistants)) {
        return data.assistants;
      }

      return [];
    } catch (error) {
      this.handleError(error, 'Failed to fetch assistants');
    }
  }

  /**
   * Get a single assistant by ID
   *
   * @param id - Assistant ID
   * @returns Assistant object
   *
   * @example
   * const assistant = await client.getAssistant('assistant-123');
   */
  async getAssistant(id: string): Promise<Assistant> {
    try {
      const headers = await this.getHeaders();

      const response = await fetch(`${this.baseUrl}/voice/assistants/${id}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Assistant not found');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.handleError(error, `Failed to get assistant ${id}`);
    }
  }

  /**
   * Create a new assistant
   *
   * @param data - Assistant creation data
   * @returns Created assistant
   *
   * @example
   * const assistant = await client.createAssistant({
   *   name: 'My Assistant',
   *   system_prompt: 'You are a helpful assistant',
   *   language: 'en'
   * });
   */
  async createAssistant(data: CreateAssistantData): Promise<Assistant> {
    try {
      const headers = await this.getHeaders();

      const response = await fetch(`${this.baseUrl}/voice/assistants/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.handleError(error, 'Failed to create assistant');
    }
  }

  /**
   * Update assistant configuration
   *
   * @param id - Assistant ID
   * @param updates - Partial assistant data to update
   * @returns Updated assistant
   *
   * @example
   * const updated = await client.updateAssistant('assistant-123', {
   *   name: 'Updated Name',
   *   system_prompt: 'New prompt'
   * });
   */
  async updateAssistant(
    id: string,
    updates: Partial<Assistant>
  ): Promise<Assistant> {
    try {
      const headers = await this.getHeaders();

      const response = await fetch(`${this.baseUrl}/voice/assistants/${id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Assistant not found');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.handleError(error, `Failed to update assistant ${id}`);
    }
  }

  /**
   * Delete an assistant
   *
   * @param id - Assistant ID
   * @returns Success message
   *
   * @example
   * await client.deleteAssistant('assistant-123');
   */
  async deleteAssistant(id: string): Promise<void> {
    try {
      const headers = await this.getHeaders();

      const response = await fetch(`${this.baseUrl}/voice/assistants/${id}`, {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Assistant not found');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Successful deletion
      return;
    } catch (error) {
      this.handleError(error, `Failed to delete assistant ${id}`);
    }
  }

  /**
   * Activate an assistant
   *
   * @param id - Assistant ID
   * @returns Success message
   *
   * @example
   * await client.activateAssistant('assistant-123');
   */
  async activateAssistant(id: string): Promise<void> {
    try {
      const headers = await this.getHeaders();

      const response = await fetch(
        `${this.baseUrl}/voice/assistants/${id}/activate`,
        {
          method: 'POST',
          headers,
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return;
    } catch (error) {
      this.handleError(error, `Failed to activate assistant ${id}`);
    }
  }

  /**
   * Deactivate an assistant
   *
   * @param id - Assistant ID
   * @returns Success message
   *
   * @example
   * await client.deactivateAssistant('assistant-123');
   */
  async deactivateAssistant(id: string): Promise<void> {
    try {
      const headers = await this.getHeaders();

      const response = await fetch(
        `${this.baseUrl}/voice/assistants/${id}/deactivate`,
        {
          method: 'POST',
          headers,
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return;
    } catch (error) {
      this.handleError(error, `Failed to deactivate assistant ${id}`);
    }
  }

  /**
   * Test an assistant with sample input
   *
   * @param id - Assistant ID
   * @param testInput - Test input text
   * @returns Test result
   *
   * @example
   * const result = await client.testAssistant('assistant-123', 'Hello');
   */
  async testAssistant(
    id: string,
    testInput: string = 'Hello, how are you?'
  ): Promise<{
    assistant_id: string;
    test_input: string;
    test_output: string;
    status: string;
    response_time: number;
  }> {
    try {
      const headers = await this.getHeaders();

      const response = await fetch(
        `${this.baseUrl}/voice/assistants/${id}/test?test_input=${encodeURIComponent(
          testInput
        )}`,
        {
          method: 'GET',
          headers,
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.handleError(error, `Failed to test assistant ${id}`);
    }
  }

  /**
   * Publish assistant changes (alias for update)
   *
   * @param id - Assistant ID
   * @param data - Assistant data to publish
   * @returns Updated assistant
   *
   * @example
   * await client.publishAssistant('assistant-123', updatedData);
   */
  async publishAssistant(id: string, data: Partial<Assistant>): Promise<Assistant> {
    return this.updateAssistant(id, data);
  }
}

// ============================================================================
// Default Export
// ============================================================================

// Export a default instance for convenience
export const assistantApiClient = new AssistantApiClient();
