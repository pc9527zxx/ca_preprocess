// entry (external): ERC1967Proxy.receive()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/Proxy.sol:75-77
receive() external payable virtual {
        _fallback();
    }

// ---- reachable (internal) [internal]: ERC1967Proxy._fallback()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/Proxy.sol:58-61
function _fallback() internal virtual {
        _beforeFallback();
        _delegate(_implementation());
    }

// ---- reachable (internal) [internal]: ERC1967Proxy._implementation()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol:29-31
function _implementation() internal view virtual override returns (address impl) {
        return ERC1967Upgrade._getImplementation();
    }

// ---- reachable (internal) [internal]: ERC1967Proxy._beforeFallback()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/Proxy.sol:85-85
function _beforeFallback() internal virtual {}

// ---- reachable (internal) [internal]: ERC1967Proxy._delegate(address)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/Proxy.sol:22-45
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

// ---- reachable (internal) [internal]: ERC1967Proxy._getImplementation()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/ERC1967/ERC1967Upgrade.sol:32-34
function _getImplementation() internal view returns (address) {
        return StorageSlot.getAddressSlot(_IMPLEMENTATION_SLOT).value;
    }

// ---- reachable (external) [internal]: StorageSlot.getAddressSlot(bytes32)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/utils/StorageSlot.sol:62-67
function getAddressSlot(bytes32 slot) internal pure returns (AddressSlot storage r) {
        /// @solidity memory-safe-assembly
        assembly {
            r.slot := slot
        }
    }
