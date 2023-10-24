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
from omspy.simulation.virtual import generate_price
from omspy_brokers.finvasia import Finvasia
from wserver import Wserver

try:
    from omspy_brokers.finvasia import Finvasia
except ImportError:
    from omspy.brokers.finvasia import Finvasia
    logger.error("omspy brokers not installed")

BROKER = Finvasia


def get_actual_broker():
    # config_file = os.path.join(
    #   os.environ["dir_path"], "systemtrader", "config.yaml")
    dir_path = "../../"
    with open(dir_path + "config2.yaml", "r") as f:
        config = yaml.safe_load(f)[0]["config"]
        broker = BROKER(**config)
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
                        name=k[4:],  # strip exchange from symbol
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


def convert_ltp_to_instruments(ltps: Dict[str, float]) -> List[Instrument]:
    instruments = []
    for k, v in ltps.items():
        try:
            # We are assigning zero to ohlc since they are mandatory
            inst = Instrument(
                name=k[4:],  # strip exchange from symbol
                last_price=v,
                open=0,
                high=0,
                low=0,
                close=0,
            )
            instruments.append(inst)
        except Exception as e:
            logger.error(f"Error {e} in symbol {k}")
    return instruments


class PaperBroker(ReplicaBroker):
    broker: BROKER
    symbols: Optional[List[str]]

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)

    def _zrun(self):
        """
        A simple runner for automation
        expects zerodha broker
        """
        quotes = self.broker.quote(self.symbols)
        instruments = convert_dict_to_instrument(quotes)
        self.update(instruments)
        # Mimicks broker order fill based on ltp
        self.run_fill()

    def _frun(self, wserver):
        """
        Run this method if use ltp from redis server
        expects any broker
        """
        ltp = wserver.ltp(self.symbols)
        instruments = convert_ltp_to_instruments(ltp)
        self.update(instruments)
        # Mimicks broker order fill based on ltp
        self.run_fill()

    def run(self):
        if isinstance(self.broker, Zerodha):
            self._zrun()
        else:
            wserver = Wserver(self.broker)
            self._frun(wserver)

    def ltp(self, symbols: List[str]) -> Dict[str, float]:
        """
        return the last price for the list of given symbols
        """
        symbols = [s[4:] for s in symbols]
        dct = {k: v.last_price for k, v in self.instruments.items()
               if k in symbols}
        return dct


def paper_broker() -> PaperBroker:
    broker = get_actual_broker()
    return PaperBroker(broker=broker)
