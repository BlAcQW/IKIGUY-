import crypto from 'node:crypto';
import { URL } from 'node:url';
import dns from 'node:dns/promises';
import net from 'node:net';

const TOOL_TIMEOUT_MS = 30_000;

/** CIDR ranges that must never be reached by tool server calls. */
const BLOCKED_CIDRS = [
  // Loopback
  { prefix: '127.0.0.0', mask: 8 },
  // Link-local / cloud metadata (AWS, GCP, Azure)
  { prefix: '169.254.0.0', mask: 16 },
  // RFC-1918 private ranges
  { prefix: '10.0.0.0', mask: 8 },
  { prefix: '172.16.0.0', mask: 12 },
  { prefix: '192.168.0.0', mask: 16 },
  // IPv6 loopback
  { prefix: '::1', mask: 128 },
  // IPv4-mapped IPv6
  { prefix: '::ffff:127.0.0.0', mask: 104 },
  { prefix: '::ffff:10.0.0.0', mask: 104 },
  { prefix: '::ffff:172.16.0.0', mask: 108 },
  { prefix: '::ffff:192.168.0.0', mask: 112 },
  { prefix: '::ffff:169.254.0.0', mask: 112 },
];

function ipToInt(ip: string): number {
  const parts = ip.split('.').map(Number);
  return ((parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]) >>> 0;
}

function isBlockedIPv4(ip: string): boolean {
  const ipInt = ipToInt(ip);
  for (const cidr of BLOCKED_CIDRS) {
    if (cidr.prefix.includes(':')) continue; // skip IPv6 entries
    const prefixInt = ipToInt(cidr.prefix);
    const mask = (~0 << (32 - cidr.mask)) >>> 0;
    if ((ipInt & mask) === (prefixInt & mask)) return true;
  }
  return false;
}

function isBlockedIP(ip: string): boolean {
  if (net.isIPv4(ip)) return isBlockedIPv4(ip);
  // For IPv6, block loopback and IPv4-mapped private addresses
  if (ip === '::1') return true;
  if (ip.startsWith('::ffff:')) {
    const v4Part = ip.slice(7);
    if (net.isIPv4(v4Part)) return isBlockedIPv4(v4Part);
  }
  // Block link-local IPv6
  if (ip.startsWith('fe80:')) return true;
  return false;
}

/**
 * Validate that a server URL does not resolve to a private/internal IP address.
 * Prevents SSRF attacks targeting cloud metadata services, internal networks, etc.
 */
async function validateServerUrl(serverUrl: string): Promise<void> {
  let parsed: URL;
  try {
    parsed = new URL(serverUrl);
  } catch {
    throw new Error('Invalid server URL');
  }

  // Only allow http/https
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new Error(`Unsupported protocol: ${parsed.protocol}`);
  }

  // Strip brackets from IPv6 hostnames (URL parser keeps them)
  const hostname = parsed.hostname.replace(/^\[|\]$/g, '');

  // If the hostname is already an IP, check directly
  if (net.isIP(hostname)) {
    if (isBlockedIP(hostname)) {
      throw new Error('Server URL resolves to a blocked internal address');
    }
    return;
  }

  // Resolve DNS and check all addresses
  try {
    const addresses = await dns.resolve4(hostname).catch(() => [] as string[]);
    const addresses6 = await dns.resolve6(hostname).catch(() => [] as string[]);
    const allAddresses = [...addresses, ...addresses6];

    if (allAddresses.length === 0) {
      throw new Error('Server URL hostname could not be resolved');
    }

    for (const addr of allAddresses) {
      if (isBlockedIP(addr)) {
        throw new Error('Server URL resolves to a blocked internal address');
      }
    }
  } catch (err) {
    if (err instanceof Error && err.message.includes('blocked')) throw err;
    if (err instanceof Error && err.message.includes('could not be resolved')) throw err;
    throw new Error('Failed to validate server URL');
  }
}

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

  // SSRF protection: block requests to private/internal networks
  try {
    await validateServerUrl(tool.serverUrl);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Invalid server URL';
    return { success: false, output: `Tool server URL rejected: ${message}` };
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
