// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title MafiaBettingV2
 * @notice Enhanced pari-mutuel betting contract for Mafia games using USDC on Monad testnet
 * @dev V2 adds: bytes32 gameId, commit-reveal fairness, multi-bet-type oracle settlement,
 *      deadline-based refunds, and pull-payment payouts set by oracle.
 */
contract MafiaBettingV2 is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    // Constants
    uint256 public constant HOUSE_FEE_BPS = 50;       // 5% = 50 basis points
    uint256 public constant FEE_DENOMINATOR = 1000;
    uint256 public constant REFUND_DELAY = 7 days;

    // USDC token contract
    IERC20 public immutable usdc;

    // Bet type enum
    enum BetType { SIDE_WIN, NEXT_ELIMINATION, IS_MAFIA, IS_AI_OR_HUMAN }

    // Structs
    struct Game {
        bool exists;
        bool locked;
        bool settled;
        bytes32 roleCommitment;
        bytes32 roleHash;       // revealed during settlement
        uint256 totalPool;
        uint256 settledAt;
        uint256 createdAt;
    }

    struct BetRecord {
        address bettor;
        BetType betType;
        bytes32 target;         // keccak256 of target string
        uint256 amount;
        bool claimed;
    }

    // State
    mapping(bytes32 => Game) public games;
    mapping(bytes32 => BetRecord[]) private gameBets;
    mapping(bytes32 => mapping(address => uint256)) public deposits;       // for refunds
    mapping(bytes32 => mapping(address => uint256)) public payouts;        // set by oracle
    mapping(bytes32 => mapping(address => bool)) public payoutClaimed;
    mapping(bytes32 => mapping(address => bool)) public refundClaimed;
    uint256 public accumulatedFees;

    // Events
    event GameCreated(bytes32 indexed gameId, bytes32 roleCommitment);
    event BetPlaced(bytes32 indexed gameId, address indexed bettor, BetType betType, bytes32 target, uint256 amount);
    event BettingLocked(bytes32 indexed gameId);
    event GameSettled(bytes32 indexed gameId, bytes32 roleHash, uint256 totalPool);
    event PayoutClaimed(bytes32 indexed gameId, address indexed claimer, uint256 amount);
    event RefundClaimed(bytes32 indexed gameId, address indexed claimer, uint256 amount);
    event FeesWithdrawn(address indexed owner, uint256 amount);

    /**
     * @notice Constructor initializes contract with USDC token address
     * @param _usdc USDC token contract address
     */
    constructor(address _usdc) Ownable(msg.sender) {
        require(_usdc != address(0), "Invalid USDC address");
        usdc = IERC20(_usdc);
    }

    /**
     * @notice Create a new game with a role commitment for commit-reveal fairness
     * @param gameId Unique game identifier (bytes32, UUID maps directly)
     * @param roleCommitment keccak256(abi.encodePacked(roleHash, secret))
     */
    function createGame(bytes32 gameId, bytes32 roleCommitment) external onlyOwner {
        require(!games[gameId].exists, "Game already exists");

        games[gameId] = Game({
            exists: true,
            locked: false,
            settled: false,
            roleCommitment: roleCommitment,
            roleHash: bytes32(0),
            totalPool: 0,
            settledAt: 0,
            createdAt: block.timestamp
        });

        emit GameCreated(gameId, roleCommitment);
    }

    /**
     * @notice Place a bet on a game using USDC
     * @dev User must approve() this contract to spend USDC before calling
     * @param gameId Game identifier
     * @param betType Type of bet (SIDE_WIN, NEXT_ELIMINATION, IS_MAFIA, IS_AI_OR_HUMAN)
     * @param target keccak256 of target string (e.g. player name or "mafia"/"citizens")
     * @param amount Amount of USDC to bet (in USDC's smallest unit, 6 decimals)
     */
    function placeBet(
        bytes32 gameId,
        BetType betType,
        bytes32 target,
        uint256 amount
    ) external nonReentrant {
        require(amount > 0, "Bet amount must be greater than 0");

        Game storage game = games[gameId];
        require(game.exists, "Game does not exist");
        require(!game.locked, "Betting is locked");

        usdc.safeTransferFrom(msg.sender, address(this), amount);

        gameBets[gameId].push(BetRecord({
            bettor: msg.sender,
            betType: betType,
            target: target,
            amount: amount,
            claimed: false
        }));

        deposits[gameId][msg.sender] += amount;
        games[gameId].totalPool += amount;

        emit BetPlaced(gameId, msg.sender, betType, target, amount);
    }

    /**
     * @notice Lock betting for a game (oracle only)
     * @param gameId Game identifier
     */
    function lockBetting(bytes32 gameId) external onlyOwner {
        Game storage game = games[gameId];
        require(game.exists, "Game does not exist");
        require(!game.locked, "Game already locked");

        game.locked = true;
        emit BettingLocked(gameId);
    }

    /**
     * @notice Settle a game with oracle-attested payouts and role reveal
     * @param gameId Game identifier
     * @param roleHash The revealed role hash
     * @param secret The secret used to create the commitment
     * @param winners Array of winner addresses
     * @param amounts Array of payout amounts for each winner
     */
    function settle(
        bytes32 gameId,
        bytes32 roleHash,
        bytes32 secret,
        address[] calldata winners,
        uint256[] calldata amounts
    ) external onlyOwner nonReentrant {
        Game storage game = games[gameId];
        require(game.exists, "Game does not exist");
        require(game.locked, "Game not locked");
        require(!game.settled, "Already settled");
        require(winners.length == amounts.length, "Length mismatch");

        // Verify commit-reveal
        require(
            keccak256(abi.encodePacked(roleHash, secret)) == game.roleCommitment,
            "Invalid role reveal"
        );

        game.roleHash = roleHash;
        game.settled = true;
        game.settledAt = block.timestamp;

        // Calculate house fee
        uint256 houseFee = (game.totalPool * HOUSE_FEE_BPS) / FEE_DENOMINATOR;
        accumulatedFees += houseFee;

        // Set payouts (oracle-computed, not on-chain calculation)
        uint256 totalPayout = 0;
        for (uint256 i = 0; i < winners.length; i++) {
            payouts[gameId][winners[i]] += amounts[i];
            totalPayout += amounts[i];
        }

        // Verify total payouts <= totalPool - houseFee
        require(totalPayout <= game.totalPool - houseFee, "Payouts exceed pool");

        emit GameSettled(gameId, roleHash, game.totalPool);
    }

    /**
     * @notice Claim oracle-assigned payout from a settled game (pull payment pattern)
     * @param gameId Game identifier
     */
    function claimPayout(bytes32 gameId) external nonReentrant {
        Game storage game = games[gameId];
        require(game.exists, "Game does not exist");
        require(game.settled, "Game not settled yet");
        require(!payoutClaimed[gameId][msg.sender], "Already claimed");

        uint256 amount = payouts[gameId][msg.sender];
        require(amount > 0, "No payout available");

        payoutClaimed[gameId][msg.sender] = true;
        usdc.safeTransfer(msg.sender, amount);

        emit PayoutClaimed(gameId, msg.sender, amount);
    }

    /**
     * @notice Claim refund if game was never settled (deadline-based, 7 days from creation)
     * @param gameId Game identifier
     */
    function claimRefund(bytes32 gameId) external nonReentrant {
        Game storage game = games[gameId];
        require(game.exists, "Game does not exist");
        require(!game.settled, "Game already settled");
        require(block.timestamp >= game.createdAt + REFUND_DELAY, "Refund not available yet");

        uint256 amount = deposits[gameId][msg.sender];
        require(amount > 0, "No deposit");
        require(!refundClaimed[gameId][msg.sender], "Already refunded");

        refundClaimed[gameId][msg.sender] = true;
        usdc.safeTransfer(msg.sender, amount);

        emit RefundClaimed(gameId, msg.sender, amount);
    }

    /**
     * @notice Withdraw accumulated house fees (owner only)
     */
    function withdrawFees() external onlyOwner nonReentrant {
        uint256 amount = accumulatedFees;
        require(amount > 0, "No fees to withdraw");

        accumulatedFees = 0;
        usdc.safeTransfer(msg.sender, amount);

        emit FeesWithdrawn(msg.sender, amount);
    }

    /**
     * @notice Get game details
     * @param gameId Game identifier
     * @return Game struct
     */
    function getGame(bytes32 gameId) external view returns (Game memory) {
        return games[gameId];
    }

    /**
     * @notice Get number of bets placed for a game
     * @param gameId Game identifier
     * @return Number of bets
     */
    function getBetCount(bytes32 gameId) external view returns (uint256) {
        return gameBets[gameId].length;
    }

    /**
     * @notice Get a specific bet record
     * @param gameId Game identifier
     * @param index Bet index
     * @return BetRecord struct
     */
    function getBet(bytes32 gameId, uint256 index) external view returns (BetRecord memory) {
        return gameBets[gameId][index];
    }

    /**
     * @notice Get deposit amount for a user in a game
     * @param gameId Game identifier
     * @param user Address of the user
     * @return Deposit amount
     */
    function getDeposit(bytes32 gameId, address user) external view returns (uint256) {
        return deposits[gameId][user];
    }

    /**
     * @notice Get payout amount for a user in a game
     * @param gameId Game identifier
     * @param user Address of the user
     * @return Payout amount
     */
    function getPayout(bytes32 gameId, address user) external view returns (uint256) {
        return payouts[gameId][user];
    }
}
