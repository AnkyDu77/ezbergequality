pragma solidity ^0.6.10;

import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v3.0.0/contracts/token/ERC20/ERC20Capped.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v3.0.0/contracts/token/ERC20/ERC20.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v3.0.0/contracts/math/SafeMath.sol";

import "./ownable.sol";

contract EzbergFundingFirstRound is ERC20Capped, Ownable {

    uint256 private initialSupply = 1075000000000000000000000;
    uint256 private multiplyer = 200;

    constructor () public ERC20('EzbergEP', 'EZBi') ERC20Capped(initialSupply) {
    }

    fallback () external payable {
        uint256 value = uint256(msg.value).mul(multiplyer);
        ERC20._mint(msg.sender, value);
        payable(owner()).transfer(address(this).balance);
    }

    function getRemainingTokens() public view returns (uint256) {
        return cap().sub(totalSupply());
    }

}
