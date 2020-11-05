# === POSITION LIQUIDATION === #

import os
import time
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from cancelAllOrders import cancelAllOrders
from sqlalchemy import create_engine

from config import Config


def liquidatePosition(strategyID, market, symbol, direcion,
                      openPrice, volume, liqPrice, positionID):

    # Get account dataset
    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)
    account_ds = pd.read_sql_query('SELECT * FROM accounts WHERE strategyID = '+str(strategyID)+' ORDER BY timestamp DESC LIMIT 1', con=engine)

    sqlConnection = engine.connect()
    # Get traderID # IS IT SAFE ????
    selectTraderID = 'SELECT traderID FROM strategies_i_ds WHERE "rowid" = '+str(strategyID)
    traderID = sqlConnection.execute(selectTraderID).fetchall()

    traderID = traderID[0][0]

    # Get cryptoAddress
    getCryptoaddress = 'SELECT cryptoAddress FROM traders WHERE traderID = "'+str(traderID)+'"'
    cryptoAddress = sqlConnection.execute(getCryptoaddress).fetchall()

    cryptoAddress = str(cryptoAddress[0][0])

    # sqlConnection.close()
    # Cancel all open orders
    # Find target orders
    orders = pd.read_sql_query('SELECT * FROM orders WHERE status="OPEN"', con=engine)
    orders = orders[orders['strategyID'] == strategyID].reset_index(drop=True)

    if len(orders)>0:
        # Cancel all open orders
        for j in range(len(orders)):
            cancelOrder = 'UPDATE orders SET status="CANCELED" WHERE orderID ="'+str(orders['orderID'][j])+'"'
            sqlConnection.execute(cancelOrder)
        sqlConnection.close()
    else:
        sqlConnection.close()

    # Define losses amount
    if direcion == 'SHORT':
        loss = round(float((liqPrice-openPrice)*volume),2)
    elif direcion == 'LONG':
        loss = round(float((openPrice-liqPrice)*volume),2)

    # Update position status to closed (0)
    sqlConnection = engine.connect()
    updatePositionStatus = 'UPDATE positions SET status = 0 WHERE positionID = "'+str(positionID)+'"'
    sqlConnection.execute(updatePositionStatus)
    sqlConnection.close()

    # Close position
    positionDict = {
        'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
        'strategyID': int(strategyID),
        'market': str(market),
        'symbol': str(symbol),
        'direction': str(direcion),
        'openPrice': float(openPrice),
        'volume': float(volume),
        'liqPrice': float(liqPrice),
        'urealisedPL': 0.0,
        'realisedPL': float(loss),
        'status': 0,
        'positionID': str(positionID)
    }

    newPosition_ds = pd.DataFrame(positionDict, index=[0])

    # Change account state

    accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': float(account_ds['endDayBalance'][0]),
                'onMargin': 0.0,
                'comissions': 0.0,
                'endDayBalance': float(account_ds['endDayBalance'][0] - account_ds['onMargin'][0])
            }

    newAccountState_ds = pd.DataFrame(accountDict, index=[0])


    # Write datasets into DB
    newPosition_ds.to_sql('positions', con=engine, if_exists='append', index=False)
    newAccountState_ds.to_sql('accounts', con=engine, if_exists='append', index=False)

    accountDict = newAccountState_ds.to_dict(orient='list')
    positionDict = newPosition_ds.to_dict(orient='list')

    # Get Json
    jsonDict = {
        'accountState': accountDict,
        'position': positionDict
    }

    outJson = json.dumps(jsonDict)

    return outJson
