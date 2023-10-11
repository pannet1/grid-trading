from pydantic import BaseModel, PrivateAttr
from omspy.order import Order, CompoundOrder
import pendulum
from typing import Any, List, Optional, Dict, Set
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
        if not(self.ltp):
            return False
        methods = [attr for attr in dir(self) if attr.startswith("before_entry")]
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
    _direction: Optional[int] = PrivateAttr()
    _initial_price: Optional[float] = PrivateAttr()
    _next_forward_price: Optional[float] = PrivateAttr()
    _next_backward_price: Optional[float] = PrivateAttr()
    _prices: set = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self.orders = []
        self._prices = set()
        self._direction = None
        self._initial_price = None
        self._next_backward_price = None
        self._next_forward_price = None
        if str(self.side).lower() == "buy":
            self._direction = 1
        elif str(self.side).lower() == "sell":
            self._direction = -1
        else:
            self._direction = None

        self.set_initial_prices()

    @property
    def direction(self):
        return self._direction

    @property
    def initial_price(self):
        return self._initial_price

    @property
    def next_forward_price(self):
        return self._next_forward_price

    @property
    def next_backward_price(self):
        return self._next_backward_price

    @property
    def prices(self):
        return self._prices
    def before_entry_check_outside_prices(self):
        """
        Check whether the current price/ltp is outside the given range
        """
        ltp = self.ltp
        # Direction check for prices greater than entry price
        if self.direction == 1:
            if ltp > self.buy_price:
                return False
            else:
                return True
        elif self.direction == -1:
            if ltp < self.sell_price:
                return False
            else:
                return True
        else:
            return False

    def before_entry_check_between_prices(self):
        """
        Check whether the current price ltp is between the backward and forward price.
        If it is between them, then no trade should be taken
        """
        if (self.ltp <= self.next_forward_price) and (self.ltp >= self.next_backward_price):
            return False
        else:
            return True

    def set_initial_prices(self):
        """
        set the initial prices for initial price, backward
        and forward prices
        """
        if self.initial_price is None:
            self._initial_price = self.ltp
        if self._next_forward_price is None or (self._next_backward_price is None):
            price = self._initial_price
            if price:
                if self.direction == 1:
                    if price >= self.buy_price:
                        self._next_forward_price = self.buy_price
                    else:
                        self._next_forward_price = price
                    self._next_backward_price = (
                        self._next_forward_price - self.buy_offset
                    )
                elif self.direction == -1:
                    if price <= self.sell_price:
                        self._next_backward_price = self.sell_price
                    else:
                        self._next_backward_price = price - self.sell_offset
                    self._next_forward_price = (
                        self._next_backward_price + self.sell_offset
                    )

    def set_next_prices(self, price:Optional[float]=None):
        """
        Set the next forward and backward prices based on the
        current ltp, direction and other settings
        """
        if price is None:
            price = self.ltp
        if self.direction == 1:
            if price < self.next_backward_price:
                self._next_forward_price = self.next_backward_price
                self._next_backward_price -= self.buy_offset
            elif price > self.next_forward_price:
                self._next_forward_price = min(
                    self.next_forward_price + self.buy_offset,
                    self.buy_price,
                )
                self._next_backward_price = self.next_forward_price - self.buy_offset
        elif self.direction == -1:
            if price < self.next_backward_price:
                self._next_backward_price = max(self.sell_price, self.next_backward_price-self.sell_offset)
                self._next_forward_price = self.next_backward_price + self.sell_offset
            elif price > self.next_forward_price:
                self._next_backward_price = self.next_forward_price
                self._next_forward_price += self.sell_offset

    def _create_entry_order(self) -> Optional[Order]:
        """
        Create a order
        """
        price = self.next_backward_price if self.direction == 1 else self.next_forward_price
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
            price=price,
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
                ltp=self.ltp, target=target.price,
                backward=self.next_backward_price,
                forward=self.next_forward_price
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
        # Execute the actual order
        order = orders.get("entry")
        self._place_one_order(order)


    def entry(self):
        """
        logic to enter into a position
        """
        if not (self.can_enter):
            return
        price = self.next_backward_price if self.direction == 1 else self.next_forward_price
        if price not in self.prices:
            self._place_entry_order()
        self._prices.add(price)
        self.set_next_prices(price=self.ltp)

    def exit(self):
        """
        logic to exit a position
        """
        if not (self.orders):
            return
        for order in self.orders:
            target = order.get("target")
            if target:
                if target.order_id:
                    # If there is an order_id, we assume the order is placed
                    pass  # Do nothing
                else:
                    side = target.side.lower()
                    price = target.price
                    if price:
                        if side == "buy":
                            if self.ltp <= price:
                                self._place_one_order(target)
                        elif side == "sell":
                            if self.ltp >= price:
                                self._place_one_order(target)
                    else:
                        logger.warning(f"No price for {target.symbol}; some error")

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
        self.set_initial_prices()
        if self.can_enter:
            self.entry()
        self.exit()
        self.cycle += 1
