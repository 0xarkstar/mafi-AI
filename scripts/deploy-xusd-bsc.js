const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("Deploying XUSD to BSC Testnet with account:", deployer.address);
  console.log(
    "Account balance:",
    ethers.formatEther(await ethers.provider.getBalance(deployer.address)),
    "tBNB"
  );

  // Deploy XUSD (EIP-3009 compatible wrapped USDC for x402)
  console.log("\n--- Deploying XUSD ---");
  const XUSD = await ethers.getContractFactory("XUSD");
  const xusd = await XUSD.deploy();
  await xusd.waitForDeployment();

  const xusdAddress = await xusd.getAddress();
  console.log("XUSD deployed to:", xusdAddress);

  // Mint initial supply to deployer (1,000,000 XUSD)
  const mintAmount = ethers.parseEther("1000000");
  const mintTx = await xusd.mint(deployer.address, mintAmount);
  await mintTx.wait();
  console.log("Minted 1,000,000 XUSD to deployer");

  // Verify EIP-3009 functions
  const domainSep = await xusd.DOMAIN_SEPARATOR();
  console.log("\nEIP-3009 verification:");
  console.log("  DOMAIN_SEPARATOR:", domainSep);
  console.log("  name:", await xusd.name());
  console.log("  symbol:", await xusd.symbol());
  console.log("  decimals:", await xusd.decimals());

  // Save deployment info
  const deploymentInfo = {
    network: "bscTestnet",
    chainId: 97,
    deployer: deployer.address,
    xusd: xusdAddress,
    xusdNote:
      "EIP-3009 compatible Wrapped USDC for x402 settlement (18 decimals, open mint)",
    domainName: "Wrapped USDC",
    domainVersion: "2",
    domainSeparator: domainSep,
    deployTxHash: xusd.deploymentTransaction().hash,
    mintTxHash: mintTx.hash,
    timestamp: new Date().toISOString(),
    x402Config: {
      facilitatorUrl: "https://api.x402.unibase.com",
      network: "eip155:97",
      assetAddress: xusdAddress,
      tokenName: "Wrapped USDC",
      tokenVersion: "2",
      tokenDecimals: 18,
    },
  };

  fs.writeFileSync(
    "deployment-xusd-bsc.json",
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log("\n--- Deployment Complete ---");
  console.log("Deployment info saved to deployment-xusd-bsc.json");
  console.log("\nBSC Testnet Explorer:");
  console.log(
    `  XUSD: https://testnet.bscscan.com/address/${xusdAddress}`
  );
  console.log(
    `  Deploy tx: https://testnet.bscscan.com/tx/${xusd.deploymentTransaction().hash}`
  );
  console.log("\nx402 Configuration:");
  console.log("  X402_FACILITATOR_URL=https://api.x402.unibase.com");
  console.log(`  X402_NETWORK=eip155:97`);
  console.log(`  X402_USDC_ADDRESS=${xusdAddress}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
