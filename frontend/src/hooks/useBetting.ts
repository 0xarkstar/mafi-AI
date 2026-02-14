import { useState } from 'react'
import { ethers } from 'ethers'
import type { BetType } from '../lib/types'
import { useWalletStore } from '../stores/walletStore'
import { useBettingStore } from '../stores/bettingStore'
import { useWallet } from './useWallet'
import { createContracts } from '../lib/blockchain'

export function useBetting() {
  const [isPlacing, setIsPlacing] = useState(false)
  const setTxStatus = useWalletStore((s) => s.setTxStatus)
  const addBet = useBettingStore((s) => s.addBet)
  const { signer, address } = useWallet()

  const placeBet = async (betType: BetType, target: string, amount: number, round: number) => {
    if (!address) {
      setTxStatus({ type: 'error', message: 'Wallet not connected' })
      return
    }

    setIsPlacing(true)
    setTxStatus({ type: 'pending', message: 'Placing bet...' })

    try {
      // Check if blockchain mode is enabled
      const blockchainConfigRes = await fetch('/api/blockchain-config')
      const blockchainConfig = await blockchainConfigRes.json()

      if (blockchainConfig.enabled && signer) {
        // Blockchain mode: approve USDC + call contract
        const { bettingContract, usdcContract } = createContracts(signer, blockchainConfig.contract_address)

        const amountWei = ethers.parseUnits(amount.toString(), 6) // USDC has 6 decimals

        // Check allowance
        const allowance = await usdcContract.allowance!(address, blockchainConfig.contract_address)

        if (allowance < amountWei) {
          setTxStatus({ type: 'pending', message: 'Approving USDC...' })
          const approveTx = await usdcContract.approve!(blockchainConfig.contract_address, amountWei)
          await approveTx.wait()
        }

        // Place bet on-chain
        setTxStatus({ type: 'pending', message: 'Placing bet on-chain...' })
        const gameId = 1 // TODO: get from game state
        const betMafia = target === 'mafia'
        const tx = await bettingContract.placeBet!(gameId, betMafia, amountWei)
        const receipt = await tx.wait()

        setTxStatus({ type: 'success', message: 'Bet placed successfully!' })

        // Add to local store
        addBet({
          id: receipt.hash,
          betType,
          target,
          amount,
          status: 'pending',
          weight: 1.0,
        })
      } else {
        // X402 mode: POST to API
        const response = await fetch('/api/bets', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            bet_type: betType,
            target,
            amount_usdc: amount,
            round,
          }),
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Failed to place bet')
        }

        const data = await response.json()

        setTxStatus({ type: 'success', message: 'Bet placed successfully!' })

        addBet({
          id: data.bet_id,
          betType,
          target,
          amount,
          status: 'pending',
          weight: data.weight || 1.0,
        })
      }

      // Auto-dismiss success message after 3s
      setTimeout(() => setTxStatus(null), 3000)
    } catch (err: any) {
      console.error('Place bet error:', err)
      setTxStatus({ type: 'error', message: err.message || 'Failed to place bet' })

      // Auto-dismiss error after 5s
      setTimeout(() => setTxStatus(null), 5000)
    } finally {
      setIsPlacing(false)
    }
  }

  return { placeBet, isPlacing }
}
