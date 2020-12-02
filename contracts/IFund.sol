pragma solidity ^0.6.10;

interface IFund {

    event ezbPriceDiscover(uint timestamp, uint ezbFairPrice);
    event settlementDiscovered(uint timestamp, uint FP, uint settlementAmountDAI);

    function requestSettlementBalance() external returns(uint);
    function getDistributionTimePeriods() external view returns(uint[] memory);
    function getLastEZBprice() external view returns(uint);

}
