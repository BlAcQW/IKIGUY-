import { prisma } from '../../database/client.js';
import { config } from '../../config/index.js';
import {
  searchAvailableNumbers,
  buyNumber,
  releaseNumber as twilioRelease,
  configureNumberWebhooks,
} from '../../telephony/twilio.js';
import type { SearchNumbersInput, PurchaseNumberInput, CreateSipNumberInput } from './schemas.js';

/**
 * Search for available phone numbers via Twilio.
 */
export async function searchNumbers(params: SearchNumbersInput) {
  return searchAvailableNumbers(params);
}

/**
 * Purchase a phone number via Twilio and store it in the database.
 */
export async function purchaseNumber(
  organizationId: string,
  input: PurchaseNumberInput
) {
  const webhookBaseUrl = config.API_URL;

  // Purchase from Twilio
  const purchased = await buyNumber(input.phoneNumber, webhookBaseUrl);

  // Store in database
  const phoneNumber = await prisma.phoneNumber.create({
    data: {
      organizationId,
      number: purchased.number,
      twilioSid: purchased.sid,
      name: input.name ?? purchased.friendlyName,
      provider: 'TWILIO',
      status: 'ACTIVE',
    },
  });

  return phoneNumber;
}

/**
 * Register a SIP trunk phone number (no Twilio API call needed).
 */
export async function createSipTrunkNumber(
  organizationId: string,
  input: CreateSipNumberInput
) {
  const phoneNumber = await prisma.phoneNumber.create({
    data: {
      organizationId,
      number: input.number,
      name: input.name ?? input.number,
      provider: 'SIP_TRUNK',
      sipDomain: input.sipDomain ?? null,
      status: 'ACTIVE',
    },
  });

  return phoneNumber;
}

/**
 * Find a phone number by its E.164 number string.
 */
export async function findByNumber(number: string) {
  return prisma.phoneNumber.findFirst({
    where: { number, status: 'ACTIVE' },
  });
}

/**
 * Release a phone number — removes from Twilio and marks as RELEASED in DB.
 */
export async function releaseNumber(id: string, organizationId: string) {
  const phoneNumber = await prisma.phoneNumber.findFirst({
    where: { id, organizationId },
  });

  if (!phoneNumber) {
    throw Object.assign(new Error('Phone number not found'), { statusCode: 404 });
  }

  if (phoneNumber.status === 'RELEASED') {
    throw Object.assign(new Error('Phone number already released'), { statusCode: 400 });
  }

  // Release from Twilio (only for Twilio-managed numbers)
  if (phoneNumber.provider === 'TWILIO' && phoneNumber.twilioSid) {
    await twilioRelease(phoneNumber.twilioSid);
  }

  // Mark as released in database
  const updated = await prisma.phoneNumber.update({
    where: { id },
    data: {
      status: 'RELEASED',
      assistantId: null,
    },
  });

  return updated;
}

/**
 * Update a phone number (assign assistant, change name).
 */
export async function updatePhoneNumber(
  id: string,
  organizationId: string,
  data: { assistantId?: string | null; name?: string }
) {
  const phoneNumber = await prisma.phoneNumber.findFirst({
    where: { id, organizationId },
  });

  if (!phoneNumber) {
    throw Object.assign(new Error('Phone number not found'), { statusCode: 404 });
  }

  if (phoneNumber.status === 'RELEASED') {
    throw Object.assign(new Error('Cannot update a released phone number'), { statusCode: 400 });
  }

  // If assigning an assistant, validate it belongs to the same org
  if (data.assistantId) {
    const assistant = await prisma.assistant.findFirst({
      where: { id: data.assistantId, organizationId },
    });
    if (!assistant) {
      throw Object.assign(new Error('Assistant not found'), { statusCode: 404 });
    }
  }

  const updated = await prisma.phoneNumber.update({
    where: { id },
    data,
  });

  return updated;
}

/**
 * Get a single phone number by ID, scoped to organization.
 */
export async function getPhoneNumber(id: string, organizationId: string) {
  const phoneNumber = await prisma.phoneNumber.findFirst({
    where: { id, organizationId },
  });

  if (!phoneNumber) {
    throw Object.assign(new Error('Phone number not found'), { statusCode: 404 });
  }

  return phoneNumber;
}

/**
 * List all phone numbers for an organization.
 */
export async function listPhoneNumbers(organizationId: string) {
  return prisma.phoneNumber.findMany({
    where: { organizationId },
    orderBy: { createdAt: 'desc' },
  });
}

/**
 * Reconfigure webhook URLs on all active phone numbers.
 * Useful when the API_URL changes.
 */
export async function reconfigureWebhooks(organizationId: string) {
  const webhookBaseUrl = config.API_URL;
  const numbers = await prisma.phoneNumber.findMany({
    where: { organizationId, status: 'ACTIVE' },
  });

  const twilioNumbers = numbers.filter((n) => n.provider === 'TWILIO' && n.twilioSid);
  const results = await Promise.allSettled(
    twilioNumbers.map((n) => configureNumberWebhooks(n.twilioSid!, webhookBaseUrl))
  );

  const failed = results.filter((r) => r.status === 'rejected').length;
  return { total: numbers.length, updated: numbers.length - failed, failed };
}
