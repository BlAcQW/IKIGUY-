/**
 * Twilio telephony integration.
 * Handles phone number management and call initiation via Twilio REST API.
 */

import Twilio from 'twilio';
import type { Twilio as TwilioClient } from 'twilio';
import { config } from '../config/index.js';

export interface TwilioConfig {
  accountSid: string;
  authToken: string;
}

export interface AvailableNumber {
  number: string;
  friendlyName: string;
  locality: string;
  region: string;
  country: string;
  capabilities: {
    voice: boolean;
    sms: boolean;
    mms: boolean;
  };
}

export interface PurchasedNumber {
  number: string;
  sid: string;
  friendlyName: string;
}

export interface SearchNumbersParams {
  country?: string;
  areaCode?: string;
  contains?: string;
  type?: 'local' | 'tollFree';
  limit?: number;
}

let twilioClient: TwilioClient | null = null;

function getClient(): TwilioClient {
  if (twilioClient) return twilioClient;

  const accountSid = config.TWILIO_ACCOUNT_SID;
  const authToken = config.TWILIO_AUTH_TOKEN;

  if (!accountSid || !authToken) {
    throw Object.assign(
      new Error('Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.'),
      { statusCode: 503 }
    );
  }

  twilioClient = Twilio(accountSid, authToken);
  return twilioClient;
}

/**
 * Search for available phone numbers to purchase.
 */
export async function searchAvailableNumbers(
  params: SearchNumbersParams
): Promise<AvailableNumber[]> {
  const client = getClient();
  const country = params.country ?? 'US';
  const limit = params.limit ?? 10;

  const searchParams: Record<string, unknown> = { limit };
  if (params.areaCode) searchParams.areaCode = params.areaCode;
  if (params.contains) searchParams.contains = params.contains;

  let numbers;
  if (params.type === 'tollFree') {
    numbers = await client.availablePhoneNumbers(country).tollFree.list(searchParams);
  } else {
    numbers = await client.availablePhoneNumbers(country).local.list(searchParams);
  }

  return numbers.map((n) => ({
    number: n.phoneNumber,
    friendlyName: n.friendlyName,
    locality: n.locality ?? '',
    region: n.region ?? '',
    country: country,
    capabilities: {
      voice: n.capabilities?.voice ?? false,
      sms: n.capabilities?.sms ?? false,
      mms: n.capabilities?.mms ?? false,
    },
  }));
}

/**
 * Purchase a phone number and configure its webhook URLs.
 */
export async function buyNumber(
  phoneNumber: string,
  webhookBaseUrl: string
): Promise<PurchasedNumber> {
  const client = getClient();

  const purchased = await client.incomingPhoneNumbers.create({
    phoneNumber,
    voiceUrl: `${webhookBaseUrl}/api/telephony/inbound`,
    voiceMethod: 'POST',
    statusCallback: `${webhookBaseUrl}/api/telephony/status`,
    statusCallbackMethod: 'POST',
  });

  return {
    number: purchased.phoneNumber,
    sid: purchased.sid,
    friendlyName: purchased.friendlyName,
  };
}

/**
 * Release a purchased phone number.
 */
export async function releaseNumber(sid: string): Promise<void> {
  const client = getClient();
  await client.incomingPhoneNumbers(sid).remove();
}

/**
 * Update webhook URLs on an existing phone number.
 */
export async function configureNumberWebhooks(
  sid: string,
  webhookBaseUrl: string
): Promise<void> {
  const client = getClient();
  await client.incomingPhoneNumbers(sid).update({
    voiceUrl: `${webhookBaseUrl}/api/telephony/inbound`,
    voiceMethod: 'POST',
    statusCallback: `${webhookBaseUrl}/api/telephony/status`,
    statusCallbackMethod: 'POST',
  });
}

/**
 * Initiate an outbound call via Twilio.
 * Returns the Twilio Call SID.
 */
export async function makeCall(
  to: string,
  from: string,
  webhookBaseUrl: string
): Promise<string> {
  const client = getClient();

  const call = await client.calls.create({
    to,
    from,
    url: `${webhookBaseUrl}/api/telephony/outbound-connect`,
    method: 'POST',
    statusCallback: `${webhookBaseUrl}/api/telephony/status`,
    statusCallbackMethod: 'POST',
    statusCallbackEvent: ['initiated', 'ringing', 'answered', 'completed'],
  });

  return call.sid;
}

/**
 * Validate that a Twilio request signature is authentic.
 */
export function validateTwilioSignature(
  signature: string,
  url: string,
  params: Record<string, string>
): boolean {
  const authToken = config.TWILIO_AUTH_TOKEN;
  if (!authToken) return false;
  return Twilio.validateRequest(authToken, signature, url, params);
}

/**
 * Reset the cached client (useful for testing).
 */
export function resetTwilioClient(): void {
  twilioClient = null;
}
