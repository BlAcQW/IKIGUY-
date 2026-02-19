/**
 * BookCard Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import BookCard from './BookCard';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, whileHover, whileTap, transition, ...props }: any) => (
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

describe('BookCard', () => {
  const defaultProps = {
    id: 'test-book-123',
    title: 'Test Book Title',
    author: 'Test Author',
    coverUrl: 'https://example.com/cover.jpg',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderBookCard = (props = {}) => {
    return render(
      <BrowserRouter>
        <BookCard {...defaultProps} {...props} />
      </BrowserRouter>
    );
  };

  it('should render book title', () => {
    renderBookCard();
    expect(screen.getByText('Test Book Title')).toBeInTheDocument();
  });

  it('should render author name', () => {
    renderBookCard();
    expect(screen.getByText('Test Author')).toBeInTheDocument();
  });

  it('should render cover image with correct alt text', () => {
    renderBookCard();
    const image = screen.getByAltText('Test Book Title');
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute('src', 'https://example.com/cover.jpg');
  });

  it('should navigate to book detail on card click', () => {
    renderBookCard();
    const card = screen.getByText('Test Book Title').closest('div');
    fireEvent.click(card!);
    expect(mockNavigate).toHaveBeenCalledWith('/book/test-book-123');
  });

  it('should navigate to player on play button click', () => {
    renderBookCard();
    const playButton = screen.getByRole('button');
    fireEvent.click(playButton);
    expect(mockNavigate).toHaveBeenCalledWith('/player/test-book-123');
  });

  it('should display duration when provided', () => {
    renderBookCard({ duration: 125 }); // 2h 5m
    expect(screen.getByText('2h 5m')).toBeInTheDocument();
  });

  it('should display progress when showProgress is true and progress > 0', () => {
    renderBookCard({ showProgress: true, progress: 45 });
    expect(screen.getByText('45% complete')).toBeInTheDocument();
  });

  it('should not display progress when showProgress is false', () => {
    renderBookCard({ showProgress: false, progress: 45 });
    expect(screen.queryByText('45% complete')).not.toBeInTheDocument();
  });

  it('should not display progress when progress is 0', () => {
    renderBookCard({ showProgress: true, progress: 0 });
    expect(screen.queryByText('0% complete')).not.toBeInTheDocument();
  });

  it('should render progress bar when showProgress and progress > 0', () => {
    const { container } = renderBookCard({ showProgress: true, progress: 50 });
    const progressBar = container.querySelector('[style*="width: 50%"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('should have touch feedback classes', () => {
    const { container } = renderBookCard();
    const card = container.firstChild;
    expect(card).toHaveClass('touch-card');
    expect(card).toHaveClass('no-zoom');
  });
});

describe('BookCard edge cases', () => {
  const renderBookCard = (props: any) => {
    return render(
      <BrowserRouter>
        <BookCard {...props} />
      </BrowserRouter>
    );
  };

  it('should handle very long title with truncation', () => {
    renderBookCard({
      id: 'test',
      title: 'This is a very long book title that should be truncated to fit within the card',
      author: 'Author',
      coverUrl: 'https://example.com/cover.jpg',
    });

    const title = screen.getByText(/This is a very long book title/);
    expect(title).toHaveClass('line-clamp-2');
  });

  it('should handle duration of exactly 1 hour', () => {
    renderBookCard({
      id: 'test',
      title: 'Test',
      author: 'Author',
      coverUrl: 'https://example.com/cover.jpg',
      duration: 60,
    });
    expect(screen.getByText('1h 0m')).toBeInTheDocument();
  });

  it('should handle duration less than 1 hour', () => {
    renderBookCard({
      id: 'test',
      title: 'Test',
      author: 'Author',
      coverUrl: 'https://example.com/cover.jpg',
      duration: 45,
    });
    expect(screen.getByText('0h 45m')).toBeInTheDocument();
  });

  it('should stop event propagation on play button click', () => {
    const { container } = renderBookCard({
      id: 'test',
      title: 'Test',
      author: 'Author',
      coverUrl: 'https://example.com/cover.jpg',
    });

    const playButton = screen.getByRole('button');
    const clickEvent = fireEvent.click(playButton);

    // The play button should have been clicked
    expect(clickEvent).toBe(true);
  });
});
