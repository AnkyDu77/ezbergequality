import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine

from config import Config

def traderRegistration(cryptoAddress, nickname='mysterious_stranger'):

    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)
    dbTraders_ds = pd.read_sql_query('SELECT * FROM traders WHERE cryptoAddress = "'+str(cryptoAddress)+'"', con=engine)

    if len(dbTraders_ds) != 0:

        message = 'This username or cryptowallet address already exists. Please, choose another one.'
        return message

    else:

        # Hash trader info
        traderStamp = str(cryptoAddress)+nickname
        traderStampHash = hashlib.sha256(traderStamp.encode('utf-8')).hexdigest() # This hash will be returned to the user

        # Create user registration dictionary
        userRegistrationDict = {
            'traderID': traderStampHash,
            'userRegTime': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
            'cryptoAddress': cryptoAddress,
            'nickname': nickname
        }

        # Create pandas dataset and write it down into database
        userRegistration_ds = pd.DataFrame(userRegistrationDict, index=[0])

        userRegistration_ds.to_sql('traders', con=engine, if_exists='append', index=False)

        return f'Your trader ID is: {traderStampHash}'
