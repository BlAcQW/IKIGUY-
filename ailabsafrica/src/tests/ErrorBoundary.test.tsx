import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ErrorBoundary from '@/components/ErrorBoundary';

// Mock console.error to avoid noise in tests
const originalConsoleError = console.error;
beforeEach(() => {
  console.error = vi.fn();
});

afterEach(() => {
  console.error = originalConsoleError;
});

// Component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error message');
  }
  return <div>Normal content</div>;
};

// Component that throws an error in render
const ThrowErrorInRender = () => {
  throw new Error('Render error');
};

// Component that throws an error in useEffect
const ThrowErrorInEffect = () => {
  React.useEffect(() => {
    throw new Error('Effect error');
  }, []);
  return <div>Effect content</div>;
};

describe('ErrorBoundary', () => {
  describe('Normal Operation', () => {
    it('renders children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div>Test content</div>
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Test content')).toBeInTheDocument();
    });

    it('renders multiple children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div>First child</div>
          <div>Second child</div>
          <div>Third child</div>
        </ErrorBoundary>
      );
      
      expect(screen.getByText('First child')).toBeInTheDocument();
      expect(screen.getByText('Second child')).toBeInTheDocument();
      expect(screen.getByText('Third child')).toBeInTheDocument();
    });
  });

  describe('Error Catching', () => {
    it('catches errors thrown by child components', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText("We're sorry, but something unexpected happened. Please try refreshing the page or go back to the home page.")).toBeInTheDocument();
    });

    it('logs error to console when error occurs', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(console.error).toHaveBeenCalledWith(
        'ErrorBoundary caught an error:',
        expect.any(Error),
        expect.any(Object)
      );
    });

    it('catches render errors', () => {
      render(
        <ErrorBoundary>
          <ThrowErrorInRender />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });
  });

  describe('Error UI', () => {
    it('renders error UI with proper styling', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const errorCard = screen.getByText('Something went wrong').closest('[class*="card"]');
      expect(errorCard).toHaveClass('w-full', 'max-w-md');
    });

    it('renders error icon', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const icon = screen.getByText('Something went wrong').previousElementSibling;
      expect(icon).toHaveClass('h-16', 'w-16', 'text-destructive');
    });

    it('renders error title', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('renders error description', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText("We're sorry, but something unexpected happened. Please try refreshing the page or go back to the home page.")).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('renders try again button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    it('renders go home button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Go Home')).toBeInTheDocument();
    });

    it('try again button resets error state', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      
      // Click try again button
      fireEvent.click(screen.getByText('Try Again'));
      
      // Re-render with no error
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Normal content')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });

    it('go home button navigates to home page', () => {
      // Mock window.location
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { href: '' } as any;
      
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      fireEvent.click(screen.getByText('Go Home'));
      
      expect(window.location.href).toBe('/');
      
      // Restore original location
      window.location = originalLocation;
    });
  });

  describe('Custom Fallback', () => {
    it('renders custom fallback when provided', () => {
      const customFallback = <div>Custom error message</div>;
      
      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Custom error message')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });

    it('does not render default error UI when custom fallback is provided', () => {
      const customFallback = <div>Custom error message</div>;
      
      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.queryByText('Try Again')).not.toBeInTheDocument();
      expect(screen.queryByText('Go Home')).not.toBeInTheDocument();
    });
  });

  describe('Development Mode', () => {
    const originalEnv = process.env.NODE_ENV;
    
    beforeEach(() => {
      process.env.NODE_ENV = 'development';
    });
    
    afterEach(() => {
      process.env.NODE_ENV = originalEnv;
    });

    it('shows error details in development mode', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Error Details (Development)')).toBeInTheDocument();
    });

    it('shows error details in collapsible section', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const details = screen.getByText('Error Details (Development)').closest('details');
      expect(details).toBeInTheDocument();
    });

    it('shows error message in details', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const details = screen.getByText('Error Details (Development)').closest('details');
      expect(details).toHaveTextContent('Test error message');
    });
  });

  describe('Production Mode', () => {
    const originalEnv = process.env.NODE_ENV;
    
    beforeEach(() => {
      process.env.NODE_ENV = 'production';
    });
    
    afterEach(() => {
      process.env.NODE_ENV = originalEnv;
    });

    it('does not show error details in production mode', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.queryByText('Error Details (Development)')).not.toBeInTheDocument();
    });
  });

  describe('Error State Management', () => {
    it('maintains error state until reset', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      
      // Re-render with no error but don't reset
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );
      
      // Should still show error UI
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.queryByText('Normal content')).not.toBeInTheDocument();
    });

    it('clears error state when try again is clicked', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      fireEvent.click(screen.getByText('Try Again'));
      
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );
      
      expect(screen.getByText('Normal content')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper button roles', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Go Home' })).toBeInTheDocument();
    });

    it('has proper heading structure', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      expect(screen.getByRole('heading', { name: 'Something went wrong' })).toBeInTheDocument();
    });

    it('has proper summary element for error details', () => {
      process.env.NODE_ENV = 'development';
      
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const summary = screen.getByText('Error Details (Development)');
      expect(summary.tagName).toBe('SUMMARY');
    });
  });

  describe('Styling and Layout', () => {
    it('has proper container styling', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const container = screen.getByText('Something went wrong').closest('div');
      expect(container).toHaveClass('min-h-screen', 'bg-background', 'flex', 'items-center', 'justify-center');
    });

    it('has proper card styling', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const card = screen.getByText('Something went wrong').closest('[class*="card"]');
      expect(card).toHaveClass('w-full', 'max-w-md');
    });

    it('has proper button layout', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      
      const buttonContainer = screen.getByText('Try Again').closest('div');
      expect(buttonContainer).toHaveClass('flex', 'flex-col', 'sm:flex-row', 'gap-2');
    });
  });
});
