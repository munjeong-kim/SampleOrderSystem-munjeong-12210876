from datetime import date

from src.domain.models import Order


class OrderController:
    def __init__(self, view, order_repository, sample_repository):
        self.view = view
        self.order_repository = order_repository
        self.sample_repository = sample_repository

    def reserve(self) -> None:
        input_data = self.view.get_order_reservation_input()
        sample_id = input_data["sample_id"]

        if self.sample_repository.read_one(sample_id) is None:
            self.view.show_message(f"등록되지 않은 시료입니다: {sample_id}")
            return

        order_id = self._generate_order_id()
        order = Order(
            order_id=order_id,
            sample_id=sample_id,
            customer_name=input_data["customer_name"],
            quantity=input_data["quantity"],
        )
        self.order_repository.create(order)
        self.view.show_message(f"주문이 접수되었습니다: {order_id}")

    def _generate_order_id(self) -> str:
        today = date.today()
        prefix = f"ORD-{today:%Y%m%d}-"
        existing_count = sum(
            1 for order in self.order_repository.read_all() if order.order_id.startswith(prefix)
        )
        sequence = existing_count + 1

        return f"{prefix}{sequence:04d}"
