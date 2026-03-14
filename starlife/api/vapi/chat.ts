import type { VercelRequest, VercelResponse } from '@vercel/node';

const VAPI_API_URL = 'https://api.vapi.ai/chat';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.VAPI_PRIVATE_KEY;

  if (!apiKey) {
    console.error('[vapi-chat] VAPI_PRIVATE_KEY is not set');
    return res.status(500).json({ error: 'Server configuration error' });
  }

  try {
    const response = await fetch(VAPI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(req.body),
    });

    const data = await response.text();

    if (!response.ok) {
      console.error('[vapi-chat] Vapi API error:', response.status, data);
      return res.status(response.status).json({ error: 'Upstream API error' });
    }

    return res.status(200).json(JSON.parse(data));
  } catch (error) {
    console.error('[vapi-chat] Proxy error:', error);
    return res.status(502).json({ error: 'Failed to reach chat service' });
  }
}
