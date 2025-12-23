// entry (external): CvgControlTowerV2.setGaugeController(IGaugeController)
// source: Etherscan/SourceCode/0xbdbddc4bf67e9bc02706e4ce53bc14d6ce3038f1/contracts/CvgControlTowerV2.sol:220-222
function setGaugeController(IGaugeController newGaugeController) external onlyOwner {
        gaugeController = newGaugeController;
    }

// ---- reachable (internal) [internal]: CvgControlTowerV2.onlyOwner()
// source: Etherscan/SourceCode/0xbdbddc4bf67e9bc02706e4ce53bc14d6ce3038f1/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol:40-43
modifier onlyOwner() {
        _checkOwner();
        _;
    }

// ---- reachable (internal) [internal]: CvgControlTowerV2._checkOwner()
// source: Etherscan/SourceCode/0xbdbddc4bf67e9bc02706e4ce53bc14d6ce3038f1/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol:55-57
function _checkOwner() internal view virtual {
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
    }

// ---- reachable (internal) [internal]: CvgControlTowerV2._msgSender()
// source: Etherscan/SourceCode/0xbdbddc4bf67e9bc02706e4ce53bc14d6ce3038f1/@openzeppelin/contracts-upgradeable/utils/ContextUpgradeable.sol:23-25
function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

// ---- reachable (internal) [public]: CvgControlTowerV2.owner()
// source: Etherscan/SourceCode/0xbdbddc4bf67e9bc02706e4ce53bc14d6ce3038f1/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol:48-50
function owner() public view virtual returns (address) {
        return _owner;
    }
