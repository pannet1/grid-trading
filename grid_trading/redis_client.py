from login_get_kite import get_kite, remove_token
from redis import Redis
import json
import time
from threading import Thread
from typing import Any, Dict, List, Optional


class RedisClient:
    def __init__(self):
        self.kite = get_kite("bypass")
        self.redis = Redis(host='localhost', port=6379)
        self.psub = self.redis.pubsub()
        self.psub.subscribe("channel")
        self.lst_exchsym: List[str] = ['NSE:NIFTYBEES']
        self.ltp: Optional[Dict[str, float]] = None

    def get_quote(self) -> Optional[Dict[str, float]]:
        try:
            resp = self.kite.ltp(self.lst_exchsym)
            if resp:
                quotes = {k: v['last_price'] for k, v in resp.items()}
                return quotes
        except Exception as e:
            print(e)
            remove_token()
            return None

    def pub(self, lst_new_symbols: Any = None) -> None:
        dct_exchsym = {}
        if lst_new_symbols and len(lst_new_symbols) > 0:
            # Method for clients to add new symbols for get_quote updates
            set_newsym = set(lst_new_symbols)
            set_oldsym = set(self.lst_exchsym)
            # Find the items that are in set_newsym but not in set_oldsym
            if (set_newsym - set_oldsym):
                # Convert both lists to sets and perform a union operation
                set_combo = set(self.lst_exchsym).union(lst_new_symbols)
                # Convert the result back to a list
                self.lst_exchsym = list(set_combo)
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
    # Start a thread to listen for messages
    message_thread = Thread(target=rz.listen_for_messages)
    message_thread.daemon = True
    message_thread.start()
    rz.pub()
    while True:
        data_to_publish = ['NSE:SBIN']
        rz.pub(data_to_publish)
        print(rz.ltp)
        time.sleep(1)
