// MetaMask + ethers.js integration for on-chain betting

// Monad Testnet configuration
const MONAD_TESTNET = {
    chainId: '0x279F',
    chainName: 'Monad Testnet',
    rpcUrls: ['https://testnet-rpc.monad.xyz'],
    nativeCurrency: { name: 'MON', symbol: 'MON', decimals: 18 },
    blockExplorerUrls: ['https://testnet.monadscan.com']
};

// Contract ABI (human-readable format)
const MAFIA_BETTING_ABI = [
    "function placeBet(uint256 gameId, bool betMafia) external payable",
    "function claimWinnings(uint256 gameId) external",
    "function calculatePayout(uint256 gameId, address bettor) public view returns (uint256)",
    "function getGame(uint256 gameId) external view returns (tuple(bool,bool,bool,bool,uint256,uint256,uint256))",
    "function getPlayerBet(uint256 gameId, address bettor) external view returns (tuple(uint256,uint256,bool))",
    "event BetPlaced(uint256 indexed gameId, address indexed bettor, bool betMafia, uint256 amount)",
    "event GameSettled(uint256 indexed gameId, bool mafiaWon, uint256 totalPool)",
    "event PayoutClaimed(uint256 indexed gameId, address indexed bettor, uint256 amount)"
];

// Global state
let provider = null;
let signer = null;
let contract = null;
let userAddress = null;
let contractAddress = null;
let currentGameId = null;
let isBlockchainMode = false;

/**
 * Initialize blockchain mode if contract address is provided
 * @param {string} contractAddr - Contract address from server
 * @param {number} gameId - Current game ID
 */
async function initBlockchain(contractAddr, gameId) {
    if (!contractAddr) {
        console.log('No contract address provided — blockchain mode disabled');
        return;
    }

    contractAddress = contractAddr;
    currentGameId = gameId;
    isBlockchainMode = true;

    // Show wallet section
    const walletSection = document.getElementById('wallet-section');
    if (walletSection) {
        walletSection.style.display = 'block';
    }

    console.log(`Blockchain mode enabled: Contract ${contractAddr}, Game ${gameId}`);

    // Auto-connect if MetaMask is already authorized
    if (typeof window.ethereum !== 'undefined') {
        try {
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            if (accounts && accounts.length > 0) {
                await connectWallet();
            }
        } catch (error) {
            console.warn('Could not auto-connect to MetaMask:', error);
        }
    }
}

/**
 * Connect MetaMask wallet
 */
async function connectWallet() {
    try {
        // Check if MetaMask is installed
        if (typeof window.ethereum === 'undefined') {
            updateWalletStatus('disconnected', 'MetaMask not installed');
            alert('MetaMask is not installed. Please install MetaMask to use on-chain betting.');
            return;
        }

        // Check if ethers is loaded
        if (typeof ethers === 'undefined') {
            updateWalletStatus('disconnected', 'ethers.js not loaded');
            console.error('ethers.js library not loaded');
            return;
        }

        updateWalletStatus('connecting', 'Connecting...');

        // Request account access
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        userAddress = accounts[0];

        // Create provider and signer
        provider = new ethers.BrowserProvider(window.ethereum);
        signer = await provider.getSigner();

        // Check current chain
        const network = await provider.getNetwork();
        const currentChainId = '0x' + network.chainId.toString(16);

        // Switch to Monad Testnet if needed
        if (currentChainId !== MONAD_TESTNET.chainId) {
            try {
                await switchToMonadTestnet();
            } catch (error) {
                console.error('Failed to switch network:', error);
                updateWalletStatus('disconnected', 'Wrong network');
                return;
            }
        }

        // Initialize contract
        if (contractAddress) {
            contract = new ethers.Contract(contractAddress, MAFIA_BETTING_ABI, signer);
            console.log('Contract initialized:', contractAddress);

            // Start listening to events
            listenToContractEvents();
        }

        // Get balance
        const balance = await provider.getBalance(userAddress);
        const balanceMON = ethers.formatEther(balance);

        updateWalletStatus('connected', `${userAddress.slice(0, 6)}...${userAddress.slice(-4)}`);
        updateWalletBalance(balanceMON);

        console.log('Wallet connected:', userAddress);
        addSystemMessage('🔗 Wallet connected: ' + userAddress.slice(0, 10) + '...', 'game-over');

        // Check if user has pending winnings
        await checkPendingWinnings();

    } catch (error) {
        console.error('Failed to connect wallet:', error);

        if (error.code === 4001) {
            updateWalletStatus('disconnected', 'Connection rejected');
            addSystemMessage('❌ Wallet connection rejected', 'elimination');
        } else {
            updateWalletStatus('disconnected', 'Connection failed');
            addSystemMessage('❌ Failed to connect wallet', 'elimination');
        }
    }
}

/**
 * Switch to Monad Testnet
 */
