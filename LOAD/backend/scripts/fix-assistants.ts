import { readFileSync } from 'fs';
import { resolve } from 'path';

const envPath = resolve(import.meta.dirname ?? '.', '../.env');
const envContent = readFileSync(envPath, 'utf8');
for (const line of envContent.split('\n')) {
  const trimmed = line.trim();
  if (trimmed.length === 0 || trimmed.startsWith('#')) continue;
  const eqIdx = trimmed.indexOf('=');
  if (eqIdx === -1) continue;
  process.env[trimmed.slice(0, eqIdx)] = trimmed.slice(eqIdx + 1);
}

async function main() {
  const { PrismaClient } = await import('@prisma/client');
  const prisma = new PrismaClient();

  // Find all assistants
  const assistants = await prisma.assistant.findMany({
    select: { id: true, name: true, model: true, organizationId: true },
  });

  console.log(`Found ${assistants.length} assistants:\n`);

  for (const a of assistants) {
    const m = a.model as Record<string, unknown>;
    const provider = m?.provider ?? 'unknown';
    console.log(`  ${a.id} | ${a.name} | provider=${provider} model=${m?.model}`);

    // Switch all assistants to google/gemini-2.0-flash
    if (provider !== 'google') {
      const updatedModel = { ...m, provider: 'google', model: 'gemini-2.0-flash' };
      await prisma.assistant.update({
        where: { id: a.id },
        data: { model: updatedModel },
      });
      console.log(`    -> UPDATED to google/gemini-2.0-flash`);
    }
  }

  console.log('\nDone.');
  await prisma.$disconnect();
}

main().catch((err) => {
  console.error('Error:', err);
  process.exit(1);
});
