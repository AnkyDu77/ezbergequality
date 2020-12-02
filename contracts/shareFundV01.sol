pragma solidity ^0.6.10;

import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v3.0.0/contracts/token/ERC20/ERC20Burnable.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v3.0.0/contracts/token/ERC20/ERC20.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v3.0.0/contracts/math/SafeMath.sol";

import "./ownable.sol";
import "./IStrategies.sol";



contract SharedFundV01 is ERC20Burnable, Ownable {

    // 1. It should get stebleCoin, pay contract's ERC20 and send SC to different accounts first.
    // 2. Then it should be able to send this coins back to accounts mentioned above and get stable coins back.
    // 3. Afterall, contract should withdraw the initial stableCoins in exchange for contract's ERC20 and burn contract's ERC20

    using SafeMath for uint;

    // address internal constant daiAddress = 0x6B175474E89094C44Da98b954EedeAC495271d0F; MAINNET
    address private daiAddress = 0xaD6D458402F60fD3Bd25163575031ACDce07538D; // ROPSTEN TESTNET

    uint256 private fairPrice;
    uint256 private shareDivider = 10; // Defines how much DAI is in 1 EZB
    uint256 private fromParttoWholeDevider = 1000000000000000000;
    uint256 private poolTokenAmount;
    uint256 private scBalance;
    uint256 private settlementTotalVolume;

    uint256 private startParticipationTime = now;
    uint256 private participationTimePeriod = 900;
    uint256 private endParticipationTime = startParticipationTime.add(participationTimePeriod);
    // uint256 private nextParticipationStart = 7200;

    uint256 private startShareTime = endParticipationTime;
    uint256 private distributionTimePeriod = 900; // 86400; // a day
    uint256 private endShareTime = startShareTime.add(distributionTimePeriod);
    // uint256 private nextDistributionStart = 6300; //604800; // a week

    uint256 private tradingTime = 1800;

    uint256 private startSettlementApplyingTime = endShareTime.add(tradingTime); // half hour (1800 sec) of trading
    uint256 private settlementApplyingTimePeriod = 900;
    uint256 private endSettlementApplyingTime = startSettlementApplyingTime.add(settlementApplyingTimePeriod);

    uint256 private startSettlementTime = endSettlementApplyingTime; //.add(518400);
    uint256 private settlementTimePeriod = 1800; //86400; // a day
    uint256 private endSettlementTime = startSettlementTime.add(settlementTimePeriod);
    // uint256 private nextSettlementStart = 600;//518400; // 6 days

    uint256 private withdrawStart = endSettlementTime;
    uint256 private withdrawalTimePeriod = 900;
    uint256 private withdrawEnd = withdrawStart.add(withdrawalTimePeriod);

    uint256 private startClearingTime = withdrawEnd;
    uint256 private clearingTimePeriod = 900;
    uint256 private endClearingTime = startClearingTime.add(clearingTimePeriod);

    // Maybe we should start next startParticipationTime with claering time ending...

    uint256 private totalComissions = 0;
    uint256 private feePercent = 200; // Equals to 0.5% by default

    address[] internal strategies;
    address[] internal usersToSettle;

    mapping (address => uint) public strategyFundShare;
    mapping (address => uint) internal settlementAmount;

    event ezbPriceDiscover(uint timestamp, uint ezbFairPrice);
    event settlementDiscovered(uint timestamp, uint FP, uint settlementAmountDAI);


    constructor () public ERC20('EzbergSharedPoolV1', 'EZBmvp_i') {
    }


    function participate() public {
        // require(startParticipationTime < now && now < endParticipationTime, "EZBERG_ERROR: IT IS NOT PARTICIPATION TIME");

        uint userBalance = ERC20(daiAddress).allowance(msg.sender, address(this));
        require(userBalance > 0, "EZBERG_ERROR: There are no DAI were allowed for transaction");
        ERC20(daiAddress).transferFrom(msg.sender, address(this), userBalance);

        uint usersCommisions = userBalance.div(feePercent); // Get 0.5% of user balance as a comissions
        totalComissions = totalComissions.add(usersCommisions);
        userBalance = userBalance.sub(usersCommisions);

        _mint(msg.sender, userBalance.div(shareDivider));

    }


    function sendSCtoTrade() public onlyOwner {
        // require(startShareTime < now && now < endShareTime, "EZBERG_ERROR: IT IS NOT DISTRIBUTION TIME");
        require(strategies.length > 0, "EZBERG_ERROR: THERE IS NO STRATEGIES ADDRESSES");

        uint tradebleDAIamount = (ERC20(daiAddress).balanceOf(address(this))).sub(totalComissions);

        for (uint i=0; i < strategies.length; i++) {

            if (tradebleDAIamount > 0) {
            // Got a logical warring here. Comming strategies will get smaller share of assets if do not
            // integrate it in mapping logic!!!!

                uint assetShare = tradebleDAIamount.div(strategyFundShare[strategies[i]]);
                tradebleDAIamount = tradebleDAIamount.sub(assetShare);
                ERC20(daiAddress).transfer(strategies[i], assetShare);
            }
        }

    }


    function transfer(address to, uint tokens) public override returns (bool success) {
        // Specifying transfer behavior for sending EZB back to the initial contract
        if (to == address(this)) {
            // require(startSettlementApplyingTime < now && now < endSettlementApplyingTime, "EZBERG_ERROR: IT IS NOT SETTLEMENT APPLYING PERIOD");

            _transfer(_msgSender(), to, tokens); // transfer tokens

            // Is user in usersToSettle array already?
            bool flag = false;
            for (uint i=0; i < usersToSettle.length; i++) {
                if (msg.sender == usersToSettle[i]) {
                    settlementAmount[usersToSettle[i]] = settlementAmount[usersToSettle[i]].add(tokens);
                    flag = true;
                    settlementTotalVolume = settlementTotalVolume.add(tokens);
                }
            }

            if (flag == false) {
                usersToSettle.push(msg.sender);
                settlementAmount[msg.sender] = tokens;
                settlementTotalVolume = settlementTotalVolume.add(tokens);
            }

            return true;

        } else {
            _transfer(_msgSender(), to, tokens); // transfer tokens
            return true;

        }
    }


    function getEZBprice() private returns(uint) {

        // require now out of final settlement boundaries

        uint totalPositionsValue = 0;
        for (uint i=0; i<strategies.length; i++) {
            totalPositionsValue = totalPositionsValue.add(IStrategies(strategies[i]).getPositionsValue());
            totalPositionsValue = totalPositionsValue.add(ERC20(daiAddress).balanceOf(strategies[i]));
        }

        uint totalDAIinSystem = totalPositionsValue.add((ERC20(daiAddress).balanceOf(address(this))).sub(totalComissions));
        shareDivider = totalDAIinSystem.div(totalSupply());

        emit ezbPriceDiscover(now, shareDivider);

        return shareDivider;
    }


    // WARNING!!! Strict strategies request order required!!!!!
    function requestSettlementBalance() external returns(uint) {
        // require(startSettlementTime < now && now < endSettlementTime , "EZBERG_ERROR: IT IS NOT A SETLLEMENT PERIOD");

        // Only strategies contracts are allowed
        bool flag = false;
        for (uint i=0; i < strategies.length; i++) {
            if (msg.sender == strategies[i]) {
                flag = true;
            }
        }
        // require(flag == true, "EZBERG_ERROR: msg sender is not a strategy contract");
        if (flag == true) {
        // Get current ezb price
        shareDivider = getEZBprice();

        uint strategySettlementBalanceEZB = balanceOf(address(this)).div(strategyFundShare[msg.sender]); // SECURITY ISSUE!!! If strategies will require settlement in order differ from initial order there will be balances missmach!!!!
        uint strategySettlementBalanceDAI = strategySettlementBalanceEZB.mul(shareDivider);

        emit settlementDiscovered(now, shareDivider, strategySettlementBalanceDAI);

        return strategySettlementBalanceDAI;


        } else{
            uint strategySettlementBalanceEZB = balanceOf(address(this)).div(1); // SECURITY ISSUE!!! If strategies will require settlement in order differ from initial order there will be balances missmach!!!!
            uint strategySettlementBalanceDAI = strategySettlementBalanceEZB.mul(shareDivider);

            emit settlementDiscovered(now, shareDivider, strategySettlementBalanceDAI);

            return strategySettlementBalanceDAI;
        }

    }



    function getSCBack() public onlyOwner {
        // require(startSettlementTime < now && now < endSettlementTime, "EZBERG_ERROR: IT IS NOT A SETTLEMENT PERIOD");

        // Get all stable coins balances to settle back
        for (uint j=0; j<strategies.length; j++) {
            uint balance = ERC20(daiAddress).allowance(strategies[j], address(this));
            ERC20(daiAddress).transferFrom(strategies[j], address(this), balance);
        }
    }



    function withdrawSC(uint256 withdrawAmount) public {
        // Get EZB back and Burn it, withdraw stable coins
        // require to hold sufficient amount of sc and to meet proper time period
        require(withdrawAmount > 0, "EZBERG_ERROR: Provide withdraw amount");
        // require(withdrawStart < now && now < withdrawEnd, "EZBERG_ERROR: IT IS NOT A WITHDRAWAL PERIOD");

        bool flag = false;
        for (uint i=0; i < usersToSettle.length; i++) {
            if (msg.sender == usersToSettle[i]) {
                flag = true;
                break;
            }
        }

        require(flag == true, "EZBERG_ERROR: Your address not in settlement list. Try to send EZB during another settlement period");

        // Get user's allowed to withdraw DAI balance
        uint userAllowedBalance = settlementAmount[msg.sender].mul(shareDivider);

        // Get users comissions
        uint usersCommisions = userAllowedBalance.div(feePercent);
        totalComissions = totalComissions.add(usersCommisions);
        userAllowedBalance = userAllowedBalance.sub(usersCommisions);

        // Check the funds allowence
        require(userAllowedBalance >= withdrawAmount, "Error: Withdraw amount exceeds the balance allowed to withdraw");
        require(withdrawAmount <= ERC20(daiAddress).balanceOf(address(this)), "Error: Construct's insufficient funds");

        // Decrease users settlement amount, withdraw stable coins and burn shared pool tokens
        uint withdrawAmountEZB = withdrawAmount.div(shareDivider);
        settlementAmount[msg.sender] = settlementAmount[msg.sender].sub(withdrawAmountEZB);
        ERC20(daiAddress).transfer(msg.sender, withdrawAmount);

        ERC20(address(this)).approve(msg.sender, withdrawAmountEZB);
        burnFrom(address(this), withdrawAmountEZB);

    }


    function withdrawComissions(uint withdrawAmount) public onlyOwner {

        require(withdrawAmount <= totalComissions, "Withdrawal amount exceeds the total comissions amount");
        require(withdrawAmount > 0, "Provide withdraw amount");
        totalComissions = totalComissions.sub(withdrawAmount);
        ERC20(daiAddress).transfer(owner(), withdrawAmount);

    }


    function withdrawAllComissions() public onlyOwner {
        ERC20(daiAddress).transfer(owner(), totalComissions);
    }


    function clearing() public onlyOwner {
        // require(startClearingTime < now && now < endClearingTime, "EZBERG_ERROR: IT IS NOT A CLEARING PERIOD");

        if (totalSupply() == 0) {
            shareDivider = 10;
            delete usersToSettle;
        } else {
            shareDivider = getEZBprice();

            for (uint i=0; i < usersToSettle.length; i++) {

                if (settlementAmount[usersToSettle[i]] > 0) {
                ERC20(address(this)).approve(msg.sender, settlementAmount[usersToSettle[i]]);
                transferFrom(address(this), usersToSettle[i], settlementAmount[usersToSettle[i]]);
                settlementAmount[usersToSettle[i]] = 0;
                }
            }
            delete usersToSettle;
        }

        // Open new participation period
        setTimePeriods(now, 900, 900, 1800, 900, 1800, 900, 900);
    }


    function changeStrategyShare(address strategyAddress, uint shareDiv) public onlyOwner {
        strategyFundShare[strategyAddress] = shareDiv;

    }


    function setTimePeriods(uint startParticipation, uint partTP, uint distrTP, uint trTime, uint settleAplP, uint settleTP, uint withdrawTP, uint clearTP) private {
        require(startParticipation >= 0, "EZBERG_ERROR: strart prticipation time have to be more or equal to zero");

         if (startParticipation == 0) {
            startParticipationTime = now;
         } else {
            startParticipationTime = startParticipation;
         }

         participationTimePeriod = partTP;
         endParticipationTime = startParticipationTime.add(participationTimePeriod);

         startShareTime = endParticipationTime;
         distributionTimePeriod = distrTP;
         endShareTime = startShareTime.add(distributionTimePeriod);

         tradingTime = trTime;

         startSettlementApplyingTime = endShareTime.add(tradingTime);
         settlementApplyingTimePeriod = settleAplP;
         endSettlementApplyingTime = startSettlementApplyingTime.add(settlementApplyingTimePeriod);

         startSettlementTime = endSettlementApplyingTime;
         settlementTimePeriod = settleTP;
         endSettlementTime = startSettlementTime.add(settlementTimePeriod);

         withdrawStart = endSettlementTime;
         withdrawalTimePeriod = withdrawTP;
         withdrawEnd = withdrawStart.add(withdrawalTimePeriod);

         startClearingTime = withdrawEnd;
         clearingTimePeriod = clearTP;
         endClearingTime = startClearingTime.add(clearingTimePeriod);

    }


    function setTimePeriodsByOwner(uint startParticipation, uint partTP, uint distrTP, uint trTime, uint settleAplP, uint settleTP, uint withdrawTP, uint clearTP) public onlyOwner {
        require(startParticipation >= 0, "EZBERG_ERROR: strart prticipation time have to be more or equal to zero");

         if (startParticipation == 0) {
            startParticipationTime = now;
         } else {
            startParticipationTime = startParticipation;
         }

         participationTimePeriod = partTP;
         endParticipationTime = startParticipationTime.add(participationTimePeriod);

         startShareTime = endParticipationTime;
         distributionTimePeriod = distrTP;
         endShareTime = startShareTime.add(distributionTimePeriod);

         tradingTime = trTime;

         startSettlementApplyingTime = endShareTime.add(tradingTime);
         settlementApplyingTimePeriod = settleAplP;
         endSettlementApplyingTime = startSettlementApplyingTime.add(settlementApplyingTimePeriod);

         startSettlementTime = endSettlementApplyingTime;
         settlementTimePeriod = settleTP;
         endSettlementTime = startSettlementTime.add(settlementTimePeriod);

         withdrawStart = endSettlementTime;
         withdrawalTimePeriod = withdrawTP;
         withdrawEnd = withdrawStart.add(withdrawalTimePeriod);

         startClearingTime = withdrawEnd;
         clearingTimePeriod = clearTP;
         endClearingTime = startClearingTime.add(clearingTimePeriod);

    }


    function setStrategy(address strategyAddress, uint shareDiv) public onlyOwner {
        strategies.push(strategyAddress);
        strategyFundShare[strategyAddress] = shareDiv;
    }


    function getDistributionTimePeriods() external view returns(uint[] memory) {
        uint[] memory timestamps = new uint[](3);
        timestamps[0] = startParticipationTime;
        timestamps[1] = tradingTime;
        timestamps[2] = endClearingTime;

        return timestamps;
    }


    function getSettleAmount(address userAddress) external view onlyOwner returns(uint)  {
        return settlementAmount[userAddress];
    }


    function getTotalSettlementVolume() external view onlyOwner returns(uint) {
        return settlementTotalVolume;
    }

    function getTotalComissions() external view returns(uint) {
        return totalComissions;
    }


    function getSettlementAddresses() external view returns(address[] memory) {
        return usersToSettle;
    }


    function getLastEZBprice() external view returns(uint) {
        return shareDivider;
    }

}
