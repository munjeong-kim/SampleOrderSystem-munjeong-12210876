from src.domain.models import Sample
from src.storage.json_storage import JsonStorage


class SampleRepository:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def create(self, sample: Sample) -> Sample:
        samples = self.storage.load()

        if any(item["sample_id"] == sample.sample_id for item in samples):
            raise ValueError(f"이미 존재하는 시료 ID입니다: {sample.sample_id}")

        samples.append(sample.to_dict())
        self.storage.save(samples)

        return sample

    def read_all(self) -> list:
        return [Sample.from_dict(item) for item in self.storage.load()]

    def read_one(self, sample_id: str):
        for sample in self.read_all():
            if sample.sample_id == sample_id:
                return sample

        return None

    def update(self, sample: Sample) -> Sample:
        samples = self.storage.load()

        for index, item in enumerate(samples):
            if item["sample_id"] == sample.sample_id:
                samples[index] = sample.to_dict()
                break
        else:
            raise ValueError(f"존재하지 않는 시료 ID입니다: {sample.sample_id}")

        self.storage.save(samples)

        return sample
