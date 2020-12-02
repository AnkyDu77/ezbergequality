pragma solidity ^0.6.10;

interface IStrategies {

    event fairPriceDiscovered(uint timestamp, uint FP);
    event positionsValueDiscovered(uint timestamp, uint PV);
    event pvDiscovered(uint timestamp, string AN, uint PV);

    function countAssets() external view returns(uint);
    function getAssetByName(string calldata assetName) external view returns(address);
    function getAssetNameByAddress(address assetAddress) external view returns(string memory);
    function getLastTotalPositionsValue() external view returns(uint);
    function getLastAssetAddresses() external view returns(address[] memory);
    function getPositionsValue() external returns(uint);

}
