/**
 * Shared Campaign Components
 *
 * Centralized, reusable React components for multi-channel campaign management.
 * Works with the centralized campaign backend system.
 */

export { CampaignList } from './CampaignList';
export type { Campaign, CampaignListProps, CampaignType, CampaignStatus } from './CampaignList';

export { CampaignAnalytics } from './CampaignAnalytics';
export type { CampaignAnalytics as CampaignAnalyticsData, CampaignAnalyticsProps } from './CampaignAnalytics';

export { ContactList } from './ContactList';
export type { Contact, ContactStats, ContactListProps } from './ContactList';

// Re-export types for convenience
export type {
  Campaign,
  CampaignType,
  CampaignStatus,
  Contact,
  ContactStats
};
