from src.domain.models import ProductionJob
from src.repository.production_queue_repository import ProductionQueueRepository
from src.storage.json_storage import JsonStorage


def _make_repository(tmp_path):
    storage = JsonStorage(str(tmp_path / "production_queue.json"))
    return ProductionQueueRepository(storage)


def test_enqueue한_순서대로_read_all이_반환된다(tmp_path):
    repository = _make_repository(tmp_path)
    job1 = ProductionJob(order_id="ORD-0001", sample_id="S-001", quantity=100, total_seconds=1000.0)
    job2 = ProductionJob(order_id="ORD-0002", sample_id="S-002", quantity=50, total_seconds=500.0)

    repository.enqueue(job1)
    repository.enqueue(job2)

    assert [job.order_id for job in repository.read_all()] == ["ORD-0001", "ORD-0002"]


def test_read_head는_가장_먼저_enqueue된_것을_반환한다(tmp_path):
    repository = _make_repository(tmp_path)
    job1 = ProductionJob(order_id="ORD-0001", sample_id="S-001", quantity=100, total_seconds=1000.0)
    job2 = ProductionJob(order_id="ORD-0002", sample_id="S-002", quantity=50, total_seconds=500.0)
    repository.enqueue(job1)
    repository.enqueue(job2)

    head = repository.read_head()

    assert head.order_id == "ORD-0001"


def test_빈_큐에서_read_head는_None을_반환한다(tmp_path):
    repository = _make_repository(tmp_path)

    assert repository.read_head() is None


def test_dequeue_head는_맨_앞_작업을_제거하고_반환하며_이후_read_head는_그다음_작업을_반환한다(tmp_path):
    repository = _make_repository(tmp_path)
    job1 = ProductionJob(order_id="ORD-0001", sample_id="S-001", quantity=100, total_seconds=1000.0)
    job2 = ProductionJob(order_id="ORD-0002", sample_id="S-002", quantity=50, total_seconds=500.0)
    repository.enqueue(job1)
    repository.enqueue(job2)

    dequeued = repository.dequeue_head()

    assert dequeued.order_id == "ORD-0001"
    assert repository.read_head().order_id == "ORD-0002"
    assert [job.order_id for job in repository.read_all()] == ["ORD-0002"]


def test_빈_큐에서_dequeue_head는_None을_반환한다(tmp_path):
    repository = _make_repository(tmp_path)

    assert repository.dequeue_head() is None


def test_update로_started_at을_갱신하면_반영된다(tmp_path):
    repository = _make_repository(tmp_path)
    job = ProductionJob(order_id="ORD-0001", sample_id="S-001", quantity=100, total_seconds=1000.0)
    repository.enqueue(job)

    job.started_at = "2026-04-16T09:00:00"
    repository.update(job)

    assert repository.read_head().started_at == "2026-04-16T09:00:00"
