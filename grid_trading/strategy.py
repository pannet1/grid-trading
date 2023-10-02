from pydantic import BaseModel, PrivateAttr
from omspy.order import Order, CompoundOrder
import pendulum
from typing import Any, List, Optional, Dict
from collections import Counter
import json
from logzero import logger
from sqlite_utils import Database

from omspy.simulation.models import OrderType, VOrder


class BaseStrategy(BaseModel):
    """
    This is just an abstract class from which other strategies
    would inherit.
    Common methods that affect all strategies are placed here
    """

    broker: Any
    datafeed: Optional[Any] = None
    connection: Optional[Database] = None
    cycle: int = 0
    _broker_name: str

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True

    def __init__(self, **data):
        super().__init__(**data)
        broker_name = type(self.broker).__name__.lower()
        self._broker_name = broker_name
        # Set datafeed
        if self.datafeed is None:
            self.datafeed = self.broker

    @property
    def broker_name(self) -> str:
        return self._broker_name

    @property
    def can_enter(self) -> bool:
        methods = [attr for attr in dir(
            self) if attr.startswith("before_entry")]
        checks = [getattr(self, attr)() for attr in methods]
        return all(checks)


class Strategy(BaseStrategy):
    exchange: str
    symbol: str
    side: str
    ltp: Optional[float]
    buy_quantity: Optional[int]
    buy_offset: Optional[float]
    buy_target: Optional[float]
    buy_price: Optional[float]
    sell_quantity: Optional[int]
    sell_offset: Optional[float]
    sell_target: Optional[float]
    sell_price: Optional[float]
    status: bool = True
    max_buy_quantity: Optional[float]
    max_sell_quantity: Optional[float]
    max_orders_cap: Optional[float]
    buy_stop_price: Optional[float]
    sell_stop_price: Optional[float]
    orders: Optional[List[CompoundOrder]]
    _direction: Optional[int]
    _next_entry_price: Optional[float]

    def __init__(self, **data):
        super().__init__(**data)
        self.orders = []
        self._next_entry_price = None
        if str(self.side).lower() == "buy":
            self._direction = 1
        elif str(self.side).lower() == "sell":
            self._direction = -1
        else:
            self._direction = None

        if self.direction == 1:
            if self.buy_price and self.buy_offset:
                self._next_entry_price = self.buy_price - self.buy_offset
        elif self.direction == -1:
            if self.sell_price and self.sell_offset:
                self._next_entry_price = self.sell_price + self.sell_offset

    @property
    def direction(self):
        return self._direction

    @property
    def next_entry_price(self):
        return self._next_entry_price

    def _create_entry_order(self) -> Optional[Order]:
        """
        Create a order
        """
        if self.direction == 1:
            quantity = self.buy_quantity
            side = "buy"
        elif self.direction == -1:
            quantity = self.sell_quantity
            side = "sell"
        else:
            logger.warning("No direction yet; so order cannot be created")
            return None
        order = Order(
            symbol=self.symbol,
            side=side,
            quantity=quantity,
            price=self.next_entry_price,
            order_type="LIMIT",
        )
        return order

    def _create_target_order(self) -> Optional[Order]:
        if self.direction == 1:
            quantity = self.buy_quantity
            price = self.ltp + self.buy_target
            side = "sell"
        elif self.direction == -1:
            quantity = self.sell_quantity
            price = self.ltp - self.sell_target
            side = "buy"
        else:
            logger.warning("No direction yet; so order cannot be created")
            return None
        order = Order(
            symbol=self.symbol,
            side=side,
            quantity=quantity,
            trigger_price=price,
            price=price,
            order_type="LIMIT",
        )
        return order

    def create_order(self) -> Optional[CompoundOrder]:
        com = CompoundOrder(broker=self.broker, connection=self.connection)
        entry = self._create_entry_order()
        target = self._create_target_order()
        info = json.dumps(
            dict(
                ltp=self.ltp, expected_entry=self.next_entry_price, target=target.price
            )
        )
        entry.JSON = info
        target.JSON = info
        if entry and target:
            com.add(order=entry, key="entry")
            com.add(order=target, key="target")
            self.orders.append(com)
        return com

    def update_next_entry_price(self) -> Optional[float]:
        """
        Update the next entry price to be entered into
        """
        if self._next_entry_price:
            if self.direction == 1:
                self._next_entry_price = self.next_entry_price - self.buy_offset
            elif self.direction == -1:
                self._next_entry_price = self.next_entry_price + self.sell_offset
            return self.next_entry_price
        else:
            logger.debug("Entry price still not configured")

    def _place_one_order(self, order: Order):
        """
        Execute one order
        """
        response = order.execute(
            broker=self.broker, order_type="LIMIT", exchange=self.exchange
        )
        if isinstance(response, VOrder):
            order_id = response.order_id
            order.order_id = order_id
            order.save_to_db()
        else:
            order_id = response
        logger.info(f"Order placed at {self.ltp} with {order_id}")

    def _place_entry_order(self):
        """
        Place the initial entry order and update the necessary fields
        """
        orders = self.create_order()
        self.update_next_entry_price()
        # Execute the actual order
        order = orders.get("entry")
        self._place_one_order(order)

    def entry(self):
        """
        logic to enter into a position
        """
        if not (self.can_enter):
            return
        if self.ltp and self.next_entry_price:
            if self.direction == 1:
                if self.ltp <= self.next_entry_price:
                    self._place_entry_order()
            elif self.direction == -1:
                if self.ltp >= self.next_entry_price:
                    self._place_entry_order()

    def exit(self):
        """
        logic to exit a position
        """
        if not (self.orders):
            return
        for order in self.orders:
            target = order.get("target")
            if target:
                if target.is_complete:
                    pass  # Do nothing
                else:
                    price = target.price
                    side = target.side
            else:
                logger.error("No target order; something wrong")

    def run(self, ltp: Dict[str, float]):
        """
        run this strategy; entry point to run the strategy
        ltp
            last price as a dictionary
        """
        for k, v in ltp.items():
            if k == self.symbol:
                self.ltp = v
        if self.can_enter:
            self.entry()
        self.cycle += 1
