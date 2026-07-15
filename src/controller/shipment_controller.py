from src.domain.models import OrderStatus


class ShipmentController:
    def __init__(self, view, order_repository):
        self.view = view
        self.order_repository = order_repository

    def _get_confirmed_orders(self) -> list:
        return [
            order
            for order in self.order_repository.read_all()
            if order.status == OrderStatus.CONFIRMED
        ]

    def ship(self, order_id: str) -> None:
        order = self.order_repository.read_one(order_id)

        if order is None:
            self.view.show_message(f"존재하지 않는 주문입니다: {order_id}")
            return

        if order.status != OrderStatus.CONFIRMED:
            self.view.show_message(f"출고할 수 없는 상태입니다: {order_id}")
            return

        order.status = OrderStatus.RELEASE
        self.order_repository.update(order)
        self.view.show_message(
            f"주문이 {order.status.name} 상태로 전환되었습니다: {order_id}"
        )
