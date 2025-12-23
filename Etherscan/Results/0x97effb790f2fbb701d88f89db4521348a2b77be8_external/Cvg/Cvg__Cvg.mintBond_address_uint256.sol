// entry (external): Cvg.mintBond(address,uint256)
// source: Etherscan/SourceCode/0x97effb790f2fbb701d88f89db4521348a2b77be8/contracts/Token/Cvg.sol:52-59
function mintBond(address account, uint256 amount) external {
        require(cvgControlTower.isBond(msg.sender), "NOT_BOND");
        uint256 newMintedBond = mintedBond + amount;
        require(newMintedBond <= MAX_BOND, "MAX_SUPPLY_BOND");

        mintedBond = newMintedBond;
        _mint(account, amount);
    }

// leaf targets (no body):
//   - (external) [abstract]: ICvgControlTower.isBond(address)

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
