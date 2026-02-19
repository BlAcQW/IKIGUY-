/**
 * PullToRefreshIndicator Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import PullToRefreshIndicator from './PullToRefreshIndicator';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => children,
}));

describe('PullToRefreshIndicator', () => {
  const defaultProps = {
    pullDistance: 0,
    progress: 0,
    canRelease: false,
    isRefreshing: false,
    isPulling: false,
  };

  it('should not render when not pulling and not refreshing', () => {
    const { container } = render(<PullToRefreshIndicator {...defaultProps} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render when isPulling is true', () => {
    render(
      <PullToRefreshIndicator
        {...defaultProps}
        isPulling={true}
        pullDistance={30}
      />
    );

    // Should show the indicator container
    const indicator = document.querySelector('.fixed');
    expect(indicator).toBeInTheDocument();
  });

  it('should render when isRefreshing is true', () => {
    render(
      <PullToRefreshIndicator
        {...defaultProps}
        isRefreshing={true}
        pullDistance={80}
      />
    );

    const indicator = document.querySelector('.fixed');
    expect(indicator).toBeInTheDocument();
  });

  it('should render when pullDistance > 0', () => {
    render(
      <PullToRefreshIndicator
        {...defaultProps}
        pullDistance={20}
      />
    );

    const indicator = document.querySelector('.fixed');
    expect(indicator).toBeInTheDocument();
  });

  it('should show purple background when canRelease is true', () => {
    const { container } = render(
      <PullToRefreshIndicator
        {...defaultProps}
        isPulling={true}
        pullDistance={100}
        canRelease={true}
      />
    );

    const iconContainer = container.querySelector('.bg-purple-500\\/90');
    expect(iconContainer).toBeInTheDocument();
  });

  it('should show gray background when canRelease is false', () => {
    const { container } = render(
      <PullToRefreshIndicator
        {...defaultProps}
        isPulling={true}
        pullDistance={30}
        canRelease={false}
      />
    );

    const iconContainer = container.querySelector('.bg-gray-800\\/90');
    expect(iconContainer).toBeInTheDocument();
  });

  it('should show purple background when refreshing', () => {
    const { container } = render(
      <PullToRefreshIndicator
        {...defaultProps}
        isRefreshing={true}
        pullDistance={80}
        canRelease={true}
      />
    );

    const iconContainer = container.querySelector('.bg-purple-500\\/90');
    expect(iconContainer).toBeInTheDocument();
  });
});

describe('PullToRefreshIndicator visual states', () => {
  it('should have safe area padding class', () => {
    const { container } = render(
      <PullToRefreshIndicator
        pullDistance={50}
        progress={0.5}
        canRelease={false}
        isRefreshing={false}
        isPulling={true}
      />
    );

    const indicator = container.querySelector('.pt-safe');
    expect(indicator).toBeInTheDocument();
  });

  it('should be positioned fixed at top', () => {
    const { container } = render(
      <PullToRefreshIndicator
        pullDistance={50}
        progress={0.5}
        canRelease={false}
        isRefreshing={false}
        isPulling={true}
      />
    );

    const indicator = container.querySelector('.fixed.top-0');
    expect(indicator).toBeInTheDocument();
  });

  it('should have pointer-events-none to not block interactions', () => {
    const { container } = render(
      <PullToRefreshIndicator
        pullDistance={50}
        progress={0.5}
        canRelease={false}
        isRefreshing={false}
        isPulling={true}
      />
    );

    const indicator = container.querySelector('.pointer-events-none');
    expect(indicator).toBeInTheDocument();
  });
});
