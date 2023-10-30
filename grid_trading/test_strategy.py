import pytest
from strategy import *
from omspy.simulation.virtual import FakeBroker
from copy import deepcopy
from unittest.mock import patch


@pytest.fixture
def strategy_args():
    broker = FakeBroker()
    return dict(
        broker=broker,
        exchange="NSE",
        symbol="BHEL",
    )


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
        broker=broker,
        exchange="NSE",
        symbol="BHEL",
        side="buy",
        ltp=100,
        buy_price=101,
        buy_offset=2,
    )
    assert strategy.symbol == "BHEL"
    assert strategy.orders == []
    assert strategy._prices == set()


def test_strategy_defaults_direction_side_case():
    broker = FakeBroker()
    strategy = Strategy(
        broker=broker,
        exchange="NSE",
        symbol="BHEL",
        side="BUY",
        ltp=100,
        buy_price=102,
        buy_offset=2,
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
    assert buy.next_forward_price == 100
    assert buy.next_backward_price == 98


def test_strategy_sell_defaults(strategy_sell):
    sell = strategy_sell
    sell.next_forward_price == 102
    sell.next_backward_price == 100


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
        print(o.JSON)
        assert json.loads(o.JSON) == dict(ltp=95, target=98, backward=98, forward=100)
    order = sell.create_order()
    for o in order.orders:
        assert json.loads(o.JSON) == dict(
            ltp=110, target=107, forward=110, backward=108
        )


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
    orders = [x.get("target") for x in buy.orders]
    assert [x.price for x in orders] == [93] * 5

    sell.ltp = 110
    for i in range(10):
        sell.entry()
    assert len(sell.orders) == 5
    orders = [x.get("target") for x in sell.orders]
    assert [x.price for x in orders] == [107] * 5


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
    buy, sell = strategy_buy, strategy_sell
    assert buy.initial_price == 100
    assert sell.initial_price == 100
    buy.ltp = 105
    buy.set_initial_prices()
    assert buy.initial_price == 100
    assert buy.next_forward_price == 100
    assert buy.next_backward_price == 98
    assert sell.next_forward_price == 102
    assert sell.next_backward_price == 100


def test_set_initial_prices_no_ltp(strategy_buy):
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


def test_set_initial_prices_buy(strategy_args):
    s = Strategy(**strategy_args, side="buy", buy_price=100, buy_offset=2, ltp=100)
    assert s.initial_price == 100
    assert s.next_forward_price
    assert s.next_backward_price == 98
    s = Strategy(**strategy_args, side="buy", buy_price=100, buy_offset=2, ltp=107)
    assert s.initial_price == 107
    assert s.next_forward_price == 100
    assert s.next_backward_price == 98
    s = Strategy(**strategy_args, side="buy", buy_price=100, buy_offset=2, ltp=94)
    assert s.initial_price == 94
    assert s.next_forward_price == 94
    assert s.next_backward_price == 92


def test_set_initial_prices_sell(strategy_args):
    s = Strategy(**strategy_args, side="sell", sell_price=100, sell_offset=2, ltp=100)
    assert s.initial_price == 100
    assert s.next_forward_price == 102
    assert s.next_backward_price == 100
    s = Strategy(**strategy_args, side="sell", sell_price=100, sell_offset=2, ltp=107)
    assert s.initial_price == 107
    assert s.next_forward_price == 107
    assert s.next_backward_price == 105

    s = Strategy(**strategy_args, side="sell", sell_price=100, sell_offset=2, ltp=97)
    assert s.initial_price == 97
    assert s.next_forward_price == 102
    assert s.next_backward_price == 100


def test_set_next_prices_buy(strategy_buy):
    s = strategy_buy
    s.set_next_prices()
    assert s.next_backward_price == 98
    assert s.next_forward_price == 100
    # price goes up
    s.set_next_prices(price=104)
    assert s.next_backward_price == 98
    assert s.next_forward_price == 100
    # price goes down
    s.ltp = 98
    s.set_next_prices()
    assert s.next_backward_price == 98
    assert s.next_forward_price == 100
    s.ltp = 97
    s.set_next_prices()
    assert s.next_backward_price == 96
    assert s.next_forward_price == 98
    s.ltp = 95.4
    s.set_next_prices()
    assert s.next_backward_price == 94
    assert s.next_forward_price == 96
    s.set_next_prices(price=97)
    assert s.next_backward_price == 96
    assert s.next_forward_price == 98


def test_set_next_prices_sell(strategy_sell):
    s = strategy_sell
    s.set_next_prices()
    s.set_next_prices()
    assert s.next_forward_price == 102
    assert s.next_backward_price == 100
    s.set_next_prices(price=103)
    assert s.next_forward_price == 104
    assert s.next_backward_price == 102
    s.set_next_prices(price=109)
    assert s.next_forward_price == 106
    assert s.next_backward_price == 104
    s.ltp = 103
    s.set_next_prices()
    assert s.next_forward_price == 104
    assert s.next_backward_price == 102


def test_next_prices_buy_outside_price(strategy_buy):
    s = strategy_buy
    for ltp in range(104, 112):
        s.ltp = ltp
        s.set_next_prices()
        assert s.next_forward_price == 100
        assert s.next_backward_price == 98
    s.set_next_prices(price=97)
    assert s.next_forward_price == 98
    assert s.next_backward_price == 96
    s.set_next_prices(price=97)
    s.ltp = 103
    s.set_next_prices()
    assert s.next_forward_price == 100
    assert s.next_backward_price == 98


def test_next_prices_sell_outside_price(strategy_sell):
    s = strategy_sell
    for ltp in range(80, 96):
        s.ltp = ltp
        s.set_next_prices()
        assert s.next_forward_price == 102
        assert s.next_backward_price == 100
    s.set_next_prices(price=103)
    assert s.next_forward_price == 104
    assert s.next_backward_price == 102
    s.ltp = 97
    s.set_next_prices()
    assert s.next_forward_price == 102
    assert s.next_backward_price == 100


def test_before_entry_check_outside_prices(strategy_buy, strategy_sell):
    buy, sell = strategy_buy, strategy_sell
    assert buy.before_entry_check_outside_prices() is True
    assert sell.before_entry_check_outside_prices() is True
    buy.ltp = 97.6
    sell.ltp = 103.2
    assert buy.before_entry_check_outside_prices() is True
    assert sell.before_entry_check_outside_prices() is True
    buy.ltp = 101
    sell.ltp = 99
    assert buy.before_entry_check_outside_prices() is False
    assert sell.before_entry_check_outside_prices() is False


def test_before_entry_check_between_prices_buy(strategy_buy):
    s = strategy_buy
    assert s.before_entry_check_between_prices() is False
    for ltp in (98, 98.4, 99.4, 99.2, 100):
        s.ltp = ltp
        assert s.before_entry_check_between_prices() is False
    s.ltp = 97.6
    assert s.before_entry_check_between_prices() is True
    s.set_next_prices()
    # Check after prices are changed
    assert s.next_forward_price == 98
    assert s.next_backward_price == 96
    for ltp in (95.6, 98.4):
        s.ltp = ltp
        assert s.before_entry_check_between_prices() is True


def test_before_entry_check_between_prices_sell(strategy_sell):
    s = strategy_sell
    assert s.before_entry_check_between_prices() is False
    for ltp in (100, 100.2, 100.5, 101.3, 102):
        s.ltp = ltp
        assert s.before_entry_check_between_prices() is False
    s.ltp = 102.05
    assert s.before_entry_check_between_prices() is True
    s.set_next_prices()
    assert s.next_forward_price == 104
    assert s.next_backward_price == 102
    for ltp in (104.6, 101.4):
        s.ltp = ltp
        assert s.before_entry_check_between_prices() is True


def test_can_enter_prices_buy(strategy_buy):
    s = strategy_buy
    assert s.can_enter is False
    s.ltp = 103
    assert s.can_enter is False
    s.ltp = 97.9
    assert s.can_enter is True


def test_can_enter_prices_sell(strategy_sell):
    s = strategy_sell
    assert s.can_enter is False
    s.ltp = 97.9
    assert s.can_enter is False
    s.ltp = 103
    assert s.can_enter is True


def test_can_enter_no_ltp(strategy_buy):
    strategy_buy.ltp = 97.9
    strategy_buy.can_enter is True
    strategy_buy.ltp = None
    strategy_buy.can_enter is False


def test_product_order_place(strategy_buy):
    s = strategy_buy
    with patch("omspy.simulation.virtual.FakeBroker") as mock_broker:
        s.broker = mock_broker
        exchanges = ("NSE", "BSE", "NFO", "MCX")
        codes = ("C", "C", "M", "M")
        for i, (e, c) in enumerate(zip(exchanges, codes)):
            order = Order(symbol=s.symbol, side="buy", quantity=100)
            s.exchange = e
            s._place_one_order(order)
            call_args = mock_broker.order_place.call_args_list[i]
            assert call_args.kwargs["product"] == c
        assert mock_broker.order_place.call_count == 4

def test_total_quantity(strategy_buy):
    s = strategy_buy
    s.run({'BHEL': 97.9})
    assert len(s.orders) == 1
    assert s.total_quantity == (10,10)
    s.run({'BHEL': 95.9})
    s.run({'BHEL': 93.9})
    assert len(s.orders) == 3
    assert s.total_quantity == (30,30)

def test_before_entry_check_max_quantity(strategy_buy):
    s = strategy_buy
    s.max_buy_quantity = 0
    s.run({'BHEL': 97.9})
    assert len(s.orders) == 0
    s.max_buy_quantity = 30
    s.run({'BHEL': 97.9})
    assert len(s.orders) == 1
    for i in range(10):
        s.run({'BHEL': 95.9})
    assert len(s.orders) == 2
    for i in range(20):
        s.run({'BHEL':95.9-i})
    assert len(s.orders) == 3
    assert s.total_quantity == (30,30)


