import { defineChain } from 'viem';

export const bscTestnet = defineChain({
  id: 97,
  name: 'BSC Testnet',
  nativeCurrency: { name: 'tBNB', symbol: 'tBNB', decimals: 18 },
  rpcUrls: { default: { http: ['https://data-seed-prebsc-1-s1.binance.org:8545'] } },
  blockExplorers: { default: { name: 'BscScan Testnet', url: 'https://testnet.bscscan.com' } },
  testnet: true,
});
