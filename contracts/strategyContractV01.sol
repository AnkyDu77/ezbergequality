pragma solidity ^0.6.10;

import "https://github.com/Uniswap/uniswap-v2-periphery/blob/master/contracts/interfaces/IUniswapV2Router02.sol";
import "https://github.com/Uniswap/uniswap-v2-core/blob/master/contracts/interfaces/IUniswapV2Factory.sol";
import "https://github.com/Uniswap/uniswap-v2-core/blob/master/contracts/interfaces/IUniswapV2Pair.sol";
import "https://github.com/Uniswap/uniswap-lib/blob/master/contracts/libraries/FixedPoint.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v3.0.0/contracts/token/ERC20/ERC20.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v3.0.0/contracts/math/SafeMath.sol";
import "./ownable.sol";
import "./tradeble.sol";
import "./IFund.sol";

contract uniETFv01 is Ownable, Tradeble{

    using SafeMath for uint;
    using SafeMath for uint112;

    address internal constant UNISWAP_ROUTER_ADDRESS = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address internal constant UNISWAP_FACTORY_ADDRESS = 0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f;

    IUniswapV2Router02 private uniswapRouter;
    IUniswapV2Factory private uniswapFactory;
    IUniswapV2Pair private uniswapPair;

    address private daiRopsten = 0xaD6D458402F60fD3Bd25163575031ACDce07538D;
    address private ezbShareFund;

    mapping (string => address) private uniAssets;
    mapping (address => string) private uniAssetsNames;
    address[] private assetAddresses;

    uint fairPrice;
    uint totalPositionsValue;

    event fairPriceDiscovered(uint timestamp, uint FP);
    event positionsValueDiscovered(uint timestamp, uint PV);
    event pvDiscovered(uint timestamp, string AN, uint PV);


    constructor() public {
    uniswapRouter = IUniswapV2Router02(UNISWAP_ROUTER_ADDRESS);
    uniswapFactory = IUniswapV2Factory(UNISWAP_FACTORY_ADDRESS);

    }


    function buyAsset(string memory assetName, uint balanceShare, uint minAmount, uint deadline) public onlyTrader {
        // require(msg.sender == trader, "EZBERG_ERROR: You are not an allowed trader!");
        // Get path

        if (uniAssets[assetName] == uniswapRouter.WETH()) {
            address[] memory path = new address[](2);
            path[0] = daiRopsten;
            path[1] = uniswapRouter.WETH();

            uint daiBalance = ERC20(daiRopsten).balanceOf(address(this));
            require(daiBalance > 0, "EZBERG_ERROR: DAI_BALANCE_IS_EMPTY");
            uint daiShare = daiBalance.div(balanceShare);

            ERC20(daiRopsten).approve(UNISWAP_ROUTER_ADDRESS, daiShare);

            uniswapRouter.swapExactTokensForTokens(daiShare, minAmount, path, address(this), deadline);

        } else {

            address[] memory path = new address[](3);
            path[0] = daiRopsten;
            path[1] = uniswapRouter.WETH();
            path[2] = uniAssets[assetName];

            uint daiBalance = ERC20(daiRopsten).balanceOf(address(this));
            require(daiBalance > 0, "EZBERG_ERROR: DAI_BALANCE_IS_EMPTY");
            uint daiShare = daiBalance.div(balanceShare);

            ERC20(daiRopsten).approve(UNISWAP_ROUTER_ADDRESS, daiShare);

            uniswapRouter.swapExactTokensForTokens(daiShare, minAmount, path, address(this), deadline);
        }

  }


    function sellAsset(string memory assetName, uint balanceShare, uint minAmount, uint deadline) public onlyTrader {
        // require(msg.sender == trader, "EZBERG_ERROR: You are not an allowed trader!");
        // Get path

        if (uniAssets[assetName] == uniswapRouter.WETH()) {
            address[] memory path = new address[](2);
            path[0] = uniswapRouter.WETH();
            path[1] = daiRopsten;

            uint assetBalance = ERC20(path[0]).balanceOf(address(this));
            require(assetBalance > 0, "EZBERG_ERROR: DAI_BALANCE_IS_EMPTY");
            uint assetShare = assetBalance.div(balanceShare);

            ERC20(path[0]).approve(UNISWAP_ROUTER_ADDRESS, assetShare);

            uniswapRouter.swapExactTokensForTokens(assetShare, minAmount, path, address(this), deadline);

        } else {

            address[] memory path = new address[](3);
            path[0] = uniAssets[assetName];
            path[1] = uniswapRouter.WETH();
            path[2] = daiRopsten;

            uint assetBalance = ERC20(path[0]).balanceOf(address(this));
            require(assetBalance > 0, "EZBERG_ERROR: DAI_BALANCE_IS_EMPTY");
            uint assetShare = assetBalance.div(balanceShare);

            ERC20(path[0]).approve(UNISWAP_ROUTER_ADDRESS, assetShare);

            uniswapRouter.swapExactTokensForTokens(assetShare, minAmount, path, address(this), deadline);

        }

    }




     // ======== ======== ======== ========

    function getFairPrice(address assetAddress) private returns(uint) {

        // Warning!!! We are using reserves method to calculate asset price instead of Oracle method in MVP. It is not safe!
        // In later versions there is going Oracle method to be used.

        address marketAddress = uniswapFactory.getPair(daiRopsten,assetAddress);

        // require(marketAddress != address(0), "EZBERG_ERROR: There is no such market");

        if (marketAddress == address(0)) {
            uint112 ethReserve;
            uint256 tokenReserve;
            uint256 daiReserve;


            address EthTokenMarket = uniswapFactory.getPair(uniswapRouter.WETH(),assetAddress);
            (uint112 reserve0Token, uint112 reserve1Token, ) = IUniswapV2Pair(EthTokenMarket).getReserves();

            address ethInPair = IUniswapV2Pair(EthTokenMarket).token0();
            if (ethInPair == uniswapRouter.WETH()) {
                ethReserve = reserve0Token;
                tokenReserve = uint256(reserve1Token).mul(1000);// to increase calculation precision
            } else {
                ethReserve = reserve1Token;
                tokenReserve = uint256(reserve0Token).mul(1000);
            }

            // Get token price in WETH
            uint ethToken = tokenReserve.div(uint256(ethReserve));

            // Get weth price in dai
            address DaiEthMarket = uniswapFactory.getPair(uniswapRouter.WETH(),daiRopsten);
            (reserve0Token, reserve1Token, ) = IUniswapV2Pair(DaiEthMarket).getReserves();

            ethInPair = IUniswapV2Pair(DaiEthMarket).token0();
            if (ethInPair == uniswapRouter.WETH()) {
                ethReserve = reserve0Token;
                daiReserve = uint256(reserve1Token).mul(10000000);// increasing dai/token precision to 4 decimals
            } else {
                ethReserve = reserve1Token;
                daiReserve = uint256(reserve0Token).mul(10000000);
            }

            uint ethDai = daiReserve.div(uint256(ethReserve));

            // Finally, get token price in Dai
            fairPrice = ethDai.div(ethToken); // ethToken == 1, cause we have no floating point here!!!


        } else {

            uint256 tokenReserve;
            uint256 daiReserve;

            (uint112 reserve0Token, uint112 reserve1Token, ) = IUniswapV2Pair(marketAddress).getReserves();
            address daiInPair = IUniswapV2Pair(marketAddress).token0();

            if (daiInPair == daiRopsten) {

                daiReserve = uint256(reserve0Token).mul(10000000);
                tokenReserve = uint256(reserve1Token).mul(1000);

            } else {
                daiReserve = uint256(reserve1Token).mul(10000000);
                tokenReserve = uint256(reserve0Token).mul(1000);

            }

            fairPrice = daiReserve.div(tokenReserve);
        }

        emit fairPriceDiscovered(now, fairPrice);
        return fairPrice;

    }


    function getPositionsValue() external returns(uint) {
        totalPositionsValue = 0;
        for (uint i = 0; i < assetAddresses.length; i++) {
            uint positionValue = (getFairPrice(assetAddresses[i]).mul(ERC20(assetAddresses[i]).balanceOf(address(this)))).div(10000); // div by 10000 is for get back to normal dai amount
            totalPositionsValue = totalPositionsValue.add(positionValue);
        }

        emit positionsValueDiscovered(now, totalPositionsValue);
        return totalPositionsValue;
    }


    function getParticularPositionsValue(string calldata assetName) external onlyTrader returns(uint)  {

        address asset = uniAssets[assetName];
        uint positionValue = getFairPrice(asset).mul(ERC20(asset).balanceOf(address(this)));

        emit pvDiscovered(now,assetName,positionValue);
        return positionValue;

    }


    function getLastFairPrice() external view onlyTrader returns(uint) {
        return fairPrice;
    }


    function getLastTotalPositionsValue() external view returns(uint) {
        return totalPositionsValue;
    }

    function getLastAssetAddresses() external view returns(address[] memory) {
        return assetAddresses;
    }


    function allowSettlement() public onlyOwner {

        uint settlementBalance = IFund(ezbShareFund).requestSettlementBalance();
        ERC20(daiRopsten).approve(ezbShareFund, settlementBalance);
    }


    function setNewUniAsset(string memory assetName, address assetAddress) public onlyOwner{
      uniAssets[assetName] = assetAddress;
      uniAssetsNames[assetAddress] = assetName;
      assetAddresses.push(assetAddress);

    }

    function setShareFundAddress(address currentShareFund) public onlyOwner {
        ezbShareFund = currentShareFund;
    }


    function countAssets() external view returns(uint){
        return assetAddresses.length;
    }

    function withdrawDai() public onlyOwner {
        ERC20(daiRopsten).transfer(owner(), ERC20(daiRopsten).balanceOf(address(this)));
    }

    function getAssetByName(string calldata assetName) external view returns(address) {
        address asset = uniAssets[assetName];
        return asset;

    }

    function getAssetNameByAddress(address assetAddress) external view returns(string memory) {
        string memory name = uniAssetsNames[assetAddress];
        return name;
    }


    receive() payable external {}


}
