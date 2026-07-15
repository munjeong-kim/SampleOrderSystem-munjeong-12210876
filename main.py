import os

from src.controller.main_controller import MainController
from src.controller.sample_controller import SampleController
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage
from src.view.console_view import ConsoleView


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    view = ConsoleView()
    sample_repository = SampleRepository(JsonStorage("data/samples.json"))
    sample_controller = SampleController(view, sample_repository)

    MainController(view, sample_controller=sample_controller).run()
