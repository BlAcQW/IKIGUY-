/**
 * Helper to conditionally skip test suites when API keys are missing.
 *
 * Usage:
 *   describeIfKey('DEEPGRAM_API_KEY', () => {
 *     it('should transcribe audio', async () => { ... });
 *   });
 */

const PLACEHOLDER_PATTERNS = [
  /^sk-your-/,       // OpenAI placeholder
  /^your[-_]/i,      // Generic placeholder
  /^xxx/i,           // Common placeholder
  /^placeholder/i,
  /^CHANGE[-_]ME/i,
  /^TODO/i,
];

/**
 * Check if an env var is set and not a placeholder value.
 */
export function hasValidKey(envVar: string): boolean {
  const value = process.env[envVar];
  if (!value || value.trim() === '') return false;
  return !PLACEHOLDER_PATTERNS.some((pattern) => pattern.test(value));
}

/**
 * Returns the API key value or throws (for use inside tests that already passed the gate).
 */
export function requireKey(envVar: string): string {
  const value = process.env[envVar];
  if (!value || !hasValidKey(envVar)) {
    throw new Error(`${envVar} is required but missing or placeholder`);
  }
  return value;
}

/**
 * Wraps `describe` to skip the entire suite if the given env var is missing.
 */
export function describeIfKey(envVar: string, suiteName: string, fn: () => void): void {
  if (hasValidKey(envVar)) {
    describe(suiteName, fn);
  } else {
    describe.skip(`${suiteName} (${envVar} not configured)`, fn);
  }
}

/**
 * Wraps `describe` to skip if ANY of the given env vars is missing.
 */
export function describeIfKeys(envVars: string[], suiteName: string, fn: () => void): void {
  const missing = envVars.filter((v) => !hasValidKey(v));
  if (missing.length === 0) {
    describe(suiteName, fn);
  } else {
    describe.skip(`${suiteName} (missing: ${missing.join(', ')})`, fn);
  }
}
