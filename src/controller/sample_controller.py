from src.domain.models import Sample


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
