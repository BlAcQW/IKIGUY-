const VAPI_API_URL = '/api/vapi/chat';
const ASSISTANT_ID = 'dabccfdc-f6d5-45dc-9699-c8aed7a15058';
const TIMEOUT_MS = 30_000;

interface ChatOutput {
  role: string;
  content: string;
}

export interface ChatResponse {
  id: string;
  output: ChatOutput[];
}

export async function sendMessage(
  input: string,
  previousChatId?: string,
): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const body: Record<string, string> = {
      assistantId: ASSISTANT_ID,
      input,
    };

    if (previousChatId) {
      body.previousChatId = previousChatId;
    }

    const response = await fetch(VAPI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text();
      console.error('[vapi-chat]', response.status, text);
      throw new Error(`Chat API error: ${response.status}`);
    }

    return (await response.json()) as ChatResponse;
  } finally {
    clearTimeout(timeout);
  }
}
