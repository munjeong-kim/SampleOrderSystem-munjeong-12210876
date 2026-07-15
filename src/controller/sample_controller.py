import math

from src.controller.menu_dispatch import INVALID_INPUT_MESSAGE, run_menu_loop
from src.domain.models import Sample

PAGE_SIZE = 5


class SampleController:
    def __init__(self, view, sample_repository):
        self.view = view
        self.sample_repository = sample_repository
        self._submenu_handlers = {
            "1": lambda: self.register(),
            "2": lambda: self._list_samples_with_navigation(),
            "3": lambda: self.search(self.view.get_search_keyword()),
        }

    def register(self) -> None:
        input_data = self.view.get_sample_registration_input()
        sample = Sample(**input_data)

        try:
            self.sample_repository.create(sample)
            self.view.show_message(f"시료가 등록되었습니다: {sample.sample_id} ({sample.name})")
        except ValueError as e:
            self.view.show_message(str(e))

    def list_samples(self, page: int = 1) -> None:
        samples = self.sample_repository.read_all()

        if not samples:
            self.view.show_message("등록된 시료가 없습니다.")
            return

        total_pages = math.ceil(len(samples) / PAGE_SIZE)

        if page < 1 or page > total_pages:
            self.view.show_message("존재하지 않는 페이지입니다.")
            return

        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        self.view.show_sample_list(samples[start:end], page, total_pages)

    def search(self, keyword: str) -> None:
        samples = self.sample_repository.read_all()
        results = [s for s in samples if keyword.lower() in s.name.lower()]

        if not results:
            self.view.show_message("검색 결과가 없습니다.")
            return

        self.view.show_search_results(results)

    def run_submenu(self) -> None:
        run_menu_loop(
            self.view.show_sample_menu,
            self.view.get_sample_menu_choice,
            self.view.show_message,
            self._submenu_handlers,
        )

    def _list_samples_with_navigation(self) -> None:
        page = self.view.get_page_number()
        self.list_samples(page)

        while True:
            navigation = self.view.get_list_navigation_choice()

            if navigation == "n":
                page += 1
                self.list_samples(page)
            elif navigation == "p":
                page -= 1
                self.list_samples(page)
            elif navigation == "b":
                return
            else:
                self.view.show_message(INVALID_INPUT_MESSAGE)
