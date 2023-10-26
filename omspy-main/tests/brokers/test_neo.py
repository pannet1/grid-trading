from pathlib import PurePath
from omspy.brokers.neo import *
import pendulum
import pytest
import json
from unittest.mock import patch, call
from copy import deepcopy


@pytest.fixture
def mock_neo():
    broker = Neo(
        "consumer_key", "consumer_secret", "mobilenumber", "password", "two_fa"
    )
    with patch("neo_api_client.NeoAPI") as mock_broker:
        broker.neo = mock_broker
        return broker


@pytest.fixture
def mock_data():
    # mock data for neo
    with open("tests/data/kotak_neo.json") as f:
        dct = json.load(f)
        return dct


@patch("neo_api_client.NeoAPI")
def test_authenticate(mock_broker):
    broker = Neo(
        "consumer_key",
        "consumer_secret",
        mobilenumber="+9112345678",
        password="password",
        twofa=1111,
    )
    broker.neo = mock_broker
    broker.authenticate()
    mock_broker.login.assert_called_once()
    mock_broker.session_2fa.assert_called_once()


def test_order_place(mock_neo):
    broker = mock_neo
    broker.order_place(symbol="SBIN-EQ", side="buy", quantity=1)
    broker.neo.place_order.assert_called_once()
    expected = dict(
        exchange_segment="NSE",
        product="MIS",
        price="0",
        order_type="MKT",
        quantity="1",
        validity="DAY",
        trading_symbol="SBIN-EQ",
        transaction_type="B",
        disclosed_quantity="0",
        trigger_price="0",
    )
    call_list = broker.neo.place_order.call_args_list
    assert call_list[0].kwargs == expected


def test_order_modify(mock_neo):
    broker = mock_neo
    broker.order_place(symbol="SBIN-EQ", side="buy", quantity=1)
    broker.neo.place_order.assert_called_once()
    broker.order_modify(order_id="12345678", quantity=10, price=100)
    expected = dict(
        order_id="12345678",
        quantity="10",
        price="100",
        amo="NO",
        product="MIS",
        validity="DAY",
    )
    broker.neo.modify_order.assert_called_once()
    call_list = broker.neo.modify_order.call_args_list
    assert call_list[0].kwargs == expected


def test_order_cancel(mock_neo):
    broker = mock_neo
    broker.order_cancel(12345678)
    broker.neo.cancel_order.assert_called_once()


def test_orders(mock_neo, mock_data):
    mock_neo.neo.order_report.side_effect = [mock_data["orders"]] * 4
    broker = mock_neo
    orders = broker.orders
    assert len(orders) == 2
    for key in (
        "order_id",
        "symbol",
        "status",
        "product",
        "average_price",
        "filled_quantity",
        "quantity",
        "price",
        "trigger_price",
        "order_type",
    ):
        for order in orders:
            assert key in order


def test_orders_no_data(mock_neo, mock_data):
    mock_neo.neo.order_report.side_effect = dict(
        stat="failure", reason="wrong connection"
    )
    broker = mock_neo
    orders = broker.orders
    assert orders == [{}]


def test_orders_positions_quantity(mock_neo, mock_data):
    expected = mock_data["positions"]
    expected_buy = deepcopy(expected)
    expected_buy["data"][0]["flBuyQty"] = "75"
    expected_sell = deepcopy(expected)
    expected_sell["data"][0]["flSellQty"] = "75"
    mock_neo.neo.positions.side_effect = [expected, expected_buy, expected_sell]
    broker = mock_neo
    positions = broker.positions
    assert len(positions) == 1
    assert positions[0]["quantity"] == 0
    assert positions[0]["side"] == "SELL"

    # Test buy position
    positions = broker.positions
    assert len(positions) == 1
    assert positions[0]["quantity"] == 50
    assert positions[0]["side"] == "BUY"

    # Test buy positions
    positions = broker.positions
    assert len(positions) == 1
    assert positions[0]["quantity"] == -50
    assert positions[0]["side"] == "SELL"


def test_positions(mock_neo, mock_data):
    mock_neo.neo.positions.side_effect = [mock_data["positions"]] * 4
    broker = mock_neo
    positions = broker.positions
    for key in (
        "buy_amount",
        "product",
        "buy_quantity",
        "sell_quantity",
        "sell_amount",
        "symbol",
    ):
        for position in positions:
            assert key in position


def test_trades(mock_neo, mock_data):
    mock_neo.neo.trade_report.side_effect = [mock_data["trades"]] * 4
    broker = mock_neo
    trades = broker.trades
    assert len(trades) == 3
    for key in ("average_price", "filled_quantity", "symbol", "order_id"):
        for trade in trades:
            assert key in trade


def test_orders_data_conversion(mock_neo, mock_data):
    mock_neo.neo.order_report.return_value = mock_data["orders"]
    orders = mock_neo.orders
    int_cols = ["cnlQty", "quantity", "dscQty", "filled_quantity"]
    float_cols = ["price", "trigger_price", "average_price", "refLmtPrc"]
    for col in int_cols:
        for order in orders:
            assert type(order[col]) == int
    for col in float_cols:
        for order in orders:
            assert type(order[col]) == float


def test_positions_data_conversion(mock_neo, mock_data):
    mock_neo.neo.positions.return_value = mock_data["positions"]
    positions = mock_neo.positions
    int_cols = ["cfBuyQty", "cfSellQty", "buy_quantity", "sell_quantity"]
    float_cols = ["buy_amount", "cfSellAmt", "cfBuyAmt", "sell_amount"]
    for col in int_cols:
        for position in positions:
            assert type(position[col]) == int
    for col in float_cols:
        for position in positions:
            assert type(position[col]) == float


def test_trades_data_conversion(mock_neo, mock_data):
    mock_neo.neo.trade_report.return_value = mock_data["trades"]
    trades = mock_neo.trades
    int_cols = ["filled_quantity"]
    float_cols = ["average_price"]
    for col in int_cols:
        for trade in trades:
            assert type(trade[col]) == int
    for col in float_cols:
        for trade in trades:
            assert type(trade[col]) == float
