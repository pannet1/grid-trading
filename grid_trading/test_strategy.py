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
        ltp=100,
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
        ltp=100,
    )


@pytest.fixture
def strategy_both(strategy_buy):
    broker = FakeBroker()
    strategy = Strategy(
        broker=broker,
        exchange="NSE",
        symbol="BHEL",
        side="both",
        buy_quantity=10,
        buy_offset=2,
        buy_price=100,
        buy_target=3,
        max_buy_quantity=50,
        max_orders_cap=30,
        buy_stop_price=70,
        ltp=100,
    )
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
    strategy = Strategy(
        broker=broker, exchange="NSE", symbol="BHEL", side="buy", ltp=100, buy_price=101, buy_offset=2
    )
    assert strategy.symbol == "BHEL"
    assert strategy.orders == []
    assert strategy._prices == set()


def test_strategy_defaults_direction_side_case():
    broker = FakeBroker()
    strategy = Strategy(
        broker=broker, exchange="NSE", symbol="BHEL", side="BUY", ltp=100, buy_price=102, buy_offset=2
    )
    assert strategy.direction == 1


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
    assert order.order_type == "LIMIT"
    assert order.quantity == 10
    assert order.side == "buy"
    strategy_buy.buy_quantity = 20
    order = strategy_buy._create_entry_order()
    assert order.quantity == 20


def test_strategy_create_entry_order_buy(strategy_buy):
    order = strategy_buy._create_entry_order()
    assert order.price == 98
    assert order.order_type == "LIMIT"
    assert order.quantity == 10
    assert order.side == "buy"
    strategy_buy.buy_quantity = 20
    order = strategy_buy._create_entry_order()
    assert order.quantity == 20


def test_strategy_create_entry_order_sell(strategy_sell):
    order = strategy_sell._create_entry_order()
    assert order.price == 102
    assert order.order_type == "LIMIT"
    assert order.quantity == 10
    assert order.side == "sell"


def test_strategy_create_target_order_buy(strategy_buy):
    strategy_buy.ltp = 98
    order = strategy_buy._create_target_order()
    assert order.trigger_price == 101
    assert order.price == 101
    assert order.order_type == "LIMIT"
    assert order.quantity == 10
    assert order.side == "sell"
    strategy_buy.buy_quantity = 20
    strategy_buy.buy_target = 4
    order = strategy_buy._create_target_order()
    assert order.quantity == 20
    assert order.trigger_price == 102
    assert order.price == 102


def test_strategy_create_target_order_sell(strategy_sell):
    strategy_sell.ltp = 102
    order = strategy_sell._create_target_order()
    assert order.trigger_price == order.price == 99
    assert order.order_type == "LIMIT"
    assert order.quantity == 10
    assert order.side == "buy"
    strategy_sell.sell_quantity = 20
    strategy_sell.sell_target = 4
    order = strategy_sell._create_target_order()
    assert order.quantity == 20
    assert order.trigger_price == order.price == 98


def test_strategy_create_order(strategy_buy, strategy_sell):
    buy = strategy_buy
    sell = strategy_sell
    buy.ltp = 98
    sell.ltp = 102
    buy.create_order()
    sell.create_order()
    assert len(buy.orders) == 1
    assert len(sell.orders) == 1
    assert buy.orders[0].get("entry").price == 98
    assert buy.orders[0].get("target").trigger_price == 101
    assert sell.orders[0].get("entry").price == 102
    assert sell.orders[0].get("target").trigger_price == 99


def test_strategy_update_next_entry_price(strategy_buy, strategy_sell, strategy_both):
    buy = strategy_buy
    sell = strategy_sell
    both = strategy_both
    assert buy.update_next_entry_price() == 96
    for i in range(3):
        buy.update_next_entry_price()
    assert buy.next_entry_price == 90
    assert sell.update_next_entry_price() == 104
    sell.sell_offset = 3
    sell.update_next_entry_price()
    sell.update_next_entry_price()
    assert sell.next_entry_price == 110
    both.update_next_entry_price()
    assert both.update_next_entry_price() is None
    both.update_next_entry_price()
    assert both.update_next_entry_price() is None


