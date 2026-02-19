/**
 * Centralized logging utility
 * Provides environment-aware logging that removes console statements in production
 */

type LogLevel = 'log' | 'warn' | 'error' | 'info' | 'debug';

class Logger {
  private isDevelopment: boolean;

  constructor() {
    this.isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development';
  }

  private shouldLog(level: LogLevel): boolean {
    // In production, only log errors
    if (!this.isDevelopment) {
      return level === 'error';
    }
    return true;
  }

  log(...args: unknown[]): void {
    if (this.shouldLog('log')) {
      console.log('[LOG]', ...args);
    }
  }

  info(...args: unknown[]): void {
    if (this.shouldLog('info')) {
      console.info('[INFO]', ...args);
    }
  }

  warn(...args: unknown[]): void {
    if (this.shouldLog('warn')) {
      console.warn('[WARN]', ...args);
    }
  }

  error(...args: unknown[]): void {
    // Always log errors, even in production
    console.error('[ERROR]', ...args);
    
    // TODO: Send to error tracking service (Sentry, etc.)
    // if (this.isDevelopment === false) {
    //   errorTrackingService.captureException(args);
    // }
  }

  debug(...args: unknown[]): void {
    if (this.shouldLog('debug')) {
      console.debug('[DEBUG]', ...args);
    }
  }
}

export const logger = new Logger();

