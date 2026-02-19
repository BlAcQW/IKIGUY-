/**
 * useCampaignSSE - Campaign-Specific SSE Hook
 *
 * A specialized React hook for managing SSE connections to campaign status streams.
 * Handles multiple concurrent campaigns with selective state updates.
 *
 * Features:
 * - Automatic connection to running campaigns
 * - Selective state updates (only changed campaigns)
 * - Per-campaign connection status tracking
 * - Memory-efficient (only connects to running campaigns)
 * - Auto-disconnects when campaigns complete
 *
 * @example
 * ```typescript
 * const { activeConnections, connectionStatus } = useCampaignSSE(
 *   campaigns,
 *   (update) => {
 *     console.log('Campaign updated:', update);
 *     setCampaigns(prev => prev.map(c =>
 *       c.id === update.id ? { ...c, ...update } : c
 *     ));
 *   },
 *   authToken
 * );
 * ```
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useSSE, SSEStatus } from './useSSE';

export interface Campaign {
  id: string;
  status: string;
  [key: string]: any;
}

export interface CampaignUpdate {
  id?: string;
  campaign_id?: string;
  status?: string;
  progress?: {
    total_recipients?: number;
    sent?: number;
    delivered?: number;
    failed?: number;
    pending?: number;
  };
  calls_made?: number;
  calls_total?: number;
  success_rate?: number;
  current_cost?: number;
  total_cost?: number;
  error_message?: string;
  [key: string]: any;
}

export interface CampaignConnectionStatus {
  campaignId: string;
  status: SSEStatus;
  error: Error | null;
  reconnectAttempts: number;
}

export type CampaignUpdateCallback = (update: CampaignUpdate) => void;

export interface UseCampaignSSEResult {
  /** Number of active SSE connections */
  activeConnections: number;

  /** Map of campaign ID to connection status */
  connectionStatus: Map<string, CampaignConnectionStatus>;

  /** Manually disconnect from a specific campaign */
  disconnect: (campaignId: string) => void;

  /** Manually reconnect to a specific campaign */
  reconnect: (campaignId: string) => void;

  /** Disconnect from all campaigns */
  disconnectAll: () => void;
}

/**
 * Hook for managing SSE connections to multiple campaigns
 *
 * @param campaigns - Array of campaign objects
 * @param onUpdate - Callback when campaign data updates
 * @param authToken - JWT authentication token
 * @param apiBaseUrl - Base API URL (e.g., 'https://api.ailabsafrica.com')
 */
