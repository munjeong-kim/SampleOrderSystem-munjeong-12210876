import math

from src.domain.models import Sample

PAGE_SIZE = 5


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
