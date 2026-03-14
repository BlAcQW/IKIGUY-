import { describe, it, expect } from 'vitest';
import { render, screen } from '@test/helpers/render';
import { PageHeader } from './PageHeader';

describe('PageHeader', () => {
  it('renders title', () => {
    render(<PageHeader title="Settings" />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(<PageHeader title="Settings" subtitle="Manage your account" />);
    expect(screen.getByText('Manage your account')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', () => {
    render(<PageHeader title="Settings" />);
    expect(screen.queryByText('Manage your account')).not.toBeInTheDocument();
  });

  it('renders children', () => {
    render(
      <PageHeader title="Settings">
        <button>Create</button>
      </PageHeader>,
    );
    expect(screen.getByRole('button', { name: 'Create' })).toBeInTheDocument();
  });
});
