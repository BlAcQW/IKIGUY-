/**
 * Campaign Execution Engine
 *
 * BullMQ-based engine that orchestrates outbound calling campaigns.
 * Uses two queues:
 *   - `campaign-execute`: one job per campaign start, fans out contact calls
 *   - `campaign-calls`:   one job per contact, handles individual call attempts
 *
 * Follows the same lazy-initialization and ioredis pattern used in
 * `src/modules/webhooks/delivery.ts`.
 */

import { Queue, Worker } from 'bullmq';
import type { ConnectionOptions, Job } from 'bullmq';
import IORedis from 'ioredis';
import { prisma } from '../../database/client.js';
import { config } from '../../config/index.js';
import { fireWebhookEvent } from '../webhooks/delivery.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CampaignContact {
  name: string;
  number: string;
  metadata?: Record<string, unknown>;
}

interface CampaignSchedule {
  maxConcurrent?: number;
  startTime?: string;
  endTime?: string;
  timezone?: string;
  delayBetweenCalls?: number;
  maxRetries?: number;
}

interface CampaignStats {
  totalContacts: number;
  completed: number;
  failed: number;
  inProgress: number;
  retried?: number;
}

interface CampaignExecuteJobData {
  campaignId: string;
  organizationId: string;
}

interface CampaignCallJobData {
  campaignId: string;
  organizationId: string;
  assistantId: string;
  phoneNumberId: string;
  contact: CampaignContact;
  contactIndex: number;
  attemptNumber?: number;
}

