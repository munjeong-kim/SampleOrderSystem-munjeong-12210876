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
