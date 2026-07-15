from src.domain.models import ProductionJob
from src.storage.json_storage import JsonStorage


class ProductionQueueRepository:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def enqueue(self, job: ProductionJob) -> ProductionJob:
        jobs = self.storage.load()
        jobs.append(job.to_dict())
        self.storage.save(jobs)

        return job

    def read_all(self) -> list:
        return [ProductionJob.from_dict(item) for item in self.storage.load()]

    def read_head(self):
        jobs = self.read_all()
        if not jobs:
            return None

        return jobs[0]

    def dequeue_head(self):
        jobs = self.storage.load()
        if not jobs:
            return None

        head = jobs.pop(0)
        self.storage.save(jobs)

        return ProductionJob.from_dict(head)

    def update(self, job: ProductionJob) -> ProductionJob:
        jobs = self.storage.load()

        for index, item in enumerate(jobs):
            if item["order_id"] == job.order_id:
                jobs[index] = job.to_dict()
                break
        else:
            raise ValueError(f"존재하지 않는 생산 작업입니다: {job.order_id}")

        self.storage.save(jobs)

        return job
