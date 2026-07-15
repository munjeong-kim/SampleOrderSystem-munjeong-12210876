from dataclasses import dataclass
from enum import Enum, auto


class OrderStatus(Enum):
    RESERVED = auto()
    REJECTED = auto()
    PRODUCING = auto()
    CONFIRMED = auto()
    RELEASE = auto()


@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float
    yield_rate: float
    stock_quantity: int = 0


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED
