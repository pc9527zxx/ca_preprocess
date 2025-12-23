// entry (external): Proxy.fallback()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/Proxy.sol:67-69
fallback() external payable virtual {
        _fallback();
    }

// leaf targets (no body):
//   - (internal) [abstract]: Proxy._implementation()

// ---- reachable (internal) [internal]: Proxy._fallback()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/Proxy.sol:58-61
function _fallback() internal virtual {
        _beforeFallback();
        _delegate(_implementation());
    }

// ---- reachable (internal) [internal]: Proxy._beforeFallback()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/Proxy.sol:85-85
function _beforeFallback() internal virtual {}

// ---- reachable (internal) [internal]: Proxy._delegate(address)
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/Proxy.sol:22-45
function _delegate(address implementation) internal virtual {
        assembly {
            // Copy msg.data. We take full control of memory in this inline assembly
            // block because it will not return to Solidity code. We overwrite the
            // Solidity scratch pad at memory position 0.
            calldatacopy(0, 0, calldatasize())

            // Call the implementation.
            // out and outsize are 0 because we don't know the size yet.
            let result := delegatecall(gas(), implementation, 0, calldatasize(), 0, 0)

            // Copy the returned data.
            returndatacopy(0, 0, returndatasize())

            switch result
            // delegatecall returns 0 on error.
            case 0 {
                revert(0, returndatasize())
            }
            default {
                return(0, returndatasize())
            }
        }
    }
