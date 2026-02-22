import bcrypt from 'bcryptjs';
import crypto from 'node:crypto';
import { prisma } from '../../database/client.js';
import type { RegisterInput, LoginInput, CreateApiKeyInput } from './schemas.js';

const SALT_ROUNDS = 12;
const API_KEY_PREFIX = 'load_';
const API_KEY_LENGTH = 32;

export async function registerUser(input: RegisterInput) {
  const existingUser = await prisma.user.findUnique({
    where: { email: input.email },
  });
  if (existingUser) {
    throw Object.assign(new Error('Email already registered'), { statusCode: 409 });
  }

  const passwordHash = await bcrypt.hash(input.password, SALT_ROUNDS);
  const slug = input.organizationName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

  const organization = await prisma.organization.create({
    data: {
      name: input.organizationName,
      slug: `${slug}-${crypto.randomBytes(3).toString('hex')}`,
    },
  });

  const user = await prisma.user.create({
    data: {
      email: input.email,
      passwordHash,
      name: input.name,
      role: 'OWNER',
      organizationId: organization.id,
    },
  });

  return {
    user: { id: user.id, email: user.email, name: user.name, role: user.role },
    organization: { id: organization.id, name: organization.name, slug: organization.slug },
  };
}

export async function loginUser(input: LoginInput) {
  const user = await prisma.user.findUnique({
    where: { email: input.email },
    include: { organization: true },
  });
  if (!user) {
    throw Object.assign(new Error('Invalid email or password'), { statusCode: 401 });
  }

  const isValid = await bcrypt.compare(input.password, user.passwordHash);
  if (!isValid) {
    throw Object.assign(new Error('Invalid email or password'), { statusCode: 401 });
  }

  return {
    user: { id: user.id, email: user.email, name: user.name, role: user.role },
    organization: {
      id: user.organization.id,
      name: user.organization.name,
      slug: user.organization.slug,
    },
  };
}

export async function createApiKey(
  input: CreateApiKeyInput,
  userId: string,
  organizationId: string
) {
  const rawKey = `${API_KEY_PREFIX}${crypto.randomBytes(API_KEY_LENGTH).toString('hex')}`;
  const prefix = rawKey.slice(0, 13); // "load_" + 8 hex chars
  const keyHash = await bcrypt.hash(rawKey, SALT_ROUNDS);

  const apiKey = await prisma.apiKey.create({
    data: {
      keyHash,
      prefix,
      name: input.name,
      organizationId,
      createdById: userId,
      expiresAt: input.expiresAt ? new Date(input.expiresAt) : null,
    },
  });

  // Return the raw key only once — it cannot be retrieved later
  return {
    id: apiKey.id,
    key: rawKey,
    prefix: apiKey.prefix,
    name: apiKey.name,
    createdAt: apiKey.createdAt,
    expiresAt: apiKey.expiresAt,
  };
}

export async function listApiKeys(organizationId: string) {
  const keys = await prisma.apiKey.findMany({
    where: { organizationId },
    select: {
      id: true,
      prefix: true,
      name: true,
      lastUsedAt: true,
      expiresAt: true,
      createdAt: true,
      createdBy: { select: { name: true, email: true } },
    },
    orderBy: { createdAt: 'desc' },
  });
  return keys;
}

export async function revokeApiKey(id: string, organizationId: string) {
  const apiKey = await prisma.apiKey.findFirst({
    where: { id, organizationId },
  });
  if (!apiKey) {
    throw Object.assign(new Error('API key not found'), { statusCode: 404 });
  }

  await prisma.apiKey.delete({ where: { id } });
}
