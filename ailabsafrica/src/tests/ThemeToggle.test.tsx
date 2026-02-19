import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ThemeToggle from '@/components/ThemeToggle';

// Mock next-themes
vi.mock('next-themes', () => ({
  useTheme: () => ({
    theme: 'light',
    setTheme: vi.fn(),
    resolvedTheme: 'light',
  }),
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('ThemeToggle', () => {
  it('renders theme toggle button', () => {
    render(<ThemeToggle />);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(<ThemeToggle />);
    const srText = screen.getByText('Toggle theme');
    expect(srText).toHaveClass('sr-only');
  });
});
