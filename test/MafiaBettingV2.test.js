const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MafiaBettingV2", function () {
  let mafiaBettingV2;
  let usdc;
  let owner;
  let player1;
  let player2;
  let player3;

  // bytes32 gameId (UUID-style, hashed)
  const GAME_ID = ethers.keccak256(ethers.toUtf8Bytes("game-001"));
  const GAME_ID_2 = ethers.keccak256(ethers.toUtf8Bytes("game-002"));
  const BET_AMOUNT = ethers.parseUnits("10", 6); // 10 USDC (6 decimals)

  // Commit-reveal helpers
  const ROLE_HASH = ethers.keccak256(ethers.toUtf8Bytes("mafia:Alice,Bob"));
  const SECRET = ethers.keccak256(ethers.toUtf8Bytes("super-secret-salt"));
  const ROLE_COMMITMENT = ethers.keccak256(
    ethers.solidityPacked(["bytes32", "bytes32"], [ROLE_HASH, SECRET])
  );

  // BetType enum values (matching contract order)
  const BetType = {
    SIDE_WIN: 0,
    NEXT_ELIMINATION: 1,
    IS_MAFIA: 2,
    IS_AI_OR_HUMAN: 3,
  };

  // Target helpers
  const TARGET_MAFIA = ethers.keccak256(ethers.toUtf8Bytes("mafia"));
  const TARGET_CITIZENS = ethers.keccak256(ethers.toUtf8Bytes("citizens"));
  const TARGET_ALICE = ethers.keccak256(ethers.toUtf8Bytes("Alice"));

  beforeEach(async function () {
    [owner, player1, player2, player3] = await ethers.getSigners();

    // Deploy mock USDC token
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    usdc = await MockERC20.deploy("USD Coin", "USDC", 6);
    await usdc.waitForDeployment();

    // Deploy MafiaBettingV2 contract with USDC address
    const MafiaBettingV2 = await ethers.getContractFactory("MafiaBettingV2");
    mafiaBettingV2 = await MafiaBettingV2.deploy(await usdc.getAddress());
    await mafiaBettingV2.waitForDeployment();

    // Mint USDC to test accounts
    await usdc.mint(player1.address, ethers.parseUnits("1000", 6));
    await usdc.mint(player2.address, ethers.parseUnits("1000", 6));
    await usdc.mint(player3.address, ethers.parseUnits("1000", 6));
  });

  // ─── Deployment ───────────────────────────────────────────────────────────

  describe("Deployment", function () {
    it("Should set the correct owner", async function () {
      expect(await mafiaBettingV2.owner()).to.equal(owner.address);
    });

    it("Should have correct fee constants", async function () {
      expect(await mafiaBettingV2.HOUSE_FEE_BPS()).to.equal(50);
      expect(await mafiaBettingV2.FEE_DENOMINATOR()).to.equal(1000);
    });

    it("Should set the correct USDC address", async function () {
      expect(await mafiaBettingV2.usdc()).to.equal(await usdc.getAddress());
    });

    it("Should reject zero address for USDC", async function () {
      const MafiaBettingV2 = await ethers.getContractFactory("MafiaBettingV2");
      await expect(
        MafiaBettingV2.deploy(ethers.ZeroAddress)
      ).to.be.revertedWith("Invalid USDC address");
    });
  });

  // ─── Game Creation ────────────────────────────────────────────────────────

  describe("Game Creation", function () {
    it("Should allow owner to create a game with role commitment", async function () {
      await expect(mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT))
        .to.emit(mafiaBettingV2, "GameCreated")
        .withArgs(GAME_ID, ROLE_COMMITMENT);

      const game = await mafiaBettingV2.getGame(GAME_ID);
      expect(game.exists).to.be.true;
      expect(game.locked).to.be.false;
      expect(game.settled).to.be.false;
      expect(game.roleCommitment).to.equal(ROLE_COMMITMENT);
      expect(game.totalPool).to.equal(0);
    });

    it("Should not allow creating duplicate games", async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);
      await expect(
        mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT)
      ).to.be.revertedWith("Game already exists");
    });

    it("Should not allow non-owner to create a game", async function () {
      await expect(
        mafiaBettingV2.connect(player1).createGame(GAME_ID, ROLE_COMMITMENT)
      ).to.be.revertedWithCustomError(mafiaBettingV2, "OwnableUnauthorizedAccount");
    });

    it("Should record createdAt timestamp on game creation", async function () {
      const tx = await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt.blockNumber);

      const game = await mafiaBettingV2.getGame(GAME_ID);
      expect(game.createdAt).to.equal(block.timestamp);
    });
  });

  // ─── Placing Bets ─────────────────────────────────────────────────────────

  describe("Placing Bets", function () {
    beforeEach(async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);
    });

    it("Should allow SIDE_WIN bet with USDC", async function () {
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);

      await expect(
        mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT)
      )
        .to.emit(mafiaBettingV2, "BetPlaced")
        .withArgs(GAME_ID, player1.address, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);

      const game = await mafiaBettingV2.getGame(GAME_ID);
      expect(game.totalPool).to.equal(BET_AMOUNT);
    });

    it("Should allow NEXT_ELIMINATION bet", async function () {
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);

      await mafiaBettingV2.connect(player1).placeBet(
        GAME_ID, BetType.NEXT_ELIMINATION, TARGET_ALICE, BET_AMOUNT
      );

      const bet = await mafiaBettingV2.getBet(GAME_ID, 0);
      expect(bet.betType).to.equal(BetType.NEXT_ELIMINATION);
      expect(bet.target).to.equal(TARGET_ALICE);
    });

    it("Should allow IS_MAFIA bet", async function () {
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);

      await mafiaBettingV2.connect(player1).placeBet(
        GAME_ID, BetType.IS_MAFIA, TARGET_ALICE, BET_AMOUNT
      );

      const bet = await mafiaBettingV2.getBet(GAME_ID, 0);
      expect(bet.betType).to.equal(BetType.IS_MAFIA);
    });

    it("Should allow IS_AI_OR_HUMAN bet", async function () {
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);

      await mafiaBettingV2.connect(player1).placeBet(
        GAME_ID, BetType.IS_AI_OR_HUMAN, TARGET_ALICE, BET_AMOUNT
      );

      const bet = await mafiaBettingV2.getBet(GAME_ID, 0);
      expect(bet.betType).to.equal(BetType.IS_AI_OR_HUMAN);
    });

    it("Should transfer USDC from bettor to contract", async function () {
      const initialBalance = await usdc.balanceOf(player1.address);
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);
      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);

      const finalBalance = await usdc.balanceOf(player1.address);
      expect(finalBalance).to.equal(initialBalance - BET_AMOUNT);

      const contractBalance = await usdc.balanceOf(await mafiaBettingV2.getAddress());
      expect(contractBalance).to.equal(BET_AMOUNT);
    });

    it("Should track deposits correctly", async function () {
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT * 2n);
      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);
      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.IS_MAFIA, TARGET_ALICE, BET_AMOUNT);

      expect(await mafiaBettingV2.getDeposit(GAME_ID, player1.address)).to.equal(BET_AMOUNT * 2n);
    });

    it("Should not allow betting without USDC approval", async function () {
      await expect(
        mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT)
      ).to.be.reverted;
    });

    it("Should not allow betting with insufficient USDC balance", async function () {
      const hugeAmount = ethers.parseUnits("10000", 6);
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), hugeAmount);

      await expect(
        mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, hugeAmount)
      ).to.be.reverted;
    });

    it("Should not allow zero-value bets", async function () {
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);

      await expect(
        mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, 0)
      ).to.be.revertedWith("Bet amount must be greater than 0");
    });

    it("Should not allow betting on non-existent game", async function () {
      const fakeGameId = ethers.keccak256(ethers.toUtf8Bytes("nonexistent"));
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);

      await expect(
        mafiaBettingV2.connect(player1).placeBet(fakeGameId, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT)
      ).to.be.revertedWith("Game does not exist");
    });

    it("Should not allow betting on locked game", async function () {
      await mafiaBettingV2.lockBetting(GAME_ID);
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);

      await expect(
        mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT)
      ).to.be.revertedWith("Betting is locked");
    });

    it("Should allow multiple bets from different players", async function () {
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);
      await usdc.connect(player2).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);

      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);
      await mafiaBettingV2.connect(player2).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_CITIZENS, BET_AMOUNT);

      expect(await mafiaBettingV2.getBetCount(GAME_ID)).to.equal(2);

      const game = await mafiaBettingV2.getGame(GAME_ID);
      expect(game.totalPool).to.equal(BET_AMOUNT * 2n);
    });
  });

  // ─── Locking Betting ──────────────────────────────────────────────────────

  describe("Locking Betting", function () {
    beforeEach(async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);
    });

    it("Should allow owner to lock betting", async function () {
      await expect(mafiaBettingV2.lockBetting(GAME_ID))
        .to.emit(mafiaBettingV2, "BettingLocked")
        .withArgs(GAME_ID);

      const game = await mafiaBettingV2.getGame(GAME_ID);
      expect(game.locked).to.be.true;
    });

    it("Should not allow non-owner to lock betting", async function () {
      await expect(
        mafiaBettingV2.connect(player1).lockBetting(GAME_ID)
      ).to.be.revertedWithCustomError(mafiaBettingV2, "OwnableUnauthorizedAccount");
    });

    it("Should not allow locking a game twice", async function () {
      await mafiaBettingV2.lockBetting(GAME_ID);
      await expect(mafiaBettingV2.lockBetting(GAME_ID)).to.be.revertedWith(
        "Game already locked"
      );
    });

    it("Should not allow locking non-existent game", async function () {
      const fakeGameId = ethers.keccak256(ethers.toUtf8Bytes("ghost"));
      await expect(mafiaBettingV2.lockBetting(fakeGameId)).to.be.revertedWith(
        "Game does not exist"
      );
    });
  });

  // ─── Settlement ───────────────────────────────────────────────────────────

  describe("Settlement", function () {
    beforeEach(async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);
      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);
      await mafiaBettingV2.lockBetting(GAME_ID);
    });

    it("Should settle with valid commit-reveal and emit event", async function () {
      const houseFee = (BET_AMOUNT * 50n) / 1000n;
      const maxPayout = BET_AMOUNT - houseFee;

      await expect(
        mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [player1.address], [maxPayout])
      )
        .to.emit(mafiaBettingV2, "GameSettled")
        .withArgs(GAME_ID, ROLE_HASH, BET_AMOUNT);

      const game = await mafiaBettingV2.getGame(GAME_ID);
      expect(game.settled).to.be.true;
      expect(game.roleHash).to.equal(ROLE_HASH);
    });

    it("Should reject invalid secret", async function () {
      const wrongSecret = ethers.keccak256(ethers.toUtf8Bytes("wrong-secret"));

      await expect(
        mafiaBettingV2.settle(GAME_ID, ROLE_HASH, wrongSecret, [], [])
      ).to.be.revertedWith("Invalid role reveal");
    });

    it("Should reject mismatched winners/amounts arrays", async function () {
      await expect(
        mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [player1.address], [])
      ).to.be.revertedWith("Length mismatch");
    });

    it("Should reject payout exceeding pool minus fee", async function () {
      const overPayout = BET_AMOUNT; // would exceed pool - fee

      await expect(
        mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [player1.address], [overPayout])
      ).to.be.revertedWith("Payouts exceed pool");
    });

    it("Should not allow non-owner to settle", async function () {
      await expect(
        mafiaBettingV2.connect(player1).settle(GAME_ID, ROLE_HASH, SECRET, [], [])
      ).to.be.revertedWithCustomError(mafiaBettingV2, "OwnableUnauthorizedAccount");
    });

    it("Should not allow settling a game that is already settled", async function () {
      await mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [], []);
      await expect(
        mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [], [])
      ).to.be.revertedWith("Already settled");
    });

    it("Should not allow settling an unlocked game", async function () {
      await mafiaBettingV2.createGame(GAME_ID_2, ROLE_COMMITMENT);
      await expect(
        mafiaBettingV2.settle(GAME_ID_2, ROLE_HASH, SECRET, [], [])
      ).to.be.revertedWith("Game not locked");
    });

    it("Should not allow settling non-existent game", async function () {
      const fakeGameId = ethers.keccak256(ethers.toUtf8Bytes("ghost"));
      await expect(
        mafiaBettingV2.settle(fakeGameId, ROLE_HASH, SECRET, [], [])
      ).to.be.revertedWith("Game does not exist");
    });

    it("Should collect correct house fee on settlement", async function () {
      const expectedFee = (BET_AMOUNT * 50n) / 1000n;
      await mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [], []);
      expect(await mafiaBettingV2.accumulatedFees()).to.equal(expectedFee);
    });

    it("Should store roleHash on settlement", async function () {
      await mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [], []);
      const game = await mafiaBettingV2.getGame(GAME_ID);
      expect(game.roleHash).to.equal(ROLE_HASH);
    });
  });

  // ─── Claiming Payouts ─────────────────────────────────────────────────────

  describe("Claiming Payouts", function () {
    const houseFee = (BET_AMOUNT * 50n) / 1000n;
    const playerPayout = BET_AMOUNT - houseFee;

    beforeEach(async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);
      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);
      await mafiaBettingV2.lockBetting(GAME_ID);
      await mafiaBettingV2.settle(
        GAME_ID, ROLE_HASH, SECRET,
        [player1.address], [playerPayout]
      );
    });

    it("Should allow winner to claim USDC payout", async function () {
      const initialBalance = await usdc.balanceOf(player1.address);

      await expect(mafiaBettingV2.connect(player1).claimPayout(GAME_ID))
        .to.emit(mafiaBettingV2, "PayoutClaimed")
        .withArgs(GAME_ID, player1.address, playerPayout);

      const finalBalance = await usdc.balanceOf(player1.address);
      expect(finalBalance).to.equal(initialBalance + playerPayout);
    });

    it("Should transfer correct USDC amount to winner", async function () {
      const initialBalance = await usdc.balanceOf(player1.address);
      await mafiaBettingV2.connect(player1).claimPayout(GAME_ID);

      expect(await usdc.balanceOf(player1.address)).to.equal(initialBalance + playerPayout);
    });

    it("Should not allow claiming payout twice", async function () {
      await mafiaBettingV2.connect(player1).claimPayout(GAME_ID);
      await expect(
        mafiaBettingV2.connect(player1).claimPayout(GAME_ID)
      ).to.be.revertedWith("Already claimed");
    });

    it("Should not allow non-winner to claim (zero payout)", async function () {
      await expect(
        mafiaBettingV2.connect(player2).claimPayout(GAME_ID)
      ).to.be.revertedWith("No payout available");
    });

    it("Should not allow claiming from unsettled game", async function () {
      await mafiaBettingV2.createGame(GAME_ID_2, ROLE_COMMITMENT);
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);
      await mafiaBettingV2.connect(player1).placeBet(GAME_ID_2, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);
      await mafiaBettingV2.lockBetting(GAME_ID_2);

      await expect(
        mafiaBettingV2.connect(player1).claimPayout(GAME_ID_2)
      ).to.be.revertedWith("Game not settled yet");
    });
  });

  // ─── Refunds ──────────────────────────────────────────────────────────────

  describe("Refunds", function () {
    beforeEach(async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);
      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);
    });

    it("Should allow refund after 7 days if not settled", async function () {
      await ethers.provider.send("evm_increaseTime", [7 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine");

      const initialBalance = await usdc.balanceOf(player1.address);

      await expect(mafiaBettingV2.connect(player1).claimRefund(GAME_ID))
        .to.emit(mafiaBettingV2, "RefundClaimed")
        .withArgs(GAME_ID, player1.address, BET_AMOUNT);

      expect(await usdc.balanceOf(player1.address)).to.equal(initialBalance + BET_AMOUNT);
    });

    it("Should reject refund before 7 days", async function () {
      await ethers.provider.send("evm_increaseTime", [6 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine");

      await expect(
        mafiaBettingV2.connect(player1).claimRefund(GAME_ID)
      ).to.be.revertedWith("Refund not available yet");
    });

    it("Should reject refund after game is settled", async function () {
      await mafiaBettingV2.lockBetting(GAME_ID);
      const houseFee = (BET_AMOUNT * 50n) / 1000n;
      const payout = BET_AMOUNT - houseFee;
      await mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [player1.address], [payout]);

      await ethers.provider.send("evm_increaseTime", [7 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine");

      await expect(
        mafiaBettingV2.connect(player1).claimRefund(GAME_ID)
      ).to.be.revertedWith("Game already settled");
    });

    it("Should not allow double refund", async function () {
      await ethers.provider.send("evm_increaseTime", [7 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine");

      await mafiaBettingV2.connect(player1).claimRefund(GAME_ID);
      await expect(
        mafiaBettingV2.connect(player1).claimRefund(GAME_ID)
      ).to.be.revertedWith("Already refunded");
    });

    it("Should not allow refund with no deposit", async function () {
      await ethers.provider.send("evm_increaseTime", [7 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine");

      await expect(
        mafiaBettingV2.connect(player2).claimRefund(GAME_ID)
      ).to.be.revertedWith("No deposit");
    });

    it("Should not allow refund for non-existent game", async function () {
      const fakeGameId = ethers.keccak256(ethers.toUtf8Bytes("ghost"));
      await ethers.provider.send("evm_increaseTime", [7 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine");

      await expect(
        mafiaBettingV2.connect(player1).claimRefund(fakeGameId)
      ).to.be.revertedWith("Game does not exist");
    });
  });

  // ─── Fee Withdrawal ───────────────────────────────────────────────────────

  describe("Fee Withdrawal", function () {
    beforeEach(async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);
      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);
      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);
      await mafiaBettingV2.lockBetting(GAME_ID);
      await mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [], []);
    });

    it("Should allow owner to withdraw USDC fees", async function () {
      const expectedFee = (BET_AMOUNT * 50n) / 1000n;
      const initialBalance = await usdc.balanceOf(owner.address);

      await expect(mafiaBettingV2.withdrawFees())
        .to.emit(mafiaBettingV2, "FeesWithdrawn")
        .withArgs(owner.address, expectedFee);

      expect(await usdc.balanceOf(owner.address)).to.equal(initialBalance + expectedFee);
      expect(await mafiaBettingV2.accumulatedFees()).to.equal(0);
    });

    it("Should not allow non-owner to withdraw fees", async function () {
      await expect(
        mafiaBettingV2.connect(player1).withdrawFees()
      ).to.be.revertedWithCustomError(mafiaBettingV2, "OwnableUnauthorizedAccount");
    });

    it("Should not allow withdrawing when no fees accumulated", async function () {
      await mafiaBettingV2.withdrawFees();
      await expect(mafiaBettingV2.withdrawFees()).to.be.revertedWith("No fees to withdraw");
    });
  });

  // ─── Complete Lifecycle ───────────────────────────────────────────────────

  describe("Complete Lifecycle", function () {
    it("Should handle full flow: create → bet → lock → settle → claim", async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);

      const bet1 = ethers.parseUnits("30", 6);
      const bet2 = ethers.parseUnits("20", 6);

      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), bet1);
      await usdc.connect(player2).approve(await mafiaBettingV2.getAddress(), bet2);

      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, bet1);
      await mafiaBettingV2.connect(player2).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_CITIZENS, bet2);

      const game = await mafiaBettingV2.getGame(GAME_ID);
      expect(game.totalPool).to.equal(bet1 + bet2);

      await mafiaBettingV2.lockBetting(GAME_ID);

      const totalPool = bet1 + bet2;
      const houseFee = (totalPool * 50n) / 1000n;
      const netPool = totalPool - houseFee;

      // Oracle assigns all net pool to player1 (won)
      await mafiaBettingV2.settle(GAME_ID, ROLE_HASH, SECRET, [player1.address], [netPool]);

      const initialBalance = await usdc.balanceOf(player1.address);
      await mafiaBettingV2.connect(player1).claimPayout(GAME_ID);

      expect(await usdc.balanceOf(player1.address)).to.equal(initialBalance + netPool);
      expect(await mafiaBettingV2.accumulatedFees()).to.equal(houseFee);
    });

    it("Should handle multi-bettor scenario with oracle payouts", async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);

      const bet1 = ethers.parseUnits("20", 6);
      const bet2 = ethers.parseUnits("10", 6);
      const bet3 = ethers.parseUnits("30", 6);

      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), bet1);
      await usdc.connect(player2).approve(await mafiaBettingV2.getAddress(), bet2);
      await usdc.connect(player3).approve(await mafiaBettingV2.getAddress(), bet3);

      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, bet1);
      await mafiaBettingV2.connect(player2).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, bet2);
      await mafiaBettingV2.connect(player3).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_CITIZENS, bet3);

      await mafiaBettingV2.lockBetting(GAME_ID);

      const totalPool = bet1 + bet2 + bet3;
      const houseFee = (totalPool * 50n) / 1000n;
      const netPool = totalPool - houseFee;

      // Oracle splits net pool proportionally (2/3 and 1/3) between winners
      const payout1 = (netPool * 2n) / 3n;
      const payout2 = netPool - payout1;

      await mafiaBettingV2.settle(
        GAME_ID, ROLE_HASH, SECRET,
        [player1.address, player2.address],
        [payout1, payout2]
      );

      await mafiaBettingV2.connect(player1).claimPayout(GAME_ID);
      await mafiaBettingV2.connect(player2).claimPayout(GAME_ID);

      // Player3 lost - no payout
      await expect(
        mafiaBettingV2.connect(player3).claimPayout(GAME_ID)
      ).to.be.revertedWith("No payout available");

      expect(await mafiaBettingV2.getPayout(GAME_ID, player1.address)).to.equal(payout1);
      expect(await mafiaBettingV2.getPayout(GAME_ID, player2.address)).to.equal(payout2);
      expect(await mafiaBettingV2.accumulatedFees()).to.equal(houseFee);
    });

    it("Should handle refund scenario when game never settles", async function () {
      await mafiaBettingV2.createGame(GAME_ID, ROLE_COMMITMENT);

      await usdc.connect(player1).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);
      await usdc.connect(player2).approve(await mafiaBettingV2.getAddress(), BET_AMOUNT);

      await mafiaBettingV2.connect(player1).placeBet(GAME_ID, BetType.SIDE_WIN, TARGET_MAFIA, BET_AMOUNT);
      await mafiaBettingV2.connect(player2).placeBet(GAME_ID, BetType.IS_MAFIA, TARGET_ALICE, BET_AMOUNT);

      // Time passes, game never locked or settled
      await ethers.provider.send("evm_increaseTime", [7 * 24 * 60 * 60]);
      await ethers.provider.send("evm_mine");

      const p1Before = await usdc.balanceOf(player1.address);
      const p2Before = await usdc.balanceOf(player2.address);

      await mafiaBettingV2.connect(player1).claimRefund(GAME_ID);
      await mafiaBettingV2.connect(player2).claimRefund(GAME_ID);

      expect(await usdc.balanceOf(player1.address)).to.equal(p1Before + BET_AMOUNT);
      expect(await usdc.balanceOf(player2.address)).to.equal(p2Before + BET_AMOUNT);
    });
  });
});
