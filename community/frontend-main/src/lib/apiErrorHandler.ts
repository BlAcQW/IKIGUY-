import { toast } from 'sonner';

export interface ApiError {
  message: string;
  code?: string;
  field?: string;
  details?: any;
  status?: number;
  timestamp?: string;
}

export interface ApiErrorResponse {
  error: ApiError;
  errors?: ApiError[];
  success: false;
  data?: null;
}

export interface ApiSuccessResponse<T = any> {
  data: T;
  success: true;
  message?: string;
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
    totalPages?: number;
  };
}

export type ApiResponse<T = any> = ApiSuccessResponse<T> | ApiErrorResponse;

class ApiErrorHandler {
  private static instance: ApiErrorHandler;

  public static getInstance(): ApiErrorHandler {
    if (!ApiErrorHandler.instance) {
      ApiErrorHandler.instance = new ApiErrorHandler();
    }
    return ApiErrorHandler.instance;
  }

  public handleError(error: any, context?: string): ApiError {
    const apiError = this.parseError(error);
    this.logError(apiError, context);
    this.showErrorNotification(apiError, context);
    return apiError;
  }

  public handleValidationErrors(errors: ApiError[], context?: string): void {
    errors.forEach(error => {
      this.logError(error, context);
    });

    if (errors.length === 1) {
      const error = errors[0];
      toast.error('Validation Error', {
        description: error.field ? `${error.field}: ${error.message}` : error.message,
        duration: 5000,
      });
    } else if (errors.length > 1) {
      toast.error('Multiple Validation Errors', {
        description: `Please fix ${errors.length} errors in the form.`,
        duration: 6000,
        action: {
          label: 'View Details',
          onClick: () => {
            const errorList = errors.map(e =>
              e.field ? `• ${e.field}: ${e.message}` : `• ${e.message}`
            ).join('\n');
            alert(`Validation Errors:\n\n${errorList}`);
          }
        }
      });
    }
  }

  public handleNetworkError(error: any, context?: string): ApiError {
    const isOffline = !navigator.onLine;
    const apiError: ApiError = {
      message: isOffline ? 'You are currently offline' : 'Network connection failed',
      code: 'NETWORK_ERROR',
      status: 0,
      details: error,
    };

    this.logError(apiError, context);

    toast.error(apiError.message, {
      description: isOffline
        ? 'Please check your internet connection and try again.'
        : 'Unable to connect to the server. Please try again.',
      duration: 8000,
      action: {
        label: 'Retry',
        onClick: () => window.location.reload(),
      }
    });

    return apiError;
  }

  public handleSuccess(message: string, description?: string): void {
    toast.success(message, {
      description,
      duration: 4000,
    });
  }

  public handleInfo(message: string, description?: string): void {
    toast(message, {
      description,
      duration: 5000,
    });
  }

  public handleWarning(message: string, description?: string): void {
    toast.warning(message, {
      description,
      duration: 6000,
    });
  }

  private parseError(error: any): ApiError {
    // Handle Axios errors
    if (error.response) {
      const { data, status, statusText } = error.response;

      // Handle structured API error response
      if (data && typeof data === 'object') {
        if (data.error) {
          return {
            message: data.error.message || data.message || statusText,
            code: data.error.code || data.code,
            field: data.error.field || data.field,
            status,
            details: data.error.details || data.details,
          };
        }

        if (data.message) {
          return {
            message: data.message,
            code: data.code,
            status,
            details: data,
          };
        }
      }

      // Handle HTTP status codes
      return this.createErrorFromStatus(status, statusText);
    }

    // Handle network errors
    if (error.request) {
      return {
        message: 'Network error occurred',
        code: 'NETWORK_ERROR',
        status: 0,
        details: error,
      };
    }

    // Handle other errors
    return {
      message: error.message || 'An unexpected error occurred',
      code: error.code || 'UNKNOWN_ERROR',
      details: error,
    };
  }

