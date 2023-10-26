import os
import sys
import logging
import time
import yaml
from time import sleep

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# sample
logging.basicConfig(level=logging.INFO)


class Wserver:
    # flag to tell us if the websocket is open
    socket_opened = False
    ltp = {}

    def __init__(self, broker):
        self.api = broker.finvasia
        ret = self.api.start_websocket(
            order_update_callback=self.event_handler_order_update,
            subscribe_callback=self.event_handler_quote_update,
            socket_open_callback=self.open_callback,
        )
        if ret:
            logging.debug(f"{ret} ws started")

    def open_callback(self):
        self.socket_opened = True
        print("app is connected")
        tokens = ["MCX|259601", "MCX|259602", "NSE|18614", "NFO|67281"]
        self.api.subscribe(tokens, feed_type="d")
        # api.subscribe(['NSE|22', 'BSE|522032'])

    # application callbacks
    def event_handler_order_update(self, message):
        logging.info("order event: " + str(message))

    def event_handler_quote_update(self, message):
        # e   Exchange
        # tk  Token
        # lp  LTP
        # pc  Percentage change
        # v   volume
        # o   Open price
        # h   High price
        # l   Low price
        # c   Close price
        # ap  Average trade price
        logging.debug(
            "quote event: {0}".format(time.strftime("%d-%m-%Y %H:%M:%S")) + str(message)
        )
        val = message.get("lp", False)
        if val:
            self.ltp[message["e"] + "|" + message["tk"]] = val


# end of callbacks


def get_time(time_string):
    data = time.strptime(time_string, "%d-%m-%Y %H:%M:%S")

    return time.mktime(data)


if __name__ == "__main__":
    from omspy_brokers.finvasia import Finvasia

    BROKER = Finvasia
    dir_path = "../../"
    with open(dir_path + "config2.yaml", "r") as f:
        config = yaml.safe_load(f)[0]["config"]
        print(config)
        broker = BROKER(**config)
        if broker.authenticate():
            print("success")

    wserver = Wserver(broker)
    while True:
        print(wserver.ltp)
