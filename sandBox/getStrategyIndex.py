# === Get strategy index by query ===

import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine

from config import Config


def getStrategyIndex(traderID, strategyKey):

    # strategyKey = bytes(strategyKey, 'utf-8')

    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)

    tradersStratedies_ds = pd.read_sql_query('SELECT * FROM strategies_i_ds WHERE \"traderID\" = \''+str(traderID)+'\'', con=engine)

    flag = False
    for i in range(len(tradersStratedies_ds)):

        salt = tradersStratedies_ds['salt'][i]
        key = tradersStratedies_ds['hashKey'][i].tobytes()
        newKey = hashlib.pbkdf2_hmac('sha256', strategyKey.encode('utf-8'), salt, 100000)

        if key == newKey:
            targetTime = tradersStratedies_ds['timestamp'][i]
            flag = True
            break

    if flag == True:
        # sqlConnection = engine.connect()
        # selectStrategyIndex = 'SELECT row_number() over() FROM strategies_i_ds WHERE \"timestamp\" = '+str(targetTime)
        # strategyIndex = sqlConnection.execute(selectStrategyIndex).fetchall()
        # sqlConnection.close()
        #
        # strategyIndex = strategyIndex[0][0]

        index_df = pd.read_sql_query('SELECT * FROM \"strategies_i_ds\" WHERE \"timestamp\" = '+str(targetTime), con=engine)
        strategyIndex = int(index_df['id'][0])

        return strategyIndex

    else:
        return None
