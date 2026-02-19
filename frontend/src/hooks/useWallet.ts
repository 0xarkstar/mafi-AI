import { usePrivy, useWallets } from '@privy-io/react-auth';
import { useAccount } from 'wagmi';
import { useMemo } from 'react';

export function useWallet() {
  const { ready, authenticated, login, logout } = usePrivy();
  const { wallets } = useWallets();
  const { address: wagmiAddress } = useAccount();

  const address = useMemo(() => {
    if (wagmiAddress) return wagmiAddress;
    if (!authenticated || !wallets.length) return null;
    const embedded = wallets.find(w => w.walletClientType === 'privy');
    return (embedded ?? wallets[0])?.address ?? null;
  }, [wagmiAddress, authenticated, wallets]);

  return { isReady: ready, isAuthenticated: authenticated, address, login, logout };
}
