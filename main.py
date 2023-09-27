import os
import yaml
import pandas as pd
import numpy as np
from typing import List, Optional
from copy import deepcopy
from strategy import Strategy
from omspy.brokers.zerodha import Zerodha
from omspy.simulation.virtual import ReplicaBroker, FakeBroker
from omspy.order import create_db
from logzero import logger
from sqlite_utils import Database

# Global variables that would be used throughout the module
DB = '/tmp/orders.sqlite'

def get_database()->Optional[Database]:
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
    parameters = pd.read_csv('parameters.csv').to_dict(orient='records')
    strategies = []
    broker = FakeBroker()
    for params in parameters:
        try:
            p = {k: v for k, v in params.items() if pd.notnull(v)}
            strategy = Strategy(**p, broker=broker, datafeed=datafeed)
            strategies.append(strategy)
        except Exception as e:
            logger.error(e)
    symbols = get_all_symbols(strategies)
    db = get_database()
    print(db)
    print(datafeed.ltp(symbols))


if __name__ == "__main__":
    config_file = os.path.join(os.environ['HOME'],'systemtrader','config.yaml')
    with open(config_file) as f:
        config = yaml.safe_load(f)[0]['config']
        datafeed = Zerodha(**config)
        datafeed.authenticate()
    main()
