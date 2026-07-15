import math

from src.domain.models import Sample

PAGE_SIZE = 5
INVALID_INPUT_MESSAGE = "잘못된 입력입니다. 다시 입력해주세요."


class SampleController:
    def __init__(self, view, sample_repository):
        self.view = view
        self.sample_repository = sample_repository

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
        while True:
            self.view.show_sample_menu()
            choice = self.view.get_sample_menu_choice()

            if choice == "1":
                self.register()
            elif choice == "2":
                self._list_samples_with_navigation()
            elif choice == "3":
                keyword = self.view.get_search_keyword()
                self.search(keyword)
            elif choice == "0":
                break
            else:
                self.view.show_message(INVALID_INPUT_MESSAGE)

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
