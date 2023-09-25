from pydantic import BaseModel, PrivateAttr
from omspy.order import Order, CompoundOrder
import pendulum
from typing import Any, List, Optional
from collections import Counter
import json
from logzero import logger


class BaseStrategy(BaseModel):
    """
    This is just an abstract class from which other strategies
    would inherit.
    Common methods that affect all strategies are placed here
    """

    broker: Any
    datafeed: Optional[Any] = None
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
        now = pendulum.now(tz=self.c.TZ)
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
    order: Optional[CompoundOrder]
    _direction: Optional[int]
    _next_entry_price: Optional[float]

    def __init__(self, **data):
        super().__init__(**data)
        com = CompoundOrder(broker=self.broker, timezone="Asia/Kolkata")
        self.order = com
        self._next_entry_price = None
        if self.side == "buy":
            self._direction = 1
        elif self.side == "sell":
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


    def _create_entry_order(self)->Optional[Order]:
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
                order_type='LIMIT'
                )
        return order

    def _create_target_order(self)->Optional[Order]:
        if self.direction == 1:
            quantity = self.buy_quantity
            trigger_price = self.next_entry_price + self.buy_target
            side = 'sell'
        elif self.direction == -1:
            quantity = self.sell_quantity
            trigger_price = self.next_entry_price - self.sell_target
            side = 'buy'
        else:
            logger.warning("No direction yet; so order cannot be created")
            return None
        order = Order(
                symbol=self.symbol,
                side=side,
                quantity=quantity,
                trigger_price=trigger_price,
                price=0.0,
                order_type='SL-M'
                )
        return order

        
