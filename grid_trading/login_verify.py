from omspy.brokers.finvasia import Finvasia
import yaml
import os

os.environ['HOME']
with open('../../finvasia.yaml') as f:
    config = yaml.safe_load(f)
    print(config)
broker = Finvasia(**config)
broker.authenticate()
