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
from omspy_brokers.finvasia import Finvasia
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
    config_file = os.path.join(
        os.environ["HOME"], "systemtrader", "config.yaml")
    with open(config_file) as f:
        config = yaml.safe_load(f)[0]["config"]
        print(config)
        broker = Finvasia(**config)
        broker.authenticate()
        print(dir(broker.finvasia))

    datafeed = RedisClient()
    datafeed.authenticate()
    connection = get_database()
    print(connection)
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
    print(datafeed.ltp(symbols))

    # Initial update for the next entry prices
    ltps = datafeed.ltp(symbols)
    for strategy in strategies:
        strategy.run(ltps)
        strategy.update_next_entry_price()

    for i in range(1000):
        ltps = datafeed.ltp(symbols)
        for strategy in strategies:
            strategy.run(ltps)
        time.sleep(1)
        if i % 5 == 0:
            orders = broker.orders
            print(orders)
            orders_dict = {k: v.dict() for k, v in broker.orders.items()}
            for strategy in strategies:
                for order in strategy.orders:
                    # Update order data from broker
                    # TODO: Correctly implement for paper broker
                    order.update_orders(orders_dict)


if __name__ == "__main__":
    main()
