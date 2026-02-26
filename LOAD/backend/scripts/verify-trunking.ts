#!/usr/bin/env tsx
/**
 * Trunking verification script.
 *
 * Checks connectivity and configuration of:
 *   1. Asterisk ARI
 *   2. PJSIP endpoints
 *   3. Twilio account
 *   4. Configured phone numbers
 *
 * Run: npx tsx scripts/verify-trunking.ts
 */

import { config as dotenvConfig } from 'dotenv';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname_ = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

dotenvConfig({ path: resolve(__dirname_, '..', '.env') });

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CheckResult {
  name: string;
  status: 'OK' | 'FAIL' | 'WARN' | 'SKIP';
  detail: string;
}

// ---------------------------------------------------------------------------
// Checks
// ---------------------------------------------------------------------------

async function checkAsteriskAri(): Promise<CheckResult> {
  const url = process.env.ASTERISK_ARI_URL;
  const username = process.env.ASTERISK_ARI_USERNAME;
  const password = process.env.ASTERISK_ARI_PASSWORD;

  if (!url || !username || !password) {
    return {
      name: 'Asterisk ARI',
      status: 'SKIP',
      detail: 'ASTERISK_ARI_URL / _USERNAME / _PASSWORD not configured in .env',
    };
  }

  try {
    const authHeader = 'Basic ' + Buffer.from(`${username}:${password}`).toString('base64');
    const res = await fetch(`${url}/ari/asterisk/info`, {
      headers: { Authorization: authHeader },
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok) {
      return {
        name: 'Asterisk ARI',
        status: 'FAIL',
        detail: `HTTP ${res.status}: ${await res.text()}`,
      };
    }

    const info = (await res.json()) as { system?: { version?: string } };
    return {
      name: 'Asterisk ARI',
      status: 'OK',
      detail: `Connected — Asterisk ${info.system?.version ?? 'unknown'}`,
    };
  } catch (error) {
    return {
      name: 'Asterisk ARI',
      status: 'FAIL',
      detail: error instanceof Error ? error.message : String(error),
    };
  }
}

async function checkPjsipEndpoints(): Promise<CheckResult> {
  const url = process.env.ASTERISK_ARI_URL;
  const username = process.env.ASTERISK_ARI_USERNAME;
  const password = process.env.ASTERISK_ARI_PASSWORD;

  if (!url || !username || !password) {
    return {
      name: 'PJSIP Endpoints',
      status: 'SKIP',
      detail: 'ARI credentials not configured',
    };
  }

  try {
    const authHeader = 'Basic ' + Buffer.from(`${username}:${password}`).toString('base64');
    const res = await fetch(`${url}/ari/endpoints`, {
      headers: { Authorization: authHeader },
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok) {
      return {
        name: 'PJSIP Endpoints',
        status: 'FAIL',
        detail: `HTTP ${res.status}`,
      };
    }

    const endpoints = (await res.json()) as Array<{
      technology: string;
      resource: string;
      state: string;
      channel_ids?: string[];
    }>;

    const pjsip = endpoints.filter((e) => e.technology === 'PJSIP');

    if (pjsip.length === 0) {
      return {
        name: 'PJSIP Endpoints',
        status: 'WARN',
        detail: 'No PJSIP endpoints found',
      };
    }

    const summary = pjsip
      .map((e) => `${e.resource}(${e.state})`)
      .join(', ');

    return {
      name: 'PJSIP Endpoints',
      status: 'OK',
      detail: `${pjsip.length} endpoints: ${summary.substring(0, 60)}`,
    };
  } catch (error) {
    return {
      name: 'PJSIP Endpoints',
      status: 'FAIL',
      detail: error instanceof Error ? error.message : String(error),
    };
  }
}

async function checkAriApplication(): Promise<CheckResult> {
  const url = process.env.ASTERISK_ARI_URL;
  const username = process.env.ASTERISK_ARI_USERNAME;
  const password = process.env.ASTERISK_ARI_PASSWORD;
  const appName = process.env.ASTERISK_ARI_APP ?? 'load';

  if (!url || !username || !password) {
    return {
      name: `ARI App (${appName})`,
      status: 'SKIP',
      detail: 'ARI credentials not configured',
    };
  }

  try {
    const authHeader = 'Basic ' + Buffer.from(`${username}:${password}`).toString('base64');
    const res = await fetch(`${url}/ari/applications/${appName}`, {
      headers: { Authorization: authHeader },
      signal: AbortSignal.timeout(5000),
    });

    if (res.status === 404) {
      return {
        name: `ARI App (${appName})`,
        status: 'WARN',
        detail: `Application "${appName}" not registered — start the backend to register it`,
      };
    }

    if (!res.ok) {
      return {
        name: `ARI App (${appName})`,
        status: 'FAIL',
        detail: `HTTP ${res.status}`,
      };
    }

    return {
      name: `ARI App (${appName})`,
      status: 'OK',
      detail: `Application "${appName}" registered`,
    };
  } catch (error) {
    return {
      name: `ARI App (${appName})`,
      status: 'FAIL',
      detail: error instanceof Error ? error.message : String(error),
    };
  }
}

async function checkTwilio(): Promise<CheckResult> {
  const sid = process.env.TWILIO_ACCOUNT_SID;
  const token = process.env.TWILIO_AUTH_TOKEN;

  if (!sid || !token) {
    return {
      name: 'Twilio Account',
      status: 'SKIP',
      detail: 'TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not configured',
    };
  }

  try {
    const authHeader = 'Basic ' + Buffer.from(`${sid}:${token}`).toString('base64');
    const res = await fetch(`https://api.twilio.com/2010-04-01/Accounts/${sid}.json`, {
      headers: { Authorization: authHeader },
      signal: AbortSignal.timeout(10000),
    });

    if (!res.ok) {
      return {
        name: 'Twilio Account',
        status: 'FAIL',
        detail: `HTTP ${res.status}: ${await res.text()}`,
      };
    }

    const account = (await res.json()) as {
      friendly_name?: string;
      status?: string;
      type?: string;
    };

    return {
      name: 'Twilio Account',
      status: 'OK',
      detail: `${account.friendly_name ?? sid} (${account.status ?? 'unknown'}, ${account.type ?? 'unknown'})`,
    };
  } catch (error) {
    return {
      name: 'Twilio Account',
      status: 'FAIL',
      detail: error instanceof Error ? error.message : String(error),
    };
  }
}

async function checkTwilioNumbers(): Promise<CheckResult> {
  const sid = process.env.TWILIO_ACCOUNT_SID;
  const token = process.env.TWILIO_AUTH_TOKEN;

  if (!sid || !token) {
    return {
      name: 'Twilio Numbers',
      status: 'SKIP',
      detail: 'Twilio credentials not configured',
    };
  }

  try {
    const authHeader = 'Basic ' + Buffer.from(`${sid}:${token}`).toString('base64');
    const res = await fetch(
      `https://api.twilio.com/2010-04-01/Accounts/${sid}/IncomingPhoneNumbers.json?PageSize=20`,
      {
        headers: { Authorization: authHeader },
        signal: AbortSignal.timeout(10000),
      },
    );

    if (!res.ok) {
      return {
        name: 'Twilio Numbers',
        status: 'FAIL',
        detail: `HTTP ${res.status}`,
      };
    }

    const data = (await res.json()) as {
      incoming_phone_numbers?: Array<{
        phone_number: string;
        friendly_name: string;
        voice_url?: string;
      }>;
    };

    const numbers = data.incoming_phone_numbers ?? [];
    if (numbers.length === 0) {
      return {
        name: 'Twilio Numbers',
        status: 'WARN',
        detail: 'No phone numbers purchased',
      };
    }

    const summary = numbers
      .map((n) => `${n.phone_number}`)
      .join(', ');

    return {
      name: 'Twilio Numbers',
      status: 'OK',
      detail: `${numbers.length} numbers: ${summary.substring(0, 60)}`,
    };
  } catch (error) {
    return {
      name: 'Twilio Numbers',
      status: 'FAIL',
      detail: error instanceof Error ? error.message : String(error),
    };
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  console.log('\n=== LOAD Trunking Verification ===\n');

  const results: CheckResult[] = await Promise.all([
    checkAsteriskAri(),
    checkPjsipEndpoints(),
    checkAriApplication(),
    checkTwilio(),
    checkTwilioNumbers(),
  ]);

  // Print results table
  console.log('┌───────────────────────┬────────┬─────────────────────────────────────────────────────────────┐');
  console.log('│ Component             │ Status │ Detail                                                      │');
  console.log('├───────────────────────┼────────┼─────────────────────────────────────────────────────────────┤');

  for (const r of results) {
    const icons: Record<string, string> = {
      OK: '\x1b[32m  OK\x1b[0m',
      FAIL: '\x1b[31mFAIL\x1b[0m',
      WARN: '\x1b[33mWARN\x1b[0m',
      SKIP: '\x1b[90mSKIP\x1b[0m',
    };
    const name = r.name.padEnd(21);
    const status = icons[r.status] ?? r.status;
    const detail = r.detail.substring(0, 59).padEnd(59);
    console.log(`│ ${name} │ ${status} │ ${detail} │`);
  }

  console.log('└───────────────────────┴────────┴─────────────────────────────────────────────────────────────┘');

  // Softphone instructions
  const hasAri = results.some((r) => r.name === 'Asterisk ARI' && r.status === 'OK');

  console.log('\n--- Softphone Test Instructions ---\n');
  if (hasAri) {
    console.log('  Asterisk is reachable. To test with a softphone:\n');
    console.log('  1. Install Zoiper or Linphone');
    console.log('  2. Register with:');
    console.log('       SIP server: localhost:5060');
    console.log('       Username:   dev1');
    console.log('       Password:   dev1pass');
    console.log('  3. Ensure an assistant is assigned to a phone number in the LOAD dashboard');
    console.log('  4. Dial the phone number extension (or use the assistant extension)');
    console.log('  5. Speak — you should hear the AI assistant respond\n');
  } else {
    console.log('  Asterisk ARI is not reachable. To enable softphone testing:\n');
    console.log('  1. Add to .env:');
    console.log('       ASTERISK_ARI_URL=http://localhost:8088');
    console.log('       ASTERISK_ARI_USERNAME=load');
    console.log('       ASTERISK_ARI_PASSWORD=load_ari_password');
    console.log('       ASTERISK_ARI_APP=load');
    console.log('  2. Start Asterisk: docker compose up asterisk');
    console.log('  3. Run this script again\n');
  }

  const hasFails = results.some((r) => r.status === 'FAIL');
  if (hasFails) {
    process.exit(1);
  }
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
