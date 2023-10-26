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
    df = pd.read_csv("https://shoonya.finvasia.com/MCX_symbols.txt.zip")
    return {int(k): v for k, v in zip(df[key].values, df[value].values)}


search_value = "CRUDEOIL15NOV23P7100"
resp = get_exchange_token_map_finvasia()
for k, v in resp.items():
    if v == search_value:
        print(f"token  for {search_value} is {k}")
        break


# Add a delay or perform other operations here

# When done, close the WebSocket connection
