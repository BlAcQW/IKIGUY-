import { GoogleGenerativeAI } from '@google/generative-ai';
import type { Content, Part, FunctionDeclaration } from '@google/generative-ai';
import type { LLMProvider, Message, LLMOptions, LLMChatResult, LLMToolCall } from './types.js';

function toGeminiContents(messages: Message[]): { contents: Content[]; systemInstruction: string | undefined } {
  const contents: Content[] = [];
  let systemInstruction: string | undefined;

  for (const m of messages) {
    if (m.role === 'system') {
      systemInstruction = m.content;
      continue;
    }

    const role = m.role === 'assistant' ? 'model' : 'user';
    contents.push({
      role,
      parts: [{ text: m.content }],
    });
  }

  return { contents, systemInstruction };
}

export class GoogleLLMProvider implements LLMProvider {
  readonly name = 'google-gemini';
  private ai: GoogleGenerativeAI;

  constructor(apiKey: string) {
    this.ai = new GoogleGenerativeAI(apiKey);
  }

  async chat(messages: Message[], options?: LLMOptions): Promise<string | LLMChatResult> {
    const { contents, systemInstruction } = toGeminiContents(messages);
    const modelName = options?.model ?? 'gemini-2.0-flash';

    // Build tool declarations for Gemini if tools are provided
    let tools: Array<{ functionDeclarations: FunctionDeclaration[] }> | undefined;
    if (options?.tools && options.tools.length > 0) {
      tools = [{
        functionDeclarations: options.tools.map((t) => ({
          name: t.function.name,
          description: t.function.description,
          parameters: t.function.parameters as FunctionDeclaration['parameters'],
        })),
      }];
    }

    const model = this.ai.getGenerativeModel({
      model: modelName,
      ...(systemInstruction ? { systemInstruction } : {}),
      generationConfig: {
        temperature: options?.temperature ?? 0.7,
        maxOutputTokens: options?.maxTokens ?? 1000,
      },
      ...(tools ? { tools } : {}),
    });

    const result = await model.generateContent({ contents });
    const response = result.response;
    const candidate = response.candidates?.[0];
    if (!candidate) return '';

    const parts: Part[] = candidate.content?.parts ?? [];
    const functionCallParts = parts.filter((p): p is Part & { functionCall: NonNullable<Part['functionCall']> } => !!p.functionCall);

    if (functionCallParts.length > 0 && tools) {
      const toolCalls: LLMToolCall[] = functionCallParts.map((p, i) => ({
        id: `call_${i}`,
        name: p.functionCall.name,
        arguments: JSON.stringify(p.functionCall.args ?? {}),
      }));

      const textParts = parts.filter((p): p is Part & { text: string } => typeof p.text === 'string');
      const content = textParts.map((p) => p.text).join('') || null;

      return { content, toolCalls };
    }

    // Plain text response
    const text = parts.map((p) => p.text ?? '').join('');
    if (tools) {
      return { content: text || null, toolCalls: [] };
    }
    return text;
  }

  async *chatStream(messages: Message[], options?: LLMOptions): AsyncIterable<string> {
    const { contents, systemInstruction } = toGeminiContents(messages);
    const modelName = options?.model ?? 'gemini-2.0-flash';

    const model = this.ai.getGenerativeModel({
      model: modelName,
      ...(systemInstruction ? { systemInstruction } : {}),
      generationConfig: {
        temperature: options?.temperature ?? 0.7,
        maxOutputTokens: options?.maxTokens ?? 1000,
      },
    });

    const result = await model.generateContentStream({ contents });

    for await (const chunk of result.stream) {
      const text = chunk.candidates?.[0]?.content?.parts?.[0]?.text;
      if (text) {
        yield text;
      }
    }
  }
}
