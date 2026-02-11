// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MafiaBetting
 * @notice Pari-mutuel betting contract for Mafia games on Monad testnet
 * @dev Uses pull payment pattern with 5% house edge
 */
contract MafiaBetting is ReentrancyGuard, Ownable {
    // Constants
    uint256 public constant HOUSE_FEE_BPS = 50; // 5% = 50 basis points
    uint256 public constant FEE_DENOMINATOR = 1000;

    // Structs
    struct Game {
        bool exists;
        bool locked;      // betting locked after game starts
        bool settled;
        bool mafiaWon;
        uint256 mafiaPool;
        uint256 citizenPool;
        uint256 totalPool;
    }

    struct PlayerBet {
        uint256 mafiaAmount;
        uint256 citizenAmount;
        bool claimed;
    }

    // State
    mapping(uint256 => Game) public games;
    mapping(uint256 => mapping(address => PlayerBet)) public bets;
    uint256 public accumulatedFees;

    // Events
    event GameCreated(uint256 indexed gameId);
    event BetPlaced(uint256 indexed gameId, address indexed bettor, bool betMafia, uint256 amount);
    event BettingLocked(uint256 indexed gameId);
    event GameSettled(uint256 indexed gameId, bool mafiaWon, uint256 totalPool);
    event PayoutClaimed(uint256 indexed gameId, address indexed bettor, uint256 amount);
    event FeesWithdrawn(address indexed owner, uint256 amount);

    constructor() Ownable(msg.sender) {}

    /**
     * @notice Create a new game (oracle only)
     * @param gameId Unique game identifier
     */
    function createGame(uint256 gameId) external onlyOwner {
        require(!games[gameId].exists, "Game already exists");

        games[gameId] = Game({
            exists: true,
            locked: false,
            settled: false,
            mafiaWon: false,
            mafiaPool: 0,
            citizenPool: 0,
            totalPool: 0
        });

        emit GameCreated(gameId);
    }

    /**
     * @notice Lock betting for a game (oracle only)
     * @param gameId Game identifier
     */
    function lockBetting(uint256 gameId) external onlyOwner {
        Game storage game = games[gameId];
        require(game.exists, "Game does not exist");
        require(!game.locked, "Game already locked");

        game.locked = true;
        emit BettingLocked(gameId);
    }

    /**
     * @notice Settle a game with final outcome (oracle only)
     * @param gameId Game identifier
     * @param mafiaWon True if mafia won, false if citizens won
     */
    function settle(uint256 gameId, bool mafiaWon) external onlyOwner nonReentrant {
        Game storage game = games[gameId];
        require(game.exists, "Game does not exist");
        require(game.locked, "Game not locked");
        require(!game.settled, "Game already settled");

        game.settled = true;
        game.mafiaWon = mafiaWon;

        // Calculate and collect house fees
        uint256 houseFee = (game.totalPool * HOUSE_FEE_BPS) / FEE_DENOMINATOR;
        accumulatedFees += houseFee;

        emit GameSettled(gameId, mafiaWon, game.totalPool);
    }

    /**
     * @notice Place a bet on a game
     * @param gameId Game identifier
     * @param betMafia True to bet on mafia, false to bet on citizens
     */
    function placeBet(uint256 gameId, bool betMafia) external payable nonReentrant {
        require(msg.value > 0, "Bet amount must be greater than 0");

        Game storage game = games[gameId];
        require(game.exists, "Game does not exist");
        require(!game.locked, "Betting is locked");

        PlayerBet storage playerBet = bets[gameId][msg.sender];

        if (betMafia) {
            playerBet.mafiaAmount += msg.value;
            game.mafiaPool += msg.value;
        } else {
            playerBet.citizenAmount += msg.value;
            game.citizenPool += msg.value;
        }

        game.totalPool += msg.value;

        emit BetPlaced(gameId, msg.sender, betMafia, msg.value);
    }

    /**
     * @notice Claim winnings from a settled game (pull payment pattern)
     * @param gameId Game identifier
     */
    function claimWinnings(uint256 gameId) external nonReentrant {
        Game storage game = games[gameId];
        require(game.exists, "Game does not exist");
        require(game.settled, "Game not settled yet");

        PlayerBet storage playerBet = bets[gameId][msg.sender];
        require(!playerBet.claimed, "Already claimed");

        uint256 payout = calculatePayout(gameId, msg.sender);
        require(payout > 0, "No winnings to claim");

        playerBet.claimed = true;

        // Transfer winnings (Checks-Effects-Interactions pattern)
        (bool success, ) = msg.sender.call{value: payout}("");
        require(success, "Transfer failed");

        emit PayoutClaimed(gameId, msg.sender, payout);
    }

    /**
     * @notice Calculate payout for a bettor
     * @param gameId Game identifier
     * @param bettor Address of the bettor
     * @return Payout amount in wei
     */
    function calculatePayout(uint256 gameId, address bettor) public view returns (uint256) {
        Game storage game = games[gameId];
        if (!game.settled) return 0;

        PlayerBet storage playerBet = bets[gameId][bettor];
        if (playerBet.claimed) return 0;

        uint256 bettorAmount;
        uint256 winnerPool;

        if (game.mafiaWon) {
            bettorAmount = playerBet.mafiaAmount;
            winnerPool = game.mafiaPool;
        } else {
            bettorAmount = playerBet.citizenAmount;
            winnerPool = game.citizenPool;
        }

        if (bettorAmount == 0 || winnerPool == 0) return 0;

        // Calculate payout: (bettorAmount * netPool) / winnerPool
        // netPool = totalPool * (1000 - 50) / 1000 = totalPool * 950 / 1000
        uint256 netPool = (game.totalPool * (FEE_DENOMINATOR - HOUSE_FEE_BPS)) / FEE_DENOMINATOR;
        uint256 payout = (bettorAmount * netPool) / winnerPool;

        return payout;
    }

    /**
     * @notice Withdraw accumulated house fees (owner only)
     */
    function withdrawFees() external onlyOwner nonReentrant {
        uint256 amount = accumulatedFees;
        require(amount > 0, "No fees to withdraw");

        accumulatedFees = 0;

        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        emit FeesWithdrawn(msg.sender, amount);
    }

    /**
     * @notice Get game details
     * @param gameId Game identifier
     * @return Game struct
     */
    function getGame(uint256 gameId) external view returns (Game memory) {
        return games[gameId];
    }

    /**
     * @notice Get player bet details
     * @param gameId Game identifier
     * @param bettor Address of the bettor
     * @return PlayerBet struct
     */
    function getPlayerBet(uint256 gameId, address bettor) external view returns (PlayerBet memory) {
        return bets[gameId][bettor];
    }
}
