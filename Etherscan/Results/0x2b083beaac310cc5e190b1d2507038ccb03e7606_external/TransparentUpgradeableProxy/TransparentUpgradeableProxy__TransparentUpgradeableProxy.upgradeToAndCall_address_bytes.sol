// entry (external): TransparentUpgradeableProxy.upgradeToAndCall(address,bytes)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/contracts/Upgradeable/TransparentUpgradeableProxy.sol:102-104
function upgradeToAndCall(address newImplementation, bytes calldata data) external payable ifAdmin {
        _upgradeToAndCall(newImplementation, data, true);
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._upgradeToAndCall(address,bytes,bool)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/ERC1967/ERC1967Upgrade.sol:59-64
function _upgradeToAndCall(address newImplementation, bytes memory data, bool forceCall) internal {
        _upgradeTo(newImplementation);
        if (data.length > 0 || forceCall) {
            Address.functionDelegateCall(newImplementation, data);
        }
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy.ifAdmin()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/contracts/Upgradeable/TransparentUpgradeableProxy.sol:41-47
modifier ifAdmin() {
        if (msg.sender == _getAdmin()) {
            _;
        } else {
            _fallback();
        }
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._getAdmin()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/ERC1967/ERC1967Upgrade.sol:97-99
function _getAdmin() internal view returns (address) {
        return StorageSlot.getAddressSlot(_ADMIN_SLOT).value;
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._fallback()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/Proxy.sol:58-61
function _fallback() internal virtual {
        _beforeFallback();
        _delegate(_implementation());
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._implementation()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol:29-31
function _implementation() internal view virtual override returns (address impl) {
        return ERC1967Upgrade._getImplementation();
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._delegate(address)
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

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._beforeFallback()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/contracts/Upgradeable/TransparentUpgradeableProxy.sol:116-119
function _beforeFallback() internal virtual override {
        require(msg.sender != _getAdmin(), "TransparentUpgradeableProxy: admin cannot fallback to proxy target");
        super._beforeFallback();
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._beforeFallback()
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/Proxy.sol:85-85
function _beforeFallback() internal virtual {}

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._getImplementation()
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

// ---- reachable (external) [internal]: Address.functionDelegateCall(address,bytes)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/utils/Address.sol:170-172
function functionDelegateCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionDelegateCall(target, data, "Address: low-level delegate call failed");
    }

// ---- reachable (internal) [internal]: TransparentUpgradeableProxy._upgradeTo(address)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/ERC1967/ERC1967Upgrade.sol:49-52
function _upgradeTo(address newImplementation) internal {
        _setImplementation(newImplementation);
        emit Upgraded(newImplementation);
    }

// ---- reachable (internal) [private]: TransparentUpgradeableProxy._setImplementation(address)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/proxy/ERC1967/ERC1967Upgrade.sol:39-42
function _setImplementation(address newImplementation) private {
        require(Address.isContract(newImplementation), "ERC1967: new implementation is not a contract");
        StorageSlot.getAddressSlot(_IMPLEMENTATION_SLOT).value = newImplementation;
    }

// ---- reachable (external) [internal]: Address.isContract(address)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/utils/Address.sol:40-46
function isContract(address account) internal view returns (bool) {
        // This method relies on extcodesize/address.code.length, which returns 0
        // for contracts in construction, since the code is only stored at the end
        // of the constructor execution.

        return account.code.length > 0;
    }

// ---- reachable (internal) [internal]: Address.functionDelegateCall(address,bytes,string)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/utils/Address.sol:180-187
function functionDelegateCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        (bool success, bytes memory returndata) = target.delegatecall(data);
        return verifyCallResultFromTarget(target, success, returndata, errorMessage);
    }

// ---- reachable (internal) [internal]: Address.verifyCallResultFromTarget(address,bool,bytes,string)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/utils/Address.sol:195-211
function verifyCallResultFromTarget(
        address target,
        bool success,
        bytes memory returndata,
        string memory errorMessage
    ) internal view returns (bytes memory) {
        if (success) {
            if (returndata.length == 0) {
                // only check isContract if the call was successful and the return data is empty
                // otherwise we already know that it was a contract
                require(isContract(target), "Address: call to non-contract");
            }
            return returndata;
        } else {
            _revert(returndata, errorMessage);
        }
    }

// ---- reachable (internal) [private]: Address._revert(bytes,string)
// source: Etherscan/SourceCode/0x2b083beaac310cc5e190b1d2507038ccb03e7606/@openzeppelin/contracts/utils/Address.sol:231-243
function _revert(bytes memory returndata, string memory errorMessage) private pure {
        // Look for revert reason and bubble it up if present
        if (returndata.length > 0) {
            // The easiest way to bubble the revert reason is using memory via assembly
            /// @solidity memory-safe-assembly
            assembly {
                let returndata_size := mload(returndata)
                revert(add(32, returndata), returndata_size)
            }
        } else {
            revert(errorMessage);
        }
    }
