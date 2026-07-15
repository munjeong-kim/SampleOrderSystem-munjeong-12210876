from src.controller.menu_dispatch import INVALID_INPUT_MESSAGE, select_order_by_number
from src.domain.models import OrderStatus


class ShipmentController:
    def __init__(self, view, order_repository, sample_repository):
        self.view = view
        self.order_repository = order_repository
        self.sample_repository = sample_repository

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

        sample = self.sample_repository.read_one(order.sample_id)
        sample.stock_quantity -= order.quantity
        self.sample_repository.update(sample)

        self.view.show_message(
            f"주문이 {order.status.name} 상태로 전환되었습니다: {order_id}"
        )

    def run_submenu(self) -> None:
        while True:
            orders = self._get_confirmed_orders()

            if not orders:
                self.view.show_message("출고 가능한 주문이 없습니다.")
            else:
                self.view.show_numbered_order_list(orders)

            self.view.show_shipment_menu()
            choice = self.view.get_shipment_menu_choice()

            if choice == "0":
                break
            elif choice == "1":
                self._select_order_and_ship(orders)
            else:
                self.view.show_message(INVALID_INPUT_MESSAGE)

    def _select_order_and_ship(self, orders: list) -> None:
        order = select_order_by_number(self.view, orders)
        if order is None:
            return

        self.ship(order.order_id)
