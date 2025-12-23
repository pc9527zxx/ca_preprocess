// entry (external): CvgControlTowerV2.getSdtStakings(uint256,uint256)
// source: Etherscan/SourceCode/0xbdbddc4bf67e9bc02706e4ce53bc14d6ce3038f1/contracts/CvgControlTowerV2.sol:151-171
function getSdtStakings(uint256 _cursorStart, uint256 _lengthDesired) external view returns (Staking[] memory) {
        uint256 _totalArrayLength = sdAndLpAssetStaking.length;

        if (_cursorStart + _lengthDesired > _totalArrayLength) {
            _lengthDesired = _totalArrayLength - _cursorStart;
        }
        /// @dev Prevent to reach an index that doesn't exist in the array
        Staking[] memory array = new Staking[](_lengthDesired);
        for (uint256 i = _cursorStart; i < _cursorStart + _lengthDesired; ) {
            ISdtStakingPositionService sdtStakingService = sdAndLpAssetStaking[i];
            array[i - _cursorStart] = Staking({
                stakingContract: address(sdtStakingService),
                stakingName: sdtStakingService.stakingAsset().name()
            });
            unchecked {
                ++i;
            }
        }

        return array;
    }
