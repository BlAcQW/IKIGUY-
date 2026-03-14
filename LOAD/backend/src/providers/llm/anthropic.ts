import Anthropic from '@anthropic-ai/sdk';
import type { LLMProvider, Message, LLMOptions, LLMChatResult, LLMToolCall } from './types.js';

function toAnthropicMessages(messages: Message[]) {
  const anthropicMessages: Array<{ role: 'user' | 'assistant'; content: string }> = [];
  let systemPrompt: string | undefined;

  for (const m of messages) {
    if (m.role === 'system') {
      systemPrompt = m.content;
      continue;
    }

    const role = m.role === 'user' || m.role === 'tool' ? 'user' : 'assistant';
    anthropicMessages.push({ role, content: m.content });
  }

  return { messages: anthropicMessages, systemPrompt };
}

export class AnthropicLLMProvider implements LLMProvider {
  readonly name = 'anthropic-claude';
  private client: Anthropic;

  constructor(apiKey: string) {
    this.client = new Anthropic({ apiKey });
  }

  async chat(messages: Message[], options?: LLMOptions): Promise<string | LLMChatResult> {
    const { messages: anthropicMessages, systemPrompt } = toAnthropicMessages(messages);
    const model = options?.model ?? 'claude-sonnet-4-20250514';

    // Build tools for Anthropic if provided
    let tools: Anthropic.Messages.Tool[] | undefined;
    if (options?.tools && options.tools.length > 0) {
      tools = options.tools.map((t) => ({
        name: t.function.name,
        description: t.function.description ?? '',
        input_schema: {
          type: 'object' as const,
          ...(t.function.parameters ?? { properties: {} }),
        },
      }));
    }

    const response = await this.client.messages.create({
      model,
      max_tokens: options?.maxTokens ?? 1000,
      messages: anthropicMessages,
      ...(systemPrompt ? { system: systemPrompt } : {}),
      ...(tools ? { tools } : {}),
      temperature: options?.temperature ?? 0.7,
    });

    // Extract tool use blocks
    const toolUseBlocks = response.content.filter((b) => b.type === 'tool_use');
    const textBlocks = response.content.filter((b) => b.type === 'text');

    if (toolUseBlocks.length > 0 && tools) {
      const toolCalls: LLMToolCall[] = toolUseBlocks.map((b) => ({
        id: b.id,
        name: b.name,
        arguments: JSON.stringify(b.input),
      }));

      const content = textBlocks.map((b) => b.text).join('') || null;
      return { content, toolCalls };
    }

    const text = textBlocks.map((b) => b.text).join('');
    if (tools) {
      return { content: text || null, toolCalls: [] };
    }
    return text;
  }

  async *chatStream(messages: Message[], options?: LLMOptions): AsyncIterable<string> {
    const { messages: anthropicMessages, systemPrompt } = toAnthropicMessages(messages);
    const model = options?.model ?? 'claude-sonnet-4-20250514';

    const stream = this.client.messages.stream({
      model,
      max_tokens: options?.maxTokens ?? 1000,
      messages: anthropicMessages,
      ...(systemPrompt ? { system: systemPrompt } : {}),
      temperature: options?.temperature ?? 0.7,
    });

    for await (const event of stream) {
      if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
        yield event.delta.text;
      }
    }
  }
}
