from omspy_brokers.finvasia import Finvasia
import yaml
from pprint import pprint

BROKER = Finvasia
dir_path = "../../"
with open(dir_path + "config2.yaml", "r") as f:
    config = yaml.safe_load(f)[0]["config"]
    print(config)
    broker = BROKER(**config)
    if broker.authenticate():
        print("success")


resp = broker.searchscrip(exchange="MCX", searchtext="C")
pprint(f"{resp=}")

# Add a delay or perform other operations here

# When done, close the WebSocket connection