def test_entry_buy_strategy(strategy_buy):
    s = strategy_buy
    s.entry()
    assert len(s.orders) == 0
    s.ltp = 98
    s.entry()
    assert len(s.orders) == 1
    for i in range(10):
        s.entry()
    assert len(s.orders) == 1
    s.ltp = 90
    for i in range(10):
        s.entry()
    # Should have placed orders till the next entry price is less than ltp
    assert len(s.orders) == 5
    # Price jump
    for i in range(10):
        s.ltp = s.ltp + 2
        s.entry()
    # Check order limit prices
    assert [x.get("entry").price for x in s.orders] == [98, 96, 94, 92, 90]


def test_entry_sell_strategy(strategy_sell):
    s = strategy_sell
    s.entry()
    assert len(s.orders) == 0
    s.ltp = 101
    s.entry()
    assert len(s.orders) == 0
    s.ltp = 102
    s.entry()
    assert len(s.orders) == 1
    for i in range(10):
        s.entry()
    assert len(s.orders) == 1
    # Price jump
    s.ltp = 110
    for i in range(10):
        s.entry()
    assert len(s.orders) == 5

    # Check order limit prices
    assert [x.get("entry").price for x in s.orders] == [102, 104, 106, 108, 110]

def test_strategy_json_info(strategy_buy, strategy_sell):
    buy = strategy_buy
    sell = strategy_sell
    buy.ltp = 95
    sell.ltp = 110
    order = buy.create_order()
    for o in order.orders:
        assert json.loads(o.JSON) == dict(ltp=95, target=98, expected_entry=98)
    order = sell.create_order()
    for o in order.orders:
        assert json.loads(o.JSON) == dict(ltp=110, target=107, expected_entry=102)

def test_strategy_price_jump_target(strategy_buy, strategy_sell):
    """
    check orders when the price jumps
    """
    buy = strategy_buy
    sell = strategy_sell 
    buy.ltp = 90
    for i in range(10):
        buy.entry()
    assert len(buy.orders) == 5
    orders = [x.get('target') for x in buy.orders]
    assert [x.price for x in orders] == [93]*5

    sell.ltp = 110
    for i in range(10):
        sell.entry()
    assert len(sell.orders) == 5
    orders = [x.get('target') for x in sell.orders]
    assert [x.price for x in orders] == [107]*5


def test_exit_buy(strategy_buy):
    s = strategy_buy
    s.run(dict(BHEL=98))
    assert len(s.orders) == 1
    assert all([x.order_id for x in s.orders[0].orders]) is False
    s.run(dict(BHEL=100))
    assert all([x.order_id for x in s.orders[0].orders]) is False
    s.run(dict(BHEL=101))
    assert all([x.order_id for x in s.orders[0].orders]) is True


def test_exit_buy(strategy_sell):
    s = strategy_sell
    s.run(dict(BHEL=102))
    assert len(s.orders) == 1
    assert all([x.order_id for x in s.orders[0].orders]) is False
    s.run(dict(BHEL=100))
    assert all([x.order_id for x in s.orders[0].orders]) is False
    s.run(dict(BHEL=99))
    assert all([x.order_id for x in s.orders[0].orders]) is True


def test_set_initial_prices(strategy_buy, strategy_sell):
    buy,sell = strategy_buy, strategy_sell
    assert buy.initial_price == 100
    assert sell.initial_price  == 100
    buy.ltp = 105
    buy.set_initial_prices()
    assert buy.initial_price == 100
    assert buy.next_forward_price == 98
    assert buy.next_backward_price == 98
    assert sell.next_forward_price == 102
    assert sell.next_backward_price == 102

def test_set_initial_price_no_ltp(strategy_buy):
    buy = strategy_buy
    buy.ltp = None
    buy.initial_price == 100
    buy._initial_price = None
    buy.ltp = None
    assert buy.initial_price is None
    buy.set_initial_prices()
    assert buy.initial_price is None
    buy.ltp = 101
    buy.set_initial_prices()
    assert buy.initial_price == 101
    buy.ltp = 102
    buy.set_initial_prices()
    assert buy.initial_price == 101
