import time


class Wserver:
    ticks = {}
    tkns = []
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
            if tick["e"] == "NSE":
                self.ticks[tick["e"] + ":" + tick["ts"][:-3]] = float(tick["lp"])
            else:
                self.ticks[tick["e" + ":"] + tick["ts"]] = float(tick["lp"])

    def socket_open_cb(self):
        self.feed_opened = True

    def ltp(self, lst):
        if not isinstance(lst, list):
            lst = [lst]
        tkns = []
        for k in lst:
            v = k.split(":")
            if v[0] == "NSE":
                v[1] = v[1] + "-EQ"
            resp = self.api.searchscrip(exchange=v[0], searchtext=v[1])
            if resp:
                tkn = resp["values"][0]["token"]
                tkns.append(v[0] + "|" + tkn)
        if any(tkns):
            if any(self.tkns):
                self.api.unsubscribe(self.tkns)
            self.ticks = {}
            self.api.subscribe(tkns)
            while not any(self.ticks):
                pass
            else:
                self.close_socket(tkns)
                return self.ticks

    def close_socket(self, tkns):
        self.tkns = tkns
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

    """
    ws = Wserver(broker)
    resp = ws.ltp(["NSE:TCS", "NSE:INFY"])
    print(resp)
    """

    obj = Datafeed(broker)
    while True:
        resp = obj.quote(["NSE:TCS", "NSE:INFY"])
        print(resp)

    # Add a delay or perform other operations here

    # When done, close the WebSocket connection
