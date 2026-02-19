import React, { createContext, useContext, useEffect, useRef } from 'react';

interface AccessibilityContextType {
  announceToScreenReader: (message: string) => void;
  focusElement: (element: HTMLElement | null) => void;
  setFocusTrap: (container: HTMLElement | null) => void;
  removeFocusTrap: () => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

interface AccessibilityProviderProps {
  children: React.ReactNode;
}

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const liveRegionRef = useRef<HTMLDivElement>(null);
  const focusTrapRef = useRef<HTMLElement | null>(null);
  const focusableElementsRef = useRef<HTMLElement[]>([]);

  // Screen reader announcements
  const announceToScreenReader = (message: string) => {
    if (liveRegionRef.current) {
      liveRegionRef.current.textContent = message;
      // Clear the message after a short delay
      setTimeout(() => {
        if (liveRegionRef.current) {
          liveRegionRef.current.textContent = '';
        }
      }, 1000);
    }
  };

  // Focus management
  const focusElement = (element: HTMLElement | null) => {
    if (element) {
      element.focus();
    }
  };

  // Focus trap management
  const setFocusTrap = (container: HTMLElement | null) => {
    if (!container) return;

    focusTrapRef.current = container;
    
    // Get all focusable elements within the container
    const focusableSelectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      'a[href]',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ];
    
    focusableElementsRef.current = Array.from(
      container.querySelectorAll(focusableSelectors.join(', '))
    ) as HTMLElement[];

    // Add keyboard event listener for focus trap
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        const firstElement = focusableElementsRef.current[0];
        const lastElement = focusableElementsRef.current[focusableElementsRef.current.length - 1];

        if (event.shiftKey) {
          // Shift + Tab: move backwards
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement?.focus();
          }
        } else {
          // Tab: move forwards
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement?.focus();
          }
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    
    // Store the event listener for cleanup
    (container as any)._focusTrapHandler = handleKeyDown;
  };

  const removeFocusTrap = () => {
    if (focusTrapRef.current && (focusTrapRef.current as any)._focusTrapHandler) {
      focusTrapRef.current.removeEventListener('keydown', (focusTrapRef.current as any)._focusTrapHandler);
      delete (focusTrapRef.current as any)._focusTrapHandler;
    }
    focusTrapRef.current = null;
    focusableElementsRef.current = [];
  };

  // Global keyboard shortcuts
  useEffect(() => {
    const handleGlobalKeyDown = (event: KeyboardEvent) => {
      // Skip if user is typing in an input field
      if (event.target instanceof HTMLInputElement || 
          event.target instanceof HTMLTextAreaElement || 
          event.target instanceof HTMLSelectElement) {
        return;
      }

      // Alt + 1: Go to Home
      if (event.altKey && event.key === '1') {
        event.preventDefault();
        window.location.href = '/';
      }

      // Alt + 2: Go to Demos
      if (event.altKey && event.key === '2') {
        event.preventDefault();
        window.location.href = '/demos';
      }

      // Alt + 3: Go to Contact
      if (event.altKey && event.key === '3') {
        event.preventDefault();
        window.location.href = '/contact';
      }

      // Alt + 4: Go to Create Assistant
      if (event.altKey && event.key === '4') {
        event.preventDefault();
        window.location.href = '/create-assistant';
      }

      // Alt + H: Show keyboard shortcuts help
      if (event.altKey && event.key === 'h') {
        event.preventDefault();
        announceToScreenReader('Keyboard shortcuts: Alt+1 Home, Alt+2 Demos, Alt+3 Contact, Alt+4 Create Assistant, Alt+H Help');
      }
    };

    document.addEventListener('keydown', handleGlobalKeyDown);
    return () => document.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  // Cleanup focus trap on unmount
  useEffect(() => {
    return () => {
      removeFocusTrap();
    };
  }, []);

  const value: AccessibilityContextType = {
    announceToScreenReader,
    focusElement,
    setFocusTrap,
    removeFocusTrap,
  };

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
      {/* Live region for screen reader announcements */}
      <div
        ref={liveRegionRef}
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        role="status"
      />
    </AccessibilityContext.Provider>
  );
};
