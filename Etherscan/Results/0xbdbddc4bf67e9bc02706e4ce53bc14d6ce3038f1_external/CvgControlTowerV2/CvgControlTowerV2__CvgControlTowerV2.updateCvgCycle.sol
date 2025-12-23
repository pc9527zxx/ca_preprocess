// entry (external): CvgControlTowerV2.updateCvgCycle()
// source: Etherscan/SourceCode/0xbdbddc4bf67e9bc02706e4ce53bc14d6ce3038f1/contracts/CvgControlTowerV2.sol:327-330
function updateCvgCycle() external {
        require(msg.sender == address(cvgRewards), "NOT_CVG_REWARDS");
        emit NewCycle(++cvgCycle);
    }
