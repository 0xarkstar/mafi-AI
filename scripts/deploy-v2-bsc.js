const { ethers } = require("hardhat");
const fs = require("fs");

// Official BSC Testnet USDC (BNB Chain faucet token, 18 decimals)
const BSC_TESTNET_USDC = "0x64544969ed7EBf5f083679233325356EbE738930";

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("Deploying MafiaBettingV2 to BSC Testnet with account:", deployer.address);
  console.log("Account balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "tBNB");
  console.log("Using official BSC Testnet USDC:", BSC_TESTNET_USDC);

  // Deploy MafiaBettingV2 with official BSC Testnet USDC
  console.log("\n--- Deploying MafiaBettingV2 ---");
  const MafiaBettingV2 = await ethers.getContractFactory("MafiaBettingV2");
  const contract = await MafiaBettingV2.deploy(BSC_TESTNET_USDC);
  await contract.waitForDeployment();

  const contractAddress = await contract.getAddress();
  console.log("MafiaBettingV2 deployed to:", contractAddress);

  // Save deployment info
  const deploymentInfo = {
    network: "bscTestnet",
    chainId: 97,
    deployer: deployer.address,
    usdc: BSC_TESTNET_USDC,
    usdcNote: "Official BSC Testnet USDC (18 decimals, from BNB Chain faucet)",
    mafiaBettingV2: contractAddress,
    deployTxHash: contract.deploymentTransaction().hash,
    timestamp: new Date().toISOString()
  };

  fs.writeFileSync(
    "deployment-bsc.json",
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log("\n--- Deployment Complete ---");
  console.log("Deployment info saved to deployment-bsc.json");
  console.log("\nBSC Testnet Explorer Links:");
  console.log(`  USDC (official):  https://testnet.bscscan.com/token/${BSC_TESTNET_USDC}`);
  console.log(`  MafiaBettingV2:   https://testnet.bscscan.com/address/${contractAddress}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
