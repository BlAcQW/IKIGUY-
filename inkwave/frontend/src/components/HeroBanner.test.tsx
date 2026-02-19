/**
 * HeroBanner Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import HeroBanner from './HeroBanner';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, initial, animate, transition, ...props }: any) => (
      <div {...props}>{children}</div>
    ),
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('HeroBanner', () => {
  const defaultProps = {
    id: 'book-123',
    title: 'The Power of Faith',
    author: 'Dr. Samuel Blessing',
    description: 'An inspiring journey through the transformative power of faith.',
    coverUrl: 'https://example.com/cover.jpg',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderHeroBanner = (props = {}) => {
    return render(
      <BrowserRouter>
        <HeroBanner {...defaultProps} {...props} />
      </BrowserRouter>
    );
  };

  it('should render the title', () => {
    renderHeroBanner();
    expect(screen.getByText('The Power of Faith')).toBeInTheDocument();
  });

  it('should render the author', () => {
    renderHeroBanner();
    expect(screen.getByText('Dr. Samuel Blessing')).toBeInTheDocument();
  });

  it('should render the description on larger screens', () => {
    renderHeroBanner();
    expect(screen.getByText(/An inspiring journey/)).toBeInTheDocument();
  });

  it('should render the cover image', () => {
    renderHeroBanner();
    const images = screen.getAllByAltText('The Power of Faith');
    expect(images.length).toBeGreaterThan(0);
  });

  it('should render genre badge when provided', () => {
    renderHeroBanner({ genre: 'Faith & Inspiration' });
    expect(screen.getByText('Faith & Inspiration')).toBeInTheDocument();
  });

  it('should not render genre badge when not provided', () => {
    renderHeroBanner();
    expect(screen.queryByText('Faith & Inspiration')).not.toBeInTheDocument();
  });

  it('should render duration when provided', () => {
    renderHeroBanner({ duration: 180 }); // 3 hours
    expect(screen.getByText('3h 0m')).toBeInTheDocument();
  });

  it('should navigate to player on Start Listening click', () => {
    renderHeroBanner();
    const playButton = screen.getByText('Start Listening');
    fireEvent.click(playButton);
    expect(mockNavigate).toHaveBeenCalledWith('/player/book-123');
  });

  it('should navigate to book detail on More Info click', () => {
    renderHeroBanner();
    const infoButton = screen.getByText('More Info');
    fireEvent.click(infoButton);
    expect(mockNavigate).toHaveBeenCalledWith('/book/book-123');
  });

  it('should have play and info buttons', () => {
    renderHeroBanner();
    const playButton = screen.getByText('Start Listening');
    const infoButton = screen.getByText('More Info');
    expect(playButton).toBeInTheDocument();
    expect(infoButton).toBeInTheDocument();
  });

  it('should use backgroundUrl when provided', () => {
    const { container } = renderHeroBanner({
      backgroundUrl: 'https://example.com/background.jpg',
    });
    const bgImage = container.querySelector('img[src="https://example.com/background.jpg"]');
    expect(bgImage).toBeInTheDocument();
  });

  it('should fall back to coverUrl when backgroundUrl not provided', () => {
    const { container } = renderHeroBanner();
    const images = container.querySelectorAll('img');
    // All images should use coverUrl
    images.forEach((img) => {
      expect(img.getAttribute('src')).toBe('https://example.com/cover.jpg');
    });
  });
});

describe('HeroBanner duration formatting', () => {
  const baseProps = {
    id: 'book-123',
    title: 'Test',
    author: 'Author',
    description: 'Description',
    coverUrl: 'https://example.com/cover.jpg',
  };

  const renderHeroBanner = (props = {}) => {
    return render(
      <BrowserRouter>
        <HeroBanner {...baseProps} {...props} />
      </BrowserRouter>
    );
  };

  it('should format duration with hours and minutes', () => {
    renderHeroBanner({ duration: 125 }); // 2h 5m
    expect(screen.getByText('2h 5m')).toBeInTheDocument();
  });

  it('should format duration with only hours', () => {
    renderHeroBanner({ duration: 120 }); // 2h 0m
    expect(screen.getByText('2h 0m')).toBeInTheDocument();
  });

  it('should format short duration', () => {
    renderHeroBanner({ duration: 45 }); // 0h 45m
    expect(screen.getByText('0h 45m')).toBeInTheDocument();
  });
});
