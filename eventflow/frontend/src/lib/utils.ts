// EventFlow Utility Functions
// Common utility functions for formatting, calculations, and helpers

import { format, formatDistanceToNow, isAfter, isBefore, differenceInDays } from 'date-fns';
import type { Task, TaskStatus, TaskPriority, Event } from '../types';

// ====================
// Date & Time Utilities
// ====================

export const formatDate = (date: string | Date, formatStr: string = 'MMM dd, yyyy'): string => {
  try {
    return format(new Date(date), formatStr);
  } catch {
    return 'Invalid date';
  }
};

export const formatDateTime = (date: string | Date): string => {
  return formatDate(date, 'MMM dd, yyyy HH:mm');
};

export const formatRelativeTime = (date: string | Date): string => {
  try {
    return formatDistanceToNow(new Date(date), { addSuffix: true });
  } catch {
    return 'Unknown';
  }
};

export const daysUntil = (date: string | Date): number => {
  return differenceInDays(new Date(date), new Date());
};

export const isOverdue = (deadline: string | Date): boolean => {
  return isBefore(new Date(deadline), new Date());
};

// ====================
// Task Utilities
// ====================

export const getTaskStatusColor = (status: TaskStatus): string => {
  const colors = {
    pending: 'text-gray-600 bg-gray-100',
    in_progress: 'text-blue-600 bg-blue-100',
    completed: 'text-green-600 bg-green-100',
    blocked: 'text-red-600 bg-red-100',
  };
  return colors[status] || colors.pending;
};

export const getTaskPriorityColor = (priority: TaskPriority): string => {
  const colors = {
    critical: 'text-red-700 bg-red-100 border-red-300',
    high: 'text-orange-700 bg-orange-100 border-orange-300',
    medium: 'text-yellow-700 bg-yellow-100 border-yellow-300',
    low: 'text-gray-700 bg-gray-100 border-gray-300',
  };
  return colors[priority] || colors.medium;
};

export const getTaskStatusIcon = (status: TaskStatus): string => {
  const icons = {
    pending: 'circle',
    in_progress: 'clock',
    completed: 'check-circle',
    blocked: 'alert-circle',
  };
  return icons[status] || 'circle';
};

export const sortTasksByPriority = (tasks: Task[]): Task[] => {
  const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  return [...tasks].sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
};

export const getOverdueTasks = (tasks: Task[]): Task[] => {
  return tasks.filter(task =>
    task.status !== 'completed' && isOverdue(task.deadline)
  );
};

export const getTaskCompletionRate = (tasks: Task[]): number => {
  if (tasks.length === 0) return 0;
  const completed = tasks.filter(t => t.status === 'completed').length;
  return Math.round((completed / tasks.length) * 100);
};

// ====================
// Currency & Number Formatting
// ====================

export const formatCurrency = (amount: number, currency: string = 'GHS'): string => {
  return new Intl.NumberFormat('en-GH', {
    style: 'currency',
    currency: currency,
  }).format(amount);
};

export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US').format(num);
};

export const formatCompactNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(num);
};

// ====================
// Event Utilities
// ====================

export const getEventStatusColor = (status: string): string => {
  const colors = {
    planning: 'text-blue-600 bg-blue-100',
    active: 'text-green-600 bg-green-100',
    completed: 'text-gray-600 bg-gray-100',
    cancelled: 'text-red-600 bg-red-100',
  };
  return colors[status as keyof typeof colors] || colors.planning;
};

export const getEventProgress = (event: Event, tasks: Task[]): number => {
  return getTaskCompletionRate(tasks);
};

export const isEventUpcoming = (event: Event): boolean => {
  return daysUntil(event.date) >= 0 && daysUntil(event.date) <= 30;
};

// ====================
// String Utilities
// ====================

export const truncate = (text: string, maxLength: number = 50): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const capitalize = (text: string): string => {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

export const slugify = (text: string): string => {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

// ====================
// Array Utilities
// ====================

export const groupBy = <T>(array: T[], key: keyof T): Record<string, T[]> => {
  return array.reduce((result, item) => {
    const group = String(item[key]);
    if (!result[group]) {
      result[group] = [];
    }
    result[group].push(item);
    return result;
  }, {} as Record<string, T[]>);
};

export const unique = <T>(array: T[]): T[] => {
  return Array.from(new Set(array));
};

// ====================
// Phone Number Utilities
// ====================

export const formatPhone = (phone: string): string => {
  // Format Ghana phone numbers: +233 XX XXX XXXX
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.startsWith('233') && cleaned.length === 12) {
    return `+233 ${cleaned.slice(3, 5)} ${cleaned.slice(5, 8)} ${cleaned.slice(8)}`;
  }
  return phone;
};

export const validatePhone = (phone: string): boolean => {
  // Basic Ghana phone validation
  const cleaned = phone.replace(/\D/g, '');
  return cleaned.length >= 10 && cleaned.length <= 13;
};

// ====================
// Local Storage Utilities
// ====================

export const storage = {
  get: <T>(key: string, defaultValue: T | null = null): T | null => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch {
      return defaultValue;
    }
  },

  set: <T>(key: string, value: T): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  },

  remove: (key: string): void => {
    localStorage.removeItem(key);
  },

  clear: (): void => {
    localStorage.clear();
  },
};

// ====================
// Validation Utilities
// ====================

export const validateEmail = (email: string): boolean => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

export const validateRequired = (value: any): boolean => {
  if (typeof value === 'string') {
    return value.trim().length > 0;
  }
  return value !== null && value !== undefined;
};

// ====================
// CSS Class Utilities
// ====================

export const cn = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};
