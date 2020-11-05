# === Open new order ===

import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from getStrategyIndex import getStrategyIndex
from sqlalchemy import create_engine

from config import Config


def openOrder(cryptoAddress, strategyID, symbol, direction, orderType, price, volume,
              timeInForce, market='binance_futures', attribute='NEW', positionID=None):

    # === Check Strategy ===
    # Get traderID
    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)

    trader_ds = pd.read_sql_query('SELECT * FROM traders WHERE cryptoAddress="'+str(cryptoAddress)+'"', con=engine)

    if len(trader_ds) == 1:
        traderID = trader_ds['traderID'][0]

        # Find strategy index
        strategyIndex = getStrategyIndex(traderID, strategyID)

        if strategyIndex != None:

            # Check if the margin level do not exceed account balance
            strategy_ds = pd.read_sql_query('SELECT * FROM strategies WHERE strategyID='+str(strategyIndex)+'', con=engine)
            account_ds = pd.read_sql_query('SELECT * FROM accounts WHERE strategyID='+str(strategyIndex)+' ORDER BY timestamp DESC LIMIT 1', con=engine)
            positions_ds = pd.read_sql_query('SELECT * FROM positions WHERE strategyID='+str(strategyIndex)+' ORDER BY timestamp DESC LIMIT 1', con=engine)

            requiredMargin = (price*volume)/strategy_ds['leverage'][0]

            # Define if there an open position and it's semi-directioness to order direction
            if len(positions_ds) != 0 and positions_ds['status'][0] == 1: # FOR SAME STRATEGY MAY BE OPENED SEVERAL POSITIONS! NOTICE IT IN THE FUTURE!!
                if direction == 'BUY': orderDirection = 'LONG'
                else: orderDirection = 'SHORT'

                if positions_ds['direction'][0] != orderDirection:

                    fullBalance = account_ds['endDayBalance'][0]+account_ds['onMargin'][0]

                else: fullBalance = account_ds['endDayBalance'][0]

            else: fullBalance = account_ds['endDayBalance'][0]

            if requiredMargin <= fullBalance:

                # Define new-order-dictionary
                newOrderDictionary = {
                    'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                    'strategyID': strategyIndex,
                    'market': market,
                    'symbol': symbol.upper(),
                    'orderID': str(uuid.uuid4()),
                    'direction': direction.upper(),
                    'orderType': orderType.upper(),
                    'price': price,
                    'volume': volume,
                    'timeInForce': timeInForce.upper(),
                    'status': 'OPEN',
                    'attribute': attribute.upper(),
                    'positionID': positionID

                }

                newOrder_ds = pd.DataFrame(newOrderDictionary, index=[0])
                newOrder_ds.to_sql('orders', con=engine, if_exists='append', index=False)

                newOrderJson = json.dumps(newOrderDictionary)

                return newOrderJson

            else: return json.dumps({'e':'It is impossible to place order. Insufficient funds.'})

        else: return json.dumps({'e':'There is no such strategy. Please register it first.'})

    else: return json.dumps({'e':'There is no such cryptowallet. Please register it first.'})
