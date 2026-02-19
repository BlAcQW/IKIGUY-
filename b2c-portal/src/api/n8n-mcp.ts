import type { NextApiRequest, NextApiResponse } from 'next';

interface N8nMcpRequest {
  command: string;
  params: any;
}

interface N8nMcpResponse {
  success: boolean;
  data?: any;
  error?: string;
}

const N8N_MCP_COMMANDS = {
  get_template: 'mcp__n8n-mcp__get_template',
  search_templates: 'mcp__n8n-mcp__search_templates',
  list_templates: 'mcp__n8n-mcp__list_templates',
  n8n_create_workflow: 'mcp__n8n-mcp__n8n_create_workflow',
  n8n_get_workflow: 'mcp__n8n-mcp__n8n_get_workflow',
  n8n_list_workflows: 'mcp__n8n-mcp__n8n_list_workflows',
  validate_workflow: 'mcp__n8n-mcp__validate_workflow'
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<N8nMcpResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed'
    });
  }

  try {
    const { command, params }: N8nMcpRequest = req.body;

    if (!command || !(command in N8N_MCP_COMMANDS)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid command'
      });
    }

    const mcpCommand = N8N_MCP_COMMANDS[command as keyof typeof N8N_MCP_COMMANDS];

    const result = await executeN8nMcpCommand(mcpCommand, params);

    return res.status(200).json({
      success: true,
      data: result
    });

  } catch (error) {
    console.error('N8n MCP API error:', error);
    return res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Internal server error'
    });
  }
}

async function executeN8nMcpCommand(command: string, params: any): Promise<any> {
  const mcpUrl = process.env.N8N_MCP_URL || 'http://localhost:3845';

  const payload = {
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: {
      name: command,
      arguments: params || {}
    }
  };

  const response = await fetch(`${mcpUrl}/mcp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.N8N_MCP_TOKEN || ''}`
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`MCP request failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();

  if (data.error) {
    throw new Error(`MCP error: ${data.error.message || data.error}`);
  }

  return data.result;
}