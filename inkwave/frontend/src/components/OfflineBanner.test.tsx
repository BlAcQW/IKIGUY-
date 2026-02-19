/**
 * OfflineBanner Component Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import OfflineBanner from './OfflineBanner';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, initial, animate, exit, transition, ...props }: any) => (
      <div {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: any) => children,
}));

// Mock useOfflineStatus hook
const mockOfflineStatus = {
  isOnline: true,
  wasOffline: false,
};

vi.mock('../hooks/useOfflineStatus', () => ({
  useOfflineStatus: () => mockOfflineStatus,
}));

describe('OfflineBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockOfflineStatus.isOnline = true;
    mockOfflineStatus.wasOffline = false;
  });

  it('should not render when online and was not offline', () => {
    mockOfflineStatus.isOnline = true;
    mockOfflineStatus.wasOffline = false;

    const { container } = render(<OfflineBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('should render offline message when offline', () => {
    mockOfflineStatus.isOnline = false;
    mockOfflineStatus.wasOffline = false;

    render(<OfflineBanner />);
    expect(screen.getByText(/You're offline/)).toBeInTheDocument();
    expect(screen.getByText(/Cached content is still available/)).toBeInTheDocument();
  });

  it('should render back online message when coming back online', () => {
    mockOfflineStatus.isOnline = true;
    mockOfflineStatus.wasOffline = true;

    render(<OfflineBanner />);
    expect(screen.getByText(/You're back online/)).toBeInTheDocument();
  });

  it('should have amber background when offline', () => {
    mockOfflineStatus.isOnline = false;

    const { container } = render(<OfflineBanner />);
    const banner = container.querySelector('.bg-amber-600');
    expect(banner).toBeInTheDocument();
  });

  it('should have green background when coming back online', () => {
    mockOfflineStatus.isOnline = true;
    mockOfflineStatus.wasOffline = true;

    const { container } = render(<OfflineBanner />);
    const banner = container.querySelector('.bg-green-600');
    expect(banner).toBeInTheDocument();
  });

  it('should have WifiOff icon when offline', () => {
    mockOfflineStatus.isOnline = false;

    const { container } = render(<OfflineBanner />);
    // Check for svg (icon)
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('should be fixed positioned at top', () => {
    mockOfflineStatus.isOnline = false;

    const { container } = render(<OfflineBanner />);
    const banner = container.querySelector('.fixed.top-0');
    expect(banner).toBeInTheDocument();
  });

  it('should have high z-index to appear above other content', () => {
    mockOfflineStatus.isOnline = false;

    const { container } = render(<OfflineBanner />);
    const banner = container.querySelector('[class*="z-"]');
    expect(banner).toBeInTheDocument();
  });

  it('should have safe-top class for notched devices', () => {
    mockOfflineStatus.isOnline = false;

    const { container } = render(<OfflineBanner />);
    const banner = container.querySelector('.safe-top');
    expect(banner).toBeInTheDocument();
  });
});
