// entry (external): AnyswapV4Router.receive()
// source: Etherscan/SourceCode/0x6b7a87899490EcE95443e979cA9485CBE7E71522/AnyswapV4Router.sol:202-204
receive() external payable {
        assert(msg.sender == wNATIVE); // only accept Native via fallback from the wNative contract
    }
