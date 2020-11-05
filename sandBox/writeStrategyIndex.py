"""
Write down new strategy's salt and hashKey
"""
import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine

from config import Config


def writeStrategyIndex(salt, hashKey, traderID):

    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)

    strategyIndexDict = {
        'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
        'salt': salt,
        'hashKey': hashKey,
        'traderID': traderID
    }

    strategyIndex_ds = pd.DataFrame(strategyIndexDict, index=[0])

    strategyIndex_ds.to_sql('strategies_i_ds', con=engine, if_exists='append', index=False)

    sqlConnection = engine.connect()
    selectStrategyIndex = 'SELECT "rowid" FROM strategies_i_ds WHERE timestamp = '+str(strategyIndexDict['timestamp'])
    strategyIndex = sqlConnection.execute(selectStrategyIndex).fetchall()
    sqlConnection.close()

    strategyIndex = strategyIndex[0][0]

    return strategyIndex
