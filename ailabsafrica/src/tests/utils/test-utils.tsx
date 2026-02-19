import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { act } from '@testing-library/react';

// Custom render function that wraps components with necessary providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );
};

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Helper to wait for Radix UI components to settle
export const waitForRadixUI = async (ms = 100) => {
  await act(async () => {
    await new Promise(resolve => setTimeout(resolve, ms));
  });
};

// Helper to click on Radix UI select options
export const clickSelectOption = async (selectElement: HTMLElement, optionText: string) => {
  await act(async () => {
    selectElement.click();
  });
  
  await waitForRadixUI();
  
  await act(async () => {
    const option = document.querySelector(`[data-value="${optionText}"]`) || 
                   document.querySelector(`[role="option"]:has-text("${optionText}")`) ||
                   document.querySelector(`[data-radix-select-item]:has-text("${optionText}")`);
    if (option) {
      (option as HTMLElement).click();
    }
  });
  
  await waitForRadixUI();
};

// Helper to fill form fields with proper act() wrapping
export const fillFormField = async (element: HTMLElement, value: string) => {
  await act(async () => {
    element.focus();
    element.setAttribute('value', value);
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await waitForRadixUI();
};

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };
