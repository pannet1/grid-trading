import pytest
from strategy import *
from omspy.simulation.virtual import FakeBroker


def test_base_strategy():
    broker = FakeBroker()
    base = BaseStrategy(broker=broker)
    assert base.broker == broker == base.datafeed


def test_base_strategy_different_datafeed():
    broker = FakeBroker()
    datafeed = FakeBroker(name='feed')
    base = BaseStrategy(broker=broker, datafeed=datafeed)
    assert base.datafeed.name == 'feed'
