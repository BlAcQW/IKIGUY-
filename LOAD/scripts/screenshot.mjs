#!/usr/bin/env node

/**
 * Puppeteer screenshot tool for LOAD frontend pages.
 *
 * Usage:
 *   node scripts/screenshot.mjs <pages...>        # specific pages
 *   node scripts/screenshot.mjs all               # all 13 pages
 *   node scripts/screenshot.mjs --no-auth /login   # skip auth (public pages)
 *   node scripts/screenshot.mjs --base-url http://localhost:5173 /
 */

import puppeteer from 'puppeteer';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const PROJECT_ROOT = resolve(__dirname, '..');

const ALL_PAGES = [
  '/login',
  '/register',
  '/',
  '/assistants',
  '/web-call',
  '/calls',
  '/phone-numbers',
  '/tools',
  '/squads',
  '/campaigns',
  '/webhooks',
  '/analytics',
  '/settings',
];

const PUBLIC_PAGES = new Set(['/login', '/register']);

const TEST_USER = {
  email: 'screenshot@load.dev',
  password: 'screenshot-pass-2026',
  name: 'Screenshot Bot',
  organizationName: 'LOAD Screenshots',
};

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const args = argv.slice(2);
  let noAuth = false;
  let baseUrl = 'http://localhost:5173';
  const pages = [];

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--no-auth') {
      noAuth = true;
    } else if (args[i] === '--base-url' && i + 1 < args.length) {
      baseUrl = args[++i];
    } else if (args[i] === 'all') {
      pages.push(...ALL_PAGES);
    } else if (args[i].startsWith('/') || args[i].startsWith('http')) {
      pages.push(args[i]);
    } else {
      console.error(`Unknown argument: ${args[i]}`);
      process.exit(1);
    }
  }

  if (pages.length === 0) {
    console.error('Usage: node scripts/screenshot.mjs [--no-auth] [--base-url <url>] <pages...|all>');
    process.exit(1);
  }

  return { noAuth, baseUrl, pages };
}

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

async function authenticate(baseUrl) {
  const apiBase = baseUrl.replace(/:5173\b/, ':3000');

  // Try login first
  let res = await fetch(`${apiBase}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: TEST_USER.email, password: TEST_USER.password }),
  });

  if (!res.ok) {
    // User doesn't exist — register
    console.log('  Test user not found, registering...');
    res = await fetch(`${apiBase}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(TEST_USER),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Registration failed (${res.status}): ${text}`);
    }
  }

  const json = await res.json();
  const { token, user, organization } = json.data;

  const authUser = {
    userId: user.id,
    organizationId: organization.id,
    role: user.role,
    name: user.name,
    email: user.email,
    organizationName: organization.name,
  };

  return { token, authUser };
}

// ---------------------------------------------------------------------------
// Screenshot logic
// ---------------------------------------------------------------------------

function slugify(pagePath) {
  if (pagePath === '/') return 'dashboard';
  return pagePath.replace(/^\//, '').replace(/\//g, '-');
}

function timestamp() {
  return new Date().toISOString().replace(/:/g, '-').replace(/\.\d+Z$/, '');
}

async function takeScreenshots({ noAuth, baseUrl, pages }) {
  const outDir = resolve(PROJECT_ROOT, '.claude', 'screenshots');
  await mkdir(outDir, { recursive: true });

  let authData = null;
  const needsAuth = !noAuth && pages.some((p) => !PUBLIC_PAGES.has(p));

  if (needsAuth) {
    console.log('Authenticating...');
    authData = await authenticate(baseUrl);
    console.log('  Authenticated as', authData.authUser.email);
  }

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const ts = timestamp();
  const results = [];

  try {
    for (const pagePath of pages) {
      const slug = slugify(pagePath);
      const filename = `${slug}-${ts}.png`;
      const filepath = resolve(outDir, filename);
      const url = pagePath.startsWith('http') ? pagePath : `${baseUrl}${pagePath}`;

      console.log(`Capturing ${pagePath} ...`);

      const page = await browser.newPage();
      await page.setViewport({ width: 1280, height: 800 });

      // Inject auth token into localStorage before navigation
      if (authData && !PUBLIC_PAGES.has(pagePath)) {
        await page.evaluateOnNewDocument(
          (token, user) => {
            localStorage.setItem('load_token', token);
            localStorage.setItem('load_user', JSON.stringify(user));
          },
          authData.token,
          authData.authUser
        );
      }

      try {
        await page.goto(url, { waitUntil: 'networkidle0', timeout: 15000 });
      } catch {
        // Fallback for WebSocket pages that never reach networkidle0
        console.log(`  networkidle0 timed out, falling back to body selector...`);
        try {
          await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
          await page.waitForSelector('body', { timeout: 5000 });
        } catch (err) {
          console.error(`  Failed to load ${pagePath}: ${err.message}`);
          await page.close();
          continue;
        }
      }

      // Buffer for CSS animations / transitions
      await new Promise((r) => setTimeout(r, 1500));

      await page.screenshot({ path: filepath, fullPage: false });
      await page.close();

      console.log(`  Saved: ${filepath}`);
      results.push({ page: pagePath, file: filepath });
    }
  } finally {
    await browser.close();
  }

  console.log(`\nDone. ${results.length} screenshot(s) saved to ${outDir}`);
  return results;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const opts = parseArgs(process.argv);
takeScreenshots(opts).catch((err) => {
  console.error('Screenshot failed:', err.message);
  process.exit(1);
});
