import time
import logging
import redis
logging.basicConfig()


def get_ltp(r: redis.Redis, itemid: int) -> None:
    error_count = 0
    while True:
        try:
            ltp = r.hget(itemid, "last_price")
            if not ltp:
                print(f"not able to get {itemid}")
                r.hset(itemid, "last_price",  -1)
                pass
            elif ltp.decode('utf-8') == -1:
                print(f"waiting for server {ltp}")
                pass
            else:
                ltp = ltp.decode('utf-8')
                print(f"found {itemid=}{ltp}")
                break
        except Exception as e:
            error_count += 1
            print(e)
            logging.warning(
                "Error #%d: %s; retrying",
                error_count, itemid
            )
            time.sleep(2)
            get_ltp(r, itemid)
    return ltp


r = redis.Redis(db=0)
while True:
    quote = get_ltp(r, "NSE:KOTAKBANK")
    print(quote)
    time.sleep(1)
