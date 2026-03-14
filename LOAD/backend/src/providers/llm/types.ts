export interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  name?: string;
}

export interface LLMOptions {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  tools?: LLMTool[];
}

export interface LLMTool {
  type: 'function';
  function: {
    name: string;
    description?: string;
    parameters?: Record<string, unknown>;
  };
}

export interface LLMToolCall {
  id: string;
  name: string;
  arguments: string;
}

export interface LLMChatResult {
  content: string | null;
  toolCalls: LLMToolCall[];
}

export interface LLMProvider {
  readonly name: string;
  chat(messages: Message[], options?: LLMOptions): Promise<string | LLMChatResult>;
  chatStream(messages: Message[], options?: LLMOptions): AsyncIterable<string>;
}
