// entry (external): CvxRewardDistributor.claimMultipleStaking(ICvxStakingPositionService[],address,uint256,bool,uint256)
// source: Etherscan/SourceCode/0x47c69e8c909ce626af73c955a5e34a20b7c71f19/contracts/Staking/Convex/CvxRewardDistributor.sol:110-193
function claimMultipleStaking(
        ICvxStakingPositionService[] calldata claimContracts,
        address _account,
        uint256 _minCvgCvxAmountOut,
        bool _isConvert,
        uint256 cvxRewardCount
    ) external {
        require(claimContracts.length != 0, "NO_STAKING_SELECTED");

        /// @dev To prevent an other user than position owner claims through swapping and grief the user rewards in cvgCVX
        if (_isConvert) {
            require(msg.sender == _account, "CANT_CONVERT_CVX_FOR_OTHER_USER");
        }
        /// @dev Accumulates amounts of CVG coming from different contracts.
        uint256 _totalCvgClaimable;

        /// @dev Array merging & accumulating rewards coming from different claims.
        ICommonStruct.TokenAmount[] memory _totalCvxClaimable = new ICommonStruct.TokenAmount[](cvxRewardCount);

        /// @dev Iterate over all staking service
        for (uint256 stakingIndex; stakingIndex < claimContracts.length; ) {
            ICvxStakingPositionService cvxStaking = claimContracts[stakingIndex];

            /** @dev Claims Cvg & Cvx
             *       Returns the amount of CVG claimed on the position.
             *       Returns the array of all CVX rewards claimed on the position.
             */
            (uint256 cvgClaimable, ICommonStruct.TokenAmount[] memory _cvxRewards) = cvxStaking.claimCvgCvxMultiple(
                _account
            );
            /// @dev increments the amount to mint at the end of function
            _totalCvgClaimable += cvgClaimable;

            uint256 cvxRewardsLength = _cvxRewards.length;
            /// @dev Iterate over all CVX rewards claimed on the iterated position
            for (uint256 positionRewardIndex; positionRewardIndex < cvxRewardsLength; ) {
                /// @dev Is the claimable amount is 0 on this token
                ///      We bypass the process to save gas
                if (_cvxRewards[positionRewardIndex].amount != 0) {
                    /// @dev Iterate over the final array to merge the iterated CvxRewards in the totalCVXClaimable
                    for (uint256 totalRewardIndex; totalRewardIndex < cvxRewardCount; ) {
                        address iteratedTotalClaimableToken = address(_totalCvxClaimable[totalRewardIndex].token);
                        /// @dev If the token is not already in the totalCVXClaimable.
                        if (iteratedTotalClaimableToken == address(0)) {
                            /// @dev Set token data in the totalClaimable array.
                            _totalCvxClaimable[totalRewardIndex] = ICommonStruct.TokenAmount({
                                token: _cvxRewards[positionRewardIndex].token,
                                amount: _cvxRewards[positionRewardIndex].amount
                            });

                            /// @dev Pass to the next token
                            break;
                        }

                        /// @dev If the token is already in the totalCVXClaimable.
                        if (iteratedTotalClaimableToken == address(_cvxRewards[positionRewardIndex].token)) {
                            /// @dev Increments the claimable amount.
                            _totalCvxClaimable[totalRewardIndex].amount += _cvxRewards[positionRewardIndex].amount;
                            /// @dev Pass to the next token
                            break;
                        }

                        /// @dev If the token is not found in the totalRewards and we are at the end of the array.
                        ///      it means the cvxRewardCount is not properly configured.
                        require(totalRewardIndex != cvxRewardCount - 1, "REWARD_COUNT_TOO_SMALL");

                        unchecked {
                            ++totalRewardIndex;
                        }
                    }
                }

                unchecked {
                    ++positionRewardIndex;
                }
            }

            unchecked {
                ++stakingIndex;
            }
        }

        _withdrawRewards(_account, _totalCvgClaimable, _totalCvxClaimable, _minCvgCvxAmountOut, _isConvert);
    }

// leaf targets (no body):
//   - (external) [abstract]: ICVX1.mint(address,uint256)
//   - (external) [abstract]: ICrvPoolPlain.exchange(int128,int128,uint256,uint256,address)
//   - (external) [abstract]: ICvg.mintStaking(address,uint256)
//   - (external) [abstract]: ICvgCVX.mint(address,uint256,bool)
//   - (external) [abstract]: ICvxStakingPositionService.claimCvgCvxMultiple(address)

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
