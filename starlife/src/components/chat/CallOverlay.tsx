import { Mic, MicOff, PhoneOff } from 'lucide-react';
import { CHAT_CONFIG } from '@/data/chat';
import type { CallStatus } from '@/hooks/useVapiCall';

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

interface CallOverlayProps {
  status: CallStatus;
  isMuted: boolean;
  duration: number;
  onToggleMute: () => void;
  onEndCall: () => void;
}

export function CallOverlay({
  status,
  isMuted,
  duration,
  onToggleMute,
  onEndCall,
}: CallOverlayProps) {
  const statusText =
    status === 'connecting'
      ? CHAT_CONFIG.call.connectingText
      : status === 'active'
        ? CHAT_CONFIG.call.connectedText
        : CHAT_CONFIG.call.endedText;

  return (
    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-gray-50/95 backdrop-blur-sm">
      {/* Pulse ring */}
      <div className="relative mb-6 flex h-24 w-24 items-center justify-center">
        {status === 'connecting' && (
          <span className="absolute inset-0 animate-call-connecting rounded-full bg-gold/30" />
        )}
        {status === 'active' && (
          <span className="absolute inset-0 animate-call-pulse rounded-full bg-navy/20" />
        )}
        <div
          className={`relative flex h-20 w-20 items-center justify-center rounded-full ${
            status === 'ended' ? 'bg-gray-300' : 'bg-navy'
          }`}
        >
          <Mic className={`h-8 w-8 ${status === 'ended' ? 'text-gray-500' : 'text-gold'}`} />
        </div>
      </div>

      {/* Status text */}
      <p className="mb-1 text-sm font-semibold text-navy">{statusText}</p>

      {/* Duration */}
      {(status === 'active' || status === 'ended') && (
        <p className="mb-6 font-mono text-xs text-gray-500">{formatDuration(duration)}</p>
      )}
      {status === 'connecting' && <p className="mb-6 text-xs text-gray-400">Requesting mic...</p>}

      {/* Controls */}
      {status !== 'ended' && (
        <div className="flex items-center gap-4">
          <button
            onClick={onToggleMute}
            disabled={status !== 'active'}
            aria-label={isMuted ? 'Unmute' : 'Mute'}
            className={`flex h-12 w-12 items-center justify-center rounded-full transition-colors ${
              isMuted
                ? 'bg-red-100 text-red-600 hover:bg-red-200'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            } disabled:opacity-40`}
          >
            {isMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </button>

          <button
            onClick={onEndCall}
            aria-label="End call"
            className="flex h-12 w-12 items-center justify-center rounded-full bg-red-500 text-white transition-colors hover:bg-red-600"
          >
            <PhoneOff className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
}
