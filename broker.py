"""
This is a paper broker module to test trades
"""
from omspy.brokers.zerodha import Zerodha
from omspy.simulation.virtual import ReplicaBroker, FakeBroker
from logzero import logger
import os
import yaml
from typing import List, Dict, Optional
from omspy.simulation.models import Instrument


def get_actual_broker() -> Zerodha:
    config_file = os.path.join(os.environ["HOME"], "systemtrader", "config.yaml")
    with open(config_file) as f:
        config = yaml.safe_load(f)[0]["config"]
        broker = Zerodha(**config)
        broker.authenticate()
        return broker


def convert_dict_to_instrument(quotes: Dict[str, Dict]) -> List[Instrument]:
    """
    Convert dictionary to instrument
    """
    instruments = []
    for k, v in quotes.items():
        try:
            keys = ("instrument_token", "last_price", "ohlc")
            if type(v) == dict:
                if all([key in v for key in keys]):
                    inst = Instrument(
                        name=k,
                        token=v["instrument_token"],
                        last_price=v["last_price"],
                        open=v["ohlc"]["open"],
                        high=v["ohlc"]["high"],
                        low=v["ohlc"]["low"],
                        close=v["ohlc"]["close"],
                    )
                    if "volume_traded" in v:
                        inst.volume = v["volume_traded"]
                    if "oi" in v:
                        inst.open_interest = v["oi"]
                    instruments.append(inst)
        except Exception as e:
            logger.error(f"Error {e} in symbol {k}")
    return instruments


class PaperBroker(ReplicaBroker):
    broker: Zerodha
    symbols: Optional[List[str]]

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)

    def run(self):
        """
        A simple runner for automation
        """
        quotes = self.broker.quote(self.symbols)
        instruments = convert_dict_to_instrument(quotes)
        self.update(instruments)
        self.run_fill()

    def ltp(self, symbols: List[str]) -> Dict[str, float]:
        """
        return the last price for the list of given symbols
        """
        dct = {k: v.last_price for k, v in self.instruments.items() if k in symbols}
        return dct


def paper_broker() -> PaperBroker:
    broker = get_actual_broker()
    return PaperBroker(broker=broker)
