# === Get open orders ==

import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from getStrategyIndex import getStrategyIndex
from sqlalchemy import create_engine

from config import Config


def getOpenOrders(cryptoAddress, strategyID):

    # Get traderID
    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)
    trader_ds = pd.read_sql_query('SELECT * FROM traders WHERE \"cryptoAddress\"=\''+str(cryptoAddress)+'\'', con=engine)

    if len(trader_ds) == 1:
        traderID = trader_ds['traderID'][0]

        # Find target strategy
        strategyIndex = getStrategyIndex(traderID, strategyID)

        if strategyIndex != None:
            # Find target orders
            orders = pd.read_sql_query('SELECT * FROM orders WHERE status=\'OPEN\'', con=engine)
            orders = orders[orders['strategyID'] == strategyIndex].reset_index(drop=True)

            if len(orders)>0:
                jsonDict = orders.to_dict(orient='index')
                outJson = json.dumps(jsonDict)

                return outJson

            else: return 'You got no open orders recorded in the SandBox. Do not hesitate to place one by "placeOrder" func!'

        # If we do not get target strategy
        else: return 'There is no such strategy. Please, register it first.'

    # If there is a mistake in cryptowallet address
    else: return 'There is no such cryptowallet. Please, register it first.'
