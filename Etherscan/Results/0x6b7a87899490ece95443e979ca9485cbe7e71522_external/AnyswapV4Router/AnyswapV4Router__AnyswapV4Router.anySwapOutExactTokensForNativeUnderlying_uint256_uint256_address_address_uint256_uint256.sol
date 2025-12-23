// entry (external): AnyswapV4Router.anySwapOutExactTokensForNativeUnderlying(uint256,uint256,address[],address,uint256,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:469-481
function anySwapOutExactTokensForNativeUnderlying(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline,
        uint toChainID
    ) external virtual ensure(deadline) {
        TransferHelper.safeTransferFrom(AnyswapV1ERC20(path[0]).underlying(), msg.sender, path[0], amountIn);
        AnyswapV1ERC20(path[0]).depositVault(amountIn, msg.sender);
        AnyswapV1ERC20(path[0]).burn(msg.sender, amountIn);
        emit LogAnySwapTradeTokensForNative(path, msg.sender, to, amountIn, amountOutMin, cID(), toChainID);
    }

// leaf targets (no body):
//   - (external) [abstract]: AnyswapV1ERC20.burn(address,uint256)
//   - (external) [abstract]: AnyswapV1ERC20.depositVault(uint256,address)
//   - (external) [abstract]: AnyswapV1ERC20.underlying()

// ---- reachable (external) [internal]: TransferHelper.safeTransferFrom(address,address,address,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:140-144
function safeTransferFrom(address token, address from, address to, uint value) internal {
        // bytes4(keccak256(bytes('transferFrom(address,address,uint256)')));
        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(0x23b872dd, from, to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), 'TransferHelper: TRANSFER_FROM_FAILED');
    }

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
