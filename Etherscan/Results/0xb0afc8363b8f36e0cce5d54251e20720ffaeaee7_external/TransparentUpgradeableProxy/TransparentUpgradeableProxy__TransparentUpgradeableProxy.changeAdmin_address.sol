// entry (external): TransparentUpgradeableProxy.changeAdmin(address)
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/contracts/Upgradeable/TransparentUpgradeableProxy.sol:82-84
function changeAdmin(address newAdmin) external virtual ifAdmin {
        _changeAdmin(newAdmin);
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._changeAdmin(address)
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/ERC1967/ERC1967Upgrade.sol:114-117
function _changeAdmin(address newAdmin) internal {
        emit AdminChanged(_getAdmin(), newAdmin);
        _setAdmin(newAdmin);
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy.ifAdmin()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/contracts/Upgradeable/TransparentUpgradeableProxy.sol:41-47
modifier ifAdmin() {
        if (msg.sender == _getAdmin()) {
            _;
        } else {
            _fallback();
        }
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._getAdmin()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/ERC1967/ERC1967Upgrade.sol:97-99
function _getAdmin() internal view returns (address) {
        return StorageSlot.getAddressSlot(_ADMIN_SLOT).value;
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._fallback()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/Proxy.sol:58-61
function _fallback() internal virtual {
        _beforeFallback();
        _delegate(_implementation());
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._implementation()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol:29-31
function _implementation() internal view virtual override returns (address impl) {
        return ERC1967Upgrade._getImplementation();
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._delegate(address)
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

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._beforeFallback()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/contracts/Upgradeable/TransparentUpgradeableProxy.sol:116-119
function _beforeFallback() internal virtual override {
        require(msg.sender != _getAdmin(), "TransparentUpgradeableProxy: admin cannot fallback to proxy target");
        super._beforeFallback();
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._beforeFallback()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/Proxy.sol:85-85
function _beforeFallback() internal virtual {}

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._getImplementation()
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/ERC1967/ERC1967Upgrade.sol:32-34
function _getImplementation() internal view returns (address) {
        return StorageSlot.getAddressSlot(_IMPLEMENTATION_SLOT).value;
    }

// ---- reachable (external) [internal]: StorageSlot.getAddressSlot(bytes32)
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/utils/StorageSlot.sol:62-67
function getAddressSlot(bytes32 slot) internal pure returns (AddressSlot storage r) {
        /// @solidity memory-safe-assembly
        assembly {
            r.slot := slot
        }
    }

// ---- reachable (internal) [private]: TransparentUpgradeableProxy._setAdmin(address)
// source: Etherscan/SourceCode/0xb0afc8363b8f36e0cce5d54251e20720ffaeaee7/@openzeppelin/contracts/proxy/ERC1967/ERC1967Upgrade.sol:104-107
function _setAdmin(address newAdmin) private {
        require(newAdmin != address(0), "ERC1967: new admin is the zero address");
        StorageSlot.getAddressSlot(_ADMIN_SLOT).value = newAdmin;
    }
