import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  eventId?: string;
}

export class ErrorBoundary extends Component<Props, State> {
  private resetTimeoutId: number | null = null;

  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to external service (would be replaced with actual logging service)
    this.logErrorToService(error, errorInfo);
  }

  private logErrorToService = (error: Error, errorInfo: ErrorInfo) => {
    // In a real application, you would send this to your logging service
    // For example: Sentry, LogRocket, Bugsnag, etc.
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    console.warn('Error logged:', errorReport);
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      eventId: undefined,
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  private handleReportBug = () => {
    const subject = encodeURIComponent(`Bug Report: ${this.state.error?.message || 'React Error'}`);
    const body = encodeURIComponent(`
Error Message: ${this.state.error?.message || 'Unknown error'}

Stack Trace:
${this.state.error?.stack || 'No stack trace available'}

Component Stack:
${this.state.errorInfo?.componentStack || 'No component stack available'}

URL: ${window.location.href}
User Agent: ${navigator.userAgent}
Timestamp: ${new Date().toISOString()}

Please describe what you were doing when this error occurred:
[Your description here]
    `);

    window.open(`mailto:support@ailabsafrica.com?subject=${subject}&body=${body}`);
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 w-20 h-20 bg-destructive/10 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-10 h-10 text-destructive" />
              </div>
              <CardTitle className="text-2xl">Something went wrong</CardTitle>
              <CardDescription className="text-base">
                We're sorry, but something unexpected happened. Our team has been notified.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Error Details (only in development) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="space-y-4">
                  <div className="p-4 bg-muted rounded-lg">
                    <h4 className="font-semibold text-sm mb-2">Error Details:</h4>
                    <p className="text-sm font-mono text-muted-foreground">
                      {this.state.error.message}
                    </p>
                  </div>

                  {this.state.error.stack && (
                    <details className="group">
                      <summary className="cursor-pointer text-sm font-medium hover:text-primary">
                        View Stack Trace
                      </summary>
                      <div className="mt-2 p-4 bg-muted rounded-lg">
                        <pre className="text-xs overflow-auto text-muted-foreground whitespace-pre-wrap">
                          {this.state.error.stack}
                        </pre>
                      </div>
                    </details>
                  )}

                  {this.state.errorInfo?.componentStack && (
                    <details className="group">
                      <summary className="cursor-pointer text-sm font-medium hover:text-primary">
                        View Component Stack
                      </summary>
                      <div className="mt-2 p-4 bg-muted rounded-lg">
                        <pre className="text-xs overflow-auto text-muted-foreground whitespace-pre-wrap">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    </details>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Button onClick={this.handleRetry} className="flex-1">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
                <Button onClick={this.handleReload} variant="outline" className="flex-1">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reload Page
                </Button>
                <Button onClick={this.handleGoHome} variant="outline" className="flex-1">
                  <Home className="w-4 h-4 mr-2" />
                  Go Home
                </Button>
              </div>

              {/* Report Bug */}
              <div className="text-center">
                <Button onClick={this.handleReportBug} variant="ghost" size="sm">
                  <Bug className="w-4 h-4 mr-2" />
                  Report this issue
                </Button>
              </div>

              {/* Help Text */}
              <div className="text-center text-sm text-muted-foreground">
                <p>If this problem persists, please try:</p>
                <ul className="mt-2 space-y-1">
                  <li>• Refreshing the page</li>
                  <li>• Clearing your browser cache</li>
                  <li>• Disabling browser extensions</li>
                  <li>• Contacting support if the issue continues</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component wrapper for easier usage
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryConfig?: {
    fallback?: ReactNode;
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
  }
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryConfig}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
};

export default ErrorBoundary;