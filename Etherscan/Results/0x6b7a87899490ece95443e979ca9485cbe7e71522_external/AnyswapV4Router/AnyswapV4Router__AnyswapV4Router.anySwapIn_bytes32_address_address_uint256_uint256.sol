// entry (external): AnyswapV4Router.anySwapIn(bytes32[],address[],address[],uint256[],uint256[])
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:340-344
function anySwapIn(bytes32[] calldata txs, address[] calldata tokens, address[] calldata to, uint256[] calldata amounts, uint[] calldata fromChainIDs) external onlyMPC {
        for (uint i = 0; i < tokens.length; i++) {
            _anySwapIn(txs[i], tokens[i], to[i], amounts[i], fromChainIDs[i]);
        }
    }

// leaf targets (no body):
//   - (external) [abstract]: AnyswapV1ERC20.mint(address,uint256)

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
