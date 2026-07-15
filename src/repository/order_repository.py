from src.domain.models import Order
from src.storage.json_storage import JsonStorage


class OrderRepository:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def create(self, order: Order) -> Order:
        orders = self.storage.load()
        orders.append(order.to_dict())
        self.storage.save(orders)

        return order

    def read_all(self) -> list:
        return [Order.from_dict(item) for item in self.storage.load()]

    def read_one(self, order_id: str):
        for order in self.read_all():
            if order.order_id == order_id:
                return order

        return None

    def update(self, order: Order) -> Order:
        orders = self.storage.load()

        for index, item in enumerate(orders):
            if item["order_id"] == order.order_id:
                orders[index] = order.to_dict()
                break
        else:
            raise ValueError(f"존재하지 않는 주문번호입니다: {order.order_id}")

        self.storage.save(orders)

        return order
