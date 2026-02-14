const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MafiaBetting", function () {
  let mafiaBetting;
  let usdc;
  let owner;
  let player1;
  let player2;
  let player3;

  const GAME_ID = 1;
  const BET_AMOUNT = ethers.parseUnits("10", 6); // 10 USDC (6 decimals)

  beforeEach(async function () {
    [owner, player1, player2, player3] = await ethers.getSigners();

    // Deploy mock USDC token
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    usdc = await MockERC20.deploy("USD Coin", "USDC", 6);
    await usdc.waitForDeployment();

    // Deploy MafiaBetting contract with USDC address
    const MafiaBetting = await ethers.getContractFactory("MafiaBetting");
    mafiaBetting = await MafiaBetting.deploy(await usdc.getAddress());
    await mafiaBetting.waitForDeployment();

    // Mint USDC to test accounts
    await usdc.mint(player1.address, ethers.parseUnits("1000", 6));
    await usdc.mint(player2.address, ethers.parseUnits("1000", 6));
    await usdc.mint(player3.address, ethers.parseUnits("1000", 6));
  });

  describe("Deployment", function () {
    it("Should set the correct owner", async function () {
      expect(await mafiaBetting.owner()).to.equal(owner.address);
    });

    it("Should have correct fee constants", async function () {
      expect(await mafiaBetting.HOUSE_FEE_BPS()).to.equal(50);
      expect(await mafiaBetting.FEE_DENOMINATOR()).to.equal(1000);
    });

    it("Should set the correct USDC address", async function () {
      expect(await mafiaBetting.usdc()).to.equal(await usdc.getAddress());
    });

    it("Should reject zero address for USDC", async function () {
      const MafiaBetting = await ethers.getContractFactory("MafiaBetting");
      await expect(
        MafiaBetting.deploy(ethers.ZeroAddress)
      ).to.be.revertedWith("Invalid USDC address");
    });
  });

  describe("Game Creation", function () {
    it("Should allow owner to create a game", async function () {
      await expect(mafiaBetting.createGame(GAME_ID))
        .to.emit(mafiaBetting, "GameCreated")
        .withArgs(GAME_ID);

      const game = await mafiaBetting.getGame(GAME_ID);
      expect(game.exists).to.be.true;
      expect(game.locked).to.be.false;
      expect(game.settled).to.be.false;
      expect(game.totalPool).to.equal(0);
    });

    it("Should not allow non-owner to create a game", async function () {
      await expect(
        mafiaBetting.connect(player1).createGame(GAME_ID)
      ).to.be.revertedWithCustomError(mafiaBetting, "OwnableUnauthorizedAccount");
    });

    it("Should not allow creating duplicate games", async function () {
      await mafiaBetting.createGame(GAME_ID);
      await expect(mafiaBetting.createGame(GAME_ID)).to.be.revertedWith(
        "Game already exists"
      );
    });
  });

  describe("Placing Bets", function () {
    beforeEach(async function () {
      await mafiaBetting.createGame(GAME_ID);
    });

    it("Should allow betting on mafia with USDC", async function () {
      // Approve USDC first
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);

      await expect(
        mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT)
      )
        .to.emit(mafiaBetting, "BetPlaced")
        .withArgs(GAME_ID, player1.address, true, BET_AMOUNT);

      const game = await mafiaBetting.getGame(GAME_ID);
      expect(game.mafiaPool).to.equal(BET_AMOUNT);
      expect(game.totalPool).to.equal(BET_AMOUNT);

      const bet = await mafiaBetting.getPlayerBet(GAME_ID, player1.address);
      expect(bet.mafiaAmount).to.equal(BET_AMOUNT);
    });

    it("Should allow betting on citizens with USDC", async function () {
      // Approve USDC first
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);

      await expect(
        mafiaBetting.connect(player1).placeBet(GAME_ID, false, BET_AMOUNT)
      )
        .to.emit(mafiaBetting, "BetPlaced")
        .withArgs(GAME_ID, player1.address, false, BET_AMOUNT);

      const game = await mafiaBetting.getGame(GAME_ID);
      expect(game.citizenPool).to.equal(BET_AMOUNT);
      expect(game.totalPool).to.equal(BET_AMOUNT);

      const bet = await mafiaBetting.getPlayerBet(GAME_ID, player1.address);
      expect(bet.citizenAmount).to.equal(BET_AMOUNT);
    });

    it("Should allow multiple bets from same player", async function () {
      // Approve USDC for 2 bets
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT * 2n);

      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);
      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);

      const bet = await mafiaBetting.getPlayerBet(GAME_ID, player1.address);
      expect(bet.mafiaAmount).to.equal(BET_AMOUNT * 2n);
    });

    it("Should not allow zero-value bets", async function () {
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);

      await expect(
        mafiaBetting.connect(player1).placeBet(GAME_ID, true, 0)
      ).to.be.revertedWith("Bet amount must be greater than 0");
    });

    it("Should not allow betting without USDC approval", async function () {
      // No approval
      await expect(
        mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT)
      ).to.be.reverted; // ERC20: insufficient allowance
    });

    it("Should not allow betting with insufficient USDC balance", async function () {
      const hugeAmount = ethers.parseUnits("10000", 6);
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), hugeAmount);

      await expect(
        mafiaBetting.connect(player1).placeBet(GAME_ID, true, hugeAmount)
      ).to.be.reverted; // ERC20: transfer amount exceeds balance
    });

    it("Should not allow betting on non-existent game", async function () {
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);

      await expect(
        mafiaBetting.connect(player1).placeBet(999, true, BET_AMOUNT)
      ).to.be.revertedWith("Game does not exist");
    });

    it("Should not allow betting on locked game", async function () {
      await mafiaBetting.lockBetting(GAME_ID);
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);

      await expect(
        mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT)
      ).to.be.revertedWith("Betting is locked");
    });

    it("Should transfer USDC from bettor to contract", async function () {
      const initialBalance = await usdc.balanceOf(player1.address);
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);
      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);

      const finalBalance = await usdc.balanceOf(player1.address);
      expect(finalBalance).to.equal(initialBalance - BET_AMOUNT);

      const contractBalance = await usdc.balanceOf(await mafiaBetting.getAddress());
      expect(contractBalance).to.equal(BET_AMOUNT);
    });
  });

  describe("Locking Betting", function () {
    beforeEach(async function () {
      await mafiaBetting.createGame(GAME_ID);
    });

    it("Should allow owner to lock betting", async function () {
      await expect(mafiaBetting.lockBetting(GAME_ID))
        .to.emit(mafiaBetting, "BettingLocked")
        .withArgs(GAME_ID);

      const game = await mafiaBetting.getGame(GAME_ID);
      expect(game.locked).to.be.true;
    });

    it("Should not allow non-owner to lock betting", async function () {
      await expect(
        mafiaBetting.connect(player1).lockBetting(GAME_ID)
      ).to.be.revertedWithCustomError(mafiaBetting, "OwnableUnauthorizedAccount");
    });

    it("Should not allow locking twice", async function () {
      await mafiaBetting.lockBetting(GAME_ID);
      await expect(mafiaBetting.lockBetting(GAME_ID)).to.be.revertedWith(
        "Game already locked"
      );
    });

    it("Should not allow locking non-existent game", async function () {
      await expect(mafiaBetting.lockBetting(999)).to.be.revertedWith(
        "Game does not exist"
      );
    });
  });

  describe("Settling Games", function () {
    beforeEach(async function () {
      await mafiaBetting.createGame(GAME_ID);
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);
      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);
      await mafiaBetting.lockBetting(GAME_ID);
    });

    it("Should allow owner to settle game", async function () {
      await expect(mafiaBetting.settle(GAME_ID, true))
        .to.emit(mafiaBetting, "GameSettled")
        .withArgs(GAME_ID, true, BET_AMOUNT);

      const game = await mafiaBetting.getGame(GAME_ID);
      expect(game.settled).to.be.true;
      expect(game.mafiaWon).to.be.true;
    });

    it("Should not allow non-owner to settle", async function () {
      await expect(
        mafiaBetting.connect(player1).settle(GAME_ID, true)
      ).to.be.revertedWithCustomError(mafiaBetting, "OwnableUnauthorizedAccount");
    });

    it("Should not allow settling unlocked game", async function () {
      await mafiaBetting.createGame(2);
      await expect(mafiaBetting.settle(2, true)).to.be.revertedWith(
        "Game not locked"
      );
    });

    it("Should not allow settling twice", async function () {
      await mafiaBetting.settle(GAME_ID, true);
      await expect(mafiaBetting.settle(GAME_ID, true)).to.be.revertedWith(
        "Game already settled"
      );
    });

    it("Should collect house fees on settlement", async function () {
      const expectedFee = (BET_AMOUNT * 50n) / 1000n; // 5% of total pool
      await mafiaBetting.settle(GAME_ID, true);
      expect(await mafiaBetting.accumulatedFees()).to.equal(expectedFee);
    });
  });

  describe("Payout Calculation", function () {
    beforeEach(async function () {
      await mafiaBetting.createGame(GAME_ID);
    });

    it("Should calculate correct payout for winner with 5% house edge", async function () {
      // Player1 bets 10 USDC on mafia, Player2 bets 10 USDC on citizens
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);
      await usdc.connect(player2).approve(await mafiaBetting.getAddress(), BET_AMOUNT);

      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);
      await mafiaBetting.connect(player2).placeBet(GAME_ID, false, BET_AMOUNT);
      await mafiaBetting.lockBetting(GAME_ID);
      await mafiaBetting.settle(GAME_ID, true); // Mafia wins

      const totalPool = BET_AMOUNT * 2n;
      const netPool = (totalPool * 950n) / 1000n; // 95% after house fee
      const expectedPayout = netPool; // Player1 gets entire net pool

      const payout = await mafiaBetting.calculatePayout(GAME_ID, player1.address);
      expect(payout).to.equal(expectedPayout);
    });

    it("Should calculate proportional payouts for multiple winners", async function () {
      // Player1 bets 20 USDC on mafia, Player2 bets 10 USDC on mafia, Player3 bets 30 USDC on citizens
      const bet1 = ethers.parseUnits("20", 6);
      const bet2 = ethers.parseUnits("10", 6);
      const bet3 = ethers.parseUnits("30", 6);

      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), bet1);
      await usdc.connect(player2).approve(await mafiaBetting.getAddress(), bet2);
      await usdc.connect(player3).approve(await mafiaBetting.getAddress(), bet3);

      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, bet1);
      await mafiaBetting.connect(player2).placeBet(GAME_ID, true, bet2);
      await mafiaBetting.connect(player3).placeBet(GAME_ID, false, bet3);
      await mafiaBetting.lockBetting(GAME_ID);
      await mafiaBetting.settle(GAME_ID, true); // Mafia wins

      const totalPool = bet1 + bet2 + bet3; // 60 USDC
      const netPool = (totalPool * 950n) / 1000n; // 57 USDC
      const mafiaPool = bet1 + bet2; // 30 USDC

      // Player1 (2/3 of mafia pool) should get 2/3 of net pool
      const payout1 = await mafiaBetting.calculatePayout(GAME_ID, player1.address);
      const expectedPayout1 = (bet1 * netPool) / mafiaPool;
      expect(payout1).to.equal(expectedPayout1);

      // Player2 (1/3 of mafia pool) should get 1/3 of net pool
      const payout2 = await mafiaBetting.calculatePayout(GAME_ID, player2.address);
      const expectedPayout2 = (bet2 * netPool) / mafiaPool;
      expect(payout2).to.equal(expectedPayout2);

      // Player3 (bet on losing side) should get 0
      const payout3 = await mafiaBetting.calculatePayout(GAME_ID, player3.address);
      expect(payout3).to.equal(0);
    });

    it("Should return 0 for non-bettors", async function () {
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);
      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);
      await mafiaBetting.lockBetting(GAME_ID);
      await mafiaBetting.settle(GAME_ID, true);

      const payout = await mafiaBetting.calculatePayout(GAME_ID, player2.address);
      expect(payout).to.equal(0);
    });

    it("Should return 0 for losers", async function () {
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);
      await usdc.connect(player2).approve(await mafiaBetting.getAddress(), BET_AMOUNT);

      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);
      await mafiaBetting.connect(player2).placeBet(GAME_ID, false, BET_AMOUNT);
      await mafiaBetting.lockBetting(GAME_ID);
      await mafiaBetting.settle(GAME_ID, true); // Mafia wins

      const payout = await mafiaBetting.calculatePayout(GAME_ID, player2.address);
      expect(payout).to.equal(0);
    });

    it("Should return 0 before game is settled", async function () {
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);
      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);
      await mafiaBetting.lockBetting(GAME_ID);

      const payout = await mafiaBetting.calculatePayout(GAME_ID, player1.address);
      expect(payout).to.equal(0);
    });
  });

  describe("Claiming Winnings", function () {
    beforeEach(async function () {
      await mafiaBetting.createGame(GAME_ID);

      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);
      await usdc.connect(player2).approve(await mafiaBetting.getAddress(), BET_AMOUNT);

      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);
      await mafiaBetting.connect(player2).placeBet(GAME_ID, false, BET_AMOUNT);
      await mafiaBetting.lockBetting(GAME_ID);
      await mafiaBetting.settle(GAME_ID, true); // Mafia wins
    });

    it("Should allow winner to claim USDC winnings", async function () {
      const initialBalance = await usdc.balanceOf(player1.address);
      const expectedPayout = await mafiaBetting.calculatePayout(GAME_ID, player1.address);

      await expect(mafiaBetting.connect(player1).claimWinnings(GAME_ID))
        .to.emit(mafiaBetting, "PayoutClaimed")
        .withArgs(GAME_ID, player1.address, expectedPayout);

      const finalBalance = await usdc.balanceOf(player1.address);
      expect(finalBalance).to.equal(initialBalance + expectedPayout);

      const bet = await mafiaBetting.getPlayerBet(GAME_ID, player1.address);
      expect(bet.claimed).to.be.true;
    });

    it("Should not allow claiming twice", async function () {
      await mafiaBetting.connect(player1).claimWinnings(GAME_ID);
      await expect(
        mafiaBetting.connect(player1).claimWinnings(GAME_ID)
      ).to.be.revertedWith("Already claimed");
    });

    it("Should not allow claiming before settlement", async function () {
      await mafiaBetting.createGame(2);
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);
      await mafiaBetting.connect(player1).placeBet(2, true, BET_AMOUNT);
      await mafiaBetting.lockBetting(2);

      await expect(
        mafiaBetting.connect(player1).claimWinnings(2)
      ).to.be.revertedWith("Game not settled yet");
    });

    it("Should not allow losers to claim", async function () {
      await expect(
        mafiaBetting.connect(player2).claimWinnings(GAME_ID)
      ).to.be.revertedWith("No winnings to claim");
    });

    it("Should not allow non-bettors to claim", async function () {
      await expect(
        mafiaBetting.connect(player3).claimWinnings(GAME_ID)
      ).to.be.revertedWith("No winnings to claim");
    });
  });

  describe("Fee Withdrawal", function () {
    beforeEach(async function () {
      await mafiaBetting.createGame(GAME_ID);
      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), BET_AMOUNT);
      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, BET_AMOUNT);
      await mafiaBetting.lockBetting(GAME_ID);
      await mafiaBetting.settle(GAME_ID, true);
    });

    it("Should allow owner to withdraw USDC fees", async function () {
      const expectedFee = (BET_AMOUNT * 50n) / 1000n;
      const initialBalance = await usdc.balanceOf(owner.address);

      await expect(mafiaBetting.withdrawFees())
        .to.emit(mafiaBetting, "FeesWithdrawn")
        .withArgs(owner.address, expectedFee);

      const finalBalance = await usdc.balanceOf(owner.address);
      expect(finalBalance).to.equal(initialBalance + expectedFee);
      expect(await mafiaBetting.accumulatedFees()).to.equal(0);
    });

    it("Should not allow non-owner to withdraw fees", async function () {
      await expect(
        mafiaBetting.connect(player1).withdrawFees()
      ).to.be.revertedWithCustomError(mafiaBetting, "OwnableUnauthorizedAccount");
    });

    it("Should not allow withdrawing with no fees", async function () {
      await mafiaBetting.withdrawFees();
      await expect(mafiaBetting.withdrawFees()).to.be.revertedWith(
        "No fees to withdraw"
      );
    });
  });

  describe("Complete Game Lifecycle", function () {
    it("Should handle complete game flow with multiple bettors using USDC", async function () {
      // Setup game
      await mafiaBetting.createGame(GAME_ID);

      // Players place bets
      const bet1 = ethers.parseUnits("30", 6);
      const bet2 = ethers.parseUnits("20", 6);
      const bet3 = ethers.parseUnits("50", 6);

      await usdc.connect(player1).approve(await mafiaBetting.getAddress(), bet1);
      await usdc.connect(player2).approve(await mafiaBetting.getAddress(), bet2);
      await usdc.connect(player3).approve(await mafiaBetting.getAddress(), bet3);

      await mafiaBetting.connect(player1).placeBet(GAME_ID, true, bet1);
      await mafiaBetting.connect(player2).placeBet(GAME_ID, true, bet2);
      await mafiaBetting.connect(player3).placeBet(GAME_ID, false, bet3);

      // Verify pool totals
      const gameBeforeLock = await mafiaBetting.getGame(GAME_ID);
      expect(gameBeforeLock.mafiaPool).to.equal(bet1 + bet2);
      expect(gameBeforeLock.citizenPool).to.equal(bet3);
      expect(gameBeforeLock.totalPool).to.equal(bet1 + bet2 + bet3);

      // Lock and settle
      await mafiaBetting.lockBetting(GAME_ID);
      await mafiaBetting.settle(GAME_ID, true); // Mafia wins

      // Winners claim
      await mafiaBetting.connect(player1).claimWinnings(GAME_ID);
      await mafiaBetting.connect(player2).claimWinnings(GAME_ID);

      // Verify payouts are proportional
      const totalPool = bet1 + bet2 + bet3;
      const netPool = (totalPool * 950n) / 1000n;
      const mafiaPool = bet1 + bet2;

      const payout1 = (bet1 * netPool) / mafiaPool;
      const payout2 = (bet2 * netPool) / mafiaPool;

      // Verify total payouts = net pool (within rounding)
      const totalPaidOut = payout1 + payout2;
      expect(totalPaidOut).to.be.closeTo(netPool, 1);

      // Verify house collected fees
      const expectedFee = (totalPool * 50n) / 1000n;
      expect(await mafiaBetting.accumulatedFees()).to.equal(expectedFee);
    });
  });
});
