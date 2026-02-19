/**
 * Shared Hooks
 */

export { useVoiceWebSocket } from './useVoiceWebSocket';
export type { UseVoiceWebSocketOptions } from './useVoiceWebSocket';

export { useVoiceWebRTC } from './useVoiceWebRTC';
export type { UseVoiceWebRTCOptions } from './useVoiceWebRTC';

export { useLLMChat } from './useLLMChat';
export type { UseLLMChatOptions, UseLLMChatResult, ChatMessage } from './useLLMChat';

export { useASRStreaming } from './useASRStreaming';
export type { UseASRStreamingOptions, UseASRStreamingResult, ASRMode, TranscriptSegment } from './useASRStreaming';

export { useSSE } from './useSSE';
export type { UseSSEOptions, UseSSEResult, SSEStatus } from './useSSE';

export { useCampaignSSE } from './useCampaignSSE';
export type {
  UseCampaignSSEResult,
  CampaignUpdateCallback,
  CampaignConnectionStatus,
  Campaign,
  CampaignUpdate
} from './useCampaignSSE';
