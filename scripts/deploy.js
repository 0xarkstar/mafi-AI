const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)));

  // Deploy MafiaBetting contract
  const MafiaBetting = await ethers.getContractFactory("MafiaBetting");
  console.log("Deploying MafiaBetting...");

  const contract = await MafiaBetting.deploy();
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
