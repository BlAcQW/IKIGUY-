import OpenAI from 'openai';
import type { ChatCompletionMessageParam, ChatCompletionTool } from 'openai/resources/chat/completions.js';
import type { LLMProvider, Message, LLMOptions, LLMChatResult } from './types.js';

function toOpenAIMessages(messages: Message[]): ChatCompletionMessageParam[] {
  return messages.map((m) => {
    switch (m.role) {
      case 'system':
        return { role: 'system' as const, content: m.content };
      case 'user':
        return { role: 'user' as const, content: m.content };
      case 'assistant':
        return { role: 'assistant' as const, content: m.content };
      case 'tool':
        return { role: 'tool' as const, content: m.content, tool_call_id: m.name ?? '' };
      default:
        return { role: 'user' as const, content: m.content };
    }
  });
}

function toOpenAITools(tools: LLMOptions['tools']): ChatCompletionTool[] | undefined {
  if (!tools || tools.length === 0) return undefined;
  return tools.map((tool) => ({
    type: 'function' as const,
    function: {
      name: tool.function.name,
      description: tool.function.description,
      parameters: tool.function.parameters as Record<string, unknown> | undefined,
    },
  }));
}

export class OpenAILLMProvider implements LLMProvider {
  readonly name = 'openai-gpt';
  private client: OpenAI;

  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey });
  }

  async chat(messages: Message[], options?: LLMOptions): Promise<string | LLMChatResult> {
    const openAITools = toOpenAITools(options?.tools);

    const response = await this.client.chat.completions.create({
      model: options?.model ?? 'gpt-4',
      messages: toOpenAIMessages(messages),
      temperature: options?.temperature ?? 0.7,
      max_tokens: options?.maxTokens ?? 1000,
      ...(openAITools ? { tools: openAITools } : {}),
    });

    const choice = response.choices[0]?.message;

    // If tools were provided, return structured result
    if (openAITools) {
      const toolCalls = (choice?.tool_calls ?? []).map((tc) => ({
        id: tc.id,
        name: tc.function.name,
        arguments: tc.function.arguments,
      }));
      return {
        content: choice?.content ?? null,
        toolCalls,
      };
    }

    // No tools — return plain string for backward compatibility
    return choice?.content ?? '';
  }

  async *chatStream(messages: Message[], options?: LLMOptions): AsyncIterable<string> {
    const stream = await this.client.chat.completions.create({
      model: options?.model ?? 'gpt-4',
      messages: toOpenAIMessages(messages),
      temperature: options?.temperature ?? 0.7,
      max_tokens: options?.maxTokens ?? 1000,
      stream: true,
    });

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content;
      if (content) {
        yield content;
      }
    }
  }
}