interface CallBridgeLike {
  initiateOutbound(params: {
    organizationId: string;
    assistantId: string;
    customerNumber: string;
    phoneNumberId: string;
    metadata?: Record<string, unknown>;
  }): Promise<{ callId: string; channelId: string }>;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const EXECUTE_QUEUE_NAME = 'campaign-execute';
const CALLS_QUEUE_NAME = 'campaign-calls';
const DEFAULT_MAX_CONCURRENT = 1;
const CALL_WORKER_CONCURRENCY = 5;

const DEFAULT_JOB_OPTIONS = {
  attempts: 2,
  backoff: {
    type: 'fixed' as const,
    delay: 5000,
  },
  removeOnComplete: { count: 200 },
  removeOnFail: { count: 500 },
};

// ---------------------------------------------------------------------------
// Lazy-initialized singletons
// ---------------------------------------------------------------------------

let redisInstance: IORedis | null = null;
let executeQueue: Queue<CampaignExecuteJobData> | null = null;
let callsQueue: Queue<CampaignCallJobData> | null = null;
let executeWorkerInstance: Worker<CampaignExecuteJobData> | null = null;
let callWorkerInstance: Worker<CampaignCallJobData> | null = null;

/**
 * Lazily create a shared ioredis connection. The cast to ConnectionOptions is
 * necessary because the top-level ioredis package may differ slightly from the
 * one BullMQ bundles internally; the runtime behaviour is identical.
 */
function getConnection(): ConnectionOptions {
  if (!redisInstance) {
    redisInstance = new IORedis(config.REDIS_URL, {
      maxRetriesPerRequest: null,
    });
  }
  return redisInstance as unknown as ConnectionOptions;
}

function getExecuteQueue(): Queue<CampaignExecuteJobData> {
  if (!executeQueue) {
    executeQueue = new Queue<CampaignExecuteJobData>(EXECUTE_QUEUE_NAME, {
      connection: getConnection(),
      defaultJobOptions: DEFAULT_JOB_OPTIONS,
    });
  }
  return executeQueue;
}

function getCallsQueue(): Queue<CampaignCallJobData> {
  if (!callsQueue) {
    callsQueue = new Queue<CampaignCallJobData>(CALLS_QUEUE_NAME, {
      connection: getConnection(),
      defaultJobOptions: DEFAULT_JOB_OPTIONS,
    });
  }
  return callsQueue;
}

// ---------------------------------------------------------------------------
// CallBridge reference (injected from outside, e.g. index.ts)
// ---------------------------------------------------------------------------

let callBridgeRef: CallBridgeLike | null = null;

export function setCallBridge(bridge: CallBridgeLike): void {
  callBridgeRef = bridge;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Read the current stats from the database to avoid stale overwrites when
 * multiple call workers update concurrently.
 */
async function readCampaignStats(campaignId: string): Promise<CampaignStats> {
  const campaign = await prisma.campaign.findUniqueOrThrow({
    where: { id: campaignId },
    select: { stats: true },
  });

  const raw = campaign.stats as Record<string, unknown> | null;

  return {
    totalContacts: Number(raw?.totalContacts ?? 0),
    completed: Number(raw?.completed ?? 0),
    failed: Number(raw?.failed ?? 0),
    inProgress: Number(raw?.inProgress ?? 0),
  };
}

async function updateCampaignStats(
  campaignId: string,
  stats: CampaignStats,
): Promise<void> {
  await prisma.campaign.update({
    where: { id: campaignId },
    data: { stats: stats as unknown as object },
  });
}

async function getCampaignStatus(
  campaignId: string,
): Promise<string | null> {
  const campaign = await prisma.campaign.findUnique({
    where: { id: campaignId },
    select: { status: true },
  });
  return campaign?.status ?? null;
}

// ---------------------------------------------------------------------------
// Execute Worker — fans out contacts into individual call jobs
// ---------------------------------------------------------------------------

async function processExecuteJob(
  job: Job<CampaignExecuteJobData>,
): Promise<void> {
  const { campaignId, organizationId } = job.data;

  const campaign = await prisma.campaign.findFirst({
    where: { id: campaignId, organizationId },
  });

  if (!campaign) {
    throw new Error(`Campaign ${campaignId} not found`);
  }

  const contacts = (campaign.contacts ?? []) as unknown as CampaignContact[];
  const schedule = (campaign.schedule ?? {}) as CampaignSchedule;
  const maxConcurrent = schedule.maxConcurrent ?? DEFAULT_MAX_CONCURRENT;

  // Initialize stats
  const initialStats: CampaignStats = {
    totalContacts: contacts.length,
    completed: 0,
    failed: 0,
    inProgress: 0,
  };

  await updateCampaignStats(campaignId, initialStats);

  // Enqueue individual call jobs with staggered delays so we never exceed
  // maxConcurrent calls at any point. Each "batch" of maxConcurrent jobs
  // starts at the same time; the next batch gets the configured delay
  // (or a 2s default).
  const q = getCallsQueue();
  const delayBetweenCallsMs = (schedule.delayBetweenCalls ?? 2) * 1000;

  const jobPromises = contacts.map((contact, index) => {
    const batchIndex = Math.floor(index / maxConcurrent);
    const delay = batchIndex * (delayBetweenCallsMs > 0 ? delayBetweenCallsMs : 2000);

    return q.add(
      CALLS_QUEUE_NAME,
      {
        campaignId,
        organizationId,
        assistantId: campaign.assistantId,
        phoneNumberId: campaign.phoneNumberId,
        contact,
        contactIndex: index,
        attemptNumber: 1,
      },
      { delay },
    );
  });

  await Promise.all(jobPromises);

  console.log(
    `[campaign-engine] Campaign ${campaignId}: enqueued ${contacts.length} call jobs (maxConcurrent=${maxConcurrent})`,
  );
}

// ---------------------------------------------------------------------------
// Call Worker — executes a single outbound call to one contact
// ---------------------------------------------------------------------------

async function processCallJob(
  job: Job<CampaignCallJobData>,
): Promise<void> {
  const {
    campaignId,
    organizationId,
    assistantId,
    phoneNumberId,
    contact,
    contactIndex,
    attemptNumber = 1,
  } = job.data;

  // Check campaign status before executing — if PAUSED, skip gracefully
  const status = await getCampaignStatus(campaignId);
  if (status === 'PAUSED') {
    console.log(
      `[campaign-engine] Campaign ${campaignId} is PAUSED — skipping contact #${contactIndex} (${contact.number})`,
    );
    // Do not re-enqueue here; resumeCampaign will handle re-enqueueing.
    return;
  }

  if (status !== 'RUNNING') {
    console.log(
      `[campaign-engine] Campaign ${campaignId} status is ${status ?? 'unknown'} — skipping contact #${contactIndex}`,
    );
    return;
  }

  // Mark contact as in-progress
  const statsBeforeCall = await readCampaignStats(campaignId);
  const inProgressStats: CampaignStats = {
    ...statsBeforeCall,
    inProgress: statsBeforeCall.inProgress + 1,
  };
  await updateCampaignStats(campaignId, inProgressStats);

  let succeeded = false;

  try {
    if (!callBridgeRef) {
      console.warn(
        `[campaign-engine] CallBridge not configured — marking contact #${contactIndex} (${contact.number}) as failed`,
      );
      throw new Error('CallBridge not available: telephony is not configured');
    }

    await callBridgeRef.initiateOutbound({
      organizationId,
      assistantId,
      customerNumber: contact.number,
      phoneNumberId,
      metadata: {
        campaignId,
        contactIndex,
        contactName: contact.name,
        ...contact.metadata,
      },
    });

    succeeded = true;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(
      `[campaign-engine] Campaign ${campaignId}: call to contact #${contactIndex} (${contact.number}) failed: ${message}`,
    );
  }

  // On failure, check if we should retry before counting as failed
  if (!succeeded) {
    const campaign = await prisma.campaign.findUnique({
      where: { id: campaignId },
      select: { schedule: true },
    });
    const campaignSchedule = (campaign?.schedule ?? {}) as CampaignSchedule;
    const maxRetries = campaignSchedule.maxRetries ?? 0;

    if (attemptNumber <= maxRetries) {
      // Re-enqueue for retry with incremented attempt number
      const retryDelay = (campaignSchedule.delayBetweenCalls ?? 5) * 1000;
      const q = getCallsQueue();
      await q.add(
        CALLS_QUEUE_NAME,
        {
          campaignId,
          organizationId,
          assistantId,
          phoneNumberId,
          contact,
          contactIndex,
          attemptNumber: attemptNumber + 1,
        },
        { delay: retryDelay },
      );

      // Update stats: decrement inProgress, increment retried counter
      const retryStats = await readCampaignStats(campaignId);
      await updateCampaignStats(campaignId, {
        ...retryStats,
        inProgress: Math.max(retryStats.inProgress - 1, 0),
        retried: (retryStats.retried ?? 0) + 1,
      });

      console.log(
        `[campaign-engine] Campaign ${campaignId}: retrying contact #${contactIndex} (${contact.number}), attempt ${attemptNumber + 1}/${maxRetries + 1}`,
      );
      return;
    }
  }

  // Read fresh stats and apply the outcome atomically
  const freshStats = await readCampaignStats(campaignId);
  const updatedStats: CampaignStats = {
    ...freshStats,
    inProgress: Math.max(freshStats.inProgress - 1, 0),
    completed: succeeded ? freshStats.completed + 1 : freshStats.completed,
    failed: succeeded ? freshStats.failed : freshStats.failed + 1,
  };
  await updateCampaignStats(campaignId, updatedStats);

  // Fire progress webhook after every call
  await fireWebhookEvent(organizationId, 'campaign.progress', {
    campaignId,
    contactIndex,
    contactNumber: contact.number,
    contactName: contact.name,
    outcome: succeeded ? 'completed' : 'failed',
    stats: updatedStats,
  }).catch((err) => {
    console.warn('[campaign-engine] Failed to fire campaign.progress webhook:', err);
  });

  // Check if all contacts have been processed
  const totalProcessed = updatedStats.completed + updatedStats.failed;

  if (totalProcessed >= updatedStats.totalContacts) {
    // Mark campaign as COMPLETED
    await prisma.campaign.update({
      where: { id: campaignId },
      data: { status: 'COMPLETED' },
    });

    console.log(
      `[campaign-engine] Campaign ${campaignId} COMPLETED — ${updatedStats.completed} succeeded, ${updatedStats.failed} failed`,
    );

    await fireWebhookEvent(organizationId, 'campaign.completed', {
      campaignId,
      stats: updatedStats,
    }).catch((err) => {
      console.warn('[campaign-engine] Failed to fire campaign.completed webhook:', err);
    });
  }
}

// ---------------------------------------------------------------------------
// Queue / Worker creation
// ---------------------------------------------------------------------------

export function createCampaignQueues(): {
  executeWorker: Worker;
  callWorker: Worker;
} {
  const connection = getConnection();

  // Ensure queues are initialized
  getExecuteQueue();
  getCallsQueue();

  const executeWorker = new Worker<CampaignExecuteJobData>(
    EXECUTE_QUEUE_NAME,
    processExecuteJob,
    { connection },
  );

  executeWorker.on('failed', (job, error) => {
    console.error(
      `[campaign-engine] Execute job ${job?.id ?? 'unknown'} failed for campaign ${job?.data.campaignId ?? 'unknown'}:`,
      error.message,
    );
  });

  const callWorker = new Worker<CampaignCallJobData>(
    CALLS_QUEUE_NAME,
    processCallJob,
    {
      connection,
      concurrency: CALL_WORKER_CONCURRENCY,
    },
  );

  callWorker.on('failed', (job, error) => {
    console.error(
      `[campaign-engine] Call job ${job?.id ?? 'unknown'} failed for campaign ${job?.data.campaignId ?? 'unknown'}, contact #${job?.data.contactIndex ?? '?'}:`,
      error.message,
    );
  });

  executeWorkerInstance = executeWorker;
  callWorkerInstance = callWorker;

  console.log('[campaign-engine] Workers started');

  return { executeWorker, callWorker };
}

// ---------------------------------------------------------------------------
// Public campaign lifecycle functions
// ---------------------------------------------------------------------------

/**
 * Start a campaign. Validates the campaign is in DRAFT or PAUSED status,
 * transitions it to RUNNING, and enqueues the execution job.
 */
export async function startCampaign(
  campaignId: string,
  organizationId: string,
): Promise<void> {
  const campaign = await prisma.campaign.findFirst({
    where: { id: campaignId, organizationId },
  });

  if (!campaign) {
    throw new Error(`Campaign ${campaignId} not found`);
  }

  if (campaign.status !== 'DRAFT' && campaign.status !== 'PAUSED') {
    throw new Error(
      `Campaign ${campaignId} cannot be started: current status is ${campaign.status}`,
    );
  }

  const contacts = (campaign.contacts ?? []) as unknown as CampaignContact[];

  if (contacts.length === 0) {
    throw new Error(`Campaign ${campaignId} has no contacts`);
  }

  // Transition to RUNNING
  await prisma.campaign.update({
    where: { id: campaignId },
    data: { status: 'RUNNING' },
  });

  // Enqueue campaign execution
  const q = getExecuteQueue();
  await q.add(EXECUTE_QUEUE_NAME, { campaignId, organizationId });

  console.log(
    `[campaign-engine] Campaign ${campaignId} started with ${contacts.length} contacts`,
  );
}

/**
 * Pause a running campaign. Updates status to PAUSED. Any in-flight call jobs
 * will check the status before executing and skip if paused.
 */
export async function pauseCampaign(
  campaignId: string,
  organizationId: string,
): Promise<void> {
  const campaign = await prisma.campaign.findFirst({
    where: { id: campaignId, organizationId },
  });

  if (!campaign) {
    throw new Error(`Campaign ${campaignId} not found`);
  }

  if (campaign.status !== 'RUNNING') {
    throw new Error(
      `Campaign ${campaignId} cannot be paused: current status is ${campaign.status}`,
    );
  }

  await prisma.campaign.update({
    where: { id: campaignId },
    data: { status: 'PAUSED' },
  });

  console.log(`[campaign-engine] Campaign ${campaignId} paused`);
}

/**
 * Resume a paused campaign. Re-enqueues the remaining (unprocessed) contacts
 * by computing which contacts still need to be called based on stats.
 */
export async function resumeCampaign(
  campaignId: string,
  organizationId: string,
): Promise<void> {
  const campaign = await prisma.campaign.findFirst({
    where: { id: campaignId, organizationId },
  });

  if (!campaign) {
    throw new Error(`Campaign ${campaignId} not found`);
  }

  if (campaign.status !== 'PAUSED') {
    throw new Error(
      `Campaign ${campaignId} cannot be resumed: current status is ${campaign.status}`,
    );
  }

  const contacts = (campaign.contacts ?? []) as unknown as CampaignContact[];
  const stats = await readCampaignStats(campaignId);
  const schedule = (campaign.schedule ?? {}) as CampaignSchedule;
  const maxConcurrent = schedule.maxConcurrent ?? DEFAULT_MAX_CONCURRENT;

  // The number of contacts already processed (completed + failed).
  const processedCount = stats.completed + stats.failed;

  // Remaining contacts start at processedCount offset.
  const remaining = contacts.slice(processedCount);

  if (remaining.length === 0) {
    // Nothing left — mark as completed
    await prisma.campaign.update({
      where: { id: campaignId },
      data: { status: 'COMPLETED' },
    });
    console.log(
      `[campaign-engine] Campaign ${campaignId} resumed but all contacts already processed — marking COMPLETED`,
    );
    return;
  }

  // Update status to RUNNING
  await prisma.campaign.update({
    where: { id: campaignId },
    data: { status: 'RUNNING' },
  });

  // Reset inProgress counter since those jobs were skipped during the pause
  const resetStats: CampaignStats = {
    ...stats,
    inProgress: 0,
  };
  await updateCampaignStats(campaignId, resetStats);

  // Enqueue remaining contacts
  const q = getCallsQueue();
  const delayBetweenCallsMs = (schedule.delayBetweenCalls ?? 2) * 1000;

  const jobPromises = remaining.map((contact, idx) => {
    const absoluteIndex = processedCount + idx;
    const batchIndex = Math.floor(idx / maxConcurrent);
    const delay = batchIndex * (delayBetweenCallsMs > 0 ? delayBetweenCallsMs : 2000);

    return q.add(
      CALLS_QUEUE_NAME,
      {
        campaignId,
        organizationId,
        assistantId: campaign.assistantId,
        phoneNumberId: campaign.phoneNumberId,
        contact,
        contactIndex: absoluteIndex,
        attemptNumber: 1,
      },
      { delay },
    );
  });

  await Promise.all(jobPromises);

  console.log(
    `[campaign-engine] Campaign ${campaignId} resumed — enqueued ${remaining.length} remaining contacts`,
  );
}

// ---------------------------------------------------------------------------
// Cleanup
// ---------------------------------------------------------------------------

export async function closeCampaignQueues(): Promise<void> {
  if (executeWorkerInstance) {
    await executeWorkerInstance.close();
    executeWorkerInstance = null;
  }
  if (callWorkerInstance) {
    await callWorkerInstance.close();
    callWorkerInstance = null;
  }
  if (executeQueue) {
    await executeQueue.close();
    executeQueue = null;
  }
  if (callsQueue) {
    await callsQueue.close();
    callsQueue = null;
  }
  if (redisInstance) {
    await redisInstance.quit();
    redisInstance = null;
  }
}
