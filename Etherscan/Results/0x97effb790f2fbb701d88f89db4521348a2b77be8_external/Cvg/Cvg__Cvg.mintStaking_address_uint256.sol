// entry (external): Cvg.mintStaking(address,uint256)
// source: Etherscan/SourceCode/0x97effb790f2fbb701d88f89db4521348a2b77be8/contracts/Token/Cvg.sol:66-80
function mintStaking(address account, uint256 amount) external {
        require(cvgControlTower.isStakingContract(msg.sender), "NOT_STAKING");
        uint256 _mintedStaking = mintedStaking;
        require(_mintedStaking < MAX_STAKING, "MAX_SUPPLY_STAKING");

        /// @dev ensure every tokens will be minted from staking
        uint256 newMintedStaking = _mintedStaking + amount;
        if (newMintedStaking > MAX_STAKING) {
            newMintedStaking = MAX_STAKING;
            amount = MAX_STAKING - _mintedStaking;
        }

        mintedStaking = newMintedStaking;
        _mint(account, amount);
    }

// leaf targets (no body):
//   - (external) [abstract]: ICvgControlTower.isStakingContract(address)

// ---- reachable (internal) [internal]: Cvg._mint(address,uint256)
// source: Etherscan/SourceCode/0x97effb790f2fbb701d88f89db4521348a2b77be8/@openzeppelin/contracts/token/ERC20/ERC20.sol:251-264
function _mint(address account, uint256 amount) internal virtual {
        require(account != address(0), "ERC20: mint to the zero address");

        _beforeTokenTransfer(address(0), account, amount);

        _totalSupply += amount;
        unchecked {
            // Overflow not possible: balance + amount is at most totalSupply + amount, which is checked above.
            _balances[account] += amount;
        }
        emit Transfer(address(0), account, amount);

        _afterTokenTransfer(address(0), account, amount);
    }

// ---- reachable (internal) [internal]: Cvg._afterTokenTransfer(address,address,uint256)
// source: Etherscan/SourceCode/0x97effb790f2fbb701d88f89db4521348a2b77be8/@openzeppelin/contracts/token/ERC20/ERC20.sol:364-364
function _afterTokenTransfer(address from, address to, uint256 amount) internal virtual {}

// ---- reachable (internal) [internal]: Cvg._beforeTokenTransfer(address,address,uint256)
// source: Etherscan/SourceCode/0x97effb790f2fbb701d88f89db4521348a2b77be8/@openzeppelin/contracts/token/ERC20/ERC20.sol:348-348
function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual {}
