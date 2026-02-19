/**
 * KasaAI Shared UI Hooks
 *
 * Reusable React hooks for AI provider management, authentication, organization switching, and more.
 *
 * @packageDocumentation
 */

export { useAIProvider } from './useAIProvider';
export { useOrganizationSwitcher } from './useOrganizationSwitcher';

export type {
  AIProvider,
  ProviderType,
  ProviderStatus,
  ProviderCapabilities,
  UseAIProviderOptions,
  UseAIProviderReturn,
} from './types';

export type {
  Organization,
  OrganizationMembership,
  UseOrganizationSwitcherOptions,
  UseOrganizationSwitcherReturn,
} from './useOrganizationSwitcher';
