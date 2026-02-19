/**
 * useSSE - Generic Server-Sent Events (SSE) Hook
 *
 * A reusable React hook for managing EventSource connections with automatic
 * reconnection, error handling, and cleanup.
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - TypeScript generics for type-safe event data
 * - Authentication support (JWT via query parameter)
 * - Connection status tracking
 * - Automatic cleanup on unmount
 *
 * @example
 * ```typescript
 * interface CampaignUpdate {
 *   status: string;
 *   progress: number;
 * }
 *
 * const { status, error, reconnect } = useSSE<CampaignUpdate>({
 *   url: '/api/campaigns/abc123/status-stream',
 *   authToken: 'jwt_token',
 *   onMessage: (data) => console.log('Received:', data),
 *   onError: (error) => console.error('Error:', error)
 * });
 * ```
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export type SSEStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface UseSSEOptions<T> {
  /** SSE endpoint URL (null to disable connection) */
  url: string | null;

  /** Callback when message received */
  onMessage: (data: T) => void;

  /** Callback when error occurs (optional) */
  onError?: (error: Error) => void;

  /** Callback when connection opens (optional) */
  onOpen?: () => void;

  /** Callback when connection closes (optional) */
  onClose?: () => void;

  /** JWT authentication token (optional) */
  authToken?: string | null;

  /** Initial reconnect delay in ms (default: 3000) */
  reconnectDelay?: number;

  /** Maximum reconnect delay in ms (default: 60000) */
  maxReconnectDelay?: number;

  /** Maximum reconnection attempts (default: 10, 0 = infinite) */
  maxReconnectAttempts?: number;
}

export interface UseSSEResult {
  /** Current connection status */
  status: SSEStatus;

  /** Last error (if any) */
  error: Error | null;

  /** Reconnection attempt count */
  reconnectAttempts: number;

  /** Manually trigger reconnection */
  reconnect: () => void;

  /** Manually disconnect */
  disconnect: () => void;
}

/**
 * Generic SSE hook for real-time event streaming
 */
export function useSSE<T>({
  url,
  onMessage,
  onError,
  onOpen,
  onClose,
  authToken,
  reconnectDelay = 3000,
  maxReconnectDelay = 60000,
  maxReconnectAttempts = 10
}: UseSSEOptions<T>): UseSSEResult {
  const [status, setStatus] = useState<SSEStatus>('disconnected');
  const [error, setError] = useState<Error | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isManualDisconnectRef = useRef(false);

  /**
   * Calculate reconnect delay with exponential backoff
   */
  const getReconnectDelay = useCallback((attempts: number): number => {
    const delay = reconnectDelay * Math.pow(2, attempts);
    return Math.min(delay, maxReconnectDelay);
  }, [reconnectDelay, maxReconnectDelay]);

  /**
   * Connect to SSE endpoint
   */
  const connect = useCallback(() => {
    // Don't connect if URL is null or we're manually disconnected
    if (!url || isManualDisconnectRef.current) {
      return;
    }

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    try {
      setStatus('connecting');
      setError(null);

      // Build URL with auth token if provided
      const fullUrl = authToken
        ? `${url}${url.includes('?') ? '&' : '?'}token=${encodeURIComponent(authToken)}`
        : url;

      console.log(`✅ SSE connecting to: ${url.split('?')[0]}`);

      const eventSource = new EventSource(fullUrl);
      eventSourceRef.current = eventSource;

      // Connection opened
      eventSource.onopen = () => {
        console.log(`✅ SSE connected: ${url.split('?')[0]}`);
        setStatus('connected');
        setReconnectAttempts(0);
        onOpen?.();
      };

      // Message received
      eventSource.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data) as T;

          // Ignore keep-alive messages
          if ((data as any)._keepalive) {
            return;
          }

          console.log(`📥 SSE message received from ${url.split('?')[0]}`);
          onMessage(data);
        } catch (parseError) {
          console.error('Error parsing SSE message:', parseError);
          const err = parseError instanceof Error
            ? parseError
            : new Error('Failed to parse SSE message');
          onError?.(err);
        }
      };

      // Connection error
      eventSource.onerror = (event) => {
        console.error(`❌ SSE error: ${url.split('?')[0]}`, event);

        const err = new Error('SSE connection error');
        setError(err);
        setStatus('error');
        onError?.(err);

        // Close the connection
        eventSource.close();
        eventSourceRef.current = null;

        // Attempt to reconnect if not manually disconnected
        if (!isManualDisconnectRef.current) {
          const currentAttempts = reconnectAttempts + 1;
          setReconnectAttempts(currentAttempts);

          // Check if we've exceeded max attempts
          if (maxReconnectAttempts > 0 && currentAttempts >= maxReconnectAttempts) {
            console.error(`❌ Max reconnection attempts (${maxReconnectAttempts}) reached`);
            setStatus('disconnected');
            return;
          }

          // Schedule reconnection
          const delay = getReconnectDelay(currentAttempts);
          console.log(`🔄 Reconnecting SSE in ${delay}ms... (attempt ${currentAttempts}/${maxReconnectAttempts || '∞'})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    } catch (err) {
      console.error('Error creating EventSource:', err);
      const error = err instanceof Error ? err : new Error('Failed to create EventSource');
      setError(error);
      setStatus('error');
      onError?.(error);
    }
  }, [url, authToken, onMessage, onError, onOpen, reconnectAttempts, getReconnectDelay, maxReconnectAttempts]);

  /**
   * Disconnect from SSE endpoint
   */
  const disconnect = useCallback(() => {
    console.log(`🔌 SSE manually disconnected: ${url?.split('?')[0]}`);

    isManualDisconnectRef.current = true;

    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close EventSource
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setStatus('disconnected');
    setReconnectAttempts(0);
    onClose?.();
  }, [url, onClose]);

  /**
   * Manually trigger reconnection
   */
  const reconnect = useCallback(() => {
    console.log(`🔄 SSE manual reconnect: ${url?.split('?')[0]}`);
    isManualDisconnectRef.current = false;
    setReconnectAttempts(0);
    disconnect();
    connect();
  }, [url, connect, disconnect]);

  /**
   * Effect to manage connection lifecycle
   */
  useEffect(() => {
    // Reset manual disconnect flag when URL changes
    isManualDisconnectRef.current = false;

    // Connect if URL is provided
    if (url) {
      connect();
    }

    // Cleanup on unmount or URL change
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [url, connect]);

  return {
    status,
    error,
    reconnectAttempts,
    reconnect,
    disconnect
  };
}
