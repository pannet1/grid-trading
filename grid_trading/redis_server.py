from toolkit.utilities import Utilities
from login_get_kite import get_kite, remove_token
from redis import Redis
import time
from typing import Dict, List, Optional

last_quote_time = -1
kite = get_kite("bypass")


def scan_keys(redis_client: redis) -> List:
    cursor = 0
    keys = []
    while True:
        cursor, batch = redis_client.scan(cursor=cursor, match='*:*')
        keys.extend(batch)
        if cursor == 0:
            break
    return keys


def get_quotes(exchsym) -> Optional[Dict[str, float]]:
    try:
        global last_quote_time
        current_time = int(time.time())
        if current_time == last_quote_time:
            Utilities().slp_til_nxt_sec()
        last_quote_time = current_time
        resp = kite.ltp(exchsym)
        if resp:
            quotes = {k: {'last_price': v['last_price']}
                      for k, v in resp.items()}
            return quotes
    except Exception as e:
        print(e)
        remove_token()
        return None


r = Redis(db=0)
r.bgsave()
while True:
    exchsym = scan_keys(r)
    quotes = get_quotes(exchsym)
    if quotes:
        for exchsym, ltp in quotes.items():
            print(f"{exchsym}:{ltp}")
            r.hmset(exchsym, ltp)
