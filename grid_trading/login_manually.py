import yaml

BROKER = Finvasia
dir_path = "../../"
with open(dir_path + "config2.yaml", "r") as f:
    config = yaml.safe_load(f)[0]["config"]
    broker = BROKER(**config)
    broker.authenticate()

Wserver.start(broker)
while True:
    quote = Wserver.ltp(["NSE:TCS", "NSE:INFY"])
    print(quote)
