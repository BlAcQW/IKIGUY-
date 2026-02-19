import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { toast } from 'sonner';

export type ErrorSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface AppError {
  id: string;
  message: string;
  description?: string;
  severity: ErrorSeverity;
  timestamp: Date;
  code?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  source?: string;
  data?: any;
}

interface ErrorContextType {
  errors: AppError[];
  showError: (error: Omit<AppError, 'id' | 'timestamp'>) => void;
  clearError: (id: string) => void;
  clearAllErrors: () => void;
  handleApiError: (error: any, source?: string) => void;
  handleValidationError: (errors: Record<string, string>, source?: string) => void;
  handleNetworkError: (error: any, source?: string) => void;
}

const ErrorContext = createContext<ErrorContextType | null>(null);

export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

interface ErrorProviderProps {
  children: ReactNode;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({ children }) => {
  const [errors, setErrors] = useState<AppError[]>([]);

  const generateId = () => Date.now().toString() + Math.random().toString(36).substr(2, 9);

  const showError = useCallback((errorData: Omit<AppError, 'id' | 'timestamp'>) => {
    const error: AppError = {
      ...errorData,
      id: generateId(),
      timestamp: new Date(),
    };

    setErrors(prev => [error, ...prev.slice(0, 49)]); // Keep max 50 errors

    // Show toast notification based on severity
    const toastDuration = {
      info: 3000,
      warning: 5000,
      error: 7000,
      critical: 10000,
    }[error.severity];

    const toastType = {
      info: 'message',
      warning: 'warning',
      error: 'error',
      critical: 'error',
    }[error.severity] as 'message' | 'warning' | 'error';

    if (toastType === 'message') {
      toast(error.message, {
        description: error.description,
        duration: toastDuration,
        action: error.action ? {
          label: error.action.label,
          onClick: error.action.onClick,
        } : undefined,
      });
    } else if (toastType === 'warning') {
      toast.warning(error.message, {
        description: error.description,
        duration: toastDuration,
        action: error.action ? {
          label: error.action.label,
          onClick: error.action.onClick,
        } : undefined,
      });
    } else {
      toast.error(error.message, {
        description: error.description,
        duration: toastDuration,
        action: error.action ? {
          label: error.action.label,
          onClick: error.action.onClick,
        } : undefined,
      });
    }

    // Log critical errors to console
    if (error.severity === 'critical') {
      console.error('Critical Error:', {
        message: error.message,
        description: error.description,
        code: error.code,
        source: error.source,
        data: error.data,
        timestamp: error.timestamp,
      });
    }
  }, []);

  const clearError = useCallback((id: string) => {
    setErrors(prev => prev.filter(error => error.id !== id));
  }, []);

  const clearAllErrors = useCallback(() => {
    setErrors([]);
  }, []);

  const handleApiError = useCallback((error: any, source?: string) => {
    const status = error?.response?.status || error?.status;
    const message = error?.response?.data?.message || error?.message || 'An unexpected error occurred';
    const code = error?.response?.data?.code || error?.code;

    let severity: ErrorSeverity = 'error';
    let errorMessage = message;
    let description = '';

    // Categorize by HTTP status code
    if (status >= 400 && status < 500) {
      severity = 'warning';
      switch (status) {
        case 400:
          errorMessage = 'Invalid request';
          description = 'Please check your input and try again.';
          break;
        case 401:
          errorMessage = 'Authentication required';
          description = 'Please sign in to continue.';
          break;
        case 403:
          errorMessage = 'Access denied';
          description = 'You don\'t have permission to perform this action.';
          break;
        case 404:
          errorMessage = 'Resource not found';
          description = 'The requested resource could not be found.';
          break;
        case 429:
          errorMessage = 'Too many requests';
          description = 'Please wait a moment before trying again.';
          break;
        default:
          description = message;
      }
    } else if (status >= 500) {
      severity = 'error';
      errorMessage = 'Server error';
      description = 'Something went wrong on our end. Please try again later.';
    } else if (!status) {
      severity = 'critical';
      errorMessage = 'Network error';
      description = 'Unable to connect to the server. Please check your internet connection.';
    }

    showError({
      message: errorMessage,
      description,
      severity,
      code: code || status?.toString(),
      source: source || 'API',
      data: error,
    });
  }, [showError]);

  const handleValidationError = useCallback((errors: Record<string, string>, source?: string) => {
    const fieldErrors = Object.entries(errors);

    if (fieldErrors.length === 1) {
      const [field, message] = fieldErrors[0];
      showError({
        message: 'Validation Error',
        description: `${field}: ${message}`,
        severity: 'warning',
        source: source || 'Validation',
        data: errors,
      });
    } else {
      showError({
        message: 'Multiple validation errors',
        description: `Please fix ${fieldErrors.length} errors in the form.`,
        severity: 'warning',
        source: source || 'Validation',
        data: errors,
      });
    }
  }, [showError]);

  const handleNetworkError = useCallback((error: any, source?: string) => {
    const isOffline = !navigator.onLine;

    showError({
      message: isOffline ? 'You are offline' : 'Network connection error',
      description: isOffline
        ? 'Please check your internet connection and try again.'
        : 'Unable to connect to the server. Please try again.',
      severity: 'error',
      source: source || 'Network',
      data: error,
      action: {
        label: 'Retry',
        onClick: () => window.location.reload(),
      },
    });
  }, [showError]);

  const value: ErrorContextType = {
    errors,
    showError,
    clearError,
    clearAllErrors,
    handleApiError,
    handleValidationError,
    handleNetworkError,
  };

  return (
    <ErrorContext.Provider value={value}>
      {children}
    </ErrorContext.Provider>
  );
};