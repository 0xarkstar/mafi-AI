import { StateCreator } from 'zustand';
import type { StoreState } from './index';

export interface SpecChatMessage {
  id: string;
  name: string;
  text: string;
  time: number;
  isAi: boolean;
}

export interface ChatSlice {
  specChatMessages: SpecChatMessage[];
  specChatName: string | null;

  addSpecChatMessage: (msg: Omit<SpecChatMessage, 'id' | 'time'>) => void;
  setSpecChatName: (name: string) => void;
  clearSpecChat: () => void;
}

export const createChatSlice: StateCreator<StoreState, [], [], ChatSlice> = (set) => ({
  specChatMessages: [],
  specChatName: null,

  addSpecChatMessage: (msg) => {
    const full: SpecChatMessage = {
      ...msg,
      id: Math.random().toString(36).substr(2, 9),
      time: Date.now(),
    };
    set((state) => ({
      specChatMessages: [...state.specChatMessages, full].slice(-50),
    }));
  },

  setSpecChatName: (name) => {
    set({ specChatName: name });
  },

  clearSpecChat: () => {
    set({ specChatMessages: [], specChatName: null });
  },
});
