import os
import yaml
import pandas as pd
import numpy as np
from typing import List, Optional
from copy import deepcopy
from strategy import Strategy
from omspy.order import create_db
from logzero import logger
from sqlite_utils import Database
from broker import paper_broker
from omspy.brokers.zerodha import Zerodha
import time
from redis_client import RedisClient

# Global variables that would be used throughout the module
DB = "/tmp/orders.sqlite"


def get_database() -> Optional[Database]:
    if os.path.exists(DB):
        return Database(DB)
    else:
        db = create_db(dbname=DB)
        if db:
            logger.info("New database created")
            return db
        else:
            logger.error("Error in database")


def get_all_symbols(strategies: List[Strategy]) -> List[str]:
    """
    Get the list of all symbols from the given list of
    strategies in the format required to extract data
    from the broker
    """
    symbols = []
    for st in strategies:
        symbol = f"{st.exchange}:{st.symbol}"
        symbols.append(symbol)
    return symbols


def main():
    parameters = pd.read_csv("parameters.csv").to_dict(orient="records")
    strategies = []
    broker = paper_broker()
    datafeed = broker # overriding datafeed here
    connection = get_database()
    for params in parameters:
        try:
            p = {k: v for k, v in params.items() if pd.notnull(v)}
            strategy = Strategy(
                **p, broker=broker, datafeed=datafeed, connection=connection
            )
            strategies.append(strategy)
        except Exception as e:
            logger.error(e)
    symbols = get_all_symbols(strategies)
    # We are mimicking broker here and seeding prices
    broker.symbols = symbols
    # Change this method to run2 if you are using redis ltp
    broker.run()
    print(connection)
    print(broker.ltp(symbols))

    # Initial update for the next entry prices
    ltps = broker.ltp(symbols)
    for strategy in strategies:
        strategy.run(ltps)
        strategy.update_next_entry_price()

    for i in range(10000):
        ltps = broker.ltp(symbols)
        for strategy in strategies:
            strategy.run(ltps)
        time.sleep(1)
        if i % 5 == 0:
            orders_dict = {k: v.dict() for k, v in broker.orders.items()}
            for strategy in strategies:
                for order in strategy.orders:
                    # Update order data from broker
                    # TODO: Correctly implement for paper broker
                    order.update_orders(orders_dict)


if __name__ == "__main__":
    datafeed = RedisClient()
    datafeed.authenticate()
    main()
