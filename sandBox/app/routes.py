from flask import render_template
from app import app

from traderRegistration import traderRegistration
from strategyRegistration import strategyRegistration
from openOrder import openOrder
from getAllOrders import getAllOrders
from getOpenOrders import getOpenOrders
from cancelAllOrders import cancelAllOrders
from cancelOrder import cancelOrder


@app.route('/')
@app.route('/index')
def index():
    version = {'version': 0.01}
    return render_template('index.html', title='Home', version = version)


# Registrate new Trader
@app.route('/traderRegistration/cryptowallet=<string:cryptoAddress>&username=<string:nickname>', methods=['GET','POST'])
def traderReg(cryptoAddress, nickname='mysterious_stranger'):

    traderID = traderRegistration(cryptoAddress, nickname)
    return traderID


# Registrate new Strategy
@app.route('/strategyRegistration/cryptowallet=<string:cryptoAddress>&algoOpenness=<string:algoOpenness>&capitalCapacity=<string:capitalCapacity>&leverage=<int:leverage>&strategyName=<string:strategyName>', methods=['GET','POST'])
def strategyReg(cryptoAddress, algoOpenness, capitalCapacity, leverage,
                        strategyName = 'mysterious_strategy'):

    strategyID = strategyRegistration(cryptoAddress, algoOpenness, capitalCapacity, leverage,
                        strategyName)
    return strategyID


# Place new oreder
@app.route('/placeOrder/cryptowallet=<string:cryptoAddress>&strategyID=<string:strategyID>&symbol=<string:symbol>&direction=<string:direction>&orderType=<string:orderType>&price=<float:price>&volume=<float:volume>&timeInForce=<string:timeInForce>', methods=['GET', 'POST'])
def placeOrder(cryptoAddress, strategyID, symbol, direction, orderType, price, volume,
              timeInForce):

    orderInfo = openOrder(cryptoAddress, strategyID, symbol, direction, orderType, price, volume,
              timeInForce)
    return orderInfo

# Get all Strategy Orders
@app.route('/getOrders/cryptowallet=<string:cryptoAddress>&strategyID=<string:strategyID>', methods=['GET'])
def getOrders(cryptoAddress, strategyID):

    orders = getAllOrders(cryptoAddress, strategyID)
    return orders


# Get open Strategy Orders
@app.route('/openOrders/cryptowallet=<string:cryptoAddress>&strategyID=<string:strategyID>', methods=['GET'])
def openOrders(cryptoAddress, strategyID):

    orders = getOpenOrders(cryptoAddress, strategyID)
    return orders

# Cancel all Open Strategy Orders
@app.route('/cancelOpenOrders/cryptowallet=<string:cryptoAddress>&strategyID=<string:strategyID>', methods=['GET', 'POST'])
def cnclAllOrders(cryptoAddress, strategyID):

    result = cancelAllOrders(cryptoAddress, strategyID)
    return result


# Cancel particular Strategy Order
@app.route('/cancelParticularOrder/cryptowallet=<string:cryptoAddress>&strategyID=<string:strategyID>&orderID=<string:orderID>', methods=['GET', 'POST'])
def cnclOrder(cryptoAddress, strategyID, orderID):

    result = cancelOrder(cryptoAddress, strategyID, orderID)
    return result
