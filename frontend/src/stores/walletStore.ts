import { create } from 'zustand'

export interface TxStatus {
  type: 'pending' | 'success' | 'error'
  message: string
}

interface WalletStore {
  connected: boolean
  address: string | null
  balance: string
  chainId: string | null
  isConnecting: boolean
  error: string | null
  txStatus: TxStatus | null

  setConnected: (address: string, chainId: string) => void
  setDisconnected: () => void
  setBalance: (balance: string) => void
  setConnecting: (connecting: boolean) => void
  setError: (error: string | null) => void
  setTxStatus: (status: TxStatus | null) => void
}

export const useWalletStore = create<WalletStore>((set) => ({
  connected: false,
  address: null,
  balance: '0',
  chainId: null,
  isConnecting: false,
  error: null,
  txStatus: null,

  setConnected: (address, chainId) => set({ connected: true, address, chainId, error: null }),
  setDisconnected: () => set({ connected: false, address: null, balance: '0', chainId: null }),
  setBalance: (balance) => set({ balance }),
  setConnecting: (connecting) => set({ isConnecting: connecting }),
  setError: (error) => set({ error }),
  setTxStatus: (status) => set({ txStatus: status }),
}))
