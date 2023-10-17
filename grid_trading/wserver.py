

import time


class Wserver:
    exchsym = []
    ticks = None
    feed_opened = False

    @classmethod
    def order_update_cb(cls, cb):
        print(cb)

    @classmethod
    def subscribe_cb(cls, ticks):
        print(ticks)
        cls.ticks = ticks

    @classmethod
    def socket_open_cb(cls):
        cls.feed_opened = True

    @classmethod
    def set_exchsym(cls, es):
        if isinstance(es, list):
            cls.exchsym.extend(es)
        else:
            cls.exchsym.append(es)

    @classmethod
    def ltp(cls, lst):
        cls.set_exchsym(lst)
        dct = {item[4:]: item[:3] for item in cls.exchsym}
        dct = {k: cls.api.searchscrip(exchange=v, searchtext=k)[
            'values'][0] for k, v in dct.items()}
        lst = [k + '|' + v['token'] for k, v in dct.items()]
        cls.api.subscribe(lst)
        return cls.ticks

    @classmethod
    def start(cls, broker):
        cls.api = broker.finvasia
        cls.api.start_websocket(
            order_update_callback=cls.order_update_cb,
            subscribe_callback=cls.subscribe_cb,
            socket_open_callback=cls.socket_open_cb)

        while not cls.feed_opened:
            print("waiting for feed to open")
            time.sleep(1)


if __name__ == "__main__":
    from omspy_brokers.finvasia import Finvasia
    import yaml

    BROKER = Finvasia
    dir_path = "../../"
    with open(dir_path + "config2.yaml", "r") as f:
        config = yaml.safe_load(f)[0]["config"]
        broker = BROKER(**config)
        broker.authenticate()

    Wserver.start(broker)
    while True:
        quote = Wserver.ltp(["NSE:TCS", "NSE:INFY"])
        print(quote)
