import os
import pandas as pd
import numpy as np
from copy import deepcopy
from strategy import Strategy
from omspy.brokers.zerodha import Zerodha
from omspy.simulation.virtual import ReplicaBroker
from logzero import logger





def main():
    parameters = pd.read_csv('parameters.csv').to_dict(orient='records')
    strategies = []
    for params in parameters:
        try:
            p = {k:v for k,v in params.items() if pd.notnull(v)}
            strategy = Strategy(**p)
            strategies.append(strategy)
        except Exception as e:
            logger.error(e)
            break
    print(len(strategies))
    for strategy in strategies:
        print(strategy.symbol)



if __name__ == "__main__":
    main()



