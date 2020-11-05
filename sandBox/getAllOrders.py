# === Get all orders ==

import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from getStrategyIndex import getStrategyIndex
from sqlalchemy import create_engine

from config import Config


def getAllOrders(cryptoAddress, strategyID):

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
            orders = pd.read_sql_query('SELECT * FROM orders', con=engine)
            orders = orders[orders['strategyID'] == strategyIndex].reset_index(drop=True)

            if len(orders)>0:
                jsonDict = orders.to_dict(orient='index')
                outJson = json.dumps({'e':'success', 'm': jsonDict})

                return outJson

            else: return json.dumps({'e':'You got no orders recorded into SandBox. Do not hesitate to place one buy "openOrder" func!'})

        # If we do not get target strategy
        else: return json.dumps({'e':'There is no such strategy. Please, register it first.'})

    # If there is a mistake in cryptowallet address
    else: return json.dumps({'e':'There is no such cryptowallet. Please, register it first.'})
