from login_get_kite import get_kite, remove_token
from redis import Redis
import json
import time
from threading import Thread
from typing import Any, Dict, List, Optional

last_quote_time = -1


class RedisClient:
    def __init__(self):
        self.kite = get_kite("bypass")
        self.redis = Redis(host='localhost', port=6379)
        self.psub = self.redis.pubsub()
        self.lst_exchsym: List[str] = ['NSE:NIFTYBEES']
        self.ltp: Optional[Dict[str, float]] = None
        self.pub()

    def get_quote(self) -> Optional[Dict[str, float]]:
        try:
            global last_quote_time
            current_time = int(time.time())

            current_time, decimal_part = divmod(time.time(), 1)
            # Check if at least 1 second has passed since the last quote request
            if current_time == last_quote_time:
                print(f"{decimal_part} you are too fast")
                time.sleep(1 - decimal_part)
            else:
                print(current_time, last_quote_time)
            last_quote_time = current_time
            resp = self.kite.ltp(self.lst_exchsym)
            if resp:
                quotes = {k: v['last_price'] for k, v in resp.items()}
                return quotes
        except Exception as e:
            print(e)
            remove_token()
            return None

    def pub(self) -> None:
        dct_exchsym = {}
        data = self.get_quote()
        if data:
            dct_exchsym = json.dumps(data)
            self.redis.set("user_data", dct_exchsym)
        self.redis.publish("channel", dct_exchsym)

    def listen_for_messages(self) -> None:
        for msg in self.psub.listen():
            if msg['type'] == 'message':
                bt_dct_exchsym = msg['data']
                self.ltp = json.loads(bt_dct_exchsym)


if __name__ == "__main__":
    rz = RedisClient()
    rz.psub.subscribe("channel")
    while True:
        print(rz.ltp)
