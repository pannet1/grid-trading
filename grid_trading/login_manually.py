from omspy_brokers.finvasia import Finvasia
import yaml
import pyotp
import time


BROKER = Finvasia
dir_path = "../../"
with open(dir_path + "config2.yaml", "r") as f:
    config = yaml.safe_load(f)[0]["config"]
    print(config)

time.sleep(5)
twoFA = pyotp.TOTP(config["pin"]).now()
print(twoFA)
