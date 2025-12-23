// entry (external): CvxRewardDistributor.initialize(ICVX1,ICvgCVX)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/contracts/Staking/Convex/CvxRewardDistributor.sol:60-74
function initialize(ICVX1 _cvx1, ICvgCVX _cvgCVX) external initializer {
        address treasuryDao = cvgControlTower.treasuryDao();

        require(address(_cvgCVX) != address(0), "CVX_LOCKER_ZERO");
        cvgCVX = _cvgCVX;

        require(address(_cvx1) != address(0), "CVX1_ZERO");
        cvx1 = _cvx1;

        CVX.approve(address(_cvx1), type(uint256).max);
        CVX.approve(address(_cvgCVX), type(uint256).max);

        require(treasuryDao != address(0), "TREASURY_DAO_ZERO");
        _transferOwnership(treasuryDao);
    }

// leaf targets (no body):
//   - (external) [abstract]: ICvgControlTowerV2.treasuryDao()
//   - (external) [abstract]: IERC20.approve(address,uint256)

// ---- reachable (internal) [internal]: CvxRewardDistributor.initializer()
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol:84-99
modifier initializer() {
        bool isTopLevelCall = !_initializing;
        require(
            (isTopLevelCall && _initialized < 1) || (!AddressUpgradeable.isContract(address(this)) && _initialized == 1),
            "Initializable: contract is already initialized"
        );
        _initialized = 1;
        if (isTopLevelCall) {
            _initializing = true;
        }
        _;
        if (isTopLevelCall) {
            _initializing = false;
            emit Initialized(1);
        }
    }

// ---- reachable (internal) [internal]: CvxRewardDistributor._transferOwnership(address)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts-upgradeable/access/Ownable2StepUpgradeable.sol:51-54
function _transferOwnership(address newOwner) internal virtual override {
        delete _pendingOwner;
        super._transferOwnership(newOwner);
    }

// ---- reachable (internal) [internal]: CvxRewardDistributor._transferOwnership(address)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol:83-87
function _transferOwnership(address newOwner) internal virtual {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }

// ---- reachable (external) [internal]: AddressUpgradeable.isContract(address)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts-upgradeable/utils/AddressUpgradeable.sol:40-46
function isContract(address account) internal view returns (bool) {
        // This method relies on extcodesize/address.code.length, which returns 0
        // for contracts in construction, since the code is only stored at the end
        // of the constructor execution.

        return account.code.length > 0;
    }
