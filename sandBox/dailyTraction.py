# === Daily Traction Module === #

import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine

from config import Config


def dailyTraction():

    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)
    # Get the Data
    strategies = pd.read_sql_query('SELECT * FROM strategies', con=engine)
    positions = pd.read_sql_query('SELECT * FROM positions', con=engine)
    accounts = pd.read_sql_query('SELECT * FROM accounts', con=engine)

    # Set time boundaries
    endTime = datetime.now()
    startTime = endTime - timedelta(hours=24)
    endTime = endTime.replace(tzinfo=timezone.utc).timestamp()
    startTime = startTime.replace(tzinfo=timezone.utc).timestamp()

    # How many days algorithm stays profitable
    for strategyID in strategies['strategyID'][i]:
        dayStrategyPositions = positions[positions['strategyID']==strategyID]
        dayStrategyPositions = dayStrategyPositions[dayStrategyPositions['timestamp']<=endTime]
        dayStrategyPositions = dayStrategyPositions[dayStrategyPositions['timestamp']>=startTime]
        dayStrategyPositions = dayStrategyPositions.reset_index(drop=True)

        # Get different positions number
        uniquePositions = dayStrategyPositions['positionID'].unique()

        # Calculate daily profit/loss
        plList = []
        for uniquePosition in uniquePositions:
            temp_ds = dayStrategyPositions[dayStrategyPositions['positionID']==uniquePosition]
            if temp_ds['realisedPL'].iloc[-1] == 0.0:
                plList.append(temp_ds['urealisedPL'].iloc[-1])
            else:
                positionAccState = pd.read_sql_query('SELECT * FROM accounts WHERE (strategyID = '+str(temp_ds['strategyID'][0])+') AND (timestamp BETWEEN '+str(temp_ds['timestamp'][0]-0.03)+' AND '+str(temp_ds['timestamp'].iloc[-1])+')', con=engine) # -0.03 in first timestamp here 'cause we write account state before position state

                positionPL = positionAccState['endDayBalance'].iloc[-1] - positionAccState['startDayBalance'].iloc[0]

                plList.append(positionPL)

        dailyPL = sum(plList)

        # Define daily winningRate
        if dailyPL>0:
            dailyWinRate = 1
        else: dailyWinRate = 0

        dailyTractionDict = {
            'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
            'strategyID': strategyID,
            'winRate': dailyWinRate,
            'PL': dailyPL
        }

        dailyTraction_ds = pd.DataFrame(dailyTractionDict, index=[0])
        dailyTraction_ds.to_sql('dailyTraction', con=engine, if_exists='append', index=False)

if __name__ == '__main__':
    dailyTraction()
