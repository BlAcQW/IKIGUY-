import { describe, it, expect } from 'vitest';
import { render, screen } from '@test/helpers/render';

import { SettingsPage } from './Settings';

describe('SettingsPage', () => {
  it('renders page title', () => {
    render(<SettingsPage />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders API Keys card with link to /api-keys', () => {
    render(<SettingsPage />);
    expect(screen.getByText('API Keys')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /manage/i })).toHaveAttribute('href', '/api-keys');
  });

  it('renders General settings placeholder', () => {
    render(<SettingsPage />);
    expect(screen.getByText('General')).toBeInTheDocument();
    expect(screen.getByText('General settings coming soon.')).toBeInTheDocument();
  });

  it('renders Security settings placeholder', () => {
    render(<SettingsPage />);
    expect(screen.getByText('Security')).toBeInTheDocument();
    expect(screen.getByText('Security settings coming soon.')).toBeInTheDocument();
  });
});
