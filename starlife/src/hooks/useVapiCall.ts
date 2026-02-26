import { useState, useCallback, useEffect, useRef } from 'react';
import {
  startCall as vapiStartCall,
  stopCall as vapiStopCall,
  toggleMute as vapiToggleMute,
  removeAllListeners as vapiRemoveAllListeners,
  getVapiInstance,
} from '@/lib/vapi-call';
import { CHAT_CONFIG } from '@/data/chat';
import type { ChatMessage } from '@/hooks/useChat';

export type CallStatus = 'idle' | 'connecting' | 'active' | 'ended';

interface CallState {
  status: CallStatus;
  isMuted: boolean;
  duration: number;
  error: string | null;
  transcripts: ChatMessage[];
}

const INITIAL_STATE: CallState = {
  status: 'idle',
  isMuted: false,
  duration: 0,
  error: null,
  transcripts: [],
};

export function useVapiCall() {
  const [state, setState] = useState<CallState>(INITIAL_STATE);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    clearTimer();
    timerRef.current = setInterval(() => {
      setState((prev) => ({ ...prev, duration: prev.duration + 1 }));
    }, 1000);
  }, [clearTimer]);

  const attachListeners = useCallback(() => {
    // Always clear existing listeners first to prevent accumulation on the singleton
    vapiRemoveAllListeners();

    const vapi = getVapiInstance();

    vapi.on('call-start', () => {
      console.log('[vapi-call] call-start');
      setState((prev) => ({ ...prev, status: 'active', error: null }));
      startTimer();
    });

    vapi.on('call-end', () => {
      console.log('[vapi-call] call-end');
      clearTimer();
      setState((prev) => ({ ...prev, status: 'ended', isMuted: false }));
      setTimeout(() => {
        setState((prev) =>
          prev.status === 'ended' ? { ...prev, status: 'idle', duration: 0 } : prev,
        );
      }, 2000);
    });

    vapi.on('message', (msg: Record<string, unknown>) => {
      if (
        msg.type === 'transcript' &&
        msg.transcriptType === 'final' &&
        typeof msg.transcript === 'string'
      ) {
        const role = msg.role === 'assistant' ? 'assistant' : 'user';
        const chatMsg: ChatMessage = {
          id: `call-${role}-${Date.now()}`,
          role: role as 'user' | 'assistant',
          content: msg.transcript,
        };
        setState((prev) => ({
          ...prev,
          transcripts: [...prev.transcripts, chatMsg],
        }));
      }
    });

    vapi.on('error', (err: unknown) => {
      console.error('[vapi-call] error', err);
      clearTimer();
      setState((prev) => ({
        ...prev,
        status: 'idle',
        error: CHAT_CONFIG.call.callFailedError,
        duration: 0,
        isMuted: false,
      }));
    });

    // Diagnostic events — surface SDK stage failures
    vapi.on('call-start-progress', (event) => {
      console.log('[vapi-call] progress', event.stage, event.status, event.duration ?? '', event.metadata ?? '');
    });

    vapi.on('call-start-failed', (event) => {
      console.error('[vapi-call] call-start-failed', {
        stage: event.stage,
        error: event.error,
        context: event.context,
        totalDuration: event.totalDuration,
      });
      clearTimer();
      setState((prev) => ({
        ...prev,
        status: 'idle',
        error: `Call failed at stage "${event.stage}": ${event.error}`,
        duration: 0,
        isMuted: false,
      }));
    });

    vapi.on('call-start-success', (event) => {
      console.log('[vapi-call] call-start-success', event.callId, `${event.totalDuration}ms`);
    });
  }, [startTimer, clearTimer]);

  const startCall = useCallback(async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setState((prev) => ({
        ...prev,
        error: CHAT_CONFIG.call.micPermissionError,
      }));
      return;
    }

    attachListeners();
    setState({
      ...INITIAL_STATE,
      status: 'connecting',
    });

    try {
      const call = await vapiStartCall();
      if (!call) {
        console.error('[vapi-call] start() resolved to null — call may already be active or SDK failed');
        setState((prev) => ({
          ...prev,
          status: 'idle',
          error: CHAT_CONFIG.call.callFailedError,
        }));
      }
    } catch (err) {
      console.error('[vapi-call] start() threw', err);
      setState((prev) => ({
        ...prev,
        status: 'idle',
        error: CHAT_CONFIG.call.callFailedError,
      }));
    }
  }, [attachListeners]);

  const endCall = useCallback(async () => {
    clearTimer();
    try {
      await vapiStopCall();
    } catch {
      // call may already be ended
    }
    setState((prev) => ({ ...prev, status: 'ended', isMuted: false }));
    setTimeout(() => {
      setState((prev) =>
        prev.status === 'ended' ? { ...prev, status: 'idle', duration: 0 } : prev,
      );
    }, 2000);
  }, [clearTimer]);

  const toggleMute = useCallback(() => {
    const nowMuted = vapiToggleMute();
    setState((prev) => ({ ...prev, isMuted: nowMuted }));
  }, []);

  // Cleanup on unmount — remove listeners from singleton to prevent stale closures
  useEffect(() => {
    return () => {
      clearTimer();
      vapiRemoveAllListeners();
      vapiStopCall().catch(() => {
        // ignore — call may not be active
      });
    };
  }, [clearTimer]);

  return {
    status: state.status,
    isMuted: state.isMuted,
    duration: state.duration,
    error: state.error,
    transcripts: state.transcripts,
    startCall,
    endCall,
    toggleMute,
  };
}
