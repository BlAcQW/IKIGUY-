import { prisma } from '../database/client.js';
import { updateAssistant, addMessage } from './session.js';

interface SquadMember {
  assistantId: string;
  transferConditions?: Record<string, unknown>;
}

/**
 * Validate that both assistants belong to the same squad.
 * Returns true if transfer is valid, false otherwise.
 */
export async function resolveTransfer(
  organizationId: string,
  currentAssistantId: string,
  targetAssistantId: string,
): Promise<boolean> {
  if (currentAssistantId === targetAssistantId) {
    return false;
  }

  // Verify target assistant exists in this org
  const targetAssistant = await prisma.assistant.findFirst({
    where: { id: targetAssistantId, organizationId },
  });
  if (!targetAssistant) {
    return false;
  }

  // Find a squad that contains both assistants
  const squads = await prisma.squad.findMany({
    where: { organizationId },
  });

  for (const squad of squads) {
    const members = squad.members as unknown as SquadMember[];
    const hasSource = members.some((m) => m.assistantId === currentAssistantId);
    const hasTarget = members.some((m) => m.assistantId === targetAssistantId);
    if (hasSource && hasTarget) {
      return true;
    }
  }

  return false;
}

/**
 * Execute the transfer: update the session's assistant and inject a system message.
 */
export async function executeTransfer(
  sessionId: string,
  targetAssistant: { id: string; name: string; model: unknown },
): Promise<void> {
  await updateAssistant(sessionId, targetAssistant.id);

  const modelConfig = targetAssistant.model as { systemPrompt?: string };
  if (modelConfig.systemPrompt) {
    await addMessage(sessionId, {
      role: 'system',
      content: `[Transfer] You are now ${targetAssistant.name}. ${modelConfig.systemPrompt}`,
    });
  } else {
    await addMessage(sessionId, {
      role: 'system',
      content: `[Transfer] The call has been transferred. You are now ${targetAssistant.name}.`,
    });
  }
}
