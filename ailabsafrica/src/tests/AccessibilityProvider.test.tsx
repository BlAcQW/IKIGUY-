import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AccessibilityProvider, useAccessibility } from '@/components/AccessibilityProvider';

// Mock component to test the accessibility context
const TestComponent = () => {
  const { announceToScreenReader, focusElement, setFocusTrap, removeFocusTrap } = useAccessibility();
  
  return (
    <div>
      <button 
        onClick={() => announceToScreenReader('Test announcement')}
        aria-label="Test announcement"
      >
        Announce
      </button>
      <button 
        onClick={() => focusElement(document.querySelector('input'))}
        aria-label="Focus input"
      >
        Focus
      </button>
      <button 
        onClick={() => setFocusTrap(document.querySelector('.container'))}
        aria-label="Set focus trap"
      >
        Set Trap
      </button>
      <button 
        onClick={() => removeFocusTrap()}
        aria-label="Remove focus trap"
      >
        Remove Trap
      </button>
      <input type="text" placeholder="Test input" />
      <div className="container">
        <button>Button 1</button>
        <button>Button 2</button>
      </div>
    </div>
  );
};

describe('AccessibilityProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders children without crashing', () => {
    render(
      <AccessibilityProvider>
        <div>Test content</div>
      </AccessibilityProvider>
    );
    
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('provides accessibility context to children', () => {
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    expect(screen.getByLabelText('Test announcement')).toBeInTheDocument();
    expect(screen.getByLabelText('Focus input')).toBeInTheDocument();
    expect(screen.getByLabelText('Set focus trap')).toBeInTheDocument();
    expect(screen.getByLabelText('Remove focus trap')).toBeInTheDocument();
  });

  it('announces messages to screen reader', async () => {
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    const announceButton = screen.getByLabelText('Test announcement');
    fireEvent.click(announceButton);
    
    // Check that the live region exists
    const liveRegion = screen.getByRole('status');
    expect(liveRegion).toBeInTheDocument();
    expect(liveRegion).toHaveClass('sr-only');
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');
    expect(liveRegion).toHaveAttribute('aria-atomic', 'true');
  });

  it('handles keyboard shortcuts', async () => {
    // Mock window.location.href assignment
    const originalLocation = window.location;
    delete (window as any).location;
    window.location = { ...originalLocation, href: '' } as any;

    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );

    // Test Alt + 1 (Home)
    fireEvent.keyDown(document, { key: '1', altKey: true });
    expect(window.location.href).toBe('/');

    // Test Alt + 2 (Demos)
    fireEvent.keyDown(document, { key: '2', altKey: true });
    expect(window.location.href).toBe('/demos');

    // Test Alt + 3 (Contact)
    fireEvent.keyDown(document, { key: '3', altKey: true });
    expect(window.location.href).toBe('/contact');

    // Test Alt + 4 (Create Assistant)
    fireEvent.keyDown(document, { key: '4', altKey: true });
    expect(window.location.href).toBe('/create-assistant');

    // Restore original location
    window.location = originalLocation;
  });

  it('does not trigger shortcuts when typing in input fields', () => {
    // Mock window.location.href assignment
    const originalLocation = window.location;
    delete (window as any).location;
    window.location = { ...originalLocation, href: '' } as any;

    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );

    const input = screen.getByPlaceholderText('Test input');
    input.focus();

    // Try to trigger shortcut while input is focused
    fireEvent.keyDown(input, { key: '1', altKey: true });
    
    // Should not trigger navigation
    expect(window.location.href).toBe('');

    // Restore original location
    window.location = originalLocation;
  });

  it('throws error when useAccessibility is used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAccessibility must be used within an AccessibilityProvider');
    
    consoleSpy.mockRestore();
  });
});
