pragma solidity ^0.6.10;

/**
* @title Tradeble
* @dev The Tradeble contract has a trader address, and provides basic authorization control
* functions, this simplifies the implementation of "user permissions".
*/

import "./ownable.sol";

contract Tradeble is Ownable {
  address private _trader;

  event TradershipTransferred(
    address indexed previousTrder,
    address indexed newTrder
  );

  /**
  * @dev The Tradeble constructor sets the original `trader` of the contract to the particular
  * account.
  */
  constructor(address trader) internal {
    _trader = trader;
    emit TradershipTransferred(address(0), _trader);
  }

  /**
  * @return the address of the trader.
  */
  function trader() public view returns(address) {
    return _trader;
  }

  /**
  * @dev Throws if called by any account other than the trader.
  */
  modifier onlyTrader() {
    require(isTrader());
    _;
  }

  /**
  * @return true if `msg.sender` is the trader of the contract.
  */
  function isTrader() public view returns(bool) {
    return msg.sender == _trader;
  }

  /**
  * @dev Allows the current owner to relinquish control of the contract.
  * @notice Renouncing to tradership will leave the contract without a trader.
  * It will not be possible to call the functions with the `onlyTrader`
  * modifier anymore.
  */
  function renounceTradership() public onlyOwner {
    emit TradershipTransferred(_trader, address(0));
    _trader = address(0);
  }

  /**
  * @dev Allows the current owner to transfer control of the contract to a newTrader.
  * @param newTrader The address to transfer ownership to.
  */
  function transferTradership(address newTrader) public onlyOwner {
    _transferTradership(newTrader);
  }

  /**
  * @dev Transfers control of the contract to a newTrader.
  * @param newTrader The address to transfer ownership to.
  */
  function _transferTradership(address newTrader) internal {
    require(newTrader != address(0));
    emit TradershipTransferred(_trader, newTrader);
    _trader = newTrader;
  }
}
