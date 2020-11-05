# === Cancel all orders ===

import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from getStrategyIndex import getStrategyIndex
from sqlalchemy import create_engine

from config import Config


def cancelAllOrders(cryptoAddress, strategyID):

    # Get traderID
    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)

    trader_ds = pd.read_sql_query('SELECT * FROM traders WHERE cryptoAddress="'+str(cryptoAddress)+'"', con=engine)

    if len(trader_ds) == 1:
        traderID = trader_ds['traderID'][0]

        # Find target strategy index
        strategyIndex = getStrategyIndex(traderID, strategyID)
        if strategyIndex != None:
            # Find target orders
            orders = pd.read_sql_query('SELECT * FROM orders WHERE status="OPEN"', con=engine)
            orders = orders[orders['strategyID'] == strategyIndex].reset_index(drop=True)

            if len(orders)>0:
                # Cancel all open orders
                sqlConnection = engine.connect()
                for j in range(len(orders)):
                    cancelOrder = 'UPDATE orders SET status="CANCELED" WHERE orderID ="'+str(orders['orderID'][j])+'"'
                    sqlConnection.execute(cancelOrder)
                sqlConnection.close()
                return 'All open orders are closed successfully. Hooray!'
            else:
                sqlConnection.close()
                return 'You got no open orders. Sorry.'

        else: return 'There is no such strategy. Please, register it first.'

    else: return 'There is no such cryptowallet. Please, register it first.'
