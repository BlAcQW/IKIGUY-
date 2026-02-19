export interface HelpContent {
  title: string;
  content: string;
}

const HELP_CONTENT: Record<string, HelpContent> = {
  dashboard_overview: {
    title: 'Dashboard Overview',
    content: 'Overview of dashboard features and navigation.',
  },
  enterprise_settings_configuration: {
    title: 'Settings',
    content: 'Manage account and workspace settings.',
  },
  enterprise_security_compliance: {
    title: 'Security & Compliance',
    content: 'Information on security controls and compliance features.',
  },
  tenant_management: {
    title: 'Tenant Management',
    content: 'Manage tenants and related options.',
  },
};

export function getHelpContent(key: string): HelpContent | null {
  return HELP_CONTENT[key] ?? null;
}

export function searchHelpContent(query: string): Array<{ key: string; content: HelpContent }> {
  const lower = query.toLowerCase();
  return Object.entries(HELP_CONTENT)
    .filter(([key, value]) =>
      key.toLowerCase().includes(lower) ||
      value.title.toLowerCase().includes(lower) ||
      value.content.toLowerCase().includes(lower)
    )
    .map(([key, content]) => ({ key, content }));
}

export function getHelpContentKeys(): string[] {
  return Object.keys(HELP_CONTENT);
}
