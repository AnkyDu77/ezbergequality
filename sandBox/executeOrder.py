# === Execute Order ===

import os
import hashlib
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine

from config import Config


def executeOrder(currentPrice, market, strategyID, orderID, price, volume, symbol, orderDirection,
                 marginCallLevel = 0.8, comission=0.0002):

    # POSITITONS TABLE EXISTANCE CHECK
    # Watch for priviously opened position and get account ds
    db_uri = Config().SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri, echo=False)
    position_ds = pd.read_sql_query('SELECT * FROM positions WHERE strategyID = "'+str(strategyID)+'" AND market = "'+str(market)+'" AND status = 1 ORDER BY timestamp DESC LIMIT 1' , con = engine)
    account_ds = pd.read_sql_query('SELECT * FROM accounts WHERE strategyID = "'+str(strategyID)+'" ORDER BY timestamp DESC LIMIT 1', con = engine)
    strategy_ds = pd.read_sql_query('SELECT * FROM strategies WHERE strategyID = "'+str(strategyID)+'"', con = engine)

    # Define if got an open position
    if len(position_ds) == 0:
        # Fill the order
        sqlConnection = engine.connect()
        fillOrder = 'UPDATE orders SET status = "FILLED" WHERE orderID="'+str(orderID)+'"'
        sqlConnection.execute(fillOrder)
        sqlConnection.close()

        # Change account state
        accountDict = {
            'strategyID': strategyID,
            'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
            'startDayBalance': round(float(account_ds['endDayBalance'][0]),2), # Make sure that the last record in ds the last indeed
            'onMargin': round(float((price*volume)/strategy_ds['leverage'][0]),2),
            'comissions': round(float(price*volume*comission),2),
            'endDayBalance': round(float(account_ds['endDayBalance'][0] - ((price*volume)/strategy_ds['leverage'][0]) - (price*volume*comission)),2)
        }

        newAccountState_ds = pd.DataFrame(accountDict, index=[0])

        # Set new position
        # Calculate direction-depended params
        if orderDirection == 'SELL':

            direction = 'SHORT'
            liqPrice = round(float(((price*volume)+(accountDict['onMargin']*marginCallLevel))/volume),2) # "+" bicause we got short!
            urealisedPL = round(float((price - currentPrice)*volume),2)

        elif orderDirection == 'BUY':

            direction = 'LONG'
            liqPrice = round(float(((price*volume)-(accountDict['onMargin']*marginCallLevel))/volume),2) # "-" bicause we got long!
            urealisedPL = round(float((currentPrice - price)*volume),2)

        # Fill position dict out
        positionDict = {
            'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
            'strategyID': int(strategyID),
            'market': str(market),
            'symbol': str(symbol),
            'direction': str(direction),
            'openPrice': round(float(price),2),
            'volume': round(float(volume),2),
            'liqPrice': round(float(liqPrice),2),
            'urealisedPL': round(float(urealisedPL),2),
            'realisedPL': 0.0,
            'status': 1,
            'positionID': str(uuid.uuid4())
        }

        newPosition_ds = pd.DataFrame(positionDict, index=[0])

        # Write datasets into DB
        newPosition_ds.to_sql('positions', con=engine, if_exists='append', index=False)
        newAccountState_ds.to_sql('accounts', con=engine, if_exists='append', index=False)

        accountDict = newPosition_ds.to_dict(orient='list')
        positionDict = newAccountState_ds.to_dict(orient='list')
        # Get Json
        jsonDict = {
            'accountState': accountDict,
            'position': positionDict
        }

        outJson = json.dumps(jsonDict)

        return outJson

    else:

        # === SAME-WAY ORDER === #

        # Act if position is SHORT and it's same-way order
        if position_ds['direction'][0] == 'SHORT' and orderDirection == 'SELL':

            # Fill the order
            sqlConnection = engine.connect()
            fillOrder = 'UPDATE orders SET status = "FILLED" WHERE orderID="'+str(orderID)+'"'
            sqlConnection.execute(fillOrder)
            sqlConnection.close()

            # Change account state
            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': round(float(((price*volume)/strategy_ds['leverage'][0])+account_ds['onMargin'][0]),2),
                'comissions': round(float(price*volume*comission),2),
                'endDayBalance': round(float(account_ds['endDayBalance'][0] - (((price*volume)/strategy_ds['leverage'][0])+account_ds['onMargin'][0]) - (price*volume*comission)),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])


            # Set new position parameters
            newPrice = round(float(((position_ds['openPrice'][0]*position_ds['volume'][0])+(price*volume))/(position_ds['volume'][0]+volume)),2)
            newVolume = round(float(position_ds['volume'][0]+volume),2)
            newLiqPrice = round(float(((newPrice*newVolume)+(accountDict['onMargin']*marginCallLevel))/newVolume),2) # "+" bicause we got short!)
            newUnrealisedPL = round(float((newPrice - currentPrice)*newVolume),2)

            # Fill position dict out
            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(position_ds['direction'][0]),
                'openPrice': round(float(newPrice),2),
                'volume': round(float(newVolume),2),
                'liqPrice': round(float(newLiqPrice),2),
                'urealisedPL': round(float(newUnrealisedPL),2),
                'realisedPL': 0.0,
                'status': 1,
                'positionID': str(position_ds['positionID'][0])
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

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


        # Act if position is LONG and it's same-way order
        elif position_ds['direction'][0] == 'LONG' and orderDirection == 'BUY':

            # Fill the order
            sqlConnection = engine.connect()
            fillOrder = 'UPDATE orders SET status = "FILLED" WHERE orderID="'+str(orderID)+'"'
            sqlConnection.execute(fillOrder)
            sqlConnection.close()

            # Change account state
            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': round(float(((price*volume)/strategy_ds['leverage'][0])+account_ds['onMargin'][0]),2),
                'comissions': round(float(price*volume*comission),2),
                'endDayBalance': round(float(account_ds['endDayBalance'][0] - (((price*volume)/strategy_ds['leverage'][0])+account_ds['onMargin'][0]) - (price*volume*comission)),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])


            # Set new position parameters
            newPrice = round(float(((position_ds['openPrice'][0]*position_ds['volume'][0])+(price*volume))/(position_ds['volume'][0]+volume)),2)
            newVolume = round(float(position_ds['volume'][0]+volume),2)
            newLiqPrice = round(float(((newPrice*newVolume)-(accountDict['onMargin']*marginCallLevel))/newVolume ),2)# "-" bicause we got long!
            newUnrealisedPL = round(float((currentPrice - newPrice)*newVolume),2)

            # Fill position dict out
            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(position_ds['direction'][0]),
                'openPrice': round(float(newPrice),2),
                'volume': round(float(newVolume),2),
                'liqPrice': round(float(newLiqPrice),2),
                'urealisedPL': round(float(newUnrealisedPL),2),
                'realisedPL': 0.0,
                'status': 1,
                'positionID': str(position_ds['positionID'][0])
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

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


        # === PERTIALLY-FILLING ORDER === #

        # Act if position is SHORT and order volume partially close position
        elif (position_ds['direction'][0] == 'SHORT' and orderDirection == 'BUY') and (position_ds['volume'][0]>volume):

            # Fill the order
            sqlConnection = engine.connect()
            fillOrder = 'UPDATE orders SET status = "FILLED" WHERE orderID="'+str(orderID)+'"'
            sqlConnection.execute(fillOrder)
            sqlConnection.close()

            # Change account state
            marginRelease = ((price*volume)/strategy_ds['leverage'][0])
            partialPL = (position_ds['openPrice'][0]-price)*volume
            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': round(float(account_ds['onMargin'][0]-marginRelease),2),
                'comissions': round(float(price*volume*comission),2),
                'endDayBalance':round(float(account_ds['endDayBalance'][0] - (price*volume*comission) + marginRelease + partialPL),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])

            # Fill position dict out
            newVolume = round(float(position_ds['volume'][0] - volume),2)
            newLiqPrice = round(float(((position_ds['openPrice'][0]*newVolume)+(accountDict['onMargin']*marginCallLevel))/newVolume ),2) # "+" bicause we got short!
            newUnrealisedPL = round(float((position_ds['openPrice'][0] - currentPrice)*newVolume),2)

            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(position_ds['direction'][0]),
                'openPrice': round(float(position_ds['openPrice'][0]),2),
                'volume': round(float(newVolume),2),
                'liqPrice': round(float(newLiqPrice),2),
                'urealisedPL': round(float(newUnrealisedPL),2),
                'realisedPL': 0.0,
                'status': 1,
                'positionID': str(position_ds['positionID'][0])
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

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


        # Act if position is LONG and order volume partially close position
        elif (position_ds['direction'][0] == 'LONG' and orderDirection == 'SELL') and (position_ds['volume'][0]>volume):

            # Fill the order
            sqlConnection = engine.connect()
            fillOrder = 'UPDATE orders SET status = "FILLED" WHERE orderID="'+str(orderID)+'"'
            sqlConnection.execute(fillOrder)
            sqlConnection.close()

            # Change account state
            marginRelease = ((price*volume)/strategy_ds['leverage'][0])
            partialPL = (price - position_ds['openPrice'][0])*volume
            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': round(float(account_ds['onMargin'][0]-marginRelease),2),
                'comissions': round(float(price*volume*comission),2),
                'endDayBalance': round(float(account_ds['endDayBalance'][0] - (price*volume*comission) + marginRelease + partialPL),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])

            # Fill position dict out
            newVolume = round(float(position_ds['volume'][0] - volume),2)
            newLiqPrice = round(float(((position_ds['openPrice'][0]*newVolume)-(accountDict['onMargin']*marginCallLevel))/newVolume ),2) # "-" bicause we got long!
            newUnrealisedPL = round(float((currentPrice - position_ds['openPrice'][0])*newVolume),2)

            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(position_ds['direction'][0]),
                'openPrice': round(float(position_ds['openPrice'][0]),2),
                'volume': round(float(newVolume),2),
                'liqPrice': round(float(newLiqPrice),2),
                'urealisedPL': round(float(newUnrealisedPL),2),
                'realisedPL': 0.0,
                'status': 1,
                'positionID': str(position_ds['positionID'][0])
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

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


        # === POSITION CLOSING ORDER === #

        # Act if position is SHORT and order volume fully close position
        elif (position_ds['direction'][0] == 'SHORT' and orderDirection == 'BUY') and (position_ds['volume'][0]==volume):
            # Fill the order
            sqlConnection = engine.connect()
            fillOrder = 'UPDATE orders SET status = "FILLED" WHERE orderID="'+str(orderID)+'"'
            sqlConnection.execute(fillOrder)
            sqlConnection.close()

            # Change account state
            PL = (position_ds['openPrice'][0]-price)*volume

            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': 0.0,
                'comissions': round(float(price*volume*comission),2),
                'endDayBalance': round(float(account_ds['endDayBalance'][0] - (price*volume*comission) + account_ds['onMargin'][0] + PL),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])

            # Update position status to closed (0)
            sqlConnection = engine.connect()
            updatePositionStatus = 'UPDATE positions SET status = 0 WHERE positionID = "'+str(position_ds['positionID'][0])+'"'
            sqlConnection.execute(updatePositionStatus)
            sqlConnection.close()

            # Fill position dict out
            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(position_ds['direction'][0]),
                'openPrice': round(float(position_ds['openPrice'][0]),2),
                'volume': round(float(position_ds['volume'][0]),2),
                'liqPrice': round(float(position_ds['liqPrice'][0]),2),
                'urealisedPL': 0.0,
                'realisedPL': round(float(PL),2),
                'status': 0,
                'positionID': str(position_ds['positionID'][0])
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

            # Write datasets into DB
            newPosition_ds.to_sql('positions', con=engine, if_exists='append', index=False)
            newAccountState_ds.to_sql('accounts', con=engine, if_exists='append', index=False)
            sqlConnection.close()

            accountDict = newAccountState_ds.to_dict(orient='list')
            positionDict = newPosition_ds.to_dict(orient='list')

            # Get Json
            jsonDict = {
                'accountState': accountDict,
                'position': positionDict
            }

            outJson = json.dumps(jsonDict)

            return outJson

        # Act if position is LONG and order volume partially close position
        elif (position_ds['direction'][0] == 'LONG' and orderDirection == 'SELL') and (position_ds['volume'][0]==volume):
            # Fill the order
            sqlConnection = engine.connect()
            fillOrder = 'UPDATE orders SET status = "FILLED" WHERE orderID="'+str(orderID)+'"'
            sqlConnection.execute(fillOrder)
            sqlConnection.close()

            # Change account state
            PL = (price - position_ds['openPrice'][0])*volume
            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': 0.0,
                'comissions': round(float(price*volume*comission),2),
                'endDayBalance': round(float(account_ds['endDayBalance'][0] - (price*volume*comission) + account_ds['onMargin'][0] + PL),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])

            # Update position status to closed (0)
            sqlConnection = engine.connect()
            updatePositionStatus = 'UPDATE positions SET status = 0 WHERE positionID = "'+str(position_ds['positionID'][0])+'"'
            sqlConnection.execute(updatePositionStatus)
            sqlConnection.close()

            # Fill position dict out
            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(position_ds['direction'][0]),
                'openPrice': round(float(position_ds['openPrice'][0]),2),
                'volume': round(float(position_ds['volume'][0]),2),
                'liqPrice': round(float(position_ds['liqPrice'][0]),2),
                'urealisedPL': 0.0,
                'realisedPL': round(float(PL),2),
                'status': 0,
                'positionID': str(position_ds['positionID'][0])
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

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


        # === CLOSING OLD POSITION AND OPEN NEW ONE ORDER === #

        # Act if position is SHORT and order volume fully closes old position and opens new one
        elif (position_ds['direction'][0] == 'SHORT' and orderDirection == 'BUY') and (position_ds['volume'][0]<volume):

            # Fill the order
            sqlConnection = engine.connect()
            fillOrder = 'UPDATE orders SET status = "FILLED" WHERE orderID="'+str(orderID)+'"'
            sqlConnection.execute(fillOrder)
            sqlConnection.close()

            # Get excessive volume
            excessiveVolume = volume-position_ds['volume'][0]

            # == Close SHORT ==
            # Change account state
            PL = (position_ds['openPrice'][0]-price)*position_ds['volume'][0]
            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': 0.0,
                'comissions': round(float(price*position_ds['volume'][0]*comission),2),
                'endDayBalance': round(float(account_ds['endDayBalance'][0] - (price*position_ds['volume'][0]*comission) + account_ds['onMargin'][0] + PL),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])

            closedPosAccState = newAccountState_ds.to_dict(orient='list')

            # Update position status to closed (0)
            sqlConnection = engine.connect()
            updatePositionStatus = 'UPDATE positions SET status = 0 WHERE positionID = "'+str(position_ds['positionID'][0])+'"'
            sqlConnection.execute(updatePositionStatus)
            sqlConnection.close()

            # Fill position dict out
            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(position_ds['direction'][0]),
                'openPrice': round(float(position_ds['openPrice'][0]),2),
                'volume': round(float(position_ds['volume'][0]),2),
                'liqPrice': round(float(position_ds['liqPrice'][0]),2),
                'urealisedPL': 0.0,
                'realisedPL': round(float(PL),2),
                'status': 0,
                'positionID': str(position_ds['positionID'][0])
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

            closedPos = newPosition_ds.to_dict(orient='list')

            # Write datasets into DB
            newPosition_ds.to_sql('positions', con=engine, if_exists='append', index=False)
            newAccountState_ds.to_sql('accounts', con=engine, if_exists='append', index=False)

            # == Open LONG ==

            # Change account state
            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': round(float((price*excessiveVolume)/strategy_ds['leverage'][0]),2),
                'comissions': round(float(price*excessiveVolume*comission),2),
                'endDayBalance': round(float(account_ds['endDayBalance'][0] - ((price*excessiveVolume)/strategy_ds['leverage'][0]) - (price*excessiveVolume*comission)),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])

            openedPosAccState = newAccountState_ds.to_dict(orient='list')

            # Set new position
            direction = 'LONG'
            liqPrice = round(float(((price*excessiveVolume)-(accountDict['onMargin']*marginCallLevel))/excessiveVolume),2)# "-" bicause we got long!
            urealisedPL = round(float((currentPrice - price)*excessiveVolume),2)

            # Fill position dict out
            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(direction),
                'openPrice': round(float(price),2),
                'volume': round(float(excessiveVolume),2),
                'liqPrice': round(float(liqPrice),2),
                'urealisedPL': round(float(urealisedPL),2),
                'realisedPL': 0.0,
                'status': 1,
                'positionID': str(uuid.uuid4())
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

            openedPos = newPosition_ds.to_dict(orient='list')

            # Write datasets into DB
            newPosition_ds.to_sql('positions', con=engine, if_exists='append', index=False)
            newAccountState_ds.to_sql('accounts', con=engine, if_exists='append', index=False)

            # Get Json
            jsonDict = {
                'accountState_closedPosition': closedPosAccState,
                'position_closed': closedPos,
                'accountState_openedPosition': openedPosAccState,
                'position_opened': openedPos
            }

            outJson = json.dumps(jsonDict)

            return outJson


        # Act if position is LONG and order volume fully closes old position and opens new one
        elif (position_ds['direction'][0] == 'LONG' and orderDirection == 'SELL') and (position_ds['volume'][0]<volume):

            # Fill the order
            sqlConnection = engine.connect()
            fillOrder = 'UPDATE orders SET status = "FILLED" WHERE orderID="'+str(orderID)+'"'
            sqlConnection.execute(fillOrder)
            sqlConnection.close()

            # Get excessive volume
            excessiveVolume = volume-position_ds['volume'][0]

            # == Close LONG ==
            # Change account state
            PL = (price - position_ds['openPrice'][0])*position_ds['volume'][0]
            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': 0.0,
                'comissions': round(float(price*position_ds['volume'][0]*comission),2),
                'endDayBalance': round(float(account_ds['endDayBalance'][0] - (price*position_ds['volume'][0]*comission) + account_ds['onMargin'][0] + PL),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])

            closedPosAccState = newAccountState_ds.to_dict(orient='list')

            # Update position status to closed (0)
            sqlConnection = engine.connect()
            updatePositionStatus = 'UPDATE positions SET status = 0 WHERE positionID = "'+str(position_ds['positionID'][0])+'"'
            sqlConnection.execute(updatePositionStatus)
            sqlConnection.close()

            # Fill position dict out
            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(position_ds['direction'][0]),
                'openPrice': round(float(position_ds['openPrice'][0]),2),
                'volume': round(float(position_ds['volume'][0]),2),
                'liqPrice': round(float(position_ds['liqPrice'][0]),2),
                'urealisedPL': 0.0,
                'realisedPL': round(float(PL),2),
                'status': 0,
                'positionID': str(position_ds['positionID'][0])
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

            closedPos = newPosition_ds.to_dict(orient='list')

            # Write datasets into DB
            newPosition_ds.to_sql('positions', con=engine, if_exists='append', index=False)
            newAccountState_ds.to_sql('accounts', con=engine, if_exists='append', index=False)

            # == Open SHORT ==
            # Change account state
            accountDict = {
                'strategyID': int(strategyID),
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'startDayBalance': round(float(account_ds['endDayBalance'][0]),2),
                'onMargin': round(float((price*excessiveVolume)/strategy_ds['leverage'][0]),2),
                'comissions': round(float(price*excessiveVolume*comission),2),
                'endDayBalance': round(float(account_ds['endDayBalance'][0] - ((price*excessiveVolume)/strategy_ds['leverage'][0]) - (price*excessiveVolume*comission)),2)
            }

            newAccountState_ds = pd.DataFrame(accountDict, index=[0])

            openedPosAccState = newAccountState_ds.to_dict(orient='list')

            # Set new position
            direction = 'SHORT'
            liqPrice = round(float(((price*excessiveVolume)+(accountDict['onMargin']*marginCallLevel))/excessiveVolume ),2)# "+" bicause we got short!
            urealisedPL = round(float((price - currentPrice)*excessiveVolume),2)

            # Fill position dict out
            positionDict = {
                'timestamp': datetime.now().replace(tzinfo=timezone.utc).timestamp(),
                'strategyID': int(strategyID),
                'market': str(market),
                'symbol': str(symbol),
                'direction': str(direction),
                'openPrice': round(float(price),2),
                'volume': round(float(excessiveVolume),2),
                'liqPrice': round(float(liqPrice),2),
                'urealisedPL': round(float(urealisedPL),2),
                'realisedPL': 0.0,
                'status': 1,
                'positionID': str(uuid.uuid4())
            }

            newPosition_ds = pd.DataFrame(positionDict, index=[0])

            openedPos = newPosition_ds.to_dict(orient='list')

            # Write datasets into DB
            newPosition_ds.to_sql('positions', con=engine, if_exists='append', index=False)
            newAccountState_ds.to_sql('accounts', con=engine, if_exists='append', index=False)

            # Get Json
            jsonDict = {
                'accountState_closedPosition': closedPosAccState,
                'position_closed': closedPos,
                'accountState_openedPosition': openedPosAccState,
                'position_opened': openedPos
            }

            outJson = json.dumps(jsonDict)

            return outJson
