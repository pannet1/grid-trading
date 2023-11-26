from omspy_brokers.finvasia import Finvasia
import yaml

BROKER = Finvasia
dir_path = "../../"
with open(dir_path + "config2.yaml", "r") as f:
    config = yaml.safe_load(f)[0]["config"]
    print(config)
    broker = BROKER(**config)
    if broker.authenticate():
        print("success")

print(broker.orders)
