# === Rotation Module === #

import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine

from config import Config


def rotateStrategies(weeksNum = 1, daysNum = 7, marketStrategyName = 'Mama Mia! It is real ETF!'):

    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)

    # Define rates
    RETE_DICT = {
        'algoPublicity': {
            'open': 1.2,
            'close': 1
        },
        'maxCapCapacity': {
            'small': 1,
            'medium': 1.2,
            'big': 1.5,
            'infinite': 1.8
        },
        'winningRate': {
            'small': 1,
            'medium': 1.5,
            'big': 1.8
         },
        'profitability': {
            'normProfitPercent': 1.5
        },
        'marketBeat': {
            'belowMarket': 1,
            'market': 1.5,
            'aboveMarket': 1.8
        }
    }


    # Set time boundaries
    endTime = datetime.now()
    startTime = endTime - timedelta(weeks=weeksNum)
    endTime = endTime.replace(tzinfo=timezone.utc).timestamp()
    startTime = startTime.replace(tzinfo=timezone.utc).timestamp()

    # Get the Data
    strategies = pd.read_sql_query('SELECT * FROM strategies', con=engine)
    positions = pd.read_sql_query('SELECT * FROM positions', con=engine)
    accounts = pd.read_sql_query('SELECT * FROM accounts', con=engine)
    dailyTractons = pd.read_sql_query('SELECT * FROM dailyTraction WHERE timestamp BETWEEN '+str(startTime)+' AND '+str(endTime) +'', con=engine)


    # Prepare profit calculations
    sumPLbyStrategy_ds = dailyTractons.order_by(['strategyID']).sum().reset_index()
    # Set datasets equalyty by strategies order
    sumPLbyStrategy_ds = sumPLbyStrategy_ds.sort_values(by=['strategyID']).reset_index(drop=True)
    strategies = strategies.sort_values(by=['strategyID']).reset_index(drop=True)

    # Check strategies numbers equality
    if len(sumPLbyStrategy_ds) == len(strategies):
        revativePLlist = []
        for plIndx in range(len(sumPLbyStrategy_ds)):
            relativePL = sumPLbyStrategy_ds['PL'][plIndx]/strategies['capitalCapacity'][plIndx]
            revativePLlist.append(relativePL)

        minPL = min(revativePLlist)
        maxPL = max(revativePLlist)

        # Get winning days list
        winRateList = sumPLbyStrategy_ds['winRate'].to_list()

        minWinRate = min(winRateList)
        maxWinRate = max(winRateList)

        # Make rate calculations for each strategy
        rateList = []
        for i in range(len(strategies)):

            # Is algorythm public?
            algoPublicity = strategies['algoOpenness'][i]
            if algoPublicity == 1:
                algoPublicity = 'open'
            else: algoPublicity = 'close'

            # How much money can algorithm works with?
            maxCapCapacity = strategies['capitalCapacity'][i]
            if maxCapCapacity == 100000.0:
                maxCapCapacity = 'small'

            elif maxCapCapacity == 1000000.0:
                maxCapCapacity = 'medium'

            elif maxCapCapacity == 100000000.0:
                maxCapCapacity = 'big'

            elif maxCapCapacity == 1000000000.0:
                maxCapCapacity = 'infinite'

            # What the winning rate?
            winRateNum = sumPLbyStrategy_ds['winRate'][i]

            if 5 < winRateNum <= 7:
                winRate = 'big'
            elif 4 <= winRateNum < 6:
                winRate = 'medium'
            elif winRateNum < 4:
                winRate = 'small'

            normWinRate = (winRateNum - minWinRate)/(maxWinRate-minWinRate)

            # How profitable the strategy was?
            normPLrate = (revativePLlist[i]-minPL)/(maxPL-minPL)

            # Was strategy PL above the market?
            marketStrategy = strategies[strategies['strategyName']==marketStrategyName]
            marketStrategy = marketStrategy.sort_values(by=['regTime']).reset_index(drop=True)
            marketPLabs = [pl for pl in sumPLbyStrategy_ds['PL'] if sumPLbyStrategy_ds['strategyID']==marketStrategy['strategyID'][0]]
            marketPLrel = marketPLabs/marketStrategy['capitalCapacity'][0]

            if revativePLlist[i] > marketPLrel:
                marketBeat = 'aboveMarket'
            elif revativePLlist[i] == marketPLrel:
                marketBeat = 'market'
            elif revativePLlist[i] < marketPLrel:
                marketBeat = 'belowMarket'


            strategyRanc = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': strategies['strategyID'][i],
                'algoOpenness': RETE_DICT['algoPublicity'][algoPublicity],
                'maxCapCapacity': RETE_DICT['maxCapCapacity'][maxCapCapacity],
                'winRate': normWinRate * RETE_DICT['winningRate'][winRate],
                'profitability': normPLrate * RETE_DICT['winningRate']['normProfitPercent'],
                'marketBeat': RETE_DICT['marketBeat'][marketBeat],
                'resultRate': strategyRanc['algoOpenness']+strategyRanc['maxCapCapacity']+strategyRanc['winRate']+strategyRanc['profitability']+strategyRanc['marketBeat']
            }

            rateList.append(strategyRanc)

        rating_ds = pd.DataFrame(rateList)
        rating_ds.to_sql('rating', con=engine, if_exists='append', index=False)

        jsonDict = {
            'e': 'success',
            'm': rateList
        }

        outJson = json.dumps(jsonDict)

        return outJson

    else:
        jsonMessage = 'We got stratedies number mismatch.'
        outJson = json.dumps({'e':jsonMessage})

        return outJson
