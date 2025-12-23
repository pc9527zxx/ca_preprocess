// entry (external): CvxRewardDistributor.claimCvgCvxSimple(address,uint256,ICommonStruct.TokenAmount[],uint256,bool)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/contracts/Staking/Convex/CvxRewardDistributor.sol:89-98
function claimCvgCvxSimple(
        address receiver,
        uint256 totalCvgClaimable,
        ICommonStruct.TokenAmount[] memory totalCvxRewardsClaimable,
        uint256 minCvgCvxAmountOut,
        bool isConvert
    ) external {
        require(cvgControlTower.isStakingContract(msg.sender), "NOT_STAKING");
        _withdrawRewards(receiver, totalCvgClaimable, totalCvxRewardsClaimable, minCvgCvxAmountOut, isConvert);
    }

// ---- reachable (internal) [internal]: CvxRewardDistributor._withdrawRewards(address,uint256,ICommonStruct.TokenAmount[],uint256,bool)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/contracts/Staking/Convex/CvxRewardDistributor.sol:203-240
function _withdrawRewards(
        address receiver,
        uint256 totalCvgClaimable,
        ICommonStruct.TokenAmount[] memory totalCvxRewardsClaimable,
        uint256 minCvgCvxAmountOut,
        bool isConvert
    ) internal {
        /// @dev Mints accumulated CVG and claim Convex rewards
        if (totalCvgClaimable > 0) {
            CVG.mintStaking(receiver, totalCvgClaimable);
        }

        for (uint256 i; i < totalCvxRewardsClaimable.length; ) {
            uint256 rewardAmount = totalCvxRewardsClaimable[i].amount;

            if (rewardAmount > 0) {
                /// @dev If the token is CVX & we want to convert it in cvgCVX
                if (isConvert && totalCvxRewardsClaimable[i].token == CVX) {
                    if (minCvgCvxAmountOut == 0) {
                        /// @dev Mint cvgCVX 1:1 via cvgCVX contract
                        cvgCVX.mint(receiver, rewardAmount, false);
                    }
                    /// @dev Else it's a swap
                    else {
                        cvx1.mint(address(this), rewardAmount);
                        poolCvgCvxCvx1.exchange(0, 1, rewardAmount, minCvgCvxAmountOut, receiver);
                    }
                }
                /// @dev Else transfer the ERC20 to the receiver
                else {
                    totalCvxRewardsClaimable[i].token.safeTransfer(receiver, rewardAmount);
                }
            }
            unchecked {
                ++i;
            }
        }
    }

// ---- reachable (external) [internal]: SafeERC20.safeTransfer(IERC20,address,uint256)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol:26-28
function safeTransfer(IERC20 token, address to, uint256 value) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transfer.selector, to, value));
    }

// ---- reachable (internal) [private]: SafeERC20._callOptionalReturn(IERC20,bytes)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol:117-124
function _callOptionalReturn(IERC20 token, bytes memory data) private {
        // We need to perform a low level call here, to bypass Solidity's return data size checking mechanism, since
        // we're implementing it ourselves. We use {Address-functionCall} to perform this call, which verifies that
        // the target address contains contract code and also asserts for success in the low-level call.

        bytes memory returndata = address(token).functionCall(data, "SafeERC20: low-level call failed");
        require(returndata.length == 0 || abi.decode(returndata, (bool)), "SafeERC20: ERC20 operation did not succeed");
    }

// ---- reachable (external) [internal]: Address.functionCall(address,bytes,string)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts/utils/Address.sol:99-105
function functionCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, 0, errorMessage);
    }

// ---- reachable (internal) [internal]: Address.functionCallWithValue(address,bytes,uint256,string)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts/utils/Address.sol:128-137
function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(address(this).balance >= value, "Address: insufficient balance for call");
        (bool success, bytes memory returndata) = target.call{value: value}(data);
        return verifyCallResultFromTarget(target, success, returndata, errorMessage);
    }

// ---- reachable (internal) [internal]: Address.verifyCallResultFromTarget(address,bool,bytes,string)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts/utils/Address.sol:195-211
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
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts/utils/Address.sol:231-243
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

// ---- reachable (internal) [internal]: Address.isContract(address)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/@openzeppelin/contracts/utils/Address.sol:40-46
function isContract(address account) internal view returns (bool) {
        // This method relies on extcodesize/address.code.length, which returns 0
        // for contracts in construction, since the code is only stored at the end
        // of the constructor execution.

        return account.code.length > 0;
    }
