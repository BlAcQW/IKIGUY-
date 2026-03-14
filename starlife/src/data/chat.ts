export const CHAT_CONFIG = {
  title: 'StarLife Assistant',
  subtitle: 'How can we help you today?',
  welcomeMessage:
    'Hello! I\'m your StarLife assistant. Ask me anything about our insurance products, claims, or services.',
  placeholder: 'Type your message...',
  errorMessage: 'Something went wrong. Please try again.',
  timeoutMessage: 'Request timed out. Please try again.',
  call: {
    connectingText: 'Connecting...',
    connectedText: 'Connected',
    endedText: 'Call ended',
    micPermissionError: 'Microphone access is required to start a voice call.',
    callFailedError: 'Failed to start call. Please try again.',
    callTooltip: 'Start voice call',
  },
} as const;
