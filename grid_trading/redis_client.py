from logzero import logger as logging
import redis

r = redis.Redis(host='localhost', port=6379)


class RedisClient:

    def authenticate(self):
        try:
            response = r.ping()
            if response:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error: {str(e)}")

    def get_one(self, itemid: int) -> None:
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

    def get_ltp(self, lst_exchsym):
        dct = {}
        new_lst = []
        if isinstance(lst_exchsym, list):
            for lst in lst_exchsym:
                quote = self.get_one(lst)
                new_lst.append(quote)
        dct = {lst_exchsym[i]: new_lst[i] for i in range(len(new_lst))}
        dct = {k: v for k, v in dct.items() if v is not None}
        return dct
