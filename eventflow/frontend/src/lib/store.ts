// EventFlow Global State Management with Zustand
// Centralized state for user, events, tasks, and wallet

import { create } from 'zustand';
import type { User, Event, Task, Wallet } from '../types';

interface AppState {
  // User state
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  clearUser: () => void;

  // Events state
  events: Event[];
  selectedEvent: Event | null;
  setEvents: (events: Event[]) => void;
  setSelectedEvent: (event: Event | null) => void;
  addEvent: (event: Event) => void;
  updateEvent: (id: string, updates: Partial<Event>) => void;
  removeEvent: (id: string) => void;

  // Tasks state
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  removeTask: (id: string) => void;

  // Wallet state
  wallet: Wallet | null;
  setWallet: (wallet: Wallet | null) => void;

  // UI state
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  // User state
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  clearUser: () => set({ user: null, isAuthenticated: false, wallet: null }),

  // Events state
  events: [],
  selectedEvent: null,
  setEvents: (events) => set({ events }),
  setSelectedEvent: (event) => set({ selectedEvent: event }),
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
  updateEvent: (id, updates) =>
    set((state) => ({
      events: state.events.map((e) => (e.id === id ? { ...e, ...updates } : e)),
      selectedEvent:
        state.selectedEvent?.id === id
          ? { ...state.selectedEvent, ...updates }
          : state.selectedEvent,
    })),
  removeEvent: (id) =>
    set((state) => ({
      events: state.events.filter((e) => e.id !== id),
      selectedEvent: state.selectedEvent?.id === id ? null : state.selectedEvent,
    })),

  // Tasks state
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
  updateTask: (id, updates) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? { ...t, ...updates } : t)),
    })),
  removeTask: (id) =>
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== id),
    })),

  // Wallet state
  wallet: null,
  setWallet: (wallet) => set({ wallet }),

  // UI state
  sidebarOpen: false,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
