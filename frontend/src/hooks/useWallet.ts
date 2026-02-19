import { useContext } from 'react';
import { WalletContext } from '../providers/Web3Provider';
import type { WalletContextValue } from '../providers/Web3Provider';

export function useWallet(): WalletContextValue {
  return useContext(WalletContext);
}
