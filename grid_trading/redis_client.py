import redis
import json
import time
import threading
from login_get_kite import get_kite, remove_token


class Rediszero:
    def __init__(self):
        self.kite = get_kite("bypass")
        self.r = redis.Redis(host='localhost', port=6379)
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe("channel")
        self.g_list = ['NSE:NIFTYBEES']

    def get_quote(self):
        try:
            resp = self.kite.ltp(self.g_list)
            if resp:
                quotes = {k: v['last_price'] for k, v in resp.items()}
                return quotes
        except Exception as e:
            print(e)
            remove_token()

    def pub(self, symbols_to_add=None):
        if symbols_to_add and len(symbols_to_add) > 0:
            # Method for clients to add new symbols for get_quote updates
            small_set = set(symbols_to_add)
            bigger_set = set(self.g_list)
            # Find the items that are in small_set but not in bigger_set
            if (small_set - bigger_set):
                # Convert both lists to sets and perform a union operation
                combined_set = set(self.g_list).union(symbols_to_add)
                # Convert the result back to a list
                self.g_list = list(combined_set)
        data = self.get_quote()
        string_data = json.dumps(data)
        self.r.set("user_data", string_data)
        self.r.publish("channel", string_data)

    def listen_for_messages(self):
        for msg in self.pubsub.listen():
            if msg['type'] == 'message':
                retrieved_data_string = msg['data']
                retrieved_data = json.loads(retrieved_data_string)
                self.ltp = retrieved_data


if __name__ == "__main__":
    rz = Rediszero()
    # Start a thread to listen for messages
    message_thread = threading.Thread(target=rz.listen_for_messages)
    message_thread.daemon = True
    message_thread.start()
    rz.pub()
    while True:
        data_to_publish = ['NSE:SBIN']
        rz.pub(data_to_publish)
        print(rz.ltp)
        time.sleep(1)
