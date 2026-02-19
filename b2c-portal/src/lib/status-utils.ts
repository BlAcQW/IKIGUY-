/**
 * Status Utility Functions
 *
 * Centralized utilities for provider status styling and display.
 * Prevents code duplication across lab components.
 */

export type ProviderStatus = 'online' | 'offline' | 'building' | 'degraded';

export interface StatusStyle {
  badge: string;
  dot: string;
  label: string;
  description: string;
}

/**
 * Get consistent styling for provider status.
 *
 * @param status - Provider status
 * @returns StatusStyle object with badge classes, dot emoji, label, and description
 *
 * @example
 * const style = getStatusStyle('online');
 * <span className={style.badge}>{style.dot} {style.label}</span>
 */
export const getStatusStyle = (status: ProviderStatus): StatusStyle => {
  const styles: Record<ProviderStatus, StatusStyle> = {
    online: {
      badge: 'bg-green-100 text-green-800',
      dot: '🟢',
      label: 'Online',
      description: 'Provider is operational',
    },
    building: {
      badge: 'bg-yellow-100 text-yellow-800',
      dot: '🟡',
      label: 'Building',
      description: 'Provider is starting up',
    },
    offline: {
      badge: 'bg-red-100 text-red-800',
      dot: '🔴',
      label: 'Offline',
      description: 'Provider is unavailable',
    },
    degraded: {
      badge: 'bg-orange-100 text-orange-800',
      dot: '🟠',
      label: 'Degraded',
      description: 'Provider responding slowly',
    },
  };

  return styles[status] || styles.offline;
};

/**
 * Check if a provider is available for use.
 *
 * @param status - Provider status
 * @returns True if provider is online or degraded, false otherwise
 */
export const isProviderAvailable = (status: ProviderStatus): boolean => {
  return status === 'online' || status === 'degraded';
};

/**
 * Get user-friendly status message with additional context.
 *
 * @param status - Provider status
 * @param responseTime - Optional response time in ms
 * @returns Formatted status message
 */
export const getStatusMessage = (
  status: ProviderStatus,
  responseTime?: number
): string => {
  const style = getStatusStyle(status);
  const timeInfo = responseTime ? ` (${responseTime.toFixed(0)}ms)` : '';

  return `${style.label}${timeInfo}: ${style.description}`;
};