export function useCampaignSSE(
  campaigns: Campaign[],
  onUpdate: CampaignUpdateCallback,
  authToken: string | null,
  apiBaseUrl: string
): UseCampaignSSEResult {
  const [connectionStatus, setConnectionStatus] = useState<Map<string, CampaignConnectionStatus>>(
    new Map()
  );

  // Track active connections
  const connectionsRef = useRef<Map<string, {
    disconnect: () => void;
    reconnect: () => void;
  }>>(new Map());

  // Base API URL
  const baseUrl = apiBaseUrl;

  /**
   * Create SSE connection for a single campaign
   */
  const createConnection = useCallback((campaign: Campaign) => {
    const campaignId = campaign.id;

    // Build SSE URL
    const url = `${baseUrl}/sms-campaigns/${campaignId}/status-stream`;

    // Connection management functions
    let disconnectFn: (() => void) | null = null;
    let reconnectFn: (() => void) | null = null;

    // Update connection status
    const updateStatus = (status: SSEStatus, error: Error | null = null, attempts: number = 0) => {
      setConnectionStatus(prev => {
        const newMap = new Map(prev);
        newMap.set(campaignId, {
          campaignId,
          status,
          error,
          reconnectAttempts: attempts
        });
        return newMap;
      });
    };

    // Handle message
    const handleMessage = (data: CampaignUpdate) => {
      // Normalize campaign ID field
      const update = {
        ...data,
        id: data.id || data.campaign_id || campaignId
      };

      onUpdate(update);
    };

    // Handle error
    const handleError = (error: Error) => {
      console.error(`SSE error for campaign ${campaignId}:`, error);
    };

    // Handle connection open
    const handleOpen = () => {
      console.log(`✅ SSE connected for campaign ${campaignId}`);
      updateStatus('connected');
    };

    // Handle connection close
    const handleClose = () => {
      console.log(`🔌 SSE disconnected for campaign ${campaignId}`);
      updateStatus('disconnected');
    };

    // Use the generic SSE hook (we'll manage this differently)
    // For now, create a manual EventSource
    let eventSource: EventSource | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;
    let reconnectAttempts = 0;

    const connect = () => {
      if (eventSource) {
        eventSource.close();
      }

      try {
        const fullUrl = authToken
          ? `${url}?token=${encodeURIComponent(authToken)}`
          : url;

        eventSource = new EventSource(fullUrl);
        updateStatus('connecting');

        eventSource.onopen = () => {
          handleOpen();
          reconnectAttempts = 0;
        };

        eventSource.onmessage = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            if (!data._keepalive) {
              handleMessage(data);
            }
          } catch (error) {
            console.error('Error parsing SSE message:', error);
          }
        };

        eventSource.onerror = (event) => {
          handleError(new Error('SSE connection error'));
          eventSource?.close();
          eventSource = null;

          // Auto-reconnect with exponential backoff
          reconnectAttempts++;
          const delay = Math.min(3000 * Math.pow(2, reconnectAttempts - 1), 60000);

          if (reconnectAttempts <= 10) {
            console.log(`🔄 Reconnecting SSE for campaign ${campaignId} in ${delay}ms... (attempt ${reconnectAttempts}/10)`);
            updateStatus('error', new Error('Connection lost'), reconnectAttempts);

            reconnectTimeout = setTimeout(() => {
              connect();
            }, delay);
          } else {
            console.error(`❌ Max reconnection attempts reached for campaign ${campaignId}`);
            updateStatus('error', new Error('Max reconnection attempts reached'), reconnectAttempts);
          }
        };
      } catch (error) {
        handleError(error instanceof Error ? error : new Error('Failed to create EventSource'));
        updateStatus('error', error instanceof Error ? error : new Error('Connection failed'));
      }
    };

    // Disconnect function
    disconnectFn = () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }

      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }

      handleClose();
    };

    // Reconnect function
    reconnectFn = () => {
      disconnectFn?.();
      reconnectAttempts = 0;
      connect();
    };

    // Start connection
    connect();

    // Store connection controls
    connectionsRef.current.set(campaignId, {
      disconnect: disconnectFn,
      reconnect: reconnectFn
    });

    // Return cleanup function
    return () => {
      disconnectFn?.();
      connectionsRef.current.delete(campaignId);
    };
  }, [baseUrl, authToken, onUpdate]);

  /**
   * Disconnect from a specific campaign
   */
  const disconnect = useCallback((campaignId: string) => {
    const connection = connectionsRef.current.get(campaignId);
    if (connection) {
      connection.disconnect();
      connectionsRef.current.delete(campaignId);

      setConnectionStatus(prev => {
        const newMap = new Map(prev);
        newMap.delete(campaignId);
        return newMap;
      });
    }
  }, []);

  /**
   * Reconnect to a specific campaign
   */
  const reconnect = useCallback((campaignId: string) => {
    const connection = connectionsRef.current.get(campaignId);
    if (connection) {
      connection.reconnect();
    }
  }, []);

  /**
   * Disconnect from all campaigns
   */
  const disconnectAll = useCallback(() => {
    connectionsRef.current.forEach((connection) => {
      connection.disconnect();
    });
    connectionsRef.current.clear();
    setConnectionStatus(new Map());
  }, []);

  /**
   * Effect to manage connections based on running campaigns
   */
  useEffect(() => {
    // Get running campaign IDs
    const runningCampaignIds = campaigns
      .filter(c => c.status === 'running')
      .map(c => c.id);

    // Connect to new running campaigns
    runningCampaignIds.forEach(campaignId => {
      if (!connectionsRef.current.has(campaignId)) {
        const campaign = campaigns.find(c => c.id === campaignId);
        if (campaign) {
          createConnection(campaign);
        }
      }
    });

    // Disconnect from campaigns that are no longer running
    connectionsRef.current.forEach((_, campaignId) => {
      if (!runningCampaignIds.includes(campaignId)) {
        disconnect(campaignId);
      }
    });
  }, [campaigns, createConnection, disconnect]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      disconnectAll();
    };
  }, [disconnectAll]);

  return {
    activeConnections: connectionsRef.current.size,
    connectionStatus,
    disconnect,
    reconnect,
    disconnectAll
  };
}
