import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from writeStrategyIndex import writeStrategyIndex
from sqlalchemy import create_engine

from config import Config

def strategyRegistration(cryptoAddress, algoOpenness, capitalCapacity, leverage,
                        strategyName = 'mysterious_strategy'):


    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)

    # Check if we have the trader in our DB
    trader_ds = pd.read_sql_query('SELECT * FROM traders WHERE \"cryptoAddress\" = \''+str(cryptoAddress)+'\'', con = engine)

    if len(trader_ds) == 0:
        return 'Sorry, there is no such cryptowallet address. Please, registrate it first by using traderRegistration() func.'

    else:
        traderID = trader_ds['traderID'][0]

        # Equal algoOpenness and capitalCapacity
        algoOpenness = algoOpenness.lower()
        capitalCapacity = capitalCapacity.lower()

        # Define convretion dictionaries
        ALGO_OPENNESS_CONVERT = {
            'open': True,
            'close': False
        }

        CAPITAL_CAPACITY_CONVERT = {
            'small': 100000.00,
            'medium': 1000000.00,
            'big': 100000000.00,
            'infinite': 1000000000.00
        }

        # Convert algo openness
        if algoOpenness == 'open':
            algoOpenness = ALGO_OPENNESS_CONVERT['open']
        else:
            algoOpenness = ALGO_OPENNESS_CONVERT['close']

        # Convert capital capacity
        capitalCapacity = [CAPITAL_CAPACITY_CONVERT[capacity] for capacity in CAPITAL_CAPACITY_CONVERT if capacity == capitalCapacity]
        capitalCapacity = capitalCapacity[0]


        # Get unic strategy hash
        strategyStamp = str(algoOpenness)+str(capitalCapacity)+str(leverage)
        uniquenessStrategyHash = hashlib.sha256(strategyStamp.encode('utf-8')).hexdigest()

        # Check table existence
        if 'strategies' in engine.table_names():

            strategy_ds = pd.read_sql_query('SELECT * FROM strategies WHERE \"ush\" = \''+str(uniquenessStrategyHash)+'\'', con = engine)

            if len(strategy_ds) > 0:
                message = 'We got to warn you. Somebody has registrated pretty similar strategy already. Thus if your strategy will get the similar performance it will not participate in a rancking process.'

            else:
                message = 'Congratulations! You got very unique strategy.'


        else:

            message = 'Congratulations! You got very unique strategy.'

        # Hash strategy
        strategyString = str(cryptoAddress)+strategyName+str(algoOpenness)+str(capitalCapacity)+str(leverage)+str(os.urandom(32))
        strategyStringHash = hashlib.sha256(strategyString.encode('utf-8')).hexdigest() # This hash will be returned to the user

        salt = os.urandom(32) # A new salt for strategy
        key = hashlib.pbkdf2_hmac('sha256', strategyStringHash.encode('utf-8'), salt, 100000)

        #  Write down new strategy's salt/hashKey and get strategy index
        strategyIndex = writeStrategyIndex(salt, key, traderID)


        # Create strategy registration dictionary
        strategyRegistrationDict = {
            'strategyID': strategyIndex,
            'regTime': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
            'ush': uniquenessStrategyHash,
            'strategyName': strategyName,
            'algoOpenness': algoOpenness,
            'capitalCapacity': capitalCapacity,
            'leverage': leverage
        }

        # Write new strategy into DB
        strategyRegistration_ds = pd.DataFrame(strategyRegistrationDict, index=[0])
        strategyRegistration_ds.to_sql('strategies', con=engine, if_exists='append', index=False)

        # Create account registration dictionary
        accountRegistrationDict = {
            'strategyID': strategyIndex,
            'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
            'startDayBalance': capitalCapacity,
            'onMargin': 0.00,
            'comissions': 0.00,
            'endDayBalance': capitalCapacity,
        }

        # Write new account into DB
        accountRegistration_ds = pd.DataFrame(accountRegistrationDict, index=[0])
        accountRegistration_ds.to_sql('accounts', con=engine, if_exists='append', index=False)

        outMessage = message+'\n\nYour unique strategy ID is: '+str(strategyStringHash)+'\n\nWARNING!!! DO NOT LOSE ID! Following interaction with platform impossible without it!'

        return outMessage
