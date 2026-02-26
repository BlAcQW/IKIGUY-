#!/usr/bin/env tsx
/**
 * WebSocket voice call test client.
 *
 * Connects to a running LOAD backend, authenticates via login API,
 * starts a WebSocket call session, sends audio, and receives responses.
 *
 * Requires a running backend and valid user credentials.
 *
 * Run: npx tsx scripts/test-ws-client.ts [options]
 *
 * Options:
 *   --url <url>              Backend URL (default: http://localhost:3000)
 *   --email <email>          User email for login
 *   --password <password>    User password for login
 *   --token <jwt>            Use existing JWT (skip login)
 *   --assistant-id <id>      Assistant ID to call
 *   --input <file>           WAV file to send (default: test fixture)
 *   --rounds <n>             Number of audio rounds to send (default: 1)
 */

import { config as dotenvConfig } from 'dotenv';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { readFileSync, existsSync } from 'fs';
import WebSocket from 'ws';

const __dirname_ = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

dotenvConfig({ path: resolve(__dirname_, '..', '.env') });

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

interface Options {
  url: string;
  email?: string;
  password?: string;
  token?: string;
  assistantId?: string;
  inputFile?: string;
  rounds: number;
}

function parseArgs(): Options {
  const args = process.argv.slice(2);
  const opts: Options = {
    url: 'http://localhost:3000',
    rounds: 1,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--url':
        opts.url = args[++i];
        break;
      case '--email':
        opts.email = args[++i];
        break;
      case '--password':
        opts.password = args[++i];
        break;
      case '--token':
        opts.token = args[++i];
        break;
      case '--assistant-id':
        opts.assistantId = args[++i];
        break;
      case '--input':
        opts.inputFile = args[++i];
        break;
      case '--rounds':
        opts.rounds = parseInt(args[++i], 10);
        break;
      case '--help':
      case '-h':
        console.log(`
Usage: npx tsx scripts/test-ws-client.ts [options]

Options:
  --url <url>              Backend URL (default: http://localhost:3000)
  --email <email>          User email for login
  --password <password>    User password for login
  --token <jwt>            Use existing JWT (skip login)
  --assistant-id <id>      Assistant ID to call
  --input <file>           WAV file to send (default: test fixture)
  --rounds <n>             Audio rounds to send (default: 1)

Example:
  npx tsx scripts/test-ws-client.ts \\
    --email test@example.com --password testpass \\
    --assistant-id abc123
`);
        process.exit(0);
    }
  }

  return opts;
}

// ---------------------------------------------------------------------------
// Login
// ---------------------------------------------------------------------------

async function login(baseUrl: string, email: string, password: string): Promise<string> {
  console.log(`  Logging in as ${email}...`);

  const res = await fetch(`${baseUrl}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Login failed (${res.status}): ${body}`);
  }

  const data = (await res.json()) as { data?: { token?: string } };
  const token = data.data?.token;
  if (!token) {
    throw new Error('Login response missing token');
  }

  console.log('  Login successful.');
  return token;
}

// ---------------------------------------------------------------------------
// WebSocket client
// ---------------------------------------------------------------------------

async function runWebSocketTest(opts: Options, token: string): Promise<void> {
  // Load audio
  let audioBuffer: Buffer;
  if (opts.inputFile) {
    audioBuffer = readFileSync(opts.inputFile);
  } else {
    const fixturePath = resolve(__dirname_, '..', 'tests', 'integration', 'fixtures', 'hello-16k-mono.wav');
    if (!existsSync(fixturePath)) {
      console.error('Test fixture not found. Run: npx tsx tests/integration/fixtures/generate-audio.ts');
      process.exit(1);
    }
    audioBuffer = readFileSync(fixturePath);
  }

  // Strip WAV header (44 bytes) to get raw PCM
  const pcmData = audioBuffer.subarray(44);

  const wsUrl = opts.url.replace(/^http/, 'ws') + '/api/calls/web';
  console.log(`\n  Connecting to ${wsUrl}...`);

  return new Promise<void>((resolvePromise, rejectPromise) => {
    const ws = new WebSocket(wsUrl, {
      headers: { Authorization: `Bearer ${token}` },
    });

    let responsesReceived = 0;
    let roundsSent = 0;
    const timeout = setTimeout(() => {
      console.error('\n  TIMEOUT: No response received within 30s');
      ws.close();
      rejectPromise(new Error('Timeout'));
    }, 30_000);

    ws.on('open', () => {
      console.log('  Connected.\n');

      // Send start message
      const startMsg = JSON.stringify({
        type: 'start',
        assistantId: opts.assistantId,
      });
      ws.send(startMsg);
      console.log('  Sent: start message');

      // Send audio after a brief delay
      setTimeout(() => {
        sendAudioRound();
      }, 500);
    });

    function sendAudioRound(): void {
      if (roundsSent >= opts.rounds) return;

      roundsSent++;
      console.log(`\n  Sending audio round ${roundsSent}/${opts.rounds} (${pcmData.length} bytes)...`);

      // Send audio in chunks (simulating real-time streaming)
      const chunkSize = 3200; // 100ms at 16kHz 16-bit
      let offset = 0;

      const interval = setInterval(() => {
        if (offset >= pcmData.length) {
          clearInterval(interval);
          // Send end-of-audio marker
          ws.send(JSON.stringify({ type: 'audio_end' }));
          console.log('  Audio sent.');
          return;
        }

        const chunk = pcmData.subarray(offset, offset + chunkSize);
        ws.send(chunk);
        offset += chunkSize;
      }, 100);
    }

    ws.on('message', (data: Buffer | string) => {
      if (typeof data === 'string' || (data instanceof Buffer && data[0] === 0x7b)) {
        // JSON message
        const msg = JSON.parse(data.toString());
        console.log(`  Received JSON: ${JSON.stringify(msg).substring(0, 120)}`);

        if (msg.type === 'transcript' || msg.type === 'response') {
          responsesReceived++;
          console.log(`  [${msg.type}] ${msg.text?.substring(0, 80) ?? msg.transcript?.substring(0, 80) ?? ''}`);

          // Send next round if needed
          if (roundsSent < opts.rounds) {
            setTimeout(sendAudioRound, 1000);
          }
        }
      } else {
        // Binary audio response
        const buf = Buffer.from(data as Buffer);
        console.log(`  Received audio: ${buf.length} bytes`);
      }
    });

    ws.on('close', (code, reason) => {
      clearTimeout(timeout);
      console.log(`\n  WebSocket closed: code=${code} reason=${reason.toString()}`);
      console.log(`  Responses received: ${responsesReceived}`);

      if (responsesReceived > 0) {
        console.log('\n  WebSocket test PASSED.\n');
        resolvePromise();
      } else {
        console.log('\n  WebSocket test COMPLETED (no responses — check server logs).\n');
        resolvePromise();
      }
    });

    ws.on('error', (error) => {
      clearTimeout(timeout);
      console.error('  WebSocket error:', error.message);
      rejectPromise(error);
    });
  });
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const opts = parseArgs();

  console.log('\n=== LOAD WebSocket Client Test ===\n');
  console.log(`  URL: ${opts.url}`);

  if (!opts.token && (!opts.email || !opts.password)) {
    console.error('ERROR: Provide --token or both --email and --password');
    process.exit(1);
  }

  const token = opts.token ?? await login(opts.url, opts.email!, opts.password!);

  await runWebSocketTest(opts, token);
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
