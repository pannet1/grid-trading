import logging
import redis

logging.basicConfig(level=10)

r = redis.Redis(db=0)


def get_one(itemid: int) -> None:
    error_count = 0
    retry = 15
    attempt = 0
    while True:
        try:
            ltp = r.hget(itemid, "last_price")
            if not ltp:
                logging.debug(f"not able to get {itemid}")
                r.hset(itemid, "last_price",  -1)
                r.expire(itemid, 15)
                continue
            elif float(ltp.decode('utf-8')) < 0:
                logging.debug(f"waiting for server {ltp}")
                if attempt <= retry:
                    attempt += 1
                    continue
                else:
                    ltp = None
                    break
            else:
                ltp = float(ltp.decode('utf-8'))
                logging.debug(f"found {itemid=}{ltp}")
                break
        except ValueError as v:
            logging.debug(f"value error {v}")
        except Exception as e:
            error_count += 1
            print(e)
            logging.warning(
                "Error #%d: %s; retrying",
                error_count, itemid
            )
            ltp = None
            break
    return ltp


def ltp(lst_exchsym):
    new_lst = []
    if isinstance(lst_exchsym, list):
        for lst in lst_exchsym:
            quote = get_one(lst)
            new_lst.append(quote)
    dct = {lst_exchsym[i]: new_lst[i] for i in range(len(new_lst))}
    return dct
