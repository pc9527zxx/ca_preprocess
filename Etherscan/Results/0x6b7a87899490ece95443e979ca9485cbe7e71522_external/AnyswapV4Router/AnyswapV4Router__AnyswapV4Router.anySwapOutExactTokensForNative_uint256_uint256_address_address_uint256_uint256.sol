// entry (external): AnyswapV4Router.anySwapOutExactTokensForNative(uint256,uint256,address[],address,uint256,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:456-466
function anySwapOutExactTokensForNative(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline,
        uint toChainID
    ) external virtual ensure(deadline) {
        AnyswapV1ERC20(path[0]).burn(msg.sender, amountIn);
        emit LogAnySwapTradeTokensForNative(path, msg.sender, to, amountIn, amountOutMin, cID(), toChainID);
    }

// leaf targets (no body):
//   - (external) [abstract]: AnyswapV1ERC20.burn(address,uint256)

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
