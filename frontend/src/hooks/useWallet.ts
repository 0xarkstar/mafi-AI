import { useEffect, useRef } from 'react'
import { ethers } from 'ethers'
import { useWalletStore } from '../stores/walletStore'
import { connectWallet, switchToMonad, getUSDCBalance, MONAD_TESTNET } from '../lib/blockchain'

export function useWallet() {
  const connected = useWalletStore((s) => s.connected)
  const address = useWalletStore((s) => s.address)
  const balance = useWalletStore((s) => s.balance)
  const isConnecting = useWalletStore((s) => s.isConnecting)
  const error = useWalletStore((s) => s.error)
  const setConnected = useWalletStore((s) => s.setConnected)
  const setDisconnected = useWalletStore((s) => s.setDisconnected)
  const setBalance = useWalletStore((s) => s.setBalance)
  const setConnecting = useWalletStore((s) => s.setConnecting)
  const setError = useWalletStore((s) => s.setError)

  const providerRef = useRef<ethers.BrowserProvider | null>(null)
  const signerRef = useRef<ethers.Signer | null>(null)

  useEffect(() => {
    // Auto-detect if already connected
    if (window.ethereum && !connected) {
      checkConnection()
    }

    // Listen for account changes
    if (window.ethereum) {
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          setDisconnected()
        } else {
          checkConnection()
        }
      }

      const handleChainChanged = () => {
        checkConnection()
      }

      window.ethereum.on('accountsChanged', handleAccountsChanged)
      window.ethereum.on('chainChanged', handleChainChanged)

      return () => {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged)
        window.ethereum.removeListener('chainChanged', handleChainChanged)
      }
    }
  }, [])

  const checkConnection = async () => {
    try {
      if (!window.ethereum) return

      const provider = new ethers.BrowserProvider(window.ethereum)
      const accounts = await provider.send('eth_accounts', [])

      if (accounts.length > 0) {
        const network = await provider.getNetwork()
        const chainId = `0x${network.chainId.toString(16)}`
        const addr = accounts[0]

        providerRef.current = provider
        signerRef.current = await provider.getSigner()

        setConnected(addr, chainId)

        // Fetch balance
        const usdcBalance = await getUSDCBalance(provider, addr)
        setBalance(usdcBalance)
      }
    } catch (err: any) {
      console.error('Check connection error:', err)
    }
  }

  const connect = async () => {
    setConnecting(true)
    setError(null)

    try {
      const { provider, signer, address: addr } = await connectWallet()

      const network = await provider.getNetwork()
      const chainId = `0x${network.chainId.toString(16)}`

      // Switch to Monad if needed
      if (chainId !== MONAD_TESTNET.chainId) {
        await switchToMonad(provider)
        const newNetwork = await provider.getNetwork()
        const newChainId = `0x${newNetwork.chainId.toString(16)}`
        setConnected(addr, newChainId)
      } else {
        setConnected(addr, chainId)
      }

      providerRef.current = provider
      signerRef.current = signer

      // Fetch balance
      const usdcBalance = await getUSDCBalance(provider, addr)
      setBalance(usdcBalance)
    } catch (err: any) {
      setError(err.message || 'Failed to connect wallet')
    } finally {
      setConnecting(false)
    }
  }

  const disconnect = () => {
    providerRef.current = null
    signerRef.current = null
    setDisconnected()
  }

  return {
    connect,
    disconnect,
    address,
    balance,
    connected,
    isConnecting,
    error,
    provider: providerRef.current,
    signer: signerRef.current,
  }
}