  private createErrorFromStatus(status: number, statusText: string): ApiError {
    let message: string;
    let code: string;

    switch (status) {
      case 400:
        message = 'Invalid request. Please check your input.';
        code = 'BAD_REQUEST';
        break;
      case 401:
        message = 'Authentication required. Please sign in.';
        code = 'UNAUTHORIZED';
        break;
      case 403:
        message = 'You don\'t have permission to perform this action.';
        code = 'FORBIDDEN';
        break;
      case 404:
        message = 'The requested resource was not found.';
        code = 'NOT_FOUND';
        break;
      case 409:
        message = 'This resource already exists or conflicts with another.';
        code = 'CONFLICT';
        break;
      case 422:
        message = 'The submitted data is invalid.';
        code = 'VALIDATION_ERROR';
        break;
      case 429:
        message = 'Too many requests. Please wait before trying again.';
        code = 'RATE_LIMITED';
        break;
      case 500:
        message = 'Internal server error. Please try again later.';
        code = 'SERVER_ERROR';
        break;
      case 502:
        message = 'Service temporarily unavailable.';
        code = 'BAD_GATEWAY';
        break;
      case 503:
        message = 'Service is currently unavailable.';
        code = 'SERVICE_UNAVAILABLE';
        break;
      case 504:
        message = 'Request timeout. Please try again.';
        code = 'TIMEOUT';
        break;
      default:
        message = statusText || `HTTP Error ${status}`;
        code = `HTTP_${status}`;
    }

    return {
      message,
      code,
      status,
    };
  }

  private showErrorNotification(error: ApiError, context?: string): void {
    const title = this.getErrorTitle(error);
    const description = context ? `${context}: ${error.message}` : error.message;

    // Don't show toast for certain errors that should be handled silently
    const silentErrors = ['UNAUTHORIZED', 'FORBIDDEN'];
    if (silentErrors.includes(error.code || '')) {
      return;
    }

    toast.error(title, {
      description,
      duration: this.getErrorDuration(error),
      action: this.getErrorAction(error),
    });
  }

  private getErrorTitle(error: ApiError): string {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return 'Connection Error';
      case 'VALIDATION_ERROR':
        return 'Validation Error';
      case 'UNAUTHORIZED':
        return 'Authentication Required';
      case 'FORBIDDEN':
        return 'Access Denied';
      case 'NOT_FOUND':
        return 'Not Found';
      case 'RATE_LIMITED':
        return 'Rate Limited';
      case 'SERVER_ERROR':
        return 'Server Error';
      case 'SERVICE_UNAVAILABLE':
        return 'Service Unavailable';
      default:
        return 'Error';
    }
  }

  private getErrorDuration(error: ApiError): number {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return 8000;
      case 'SERVER_ERROR':
        return 7000;
      case 'VALIDATION_ERROR':
        return 6000;
      default:
        return 5000;
    }
  }

  private getErrorAction(error: ApiError) {
    switch (error.code) {
      case 'NETWORK_ERROR':
      case 'SERVER_ERROR':
      case 'SERVICE_UNAVAILABLE':
        return {
          label: 'Retry',
          onClick: () => window.location.reload(),
        };
      case 'UNAUTHORIZED':
        return {
          label: 'Sign In',
          onClick: () => {
            // Redirect to login or trigger auth modal
            window.location.href = '/auth';
          },
        };
      default:
        return undefined;
    }
  }

  private logError(error: ApiError, context?: string): void {
    const logLevel = this.getLogLevel(error);
    const logMessage = `[${context || 'API'}] ${error.code || 'ERROR'}: ${error.message}`;

    switch (logLevel) {
      case 'error':
        console.error(logMessage, error);
        break;
      case 'warn':
        console.warn(logMessage, error);
        break;
      case 'info':
        console.info(logMessage, error);
        break;
      default:
        console.log(logMessage, error);
    }

    // In production, you might want to send critical errors to a logging service
    if (logLevel === 'error' && process.env.NODE_ENV === 'production') {
      this.sendToLoggingService(error, context);
    }
  }

  private getLogLevel(error: ApiError): 'error' | 'warn' | 'info' | 'log' {
    if (error.status && error.status >= 500) {
      return 'error';
    }
    if (error.code === 'NETWORK_ERROR') {
      return 'error';
    }
    if (error.status && error.status >= 400) {
      return 'warn';
    }
    return 'info';
  }

  private sendToLoggingService(error: ApiError, context?: string): void {
    // Implement actual logging service integration here
    // For example: Sentry, LogRocket, DataDog, etc.
    console.log('Would send to logging service:', { error, context });
  }
}

// Create and export singleton instance
export const apiErrorHandler = ApiErrorHandler.getInstance();

// Helper function for API calls with error handling
export async function handleApiCall<T>(
  apiCall: () => Promise<T>,
  context?: string,
  options?: {
    showSuccess?: boolean;
    successMessage?: string;
    showErrors?: boolean;
  }
): Promise<T | null> {
  try {
    const result = await apiCall();

    if (options?.showSuccess && options?.successMessage) {
      apiErrorHandler.handleSuccess(options.successMessage);
    }

    return result;
  } catch (error) {
    if (options?.showErrors !== false) {
      apiErrorHandler.handleError(error, context);
    }
    return null;
  }
}

export default ApiErrorHandler;