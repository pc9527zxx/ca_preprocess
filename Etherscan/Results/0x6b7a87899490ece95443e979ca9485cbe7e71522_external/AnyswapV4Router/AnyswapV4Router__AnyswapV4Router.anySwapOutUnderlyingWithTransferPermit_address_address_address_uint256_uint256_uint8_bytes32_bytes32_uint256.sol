// entry (external): AnyswapV4Router.anySwapOutUnderlyingWithTransferPermit(address,address,address,uint256,uint256,uint8,bytes32,bytes32,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:283-297
function anySwapOutUnderlyingWithTransferPermit(
        address from,
        address token,
        address to,
        uint amount,
        uint deadline,
        uint8 v,
        bytes32 r,
        bytes32 s,
        uint toChainID
    ) external {
        IERC20(AnyswapV1ERC20(token).underlying()).transferWithPermit(from, token, amount, deadline, v, r, s);
        AnyswapV1ERC20(token).depositVault(amount, from);
        _anySwapOut(from, token, to, amount, toChainID);
    }

// leaf targets (no body):
//   - (external) [abstract]: AnyswapV1ERC20.burn(address,uint256)
//   - (external) [abstract]: AnyswapV1ERC20.depositVault(uint256,address)
//   - (external) [abstract]: AnyswapV1ERC20.underlying()
//   - (external) [abstract]: IERC20.transferWithPermit(address,address,uint256,uint256,uint8,bytes32,bytes32)

// ---- reachable (internal) [internal]: AnyswapV4Router._anySwapOut(address,address,address,uint256,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:248-251
function _anySwapOut(address from, address token, address to, uint amount, uint toChainID) internal {
        AnyswapV1ERC20(token).burn(from, amount);
        emit LogAnySwapOut(token, from, to, amount, cID(), toChainID);
    }

// ---- reachable (internal) [public]: AnyswapV4Router.cID()
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:230-232
function cID() public view returns (uint id) {
        assembly {id := chainid()}
    }
