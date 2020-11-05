# === Watch current marcet price ===

import os
import time
import hashlib
import logging
import uuid
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
from unicorn_fy.unicorn_fy import UnicornFy as ufy
from executeOrder import executeOrder
from liquidatePosition import liquidatePosition
from tqdm import tqdm
from sqlalchemy import create_engine

from config import Config


def watchingDaemon(workingPeriod=87600, parsePeriod=250000, symbol='BTCUSDT'):

    for wp in tqdm(range(workingPeriod)):

        db_uri = Config().SQLALCHEMY_DATABASE_URI
        engine = create_engine(db_uri, echo=False)

        #Set up logger
        logging.basicConfig(level=logging.INFO,
                            filename='./watchingDaemon.log',
                            format='{asctime} [{levelname:8}] {process} {thread} {module}: {message}',
                            style='{')

        logger = logging.getLogger(__name__)

        # Connect to Binance
        streams = ['trade']

        binance_com_websocket_api_manager = BinanceWebSocketApiManager(exchange="binance.com",
                                                                       throw_exception_if_unrepairable=True)
        binance_com_websocket_api_manager.create_stream(streams, [symbol.lower()])

        for pp in tqdm(range(parsePeriod)):

            # Get all open orders and positions
            openOrders = pd.read_sql_query('SELECT * FROM orders WHERE status = "OPEN"', con=engine)
            openPositions = pd.read_sql_query('SELECT * FROM positions WHERE status = 1', con=engine)

            # Check if we got an open orders
            if len(openOrders)>0:

                streamData = binance_com_websocket_api_manager.pop_stream_data_from_stream_buffer()
                if streamData != False:
                    msg = ufy.binance_com_websocket(streamData)

                    if 'event_type' in msg.keys() and msg['event_type']=='error':
                        print(msg['message'])

                    # Trades parse
                    elif 'stream_type' in msg.keys() and msg['stream_type']==symbol.lower()+'@'+streams[0]:

                        lastPrice = round(float(msg['price']),2)
                        # print(lastPrice)

                        # Check order execution possibility
                        for i in range(len(openOrders)):

                            # Define if we can execute order or not
                            if openOrders['direction'][i] == 'SELL' and lastPrice >= float(openOrders['price'][i]):

                                executeOrder(lastPrice, openOrders['market'][i],
                                             openOrders['strategyID'][i], openOrders['orderID'][i],
                                             openOrders['price'][i], openOrders['volume'][i],
                                             openOrders['symbol'][i], openOrders['direction'][i]
                                             )

                                message = '{} {} order executed {}@{}'.format(openOrders['orderID'][i], openOrders['direction'][i],
                                                                        openOrders['volume'][i], openOrders['price'][i])
                                print(message)
                                logger.info(message)

                            elif openOrders['direction'][i] == 'BUY' and lastPrice <= openOrders['price'][i]:

                                executeOrder(lastPrice, openOrders['market'][i],
                                             openOrders['strategyID'][i], openOrders['orderID'][i],
                                             openOrders['price'][i], openOrders['volume'][i],
                                             openOrders['symbol'][i], openOrders['direction'][i]
                                            )

                                message = '{} {} order executed {}@{}'.format(openOrders['orderID'][i], openOrders['direction'][i],
                                                                        openOrders['volume'][i], openOrders['price'][i])
                                print(message)
                                logger.info(message)


                        for j in range(len(openPositions)):

                            # Watch if there liquidation event appeare
                            if openPositions['direction'][j] == 'SHORT' and lastPrice >= openPositions['liqPrice'][j]:

                                liquidatePosition(openPositions['strategyID'][j],
                                                  openPositions['market'][j], openPositions['symbol'][j],
                                                  openPositions['direction'][j],
                                                  openPositions['openPrice'][j], openPositions['volume'][j],
                                                  openPositions['liqPrice'][j], openPositions['positionID'][j]
                                                 )
                                message = '{} {} position liquidated {}@{}'.format(openPositions['positionID'][j], openPositions['direction'][j],
                                                                        openPositions['volume'][j], openPositions['liqPrice'][j])
                                print(message)
                                logger.info(message)

                            elif openPositions['direction'][j] == 'LONG' and lastPrice <= openPositions['liqPrice'][j]:

                                liquidatePosition(openPositions['strategyID'][j],
                                                  openPositions['market'][j], openPositions['symbol'][j],
                                                  openPositions['direction'][j],
                                                  openPositions['openPrice'][j], openPositions['volume'][j],
                                                  openPositions['liqPrice'][j], openPositions['positionID'][j]
                                                 )

                                message = '{} {} position liquidated {}@{}'.format(openPositions['positionID'][j], openPositions['direction'][j],
                                                                        openPositions['volume'][j], openPositions['liqPrice'][j])
                                print(message)
                                logger.info(message)


            # Act if we got no open orders but got open positions
            elif len(openPositions) > 0:

                streamData = binance_com_websocket_api_manager.pop_stream_data_from_stream_buffer()
                if streamData != False:
                    msg = ufy.binance_com_websocket(streamData)

                    if 'event_type' in msg.keys() and msg['event_type']=='error':
                        print(msg['message'])

                    # Trades parse
                    elif 'stream_type' in msg.keys() and msg['stream_type']==symbol.lower()+'@'+streams[0]:

                        lastPrice = round(float(msg['price']),2)
                        # print(lastPrice)

                        for j in range(len(openPositions)):

                            # Watch if there liquidation event appeare
                            if openPositions['direction'][j] == 'SHORT' and lastPrice >= openPositions['liqPrice'][j]:

                                liquidatePosition(openPositions['strategyID'][j],
                                                  openPositions['market'][j], openPositions['symbol'][j],
                                                  openPositions['direction'][j],
                                                  openPositions['openPrice'][j], openPositions['volume'][j],
                                                  openPositions['liqPrice'][j], openPositions['positionID'][j]
                                                 )
                                message = '{} {} position liquidated {}@{}'.format(openPositions['positionID'][j], openPositions['direction'][j],
                                                                        openPositions['volume'][j], openPositions['liqPrice'][j])
                                print(message)
                                logger.info(message)

                            elif openPositions['direction'][j] == 'LONG' and lastPrice <= openPositions['liqPrice'][j]:

                                liquidatePosition(openPositions['strategyID'][j],
                                                  openPositions['market'][j], openPositions['symbol'][j],
                                                  openPositions['direction'][j],
                                                  openPositions['openPrice'][j], openPositions['volume'][j],
                                                  openPositions['liqPrice'][j], openPositions['positionID'][j]
                                                 )

                                message = '{} {} position liquidated {}@{}'.format(openPositions['positionID'][j], openPositions['direction'][j],
                                                                        openPositions['volume'][j], openPositions['liqPrice'][j])
                                print(message)
                                logger.info(message)

                # Check if there is still no open orders
                openOrders = pd.read_sql_query('SELECT * FROM orders WHERE status = "OPEN"', con=engine)

                if len(openOrders)>0:
                    break

            # If there is no open posititons as well as orders just sleep for 15 seconds
            else:
                time.sleep(15)


            time.sleep(0.001)


if __name__ == '__main__':
    watchingDaemon()
