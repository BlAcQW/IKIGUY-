import React from 'react';

interface LoadingStateProps {
  isLoading: boolean;
  error?: Error | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  loadingMessage?: string;
  errorMessage?: string;
  onRetry?: () => void;
  children?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'skeleton' | 'dots' | 'pulse';
}

/**
 * Comprehensive loading state component
 * 
 * Handles loading, error, and empty states with consistent UI
 */
export function LoadingState({
  isLoading,
  error,
  isEmpty = false,
  emptyMessage = 'No data available',
  loadingMessage = 'Loading...',
  errorMessage,
  onRetry,
  children,
  size = 'md',
  variant = 'spinner',
}: LoadingStateProps) {
  // Show error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
          <svg
            className="w-6 h-6 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Something went wrong
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          {errorMessage || error.message || 'An unexpected error occurred'}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Try Again
          </button>
        )}
      </div>
    );
  }

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <LoadingIndicator size={size} variant={variant} />
        <p className="mt-4 text-sm text-gray-500">{loadingMessage}</p>
      </div>
    );
  }

  // Show empty state
  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-gray-100 rounded-full mb-4">
          <svg
            className="w-6 h-6 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        </div>
        <p className="text-sm text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  // Show content
  return <>{children}</>;
}

/**
 * Loading indicator component with different variants
 */
function LoadingIndicator({ size, variant }: { size: string; variant: string }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const sizeClass = sizeClasses[size as keyof typeof sizeClasses] || sizeClasses.md;

  switch (variant) {
    case 'spinner':
      return (
        <div className={`${sizeClass} animate-spin rounded-full border-2 border-gray-300 border-t-blue-600`} />
      );

    case 'dots':
      return (
        <div className="flex space-x-1">
          <div className={`${sizeClass} bg-blue-600 rounded-full animate-bounce`} style={{ animationDelay: '0ms' }} />
          <div className={`${sizeClass} bg-blue-600 rounded-full animate-bounce`} style={{ animationDelay: '150ms' }} />
          <div className={`${sizeClass} bg-blue-600 rounded-full animate-bounce`} style={{ animationDelay: '300ms' }} />
        </div>
      );

    case 'pulse':
      return (
        <div className={`${sizeClass} bg-blue-600 rounded-full animate-pulse`} />
      );

    case 'skeleton':
      return (
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 bg-gray-200 rounded animate-pulse w-5/6" />
          <div className="h-4 bg-gray-200 rounded animate-pulse w-4/6" />
        </div>
      );

    default:
      return (
        <div className={`${sizeClass} animate-spin rounded-full border-2 border-gray-300 border-t-blue-600`} />
      );
  }
}

/**
 * Skeleton loading component for content areas
 */
export function SkeletonLoader({ rows = 3, className = '' }: { rows?: number; className?: string }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className="h-4 bg-gray-200 rounded animate-pulse"
          style={{ width: `${Math.random() * 40 + 60}%` }}
        />
      ))}
    </div>
  );
}

/**
 * Table skeleton loader
 */
export function TableSkeletonLoader({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
      <table className="min-w-full divide-y divide-gray-300">
        <thead className="bg-gray-50">
          <tr>
            {Array.from({ length: columns }).map((_, index) => (
              <th
                key={index}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                <div className="h-4 bg-gray-200 rounded animate-pulse" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <tr key={rowIndex}>
              {Array.from({ length: columns }).map((_, colIndex) => (
                <td key={colIndex} className="px-6 py-4 whitespace-nowrap">
                  <div className="h-4 bg-gray-200 rounded animate-pulse" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Card skeleton loader
 */
export function CardSkeletonLoader({ cards = 3 }: { cards?: number }) {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: cards }).map((_, index) => (
        <div key={index} className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse" />
              </div>
              <div className="ml-4 flex-1">
                <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
                <div className="mt-2 h-3 bg-gray-200 rounded animate-pulse w-1/2" />
              </div>
            </div>
            <div className="mt-4 space-y-2">
              <div className="h-3 bg-gray-200 rounded animate-pulse" />
              <div className="h-3 bg-gray-200 rounded animate-pulse w-5/6" />
              <div className="h-3 bg-gray-200 rounded animate-pulse w-4/6" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Hook for managing loading states
 */
export function useLoadingState() {
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const startLoading = React.useCallback(() => {
    setIsLoading(true);
    setError(null);
  }, []);

  const stopLoading = React.useCallback(() => {
    setIsLoading(false);
  }, []);

  const setErrorState = React.useCallback((err: Error) => {
    setError(err);
    setIsLoading(false);
  }, []);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  const reset = React.useCallback(() => {
    setIsLoading(false);
    setError(null);
  }, []);

  return {
    isLoading,
    error,
    startLoading,
    stopLoading,
    setErrorState,
    clearError,
    reset,
  };
}
