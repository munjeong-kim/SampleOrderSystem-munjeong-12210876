import math
from datetime import date, datetime

from src.controller.menu_dispatch import (
    INVALID_INPUT_MESSAGE,
    run_menu_loop,
    select_order_by_number,
)
from src.domain.models import Order, OrderStatus, ProductionJob


class OrderController:
    def __init__(self, view, order_repository, sample_repository, production_queue_repository):
        self.view = view
        self.order_repository = order_repository
        self.sample_repository = sample_repository
        self.production_queue_repository = production_queue_repository
        self._submenu_handlers = {
            "1": lambda: self.reserve(),
        }

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

    def _get_pending_orders(self) -> list:
        return [
            order
            for order in self.order_repository.read_all()
            if order.status == OrderStatus.RESERVED
        ]

    def list_pending_orders(self) -> None:
        orders = self._get_pending_orders()

        if not orders:
            self.view.show_message("접수된 주문이 없습니다.")
            return

        self.view.show_order_list(orders)

    def _get_reserved_order(self, order_id: str, action_label: str):
        order = self.order_repository.read_one(order_id)

        if order is None:
            self.view.show_message(f"존재하지 않는 주문입니다: {order_id}")
            return None

        if order.status != OrderStatus.RESERVED:
            self.view.show_message(f"{action_label}할 수 없는 상태입니다: {order_id}")
            return None

        return order

    def approve(self, order_id: str) -> None:
        order = self._get_reserved_order(order_id, "승인")
        if order is None:
            return

        sample = self.sample_repository.read_one(order.sample_id)
        if order.quantity <= sample.stock_quantity:
            order.status = OrderStatus.CONFIRMED
        else:
            order.status = OrderStatus.PRODUCING
            self._enqueue_production_job(order, sample)

        self.order_repository.update(order)
        self.view.show_message(
            f"주문이 승인되어 {order.status.name} 상태로 전환되었습니다: {order_id}"
        )

    def _enqueue_production_job(self, order: Order, sample) -> None:
        shortage = order.quantity - sample.stock_quantity
        actual_quantity = math.ceil(shortage / sample.yield_rate)
        total_seconds = sample.avg_production_time * actual_quantity

        is_queue_empty = self.production_queue_repository.read_head() is None
        started_at = datetime.now().isoformat() if is_queue_empty else None

        job = ProductionJob(
            order_id=order.order_id,
            sample_id=order.sample_id,
            quantity=actual_quantity,
            total_seconds=total_seconds,
            started_at=started_at,
        )
        self.production_queue_repository.enqueue(job)

    def reject(self, order_id: str) -> None:
        order = self._get_reserved_order(order_id, "거절")
        if order is None:
            return

        order.status = OrderStatus.REJECTED
        self.order_repository.update(order)
        self.view.show_message(
            f"주문이 {order.status.name} 상태로 전환되었습니다: {order_id}"
        )

    def run_submenu(self) -> None:
        run_menu_loop(
            self.view.show_order_menu,
            self.view.get_order_menu_choice,
            self.view.show_message,
            self._submenu_handlers,
        )

    def run_approval_submenu(self) -> None:
        while True:
            orders = self._get_pending_orders()

            if not orders:
                self.view.show_message("접수된 주문이 없습니다.")
            else:
                self.view.show_numbered_order_list(orders)

            self.view.show_order_approval_menu()
            choice = self.view.get_order_approval_menu_choice()

            if choice == "0":
                break
            elif choice in ("1", "2"):
                self._select_order_and_process(orders, choice)
            else:
                self.view.show_message(INVALID_INPUT_MESSAGE)

    def _select_order_and_process(self, orders: list, choice: str) -> None:
        order = select_order_by_number(self.view, orders)
        if order is None:
            return

        if choice == "1":
            self.approve(order.order_id)
        else:
            self.reject(order.order_id)
