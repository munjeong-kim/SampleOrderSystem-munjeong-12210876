from dataclasses import asdict, dataclass
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

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Sample":
        return cls(**data)


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED

    def to_dict(self) -> dict:
        data = asdict(self)
        data["status"] = self.status.name
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        data = dict(data)
        data["status"] = OrderStatus[data["status"]]
        return cls(**data)