async function switchToMonadTestnet() {
    try {
        await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: MONAD_TESTNET.chainId }],
        });
    } catch (switchError) {
        // This error code indicates that the chain has not been added to MetaMask
        if (switchError.code === 4902) {
            try {
                await window.ethereum.request({
                    method: 'wallet_addEthereumChain',
                    params: [MONAD_TESTNET],
                });
            } catch (addError) {
                console.error('Failed to add Monad Testnet:', addError);
                throw addError;
            }
        } else {
            throw switchError;
        }
    }
}

/**
 * Place bet on-chain via MetaMask
 * @param {boolean} betMafia - True if betting on mafia, false for citizens
 * @param {number} amountMON - Amount in MON to bet
 */
async function placeBetOnChain(betMafia, amountMON) {
    if (!contract || !signer) {
        addSystemMessage('❌ Wallet not connected', 'elimination');
        return;
    }

    if (!currentGameId) {
        addSystemMessage('❌ No active game', 'elimination');
        return;
    }

    try {
        updateTxStatus('pending', '⏳ Sending transaction...');

        const amountWei = ethers.parseEther(amountMON.toString());

        console.log(`Placing bet: ${amountMON} MON on ${betMafia ? 'Mafia' : 'Citizens'}, Game ${currentGameId}`);

        // Send transaction
        const tx = await contract.placeBet(currentGameId, betMafia, {
            value: amountWei
        });

        updateTxStatus('pending', `⏳ Confirming... (tx: ${tx.hash.slice(0, 10)}...)`);
        console.log('Transaction sent:', tx.hash);

        // Wait for confirmation
        const receipt = await tx.wait();

        updateTxStatus('success', '✅ Bet placed on-chain!');
        setTimeout(() => hideTxStatus(), 3000);

        const targetName = betMafia ? '😈 Mafia' : '🎉 Citizens';
        addSystemMessage(`✅ On-chain bet: ${amountMON} MON on ${targetName}`, 'game-over');

        // Update balance
        const newBalance = await provider.getBalance(userAddress);
        const balanceMON = ethers.formatEther(newBalance);
        updateWalletBalance(balanceMON);

        console.log('Transaction confirmed:', receipt.transactionHash);

    } catch (error) {
        console.error('Failed to place bet:', error);

        let errorMsg = 'Transaction failed';

        if (error.code === 'ACTION_REJECTED') {
            errorMsg = 'Transaction rejected';
        } else if (error.message && error.message.includes('Betting is locked')) {
            errorMsg = 'Betting is locked';
        } else if (error.message) {
            // Extract revert reason if available
            const match = error.message.match(/reason="([^"]+)"/);
            if (match) {
                errorMsg = match[1];
            }
        }

        updateTxStatus('error', `❌ ${errorMsg}`);
        setTimeout(() => hideTxStatus(), 5000);

        addSystemMessage(`❌ On-chain bet failed: ${errorMsg}`, 'elimination');
    }
}

/**
 * Claim winnings after game settles
 */
async function claimWinnings() {
    if (!contract || !signer) {
        addSystemMessage('❌ Wallet not connected', 'elimination');
        return;
    }

    if (!currentGameId) {
        addSystemMessage('❌ No active game', 'elimination');
        return;
    }

    try {
        updateTxStatus('pending', '⏳ Claiming winnings...');

        // Check payout amount
        const payoutWei = await contract.calculatePayout(currentGameId, userAddress);
        const payoutMON = ethers.formatEther(payoutWei);

        if (parseFloat(payoutMON) === 0) {
            updateTxStatus('error', '❌ No winnings to claim');
            setTimeout(() => hideTxStatus(), 3000);
            addSystemMessage('❌ No winnings to claim', 'elimination');
            return;
        }

        console.log(`Claiming ${payoutMON} MON from game ${currentGameId}`);

        // Send claim transaction
        const tx = await contract.claimWinnings(currentGameId);

        updateTxStatus('pending', `⏳ Confirming claim... (tx: ${tx.hash.slice(0, 10)}...)`);
        console.log('Claim transaction sent:', tx.hash);

        // Wait for confirmation
        const receipt = await tx.wait();

        updateTxStatus('success', `🎉 Claimed ${payoutMON} MON!`);
        setTimeout(() => hideTxStatus(), 5000);

        addSystemMessage(`🎉 Claimed winnings: ${payoutMON} MON!`, 'game-over');

        // Update balance
        const newBalance = await provider.getBalance(userAddress);
        const balanceMON = ethers.formatEther(newBalance);
        updateWalletBalance(balanceMON);

        // Hide claim button
        document.getElementById('blockchain-claim').style.display = 'none';

        console.log('Claim confirmed:', receipt.transactionHash);

    } catch (error) {
        console.error('Failed to claim winnings:', error);

        let errorMsg = 'Claim failed';

        if (error.code === 'ACTION_REJECTED') {
            errorMsg = 'Claim rejected';
        } else if (error.message) {
            const match = error.message.match(/reason="([^"]+)"/);
            if (match) {
                errorMsg = match[1];
            }
        }

        updateTxStatus('error', `❌ ${errorMsg}`);
        setTimeout(() => hideTxStatus(), 5000);

        addSystemMessage(`❌ Claim failed: ${errorMsg}`, 'elimination');
    }
}

