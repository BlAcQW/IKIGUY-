import { PrismaClient, CallType, CallStatus, CampaignStatus, ToolType } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomChoice<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomDate(daysAgo: number): Date {
  const now = Date.now();
  const past = now - daysAgo * 24 * 60 * 60 * 1000;
  return new Date(past + Math.random() * (now - past));
}

async function main() {
  console.log('Seeding database...');

  // Clean existing data
  await prisma.webhookDelivery.deleteMany();
  await prisma.webhook.deleteMany();
  await prisma.campaign.deleteMany();
  await prisma.squad.deleteMany();
  await prisma.tool.deleteMany();
  await prisma.call.deleteMany();
  await prisma.phoneNumber.deleteMany();
  await prisma.assistant.deleteMany();
  await prisma.apiKey.deleteMany();
  await prisma.user.deleteMany();
  await prisma.organization.deleteMany();

  // Organization
  const org = await prisma.organization.create({
    data: {
      name: 'LOAD Demo',
      slug: 'load-demo',
      plan: 'PRO',
    },
  });
  console.log('  Created organization:', org.name);

  // Users
  const passwordHash = await bcrypt.hash('demo1234', 10);
  const owner = await prisma.user.create({
    data: {
      email: 'admin@load.dev',
      passwordHash,
      name: 'Alex Carter',
      role: 'OWNER',
      organizationId: org.id,
    },
  });
  const member = await prisma.user.create({
    data: {
      email: 'member@load.dev',
      passwordHash,
      name: 'Jordan Lee',
      role: 'MEMBER',
      organizationId: org.id,
    },
  });
  console.log('  Created 2 users (login: admin@load.dev / demo1234)');

  // Assistants
  const assistantConfigs = [
    {
      name: 'Sales Agent',
      firstMessage: "Hi there! I'm your sales assistant. How can I help you today?",
      endCallMessage: 'Thanks for your time! Have a great day.',
      endCallPhrases: ['goodbye', 'bye', 'talk later'],
      model: { provider: 'openai', model: 'gpt-4o', temperature: 0.7, maxTokens: 500, systemPrompt: 'You are a friendly sales agent for a SaaS company. Help users understand our pricing and features.' },
      voice: { provider: 'openai', voiceId: 'alloy', speed: 1.0 },
      transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
      metadata: { pipeline: { silenceTimeout: 2000, responseDelay: 300, interruptionThreshold: 100 } },
    },
    {
      name: 'Support Bot',
      firstMessage: "Hello! I'm here to help with any technical issues. What's going on?",
      endCallMessage: 'Glad I could help! Feel free to call back anytime.',
      endCallPhrases: ['thanks', 'all good', 'bye'],
      model: { provider: 'openai', model: 'gpt-4o', temperature: 0.3, maxTokens: 800, systemPrompt: 'You are a technical support agent. Help users troubleshoot issues clearly and patiently.' },
      voice: { provider: 'openai', voiceId: 'nova', speed: 0.95 },
      transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
      metadata: { pipeline: { silenceTimeout: 3000, responseDelay: 200, interruptionThreshold: 150 } },
    },
    {
      name: 'Appointment Scheduler',
      firstMessage: "Hi! I can help you schedule an appointment. What date works best for you?",
      endCallMessage: "Your appointment is confirmed. We'll send a reminder!",
      endCallPhrases: ['done', 'all set', 'thanks bye'],
      model: { provider: 'openai', model: 'gpt-4o-mini', temperature: 0.5, maxTokens: 400, systemPrompt: 'You are an appointment scheduling assistant. Collect date, time, and contact info.' },
      voice: { provider: 'openai', voiceId: 'echo', speed: 1.0 },
      transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
      metadata: { pipeline: { silenceTimeout: 2500, responseDelay: 250, interruptionThreshold: 120 } },
    },
    {
      name: 'Survey Caller',
      firstMessage: "Hi! We're conducting a brief customer satisfaction survey. Do you have a moment?",
      endCallMessage: 'Thank you for your feedback! It really helps us improve.',
      endCallPhrases: ['no thanks', 'not interested', 'bye'],
      model: { provider: 'openai', model: 'gpt-4o-mini', temperature: 0.4, maxTokens: 300, systemPrompt: 'You are a survey caller. Ask 5 questions about customer satisfaction, collect ratings 1-5.' },
      voice: { provider: 'openai', voiceId: 'shimmer', speed: 1.05 },
      transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
      metadata: { pipeline: { silenceTimeout: 4000, responseDelay: 400, interruptionThreshold: 200 } },
    },
  ];

  const assistants = await Promise.all(
    assistantConfigs.map((config) =>
      prisma.assistant.create({
        data: { ...config, organizationId: org.id },
      }),
    ),
  );
  console.log(`  Created ${assistants.length} assistants`);

  // Phone Numbers
  const phoneNumbers = await Promise.all(
    [
      { number: '+14155551234', name: 'Main Line', twilioSid: 'PN_demo_001' },
      { number: '+14155555678', name: 'Sales Line', twilioSid: 'PN_demo_002' },
      { number: '+14155559012', name: 'Support Line', twilioSid: 'PN_demo_003' },
    ].map((pn, i) =>
      prisma.phoneNumber.create({
        data: {
          ...pn,
          organizationId: org.id,
          assistantId: assistants[i % assistants.length].id,
          provider: 'TWILIO',
          status: 'ACTIVE',
        },
      }),
    ),
  );
  console.log(`  Created ${phoneNumbers.length} phone numbers`);

  // Calls — generate 150 calls over the last 30 days
  const callStatuses: CallStatus[] = ['ENDED', 'ENDED', 'ENDED', 'ENDED', 'FAILED', 'ENDED', 'ENDED', 'IN_PROGRESS'];
  const callTypes: CallType[] = ['WEB', 'WEB', 'INBOUND', 'INBOUND', 'OUTBOUND'];
  const endReasons = ['customer-ended', 'assistant-ended', 'silence-timeout', 'max-duration', 'error'];

  const sampleTranscripts = [
    [
      { role: 'assistant', content: "Hi there! I'm your sales assistant. How can I help you today?" },
      { role: 'user', content: "I'd like to know about your pricing plans." },
      { role: 'assistant', content: "We have three plans: Free, Pro at $49/mo, and Enterprise. What size is your team?" },
      { role: 'user', content: "About 20 people. The Pro plan sounds good." },
      { role: 'assistant', content: "Pro is perfect for teams that size. Shall I set up a trial?" },
    ],
    [
      { role: 'assistant', content: "Hello! I'm here to help with any technical issues. What's going on?" },
      { role: 'user', content: "My API calls are returning 403 errors." },
      { role: 'assistant', content: "That usually means an authentication issue. Can you check if your API key is still valid in Settings?" },
      { role: 'user', content: "Oh, it expired yesterday. Let me regenerate it." },
      { role: 'assistant', content: "That should fix it! Let me know if you need anything else." },
    ],
    [
      { role: 'assistant', content: "Hi! I can help you schedule an appointment. What date works best for you?" },
      { role: 'user', content: "Next Tuesday at 2pm would be great." },
      { role: 'assistant', content: "Tuesday at 2pm is available. Can I get your name and email?" },
      { role: 'user', content: "Sure, it's Maria Santos, maria@example.com" },
      { role: 'assistant', content: "You're all set for Tuesday at 2pm, Maria. We'll send a confirmation email." },
    ],
  ];

  const calls = [];
  for (let i = 0; i < 150; i++) {
    const status = randomChoice(callStatuses);
    const type = randomChoice(callTypes);
    const assistant = randomChoice(assistants);
    const createdAt = randomDate(30);
    const duration = status === 'ENDED' ? randomInt(15, 600) : (status === 'IN_PROGRESS' ? null : randomInt(5, 30));
    const startedAt = new Date(createdAt.getTime() + randomInt(1000, 5000));
    const endedAt = status === 'ENDED' && duration ? new Date(startedAt.getTime() + duration * 1000) : null;
    const phoneNumber = type !== 'WEB' ? randomChoice(phoneNumbers) : null;

    calls.push({
      organizationId: org.id,
      assistantId: assistant.id,
      type,
      status,
      phoneNumberId: phoneNumber?.id ?? null,
      customerNumber: type !== 'WEB' ? `+1${randomInt(200, 999)}${randomInt(100, 999)}${randomInt(1000, 9999)}` : null,
      startedAt,
      endedAt,
      duration,
      endReason: status === 'ENDED' ? randomChoice(endReasons) : (status === 'FAILED' ? 'error' : null),
      transcript: status === 'ENDED' ? randomChoice(sampleTranscripts) : null,
      cost: status === 'ENDED' ? Number((duration! * 0.005 + 0.01).toFixed(4)) : null,
      metadata: { source: 'seed' },
      createdAt,
    });
  }

  await prisma.call.createMany({ data: calls });
  console.log(`  Created ${calls.length} calls`);

  // Tools
  const tools = await Promise.all(
    [
      {
        name: 'lookup_customer',
        type: 'FUNCTION' as ToolType,
        description: 'Look up customer information by email or phone number',
        function: {
          name: 'lookup_customer',
          description: 'Retrieve customer details from CRM',
          parameters: {
            type: 'object',
            properties: {
              email: { type: 'string', description: 'Customer email address' },
              phone: { type: 'string', description: 'Customer phone number' },
            },
          },
        },
        serverUrl: 'https://api.example.com/crm/lookup',
      },
      {
        name: 'create_ticket',
        type: 'FUNCTION' as ToolType,
        description: 'Create a support ticket in the helpdesk system',
        function: {
          name: 'create_ticket',
          description: 'Create a new support ticket',
          parameters: {
            type: 'object',
            properties: {
              subject: { type: 'string', description: 'Ticket subject' },
              description: { type: 'string', description: 'Issue description' },
              priority: { type: 'string', enum: ['low', 'medium', 'high', 'urgent'] },
            },
            required: ['subject', 'description'],
          },
        },
        serverUrl: 'https://api.example.com/helpdesk/tickets',
      },
      {
        name: 'schedule_appointment',
        type: 'FUNCTION' as ToolType,
        description: 'Book an appointment in the calendar system',
        function: {
          name: 'schedule_appointment',
          description: 'Schedule a new appointment',
          parameters: {
            type: 'object',
            properties: {
              date: { type: 'string', description: 'Appointment date (YYYY-MM-DD)' },
              time: { type: 'string', description: 'Appointment time (HH:MM)' },
              name: { type: 'string', description: 'Customer name' },
              email: { type: 'string', description: 'Customer email' },
            },
            required: ['date', 'time', 'name'],
          },
        },
        serverUrl: 'https://api.example.com/calendar/book',
      },
      {
        name: 'transfer_to_human',
        type: 'TRANSFER_CALL' as ToolType,
        description: 'Transfer the call to a human agent',
        metadata: { transferNumber: '+14155550000', department: 'support' },
      },
      {
        name: 'end_conversation',
        type: 'END_CALL' as ToolType,
        description: 'End the call when the conversation is complete',
      },
    ].map((tool) =>
      prisma.tool.create({
        data: { ...tool, organizationId: org.id },
      }),
    ),
  );
  console.log(`  Created ${tools.length} tools`);

  // Squads
  await prisma.squad.createMany({
    data: [
      {
        name: 'Customer Success',
        organizationId: org.id,
        members: [
          { assistantId: assistants[0].id, role: 'primary' },
          { assistantId: assistants[1].id, role: 'fallback' },
        ],
        metadata: { description: 'Handles sales inquiries with support fallback' },
      },
      {
        name: 'Outbound Team',
        organizationId: org.id,
        members: [
          { assistantId: assistants[2].id, role: 'primary' },
          { assistantId: assistants[3].id, role: 'secondary' },
        ],
        metadata: { description: 'Appointment scheduling and survey campaigns' },
      },
    ],
  });
  console.log('  Created 2 squads');

  // Campaigns
  const sampleContacts = [
    { name: 'John Smith', phone: '+12025551001', email: 'john@example.com' },
    { name: 'Sarah Johnson', phone: '+12025551002', email: 'sarah@example.com' },
    { name: 'Mike Chen', phone: '+12025551003', email: 'mike@example.com' },
    { name: 'Lisa Park', phone: '+12025551004', email: 'lisa@example.com' },
    { name: 'David Brown', phone: '+12025551005', email: 'david@example.com' },
    { name: 'Emma Wilson', phone: '+12025551006', email: 'emma@example.com' },
    { name: 'Carlos Rivera', phone: '+12025551007', email: 'carlos@example.com' },
    { name: 'Aisha Khan', phone: '+12025551008', email: 'aisha@example.com' },
  ];

  await prisma.campaign.createMany({
    data: [
      {
        name: 'Q1 Sales Outreach',
        organizationId: org.id,
        assistantId: assistants[0].id,
        phoneNumberId: phoneNumbers[1].id,
        status: 'COMPLETED' as CampaignStatus,
        contacts: sampleContacts.slice(0, 5),
        schedule: { startTime: '09:00', endTime: '17:00', timezone: 'America/New_York', daysOfWeek: [1, 2, 3, 4, 5] },
        stats: { totalContacts: 5, called: 5, answered: 4, voicemail: 1, avgDuration: 180 },
      },
      {
        name: 'Customer Satisfaction Survey',
        organizationId: org.id,
        assistantId: assistants[3].id,
        phoneNumberId: phoneNumbers[0].id,
        status: 'RUNNING' as CampaignStatus,
        contacts: sampleContacts,
        schedule: { startTime: '10:00', endTime: '16:00', timezone: 'America/Chicago', daysOfWeek: [1, 2, 3, 4, 5] },
        stats: { totalContacts: 8, called: 3, answered: 2, voicemail: 1, avgDuration: 120 },
      },
      {
        name: 'March Appointment Reminders',
        organizationId: org.id,
        assistantId: assistants[2].id,
        phoneNumberId: phoneNumbers[2].id,
        status: 'DRAFT' as CampaignStatus,
        contacts: sampleContacts.slice(0, 3),
        schedule: { startTime: '08:00', endTime: '12:00', timezone: 'America/Los_Angeles', daysOfWeek: [1, 3, 5] },
        stats: null,
      },
    ],
  });
  console.log('  Created 3 campaigns');

  // Webhooks
  const webhook = await prisma.webhook.create({
    data: {
      organizationId: org.id,
      url: 'https://hooks.example.com/load-events',
      events: ['call.started', 'call.ended', 'call.failed'],
      secret: 'whsec_demo_secret_key_123',
      active: true,
    },
  });

  // Sample webhook deliveries
  const deliveries = [];
  for (let i = 0; i < 20; i++) {
    const event = randomChoice(['call.started', 'call.ended', 'call.failed']);
    const success = Math.random() > 0.15;
    deliveries.push({
      webhookId: webhook.id,
      event,
      status: success ? 'success' : 'failed',
      requestBody: { event, data: { callId: `call_${i}`, timestamp: randomDate(7).toISOString() } },
      responseCode: success ? 200 : randomChoice([500, 502, 408]),
      responseBody: success ? '{"ok":true}' : null,
      responseTime: randomInt(50, 800),
      error: success ? null : 'Connection timeout',
      attemptNumber: success ? 1 : randomInt(1, 3),
      createdAt: randomDate(7),
    });
  }
  await prisma.webhookDelivery.createMany({ data: deliveries });
  console.log(`  Created 1 webhook + ${deliveries.length} deliveries`);

  console.log('\nSeed complete!');
  console.log('Login: admin@load.dev / demo1234');
}

main()
  .catch((e) => {
    console.error('Seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
