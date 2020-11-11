# === Cancel particular order ===

import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from getStrategyIndex import getStrategyIndex
from sqlalchemy import create_engine

from config import Config


def cancelOrder(cryptoAddress, strategyID, orderID):
    # Get traderID
    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)
    trader_ds = pd.read_sql_query('SELECT * FROM traders WHERE \"cryptoAddress\"=\''+str(cryptoAddress)+'\'', con=engine)

    if len(trader_ds) == 1:
        traderID = trader_ds['traderID'][0]

        # Find target strategy index
        strategyIndex = getStrategyIndex(traderID, strategyID)

        if strategyIndex != None:
            # Find target orders
            sqlConnection = engine.connect()
            # Check if target order is open
            findOpenOrder = 'SELECT * FROM orders WHERE \"orderID\" = \''+str(orderID)+'\' AND status=\'OPEN\''
            order = sqlConnection.execute(findOpenOrder).fetchall()
            if len(order)==1:
                # Cancel target order
                cancelOrder = 'UPDATE orders SET status=\'CANCELED\' WHERE \"orderID\" = \''+str(orderID)+'\' AND status=\'OPEN\''
                sqlConnection.execute(cancelOrder)
                sqlConnection.close()

                return f'Order {orderID} is canceled successfully. Hooray!'

            else: return f'We got no order with id {orderID} or this order is already closed. Please, check your open orders.'

        # If we do not get target strategy
        else: return 'There is no such strategy. Please, register it first.'

    # If there is a mistake in cryptowallet address
    else: return 'There is no such cryptowallet. Please, register it first.'
