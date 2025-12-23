// entry (external): AnyswapV4Router.anySwapOutUnderlyingWithPermit(address,address,address,uint256,uint256,uint8,bytes32,bytes32,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:265-281
function anySwapOutUnderlyingWithPermit(
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
        address _underlying = AnyswapV1ERC20(token).underlying();
        IERC20(_underlying).permit(from, address(this), amount, deadline, v, r, s);
        TransferHelper.safeTransferFrom(_underlying, from, token, amount);
        AnyswapV1ERC20(token).depositVault(amount, from);
        _anySwapOut(from, token, to, amount, toChainID);
    }

// leaf targets (no body):
//   - (external) [abstract]: AnyswapV1ERC20.burn(address,uint256)
//   - (external) [abstract]: AnyswapV1ERC20.depositVault(uint256,address)
//   - (external) [abstract]: AnyswapV1ERC20.underlying()
//   - (external) [abstract]: IERC20.permit(address,address,uint256,uint256,uint8,bytes32,bytes32)

// ---- reachable (external) [internal]: TransferHelper.safeTransferFrom(address,address,address,uint256)
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:140-144
function safeTransferFrom(address token, address from, address to, uint value) internal {
        // bytes4(keccak256(bytes('transferFrom(address,address,uint256)')));
        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(0x23b872dd, from, to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), 'TransferHelper: TRANSFER_FROM_FAILED');
    }

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
