import bcrypt from 'bcryptjs';
import crypto from 'node:crypto';
import { prisma } from '../../database/client.js';
import type { RegisterInput, LoginInput, CreateApiKeyInput, UpdateProfileInput } from './schemas.js';

const SALT_ROUNDS = 12;
const API_KEY_PREFIX = 'load_';
const API_KEY_LENGTH = 32;
const REFRESH_TOKEN_LENGTH = 48;
const REFRESH_TOKEN_EXPIRY_DAYS = 7;

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

// --- Refresh Token Management ---

export async function createRefreshToken(userId: string, organizationId: string): Promise<string> {
  const rawToken = crypto.randomBytes(REFRESH_TOKEN_LENGTH).toString('hex');
  const tokenHash = await bcrypt.hash(rawToken, SALT_ROUNDS);
  const expiresAt = new Date(Date.now() + REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60 * 1000);

  await prisma.refreshToken.create({
    data: {
      tokenHash,
      userId,
      organizationId,
      expiresAt,
    },
  });

  return rawToken;
}

export async function rotateRefreshToken(rawToken: string) {
  // Find all non-expired, non-revoked tokens for comparison
  const candidates = await prisma.refreshToken.findMany({
    where: {
      revokedAt: null,
      expiresAt: { gt: new Date() },
    },
    include: {
      user: {
        select: { id: true, email: true, name: true, role: true },
      },
      organization: {
        select: { id: true, name: true, slug: true },
      },
    },
  });

  // Find the matching token by comparing hashes
  let matchedToken: (typeof candidates)[number] | null = null;
  for (const candidate of candidates) {
    const isMatch = await bcrypt.compare(rawToken, candidate.tokenHash);
    if (isMatch) {
      matchedToken = candidate;
      break;
    }
  }

  if (!matchedToken) {
    // Check if this token was already revoked (stolen token detection)
    const allTokens = await prisma.refreshToken.findMany({
      where: { revokedAt: { not: null } },
    });
    for (const revokedToken of allTokens) {
      const isRevokedMatch = await bcrypt.compare(rawToken, revokedToken.tokenHash);
      if (isRevokedMatch) {
        // Stolen token detected — revoke ALL tokens for this user
        await prisma.refreshToken.updateMany({
          where: { userId: revokedToken.userId, revokedAt: null },
          data: { revokedAt: new Date() },
        });
        throw Object.assign(new Error('Token reuse detected — all sessions revoked'), { statusCode: 401 });
      }
    }
    throw Object.assign(new Error('Invalid or expired refresh token'), { statusCode: 401 });
  }

  // Revoke the current token (single-use rotation)
  await prisma.refreshToken.update({
    where: { id: matchedToken.id },
    data: { revokedAt: new Date() },
  });

  // Issue a new refresh token
  const newRawToken = await createRefreshToken(matchedToken.userId, matchedToken.organizationId);

  return {
    refreshToken: newRawToken,
    user: matchedToken.user,
    organization: matchedToken.organization,
  };
}

export async function revokeAllRefreshTokens(userId: string) {
  await prisma.refreshToken.updateMany({
    where: { userId, revokedAt: null },
    data: { revokedAt: new Date() },
  });
}

// --- Profile Management ---

export async function updateProfile(userId: string, input: UpdateProfileInput) {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) {
    throw Object.assign(new Error('User not found'), { statusCode: 404 });
  }

  const updateData: Record<string, unknown> = {};

  if (input.name) {
    updateData.name = input.name;
  }

  if (input.email) {
    const existing = await prisma.user.findUnique({ where: { email: input.email } });
    if (existing && existing.id !== userId) {
      throw Object.assign(new Error('Email already in use'), { statusCode: 409 });
    }
    updateData.email = input.email;
  }

  if (input.newPassword && input.currentPassword) {
    const isValid = await bcrypt.compare(input.currentPassword, user.passwordHash);
    if (!isValid) {
      throw Object.assign(new Error('Current password is incorrect'), { statusCode: 400 });
    }
    updateData.passwordHash = await bcrypt.hash(input.newPassword, SALT_ROUNDS);
  }

  if (Object.keys(updateData).length === 0) {
    throw Object.assign(new Error('No fields to update'), { statusCode: 400 });
  }

  const updated = await prisma.user.update({
    where: { id: userId },
    data: updateData,
    select: { id: true, email: true, name: true, role: true },
  });

  return updated;
}

// --- Organization Management ---

export async function getOrganization(organizationId: string) {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
  });
  if (!org) {
    throw Object.assign(new Error('Organization not found'), { statusCode: 404 });
  }
  return org;
}

export async function updateOrganization(organizationId: string, name: string, userRole: string) {
  if (userRole !== 'OWNER' && userRole !== 'ADMIN') {
    throw Object.assign(new Error('Only owners and admins can update organization'), { statusCode: 403 });
  }
  const org = await prisma.organization.update({
    where: { id: organizationId },
    data: { name },
  });
  return org;
}

export async function listOrgMembers(organizationId: string) {
  const members = await prisma.user.findMany({
    where: { organizationId },
    select: { id: true, email: true, name: true, role: true, createdAt: true },
    orderBy: { createdAt: 'asc' },
  });
  return members;
}

export async function removeOrgMember(organizationId: string, userId: string, requestingUserRole: string) {
  if (requestingUserRole !== 'OWNER') {
    throw Object.assign(new Error('Only owners can remove members'), { statusCode: 403 });
  }

  const member = await prisma.user.findFirst({
    where: { id: userId, organizationId },
  });
  if (!member) {
    throw Object.assign(new Error('Member not found'), { statusCode: 404 });
  }
  if (member.role === 'OWNER') {
    throw Object.assign(new Error('Cannot remove organization owner'), { statusCode: 400 });
  }

  await prisma.user.delete({ where: { id: userId } });
}

// --- API Key Management ---

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
