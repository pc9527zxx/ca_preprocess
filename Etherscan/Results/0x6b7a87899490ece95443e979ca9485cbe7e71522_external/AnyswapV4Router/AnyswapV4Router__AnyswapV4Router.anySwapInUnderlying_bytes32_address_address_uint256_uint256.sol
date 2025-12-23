// entry (external): AnyswapV4Router.anySwapInUnderlying(bytes32,address,address,uint256,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:318-321
function anySwapInUnderlying(bytes32 txs, address token, address to, uint amount, uint fromChainID) external onlyMPC {
        _anySwapIn(txs, token, to, amount, fromChainID);
        AnyswapV1ERC20(token).withdrawVault(to, amount, to);
    }

// leaf targets (no body):
//   - (external) [abstract]: AnyswapV1ERC20.mint(address,uint256)
//   - (external) [abstract]: AnyswapV1ERC20.withdrawVault(address,uint256,address)

// ---- reachable (internal) [internal]: AnyswapV4Router._anySwapIn(bytes32,address,address,uint256,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:306-309
function _anySwapIn(bytes32 txs, address token, address to, uint amount, uint fromChainID) internal {
        AnyswapV1ERC20(token).mint(to, amount);
        emit LogAnySwapIn(txs, token, to, amount, fromChainID, cID());
    }

// ---- reachable (internal) [internal]: AnyswapV4Router.onlyMPC()
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:218-221
modifier onlyMPC() {
        require(msg.sender == mpc(), "AnyswapV3Router: FORBIDDEN");
        _;
    }

// ---- reachable (internal) [public]: AnyswapV4Router.mpc()
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:223-228
function mpc() public view returns (address) {
        if (block.timestamp >= _newMPCEffectiveTime) {
            return _newMPC;
        }
        return _oldMPC;
    }

// ---- reachable (internal) [public]: AnyswapV4Router.cID()
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:230-232
function cID() public view returns (uint id) {
        assembly {id := chainid()}
    }
