// entry (external): AnyswapV4Router.anySwapOutExactTokensForTokensUnderlyingWithTransferPermit(address,uint256,uint256,address[],address,uint256,uint8,bytes32,bytes32,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:420-436
function anySwapOutExactTokensForTokensUnderlyingWithTransferPermit(
        address from,
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline,
        uint8 v,
        bytes32 r,
        bytes32 s,
        uint toChainID
    ) external virtual ensure(deadline) {
        IERC20(AnyswapV1ERC20(path[0]).underlying()).transferWithPermit(from, path[0], amountIn, deadline, v, r, s);
        AnyswapV1ERC20(path[0]).depositVault(amountIn, from);
        AnyswapV1ERC20(path[0]).burn(from, amountIn);
        emit LogAnySwapTradeTokensForTokens(path, from, to, amountIn, amountOutMin, cID(), toChainID);
    }

// leaf targets (no body):
//   - (external) [abstract]: AnyswapV1ERC20.burn(address,uint256)
//   - (external) [abstract]: AnyswapV1ERC20.depositVault(uint256,address)
//   - (external) [abstract]: AnyswapV1ERC20.underlying()
//   - (external) [abstract]: IERC20.transferWithPermit(address,address,uint256,uint256,uint8,bytes32,bytes32)

// ---- reachable (internal) [public]: AnyswapV4Router.cID()
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:230-232
function cID() public view returns (uint id) {
        assembly {id := chainid()}
    }

// ---- reachable (internal) [internal]: AnyswapV4Router.ensure(uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:190-193
modifier ensure(uint deadline) {
        require(deadline >= block.timestamp, 'AnyswapV3Router: EXPIRED');
        _;
    }
