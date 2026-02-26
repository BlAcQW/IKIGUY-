/**
 * Integration test setup — loads real .env, no Prisma mocking.
 * Provider tests hit real APIs so keys must be present in .env.
 */
import { config } from 'dotenv';
import path from 'path';

// Load .env from the backend root
config({ path: path.resolve(__dirname, '..', '.env') });

// Ensure we're in test mode
process.env.NODE_ENV = 'test';
