import redis
import json
from login_get_kite import get_kite, remove_token
from threading import Thread
import time


class Rediszero:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379,
                             decode_responses=True)
        self.channel_name = 'json_updates'
        self.kite = get_kite("bypass")
        self.g_list = ['NSE:NIFTYBEES']

        # Create a Redis Pub/Sub subscriber
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe(self.channel_name)

    def _store_message(self, key, value):
        # Create a dictionary with the given key and value
        message_data = {key: value}

        # Serialize the message data to JSON
        message_json = json.dumps(message_data)

        # Store the message in a Redis list
        self.r.lpush('message_list', message_json)

    def get_quote(self):
        try:
            resp = self.kite.ltp(self.g_list)
            if resp:
                quotes = [{k: v['last_price'] for k, v in resp.items()}]
                for quote in quotes:
                    for k, v in quote.items():
                        self._store_message(k, v)
        except Exception as e:
            print(e)
            remove_token()

    def process_messages(self):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                print("Received JSON data:", data)

    def fetch_and_publish_prices(self, interval=1):
        while True:
            self.get_quote()  # Fetch prices
            time.sleep(interval)

    def add_symbols(self, symbols_to_add):
        # Method for clients to add new symbols for get_quote updates
        small_set = set(symbols_to_add)
        bigger_set = set(self.g_list)
        # Find the items that are in small_set but not in bigger_set
        if (small_set - bigger_set):
            # Convert both lists to sets and perform a union operation
            combined_set = set(self.g_list).union(symbols_to_add)
            # Convert the result back to a list
            self.g_list = list(combined_set)


if __name__ == "__main__":
    rz = Rediszero()

    # Start a thread to fetch and publish prices every 1 second
    price_update_thread = Thread(target=rz.fetch_and_publish_prices, args=(1,))
    price_update_thread.daemon = True
    price_update_thread.start()

    # Start multiple Redis clients
    redis_client1 = Thread(target=rz.add_symbols, args=(["NSE:INFY"],))
    redis_client2 = Thread(target=rz.add_symbols, args=(["NSE:TCS"],))

    redis_client1.start()
    redis_client2.start()

    # Start processing messages in the main thread
    rz.process_messages()
