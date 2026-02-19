import React, { useState, useCallback } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface ConfirmationConfig {
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'default' | 'destructive';
}

interface ConfirmationState {
  isOpen: boolean;
  config: ConfirmationConfig | null;
  resolve: ((confirmed: boolean) => void) | null;
}

export const useConfirmation = () => {
  const [state, setState] = useState<ConfirmationState>({
    isOpen: false,
    config: null,
    resolve: null,
  });

  const confirm = useCallback(
    (config: ConfirmationConfig): Promise<boolean> => {
      return new Promise((resolve) => {
        setState({
          isOpen: true,
          config: {
            confirmText: 'Confirm',
            cancelText: 'Cancel',
            variant: 'default',
            ...config,
          },
          resolve,
        });
      });
    },
    []
  );

  const handleConfirm = useCallback(() => {
    if (state.resolve) {
      state.resolve(true);
    }
    setState({ isOpen: false, config: null, resolve: null });
  }, [state.resolve]);

  const handleCancel = useCallback(() => {
    if (state.resolve) {
      state.resolve(false);
    }
    setState({ isOpen: false, config: null, resolve: null });
  }, [state.resolve]);

  const ConfirmationDialog = useCallback(() => {
    if (!state.config) return null;

    return (
      <AlertDialog open={state.isOpen} onOpenChange={(open) => !open && handleCancel()}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{state.config.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {state.config.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancel}>
              {state.config.cancelText}
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirm}
              className={
                state.config.variant === 'destructive'
                  ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
                  : ''
              }
            >
              {state.config.confirmText}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    );
  }, [state, handleConfirm, handleCancel]);

  return {
    confirm,
    ConfirmationDialog,
  };
};

// Helper functions for common confirmation dialogs
export const useConfirmationHelpers = () => {
  const { confirm, ConfirmationDialog } = useConfirmation();

  const confirmDelete = useCallback(
    (itemName?: string) =>
      confirm({
        title: 'Delete Item',
        description: itemName 
          ? `Are you sure you want to delete "${itemName}"? This action cannot be undone.`
          : 'Are you sure you want to delete this item? This action cannot be undone.',
        confirmText: 'Delete',
        cancelText: 'Cancel',
        variant: 'destructive',
      }),
    [confirm]
  );

  const confirmCancel = useCallback(
    (hasUnsavedChanges: boolean = true) =>
      hasUnsavedChanges
        ? confirm({
            title: 'Discard Changes?',
            description: 'Are you sure you want to cancel? All unsaved changes will be lost.',
            confirmText: 'Discard',
            cancelText: 'Continue Editing',
            variant: 'destructive',
          })
        : Promise.resolve(true),
    [confirm]
  );

  const confirmNavigation = useCallback(
    () =>
      confirm({
        title: 'Leave Page?',
        description: 'Are you sure you want to leave? You have unsaved changes that will be lost.',
        confirmText: 'Leave',
        cancelText: 'Stay',
        variant: 'destructive',
      }),
    [confirm]
  );

  const confirmAction = useCallback(
    (action: string, description?: string) =>
      confirm({
        title: `${action}?`,
        description: description || `Are you sure you want to ${action.toLowerCase()}?`,
        confirmText: action,
        cancelText: 'Cancel',
      }),
    [confirm]
  );

  return {
    confirm,
    confirmDelete,
    confirmCancel,
    confirmNavigation,
    confirmAction,
    ConfirmationDialog,
  };
};