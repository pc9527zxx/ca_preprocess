// entry (external): AnyswapV4Router.anySwapFeeTo(address,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:334-338
function anySwapFeeTo(address token, uint amount) external onlyMPC {
        address _mpc = mpc();
        AnyswapV1ERC20(token).mint(_mpc, amount);
        AnyswapV1ERC20(token).withdrawVault(_mpc, amount, _mpc);
    }

// leaf targets (no body):
//   - (external) [abstract]: AnyswapV1ERC20.mint(address,uint256)
//   - (external) [abstract]: AnyswapV1ERC20.withdrawVault(address,uint256,address)

// ---- reachable (internal) [public]: AnyswapV4Router.mpc()
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:223-228
function mpc() public view returns (address) {
        if (block.timestamp >= _newMPCEffectiveTime) {
            return _newMPC;
        }
        return _oldMPC;
    }

// ---- reachable (internal) [internal]: AnyswapV4Router.onlyMPC()
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:218-221
modifier onlyMPC() {
        require(msg.sender == mpc(), "AnyswapV3Router: FORBIDDEN");
        _;
    }
