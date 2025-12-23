// entry (external): CvxRewardDistributor.setPoolCvgCvxCvx1AndApprove(ICrvPoolPlain)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/contracts/Staking/Convex/CvxRewardDistributor.sol:247-255
function setPoolCvgCvxCvx1AndApprove(ICrvPoolPlain _poolCvgCvxCvx1) external onlyOwner {
        /// @dev Remove approval from previous pool
        if (address(poolCvgCvxCvx1) != address(0)) {
            cvx1.approve(address(poolCvgCvxCvx1), 0);
        }

        poolCvgCvxCvx1 = _poolCvgCvxCvx1;
        cvx1.approve(address(_poolCvgCvxCvx1), type(uint256).max);
    }

// ---- reachable (internal) [internal]: CvxRewardDistributor.onlyOwner()
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol:40-43
modifier onlyOwner() {
        _checkOwner();
        _;
    }

// ---- reachable (internal) [internal]: CvxRewardDistributor._checkOwner()
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol:55-57
function _checkOwner() internal view virtual {
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
    }

// ---- reachable (internal) [internal]: CvxRewardDistributor._msgSender()
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts-upgradeable/utils/ContextUpgradeable.sol:23-25
function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

// ---- reachable (internal) [public]: CvxRewardDistributor.owner()
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol:48-50
function owner() public view virtual returns (address) {
        return _owner;
    }