/**
 * Listen to contract events
 */
function listenToContractEvents() {
    if (!contract) return;

    console.log('Listening to contract events...');

    // Listen for BetPlaced events
    contract.on('BetPlaced', (gameId, bettor, betMafia, amount, event) => {
        const amountMON = ethers.formatEther(amount);
        const side = betMafia ? 'Mafia' : 'Citizens';

        console.log(`BetPlaced event: Game ${gameId}, ${bettor} bet ${amountMON} MON on ${side}`);

        if (bettor.toLowerCase() === userAddress.toLowerCase()) {
            addSystemMessage(`📡 Your bet confirmed on-chain: ${amountMON} MON on ${side}`, 'game-over');
        }
    });

    // Listen for GameSettled events
    contract.on('GameSettled', (gameId, mafiaWon, totalPool, event) => {
        const poolMON = ethers.formatEther(totalPool);
        const winner = mafiaWon ? '😈 Mafia' : '🎉 Citizens';

        console.log(`GameSettled event: Game ${gameId}, ${winner} won, Pool: ${poolMON} MON`);

        addSystemMessage(`📡 Game settled on-chain: ${winner} wins! Pool: ${poolMON} MON`, 'game-over');

        // Show claim button
        showClaimButton();
    });

    // Listen for PayoutClaimed events
    contract.on('PayoutClaimed', (gameId, bettor, amount, event) => {
        const amountMON = ethers.formatEther(amount);

        console.log(`PayoutClaimed event: Game ${gameId}, ${bettor} claimed ${amountMON} MON`);

        if (bettor.toLowerCase() === userAddress.toLowerCase()) {
            addSystemMessage(`📡 Payout confirmed: ${amountMON} MON claimed!`, 'game-over');
        }
    });
}

/**
 * Check if user has pending winnings
 */
async function checkPendingWinnings() {
    if (!contract || !userAddress || !currentGameId) return;

    try {
        const payoutWei = await contract.calculatePayout(currentGameId, userAddress);
        const payoutMON = ethers.formatEther(payoutWei);

        if (parseFloat(payoutMON) > 0) {
            console.log(`Pending winnings: ${payoutMON} MON`);
            showClaimButton();
            addSystemMessage(`💰 You have ${payoutMON} MON to claim!`, 'game-over');
        }
    } catch (error) {
        console.warn('Could not check pending winnings:', error);
    }
}

/**
 * Show claim button
 */
function showClaimButton() {
    const claimSection = document.getElementById('blockchain-claim');
    if (claimSection) {
        claimSection.style.display = 'block';
    }
}

/**
 * Update wallet status UI
 * @param {string} status - 'connected', 'disconnected', or 'connecting'
 * @param {string} text - Status text to display
 */
function updateWalletStatus(status, text) {
    const statusEl = document.getElementById('wallet-status');
    if (!statusEl) return;

    statusEl.textContent = text;
    statusEl.className = 'wallet-status ' + status;
}

/**
 * Update wallet balance display
 * @param {string} balanceMON - Balance in MON
 */
function updateWalletBalance(balanceMON) {
    const balanceEl = document.getElementById('wallet-balance');
    if (!balanceEl) return;

    const formatted = parseFloat(balanceMON).toFixed(4);
    balanceEl.textContent = `💎 ${formatted} MON`;
}

/**
 * Update transaction status UI
 * @param {string} status - 'pending', 'success', or 'error'
 * @param {string} message - Status message
 */
function updateTxStatus(status, message) {
    const txStatusEl = document.getElementById('tx-status');
    if (!txStatusEl) return;

    txStatusEl.textContent = message;
    txStatusEl.className = 'tx-status ' + status;
    txStatusEl.style.display = 'inline-block';
}

/**
 * Hide transaction status
 */
function hideTxStatus() {
    const txStatusEl = document.getElementById('tx-status');
    if (txStatusEl) {
        txStatusEl.style.display = 'none';
    }
}

// Listen for account changes
if (typeof window.ethereum !== 'undefined') {
    window.ethereum.on('accountsChanged', (accounts) => {
        if (accounts.length === 0) {
            console.log('Wallet disconnected');
            updateWalletStatus('disconnected', 'Not connected');
            provider = null;
            signer = null;
            contract = null;
            userAddress = null;
        } else {
            console.log('Account changed, reconnecting...');
            connectWallet();
        }
    });

    window.ethereum.on('chainChanged', (chainId) => {
        console.log('Chain changed:', chainId);
        if (chainId !== MONAD_TESTNET.chainId) {
            updateWalletStatus('disconnected', 'Wrong network');
            addSystemMessage('⚠️ Please switch to Monad Testnet', 'elimination');
        } else {
            // Reconnect
            connectWallet();
        }
    });
}
