import crypto from 'node:crypto';

const TOOL_TIMEOUT_MS = 30_000;

interface ToolDefinition {
  id: string;
  type: 'FUNCTION' | 'TRANSFER_CALL' | 'END_CALL';
  name: string;
  serverUrl?: string | null;
  serverSecret?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface ToolExecutionResult {
  success: boolean;
  output: string | Record<string, unknown>;
  signal?: 'transfer_call' | 'end_call';
  targetAssistantId?: string;
}

export async function executeTool(
  tool: ToolDefinition,
  argsJson: string,
  sessionId: string,
): Promise<ToolExecutionResult> {
  switch (tool.type) {
    case 'FUNCTION':
      return executeFunctionTool(tool, argsJson, sessionId);
    case 'TRANSFER_CALL':
      return executeTransferCallTool(tool, argsJson);
    case 'END_CALL':
      return executeEndCallTool(argsJson);
    default:
      return { success: false, output: `Unknown tool type: ${tool.type}` };
  }
}

async function executeFunctionTool(
  tool: ToolDefinition,
  argsJson: string,
  sessionId: string,
): Promise<ToolExecutionResult> {
  if (!tool.serverUrl) {
    return { success: false, output: 'Tool has no server URL configured' };
  }

  const body = JSON.stringify({
    toolId: tool.id,
    toolName: tool.name,
    arguments: safeParseJson(argsJson),
    sessionId,
  });

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (tool.serverSecret) {
    const signature = crypto
      .createHmac('sha256', tool.serverSecret)
      .update(body)
      .digest('hex');
    headers['X-Load-Signature'] = `sha256=${signature}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TOOL_TIMEOUT_MS);

  try {
    const response = await fetch(tool.serverUrl, {
      method: 'POST',
      headers,
      body,
      signal: controller.signal,
    });

    const responseText = await response.text();
    let responseData: Record<string, unknown>;
    try {
      responseData = JSON.parse(responseText);
    } catch {
      responseData = { raw: responseText };
    }

    if (!response.ok) {
      return {
        success: false,
        output: responseData.error
          ? String(responseData.error)
          : `Tool server returned ${response.status}`,
      };
    }

    return {
      success: true,
      output: responseData.result !== undefined ? responseData.result as string : responseData,
    };
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      return { success: false, output: 'Tool execution timed out' };
    }
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { success: false, output: `Tool execution failed: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}

function executeTransferCallTool(
  tool: ToolDefinition,
  argsJson: string,
): Promise<ToolExecutionResult> {
  const args = safeParseJson(argsJson);
  const targetAssistantId = (tool.metadata as Record<string, unknown>)?.targetAssistantId as string | undefined;

  if (!targetAssistantId) {
    return Promise.resolve({
      success: false,
      output: 'Transfer tool has no targetAssistantId configured in metadata',
    });
  }

  return Promise.resolve({
    success: true,
    output: `Transferring call to assistant. Reason: ${args.reason ?? 'not specified'}`,
    signal: 'transfer_call' as const,
    targetAssistantId,
  });
}

function executeEndCallTool(argsJson: string): Promise<ToolExecutionResult> {
  const args = safeParseJson(argsJson);
  return Promise.resolve({
    success: true,
    output: `Ending call. Reason: ${args.reason ?? 'not specified'}`,
    signal: 'end_call' as const,
  });
}

function safeParseJson(json: string): Record<string, unknown> {
  try {
    return JSON.parse(json);
  } catch {
    return {};
  }
}
