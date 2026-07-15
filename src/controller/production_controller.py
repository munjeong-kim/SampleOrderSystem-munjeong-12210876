from datetime import datetime

from src.controller.menu_dispatch import run_menu_loop
from src.domain.models import OrderStatus


class ProductionController:
    def __init__(self, view, production_queue_repository, order_repository, sample_repository):
        self.view = view
        self.production_queue_repository = production_queue_repository
        self.order_repository = order_repository
        self.sample_repository = sample_repository
        self._submenu_handlers = {
            "1": lambda: self.show_status(),
            "2": lambda: self.show_waiting_queue(),
        }

    def process_queue(self) -> None:
        while True:
            job = self.production_queue_repository.read_head()
            if job is None:
                return

            if job.started_at is None:
                job.started_at = datetime.now().isoformat()
                self.production_queue_repository.update(job)
                continue

            started_at = datetime.fromisoformat(job.started_at)
            elapsed = (datetime.now() - started_at).total_seconds()

            if elapsed < job.total_seconds:
                return

            self._complete_job(job)

    def _complete_job(self, job) -> None:
        order = self.order_repository.read_one(job.order_id)

        sample = self.sample_repository.read_one(job.sample_id)
        # 실생산량은 재고에 더하고, 이번에 CONFIRMED로 전환되는 주문 수량만큼은 차감한다
        # (승인 시 즉시 CONFIRMED되는 경우와 동일한 재고 차감 규칙).
        sample.stock_quantity += job.quantity - order.quantity
        self.sample_repository.update(sample)

        order.status = OrderStatus.CONFIRMED
        self.order_repository.update(order)

        self.production_queue_repository.dequeue_head()

    def show_status(self) -> None:
        self.process_queue()

        job = self.production_queue_repository.read_head()
        if job is None:
            self.view.show_message("현재 생산 중인 작업이 없습니다.")
            return

        self.view.show_current_production(job)

    def show_waiting_queue(self) -> None:
        self.process_queue()

        jobs = self.production_queue_repository.read_all()
        if not jobs:
            self.view.show_message("대기 중인 생산 작업이 없습니다.")
            return

        self.view.show_production_queue(jobs)

    def run_submenu(self) -> None:
        run_menu_loop(
            self.view.show_production_menu,
            self.view.get_production_menu_choice,
            self.view.show_message,
            self._submenu_handlers,
        )
