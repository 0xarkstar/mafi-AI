import { StateCreator } from 'zustand';
import { ActionRequest } from '../types';
import type { StoreState } from './index';

export interface UISlice {
  isSpectator: boolean;
  nickname: string;
  currentAction: ActionRequest | null;
}

export const createUISlice: StateCreator<StoreState, [], [], UISlice> = () => ({
  isSpectator: false,
  nickname: '',
  currentAction: null,
});
