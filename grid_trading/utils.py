"""
General utility functions that cwould be used across the project
"""

from typing import Dict
import pandas as pd


def get_exchange_token_map_finvasia(
    key: str = "Token", value: str = "TradingSymbol"
) -> Dict[int, str]:
    """
    Get the exchange token map for finvasia broker
    key
        column name to be considered as key
    value
        column name to be considered as value
    Note
    ----
    1) Exchange token map generated only for NSE,NFO exchanges
    2) Token is always in `int` format
    """
    df1 = pd.read_csv("https://api.shoonya.com/NSE_symbols.txt.zip")
    df2 = pd.read_csv("https://api.shoonya.com/NFO_symbols.txt.zip")
    df3 = pd.read_csv("https://api.shoonya.com/MCX_symbols.txt.zip")
    df = pd.concat([df1, df2, df3])
    df["TradingSymbol"] = df["Exchange"] + ":" + df["TradingSymbol"]
    return {int(k): v for k, v in zip(df[key].values, df[value].values)}


def ltp_by_symbol(ltps: Dict[str, str], mapper: Dict[int, str]) -> Dict[str, float]:
    vals = dict()
    for k, v in ltps.items():
        try:
            token = int(k.split("|")[-1])
            ltp = float(v)
            symbol = mapper.get(token)[4:]
            if symbol:
                vals[symbol] = ltp
        except Exception as e:
            pass
    return vals
