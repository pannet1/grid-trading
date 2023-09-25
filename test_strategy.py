import pytest
from strategy import *
from omspy.simulation.virtual import FakeBroker
from copy import deepcopy


@pytest.fixture
def strategy_buy():
    broker = FakeBroker()
    return Strategy(
        broker=broker,
        exchange="NSE",
        symbol="BHEL",
        side="buy",
        buy_quantity=10,
        buy_offset=2,
        buy_price=100,
        buy_target=3,
        max_buy_quantity=50,
        max_orders_cap=30,
        buy_stop_price=70,
    )


@pytest.fixture
def strategy_sell():
    broker = FakeBroker()
    return Strategy(
        broker=broker,
        exchange="NSE",
        symbol="BHEL",
        side="sell",
        sell_quantity=10,
        sell_offset=2,
        sell_price=100,
        sell_target=3,
        max_sell_quantity=50,
        max_orders_cap=30,
        sell_stop_price=120,
    )


@pytest.fixture
def strategy_both(strategy_buy):
    strategy = deepcopy(strategy_buy)
    strategy.side = "both"
    strategy.sell_quantity = 10
    strategy.sell_offset = 2
    strategy.sell_price = 100
    strategy.sell_target = 3
    strategy.max_sell_quantity = 50
    strategy.sell_stop_price = 120
    return strategy


def test_base_strategy():
    broker = FakeBroker()
    base = BaseStrategy(broker=broker)
    assert base.broker == broker == base.datafeed


def test_base_strategy_different_datafeed():
    broker = FakeBroker()
    datafeed = FakeBroker(name="feed")
    base = BaseStrategy(broker=broker, datafeed=datafeed)
    assert base.datafeed.name == "feed"


def test_strategy_defaults():
    broker = FakeBroker()
    strategy = Strategy(broker=broker, exchange="NSE", symbol="BHEL", side="buy")
    assert strategy.symbol == "BHEL"
    assert strategy.order is not None
    assert strategy.order.count == 0
    assert strategy.next_entry_price is None


def test_strategy_defaults_mixed(strategy_buy, strategy_sell, strategy_both):
    # shortcuts only
    buy = strategy_buy
    sell = strategy_sell
    both = strategy_both
    assert buy.buy_price == sell.sell_price == both.buy_price == both.sell_price
    assert buy.sell_price is None
    assert sell.buy_price is None
    assert both.sell_target == both.buy_target == buy.buy_target == sell.sell_target


def test_strategy_direction(strategy_buy, strategy_sell):
    assert strategy_buy.direction == 1
    assert strategy_sell.direction == -1
    broker = FakeBroker()
    strategy = Strategy(broker=broker, exchange="NSE", symbol="BHEL", side="both")
    assert strategy.direction is None


def test_strategy_buy_defaults(strategy_buy):
    buy = strategy_buy
    assert buy.next_entry_price == 98


def test_strategy_sell_defaults(strategy_sell):
    sell = strategy_sell
    assert sell.next_entry_price == 102

def test_strategy_create_entry_order_buy(strategy_buy):
    order = strategy_buy._create_entry_order()
    assert order.price == 98
    assert order.order_type == 'LIMIT'
    assert order.quantity == 10
    assert order.side == "buy"
    strategy_buy.buy_quantity = 20
    order = strategy_buy._create_entry_order()
    assert order.quantity == 20

def test_strategy_create_entry_order_buy(strategy_buy):
    order = strategy_buy._create_entry_order()
    assert order.price == 98
    assert order.order_type == 'LIMIT'
    assert order.quantity == 10
    assert order.side == "buy"
    strategy_buy.buy_quantity = 20
    order = strategy_buy._create_entry_order()
    assert order.quantity == 20

def test_strategy_create_entry_order_sell(strategy_sell):
    order = strategy_sell._create_entry_order()
    assert order.price == 102
    assert order.order_type == 'LIMIT'
    assert order.quantity == 10
    assert order.side == "sell"

def test_strategy_create_target_order_buy(strategy_buy):
    order = strategy_buy._create_target_order()
    assert order.trigger_price == 101
    assert order.price == 0
    assert order.order_type == 'SL-M'
    assert order.quantity == 10
    assert order.side == "sell"
    strategy_buy.buy_quantity = 20
    strategy_buy.buy_target = 4
    order = strategy_buy._create_target_order()
    assert order.quantity == 20
    assert order.trigger_price == 102
    assert order.price == 0

def test_strategy_create_target_order_sell(strategy_sell):
    order = strategy_sell._create_target_order()
    assert order.trigger_price == 99
    assert order.price == 0
    assert order.order_type == 'SL-M'
    assert order.quantity == 10
    assert order.side == "buy"
    strategy_sell.sell_quantity = 20
    strategy_sell.sell_target = 4
    order = strategy_sell._create_target_order()
    assert order.quantity == 20
    assert order.trigger_price == 98
