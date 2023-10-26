import time


class Wserver:
    ticks = {}
    subscribed_tkns = []
    feed_opened = False

    def __init__(self, broker):
        self.api = broker.finvasia
        self.api.start_websocket(
            order_update_callback=self.order_update_cb,
            subscribe_callback=self.subscribe_cb,
            socket_open_callback=self.socket_open_cb,
        )
        self.keys = ["lp", "e", "ts"]

    def order_update_cb(self, cb):
        pass
        # print(cb)

    def subscribe_cb(self, tick):
        if isinstance(tick, dict):
            self.ticks[tick["e"] + "|" + tick["tk"]] = float(tick["lp"])

    def socket_open_cb(self):
        self.feed_opened = True

    def ltp(self, tkns):
        if not isinstance(tkns, list):
            tkns = [tkns]
        if any(self.subscribed_tkns):
            self.api.unsubscribe(self.subscribed_tkns)
        self.ticks = {}
        self.api.subscribe(tkns)
        while not any(self.ticks):
            pass
        else:
            self.close_socket(tkns)
            return self.ticks

    def close_socket(self, tkns):
        self.subscribed_tkns = tkns
        self.api.close_websocket()


class Datafeed:
    def __init__(self, broker):
        self.broker = broker

    def ltp(self, exchsym):
        return Wserver(self.broker).ltp(exchsym)


if __name__ == "__main__":
    from omspy_brokers.finvasia import Finvasia
    import yaml
    from time import sleep

    BROKER = Finvasia
    dir_path = "../../"
    with open(dir_path + "config2.yaml", "r") as f:
        config = yaml.safe_load(f)[0]["config"]
        print(config)
        broker = BROKER(**config)
        if broker.authenticate():
            print("success")

    tokens = ["NSE|15332", "NSE|14366", "NSE|18614", "NFO|67281"]
    ws = Wserver(broker)
    while True:
        resp = ws.ltp(tokens)
        print(resp)
        sleep(1)
    obj = Datafeed(broker)
    while True:
        resp = obj.ltp(tokens)
        print(resp)
