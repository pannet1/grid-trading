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
from broker import paper_broker, PaperBroker
import time
from redis_client import RedisClient

try:
    from omspy.brokers.finvasia import Finvasia
except Exception as e:
    print(e)

# Global variables that would be used throughout the module
DB = "/tmp/orders.sqlite"
MODE = "DEV"  # change mode to PROD when using in production


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
    if MODE == "DEV":
        broker = paper_broker()
        datafeed = broker
    elif MODE == "PROD":
        config_file = os.path.join(os.environ["HOME"], "config2.yaml")
        with open(config_file) as f:
            config = yaml.safe_load(f)[0]["config"]
            broker = Finvasia(**config)
            broker.authenticate()
            datafeed = RedisClient()
            datafeed.authenticate()
            # Would use this on my machine; not recommended
            # datafeed = paper_broker()
    else:
        logger.error(f"Invalid {MODE}; exiting program")
        return

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
    if isinstance(datafeed, PaperBroker):
        datafeed.symbols = symbols
        datafeed.run()

    print(connection)

    # Initial update for the next entry prices
    ltps = datafeed.ltp(symbols)
    print(ltps)
    for strategy in strategies:
        strategy.run(ltps)

    for i in range(10000):
        # This would be run only when it is mock instance
        if isinstance(datafeed, PaperBroker):
            datafeed.run()
        ltps = datafeed.ltp(symbols)
        for strategy in strategies:
            strategy.run(ltps)
        time.sleep(1)
        if i % 5 == 0:
            pass
            # TODO: Update orders


if __name__ == "__main__":
    main()
