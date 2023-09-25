from pydantic import BaseModel, PrivateAttr
from omspy.order import Order, CompoundOrder
import pendulum
from typing import Any, List, Optional


class BaseStrategy(BaseModel):
    """
    This is just an abstract class from which other strategies
    would inherit.
    Common methods that affect all strategies are placed here
    """
    broker: Any
    datafeed: Optional[Any] = None
    cycle:int = 0
    _broker_name:str

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
    exchange:str
    symbol: str
    side: str
    buy_quantity: Optional[int]
    buy_offset: Optional[float]
    buy_target: Optional[float]
    buy_price: Optional[float]
    sell_quantity: Optional[int]
    sell_offset: Optional[float]
    sell_target: Optional[float]
    sell_price: Optional[float]
    status:bool = True
    max_buy_quantity: Optional[float]
    max_sell_quantity:Optional[float]
    max_orders_cap: Optional[float]
    buy_stop_price: Optional[float]
    sell_stop_price: Optional[float]
    order: Optional[CompoundOrder]
    direction:Optional[str]
    _next_entry_price:Optional[float]
    _current_entry_price: Optional[float]



