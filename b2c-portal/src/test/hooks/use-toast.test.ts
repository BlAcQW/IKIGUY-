import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToast, toast, reducer } from '@/hooks/use-toast';

describe('useToast Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('reducer', () => {
    const initialState = { toasts: [] };

    it('should add toast on ADD_TOAST action', () => {
      const toastData = {
        id: '1',
        title: 'Test Toast',
        description: 'Test Description',
        open: true,
      };

      const action = {
        type: 'ADD_TOAST' as const,
        toast: toastData,
      };

      const newState = reducer(initialState, action);

      expect(newState.toasts).toHaveLength(1);
      expect(newState.toasts[0]).toEqual(toastData);
    });

    it('should limit toasts to TOAST_LIMIT', () => {
      const existingToasts = [
        { id: '1', title: 'Toast 1', open: true },
        { id: '2', title: 'Toast 2', open: true },
        { id: '3', title: 'Toast 3', open: true },
        { id: '4', title: 'Toast 4', open: true },
        { id: '5', title: 'Toast 5', open: true },
      ];

      const state = { toasts: existingToasts };
      const newToast = { id: '6', title: 'Toast 6', open: true };

      const action = {
        type: 'ADD_TOAST' as const,
        toast: newToast,
      };

      const newState = reducer(state, action);

      expect(newState.toasts).toHaveLength(1); // TOAST_LIMIT is 1
      expect(newState.toasts[0]).toEqual(newToast);
    });

    it('should update toast on UPDATE_TOAST action', () => {
      const existingToast = { id: '1', title: 'Original Title', open: true };
      const state = { toasts: [existingToast] };

      const updateAction = {
        type: 'UPDATE_TOAST' as const,
        toast: { id: '1', title: 'Updated Title' },
      };

      const newState = reducer(state, updateAction);

      expect(newState.toasts).toHaveLength(1);
      expect(newState.toasts[0].title).toBe('Updated Title');
      expect(newState.toasts[0].open).toBe(true); // Should preserve other properties
    });

    it('should not update non-existent toast', () => {
      const existingToast = { id: '1', title: 'Original Title', open: true };
      const state = { toasts: [existingToast] };

      const updateAction = {
        type: 'UPDATE_TOAST' as const,
        toast: { id: '2', title: 'Updated Title' },
      };

      const newState = reducer(state, updateAction);

      expect(newState.toasts).toHaveLength(1);
      expect(newState.toasts[0]).toEqual(existingToast); // Should remain unchanged
    });

    it('should dismiss specific toast on DISMISS_TOAST action', () => {
      const existingToasts = [
        { id: '1', title: 'Toast 1', open: true },
        { id: '2', title: 'Toast 2', open: true },
      ];
      const state = { toasts: existingToasts };

      const dismissAction = {
        type: 'DISMISS_TOAST' as const,
        toastId: '1',
      };

      const newState = reducer(state, dismissAction);

      expect(newState.toasts).toHaveLength(2);
      expect(newState.toasts[0].open).toBe(false);
      expect(newState.toasts[1].open).toBe(true); // Should remain open
    });

    it('should dismiss all toasts when no toastId provided', () => {
      const existingToasts = [
        { id: '1', title: 'Toast 1', open: true },
        { id: '2', title: 'Toast 2', open: true },
      ];
      const state = { toasts: existingToasts };

      const dismissAction = {
        type: 'DISMISS_TOAST' as const,
        toastId: undefined,
      };

      const newState = reducer(state, dismissAction);

      expect(newState.toasts).toHaveLength(2);
      expect(newState.toasts[0].open).toBe(false);
      expect(newState.toasts[1].open).toBe(false);
    });

    it('should remove specific toast on REMOVE_TOAST action', () => {
      const existingToasts = [
        { id: '1', title: 'Toast 1', open: true },
        { id: '2', title: 'Toast 2', open: true },
      ];
      const state = { toasts: existingToasts };

      const removeAction = {
        type: 'REMOVE_TOAST' as const,
        toastId: '1',
      };

      const newState = reducer(state, removeAction);

      expect(newState.toasts).toHaveLength(1);
      expect(newState.toasts[0].id).toBe('2');
    });

    it('should remove all toasts when no toastId provided', () => {
      const existingToasts = [
        { id: '1', title: 'Toast 1', open: true },
        { id: '2', title: 'Toast 2', open: true },
      ];
      const state = { toasts: existingToasts };

      const removeAction = {
        type: 'REMOVE_TOAST' as const,
        toastId: undefined,
      };

      const newState = reducer(state, removeAction);

      expect(newState.toasts).toHaveLength(0);
    });

    it('should handle unknown action type', () => {
      const action = {
        type: 'UNKNOWN_ACTION' as any,
        payload: {},
      };

      const newState = reducer(initialState, action);

      expect(newState).toBeUndefined();
    });
  });

  describe('toast function', () => {
    it('should create a toast with generated ID', () => {
      const toastProps = {
        title: 'Test Toast',
        description: 'Test Description',
      };

      const result = toast(toastProps);

      expect(result.id).toBeDefined();
      expect(typeof result.id).toBe('string');
      expect(result.dismiss).toBeDefined();
      expect(result.update).toBeDefined();
    });

    it('should provide update function', () => {
      const toastProps = {
        title: 'Test Toast',
        description: 'Test Description',
      };

      const result = toast(toastProps);

      const updateProps = { title: 'Updated Title' };
      expect(() => result.update(updateProps)).not.toThrow();
    });

    it('should provide dismiss function', () => {
      const toastProps = {
        title: 'Test Toast',
        description: 'Test Description',
      };

      const result = toast(toastProps);

      expect(() => result.dismiss()).not.toThrow();
    });
  });

  describe('useToast hook', () => {
    it('should return current state', () => {
      const { result } = renderHook(() => useToast());

      expect(result.current.toasts).toBeDefined();
      expect(Array.isArray(result.current.toasts)).toBe(true);
      expect(result.current.toast).toBeDefined();
      expect(result.current.dismiss).toBeDefined();
    });

    it('should provide dismiss function that accepts toastId', () => {
      const { result } = renderHook(() => useToast());

      expect(() => result.current.dismiss('test-id')).not.toThrow();
    });

    it('should provide dismiss function that dismisses all when no ID provided', () => {
      const { result } = renderHook(() => useToast());

      expect(() => result.current.dismiss()).not.toThrow();
    });

    it('should handle toast creation', () => {
      const { result } = renderHook(() => useToast());

      expect(() => result.current.toast({ title: 'Test Toast' })).not.toThrow();
    });

    it('should handle toast with all properties', () => {
      const { result } = renderHook(() => useToast());

      const toastProps = {
        title: 'Complete Toast',
        description: 'Complete Description',
        action: {
          altText: 'Action',
          action: vi.fn(),
        },
        variant: 'destructive' as const,
        duration: 5000,
      };

      expect(() => result.current.toast(toastProps)).not.toThrow();
    });
  });
});
