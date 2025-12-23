// entry (external): CvgControlTowerV2.insertNewSdtStaking(ISdtStakingPositionService)
// source: Etherscan/SourceCode/0xbdbddc4bf67e9bc02706e4ce53bc14d6ce3038f1/contracts/CvgControlTowerV2.sol:129-134
function insertNewSdtStaking(ISdtStakingPositionService _sdtStakingClone) external {
        require(msg.sender == cloneFactory, "CLONE_FACTORY");
        sdAndLpAssetStaking.push(_sdtStakingClone);
        isSdtStaking[address(_sdtStakingClone)] = true;
        isStakingContract[address(_sdtStakingClone)] = true;
    }
