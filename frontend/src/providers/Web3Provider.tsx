import { createContext, useMemo } from 'react';
import { PrivyProvider, usePrivy, useWallets } from '@privy-io/react-auth';
import { WagmiProvider, createConfig } from '@privy-io/wagmi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RainbowKitProvider, darkTheme } from '@rainbow-me/rainbowkit';
import { http, useAccount } from 'wagmi';
import { bscTestnet } from './chains';
import '@rainbow-me/rainbowkit/styles.css';

const PRIVY_APP_ID = import.meta.env.VITE_PRIVY_APP_ID as string | undefined;
const queryClient = new QueryClient();

const wagmiConfig = createConfig({
  chains: [bscTestnet],
  transports: { [bscTestnet.id]: http() },
});

export interface WalletContextValue {
  isReady: boolean;
  isAuthenticated: boolean;
  address: string | null;
  login: (() => void) | null;
  logout: (() => Promise<void>) | null;
}

const DISABLED_STATE: WalletContextValue = {
  isReady: true,
  isAuthenticated: false,
  address: null,
  login: null,
  logout: null,
};

export const WalletContext = createContext<WalletContextValue>(DISABLED_STATE);

/** Calls Privy/wagmi hooks (safe — always rendered inside PrivyProvider). */
function PrivyWalletBridge({ children }: { children: React.ReactNode }) {
  const { ready, authenticated, login, logout } = usePrivy();
  const { wallets } = useWallets();
  const { address: wagmiAddress } = useAccount();

  const address = useMemo(() => {
    if (wagmiAddress) return wagmiAddress;
    if (!authenticated || !wallets.length) return null;
    const embedded = wallets.find((w: { walletClientType: string }) => w.walletClientType === 'privy');
    return (embedded ?? wallets[0])?.address ?? null;
  }, [wagmiAddress, authenticated, wallets]);

  const value = useMemo<WalletContextValue>(() => ({
    isReady: ready,
    isAuthenticated: authenticated,
    address,
    login,
    logout,
  }), [ready, authenticated, address, login, logout]);

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
}

export const Web3Provider = ({ children }: { children: React.ReactNode }) => {
  if (!PRIVY_APP_ID) {
    return <WalletContext.Provider value={DISABLED_STATE}>{children}</WalletContext.Provider>;
  }

  return (
    <PrivyProvider
      appId={PRIVY_APP_ID}
      config={{
        appearance: { theme: 'dark', accentColor: '#D4A853' },
        loginMethods: ['email', 'wallet'],
        embeddedWallets: { ethereum: { createOnLogin: 'users-without-wallets' } },
        defaultChain: bscTestnet,
        supportedChains: [bscTestnet],
      }}
    >
      <QueryClientProvider client={queryClient}>
        <WagmiProvider config={wagmiConfig}>
          <RainbowKitProvider theme={darkTheme({ accentColor: '#D4A853' })}>
            <PrivyWalletBridge>
              {children}
            </PrivyWalletBridge>
          </RainbowKitProvider>
        </WagmiProvider>
      </QueryClientProvider>
    </PrivyProvider>
  );
};
