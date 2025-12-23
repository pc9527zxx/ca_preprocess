// entry (external): Cvg.burn(uint256)
// source: Etherscan/SourceCode/0x97effb790f2fbb701d88f89db4521348a2b77be8/contracts/Token/Cvg.sol:86-88
function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }

// ---- reachable (internal) [internal]: Cvg._burn(address,uint256)
// source: Etherscan/SourceCode/0x97effb790f2fbb701d88f89db4521348a2b77be8/@openzeppelin/contracts/token/ERC20/ERC20.sol:277-293
function _burn(address account, uint256 amount) internal virtual {
        require(account != address(0), "ERC20: burn from the zero address");

        _beforeTokenTransfer(account, address(0), amount);

        uint256 accountBalance = _balances[account];
        require(accountBalance >= amount, "ERC20: burn amount exceeds balance");
        unchecked {
            _balances[account] = accountBalance - amount;
            // Overflow not possible: amount <= accountBalance <= totalSupply.
            _totalSupply -= amount;
        }

        emit Transfer(account, address(0), amount);

        _afterTokenTransfer(account, address(0), amount);
    }

// ---- reachable (internal) [internal]: Cvg._afterTokenTransfer(address,address,uint256)
// source: Etherscan/SourceCode/0x97effb790f2fbb701d88f89db4521348a2b77be8/@openzeppelin/contracts/token/ERC20/ERC20.sol:364-364
function _afterTokenTransfer(address from, address to, uint256 amount) internal virtual {}

// ---- reachable (internal) [internal]: Cvg._beforeTokenTransfer(address,address,uint256)
// source: Etherscan/SourceCode/0x97effb790f2fbb701d88f89db4521348a2b77be8/@openzeppelin/contracts/token/ERC20/ERC20.sol:348-348
function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual {}
