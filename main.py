import os

from src.controller.main_controller import MainController
from src.controller.order_controller import OrderController
from src.controller.sample_controller import SampleController
from src.repository.order_repository import OrderRepository
from src.repository.production_queue_repository import ProductionQueueRepository
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage
from src.view.console_view import ConsoleView


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    view = ConsoleView()
    sample_repository = SampleRepository(JsonStorage("data/samples.json"))
    order_repository = OrderRepository(JsonStorage("data/orders.json"))
    production_queue_repository = ProductionQueueRepository(
        JsonStorage("data/production_queue.json")
    )
    sample_controller = SampleController(view, sample_repository)
    order_controller = OrderController(
        view, order_repository, sample_repository, production_queue_repository
    )

    MainController(
        view,
        sample_controller=sample_controller,
        order_controller=order_controller,
    ).run()
