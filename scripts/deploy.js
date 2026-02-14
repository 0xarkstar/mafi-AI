const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)));

  // Monad testnet USDC address
  const USDC_ADDRESS = "0x534b2f3A21130d7a60830c2Df862319e593943A3";
  console.log("Using USDC address:", USDC_ADDRESS);

  // Deploy MafiaBetting contract with USDC address
  const MafiaBetting = await ethers.getContractFactory("MafiaBetting");
  console.log("Deploying MafiaBetting...");

  const contract = await MafiaBetting.deploy(USDC_ADDRESS);
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("MafiaBetting deployed to:", address);

  // Save deployment info
  const deploymentInfo = {
    address: address,
    network: network.name,
    chainId: network.config.chainId,
    deployer: deployer.address,
    timestamp: new Date().toISOString()
  };

  fs.writeFileSync(
    "deployment.json",
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log("Deployment info saved to deployment.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
