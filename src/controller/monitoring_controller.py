from src.domain.models import OrderStatus

VALID_ORDER_STATUSES = ["RESERVED", "CONFIRMED", "PRODUCING", "RELEASE"]


class MonitoringController:
    def __init__(self, view, order_repository, sample_repository):
        self.view = view
        self.order_repository = order_repository
        self.sample_repository = sample_repository

    def show_order_status_summary(self) -> None:
        counts = {status: 0 for status in VALID_ORDER_STATUSES}

        for order in self.order_repository.read_all():
            if order.status.name in counts:
                counts[order.status.name] += 1

        self.view.show_order_status_summary(counts)

    def show_stock_status(self) -> None:
        orders = self.order_repository.read_all()
        rows = []

        for sample in self.sample_repository.read_all():
            required = sum(
                order.quantity
                for order in orders
                if order.sample_id == sample.sample_id and order.status == OrderStatus.RESERVED
            )

            if sample.stock_quantity == 0:
                status = "고갈"
            elif sample.stock_quantity < required:
                status = "부족"
            else:
                status = "여유"

            rows.append((sample, required, status))

        self.view.show_stock_status(rows)
