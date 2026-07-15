from datetime import datetime

from src.controller.production_controller import ProductionController
from src.domain.models import Order, OrderStatus, ProductionJob, Sample
from src.repository.order_repository import OrderRepository
from src.repository.production_queue_repository import ProductionQueueRepository
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage


def _make_repositories(tmp_path):
    sample_repository = SampleRepository(JsonStorage(str(tmp_path / "samples.json")))
    order_repository = OrderRepository(JsonStorage(str(tmp_path / "orders.json")))
    production_queue_repository = ProductionQueueRepository(
        JsonStorage(str(tmp_path / "production_queue.json"))
    )
    return sample_repository, order_repository, production_queue_repository


def test_완료_시간이_지난_선두_작업은_재고_반영_CONFIRMED_전환_큐_제거되고_다음_작업이_시작된다(
    tmp_path, mocker
):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(
            sample_id="S-001",
            name="실리콘 웨이퍼-8인치",
            avg_production_time=10.0,
            yield_rate=0.8,
            stock_quantity=50,
        )
    )
    order_repository.create(
        Order(
            order_id="ORD-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.PRODUCING,
        )
    )
    production_queue_repository.enqueue(
        ProductionJob(
            order_id="ORD-0001",
            sample_id="S-001",
            quantity=63,
            total_seconds=630.0,
            started_at="2026-04-16T09:00:00",
        )
    )
    production_queue_repository.enqueue(
        ProductionJob(order_id="ORD-0002", sample_id="S-002", quantity=10, total_seconds=100.0)
    )
    mocker.patch(
        "src.controller.production_controller.datetime"
    ).now.return_value = datetime(2026, 4, 16, 9, 10, 30)
    mocker.patch(
        "src.controller.production_controller.datetime"
    ).fromisoformat.side_effect = datetime.fromisoformat
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )

    controller.process_queue()

    sample = sample_repository.read_one("S-001")
    assert sample.stock_quantity == 113  # 50 + 63

    order = order_repository.read_one("ORD-0001")
    assert order.status == OrderStatus.CONFIRMED

    jobs = production_queue_repository.read_all()
    assert [job.order_id for job in jobs] == ["ORD-0002"]
    assert jobs[0].started_at == "2026-04-16T09:10:30"


def test_완료_시간이_안_지났으면_아무_변화_없다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(
            sample_id="S-001",
            name="실리콘 웨이퍼-8인치",
            avg_production_time=10.0,
            yield_rate=0.8,
            stock_quantity=50,
        )
    )
    order_repository.create(
        Order(
            order_id="ORD-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.PRODUCING,
        )
    )
    production_queue_repository.enqueue(
        ProductionJob(
            order_id="ORD-0001",
            sample_id="S-001",
            quantity=63,
            total_seconds=630.0,
            started_at="2026-04-16T09:00:00",
        )
    )
    mock_datetime = mocker.patch("src.controller.production_controller.datetime")
    mock_datetime.now.return_value = datetime(2026, 4, 16, 9, 5, 0)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )

    controller.process_queue()

    sample = sample_repository.read_one("S-001")
    assert sample.stock_quantity == 50

    order = order_repository.read_one("ORD-0001")
    assert order.status == OrderStatus.PRODUCING

    jobs = production_queue_repository.read_all()
    assert [job.order_id for job in jobs] == ["ORD-0001"]


def test_여러_작업이_연쇄로_완료_시간을_지났으면_모두_순서대로_처리된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    for sample_id in ("S-001", "S-002", "S-003"):
        sample_repository.create(
            Sample(
                sample_id=sample_id,
                name=f"시료-{sample_id}",
                avg_production_time=1.0,
                yield_rate=1.0,
                stock_quantity=0,
            )
        )
    for order_id, sample_id in (
        ("ORD-0001", "S-001"),
        ("ORD-0002", "S-002"),
        ("ORD-0003", "S-003"),
    ):
        order_repository.create(
            Order(
                order_id=order_id,
                sample_id=sample_id,
                customer_name="홍길동",
                quantity=10,
                status=OrderStatus.PRODUCING,
            )
        )
    production_queue_repository.enqueue(
        ProductionJob(
            order_id="ORD-0001",
            sample_id="S-001",
            quantity=10,
            total_seconds=100.0,
            started_at="2026-04-16T09:00:00",
        )
    )
    production_queue_repository.enqueue(
        ProductionJob(order_id="ORD-0002", sample_id="S-002", quantity=20, total_seconds=0.0)
    )
    production_queue_repository.enqueue(
        ProductionJob(order_id="ORD-0003", sample_id="S-003", quantity=30, total_seconds=0.0)
    )
    mock_datetime = mocker.patch("src.controller.production_controller.datetime")
    mock_datetime.now.return_value = datetime(2026, 4, 16, 9, 10, 0)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )

    controller.process_queue()

    assert production_queue_repository.read_all() == []
    assert sample_repository.read_one("S-001").stock_quantity == 10
    assert sample_repository.read_one("S-002").stock_quantity == 20
    assert sample_repository.read_one("S-003").stock_quantity == 30
    assert order_repository.read_one("ORD-0001").status == OrderStatus.CONFIRMED
    assert order_repository.read_one("ORD-0002").status == OrderStatus.CONFIRMED
    assert order_repository.read_one("ORD-0003").status == OrderStatus.CONFIRMED


def test_빈_큐에서는_아무_일도_안_일어난다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )

    controller.process_queue()

    assert production_queue_repository.read_all() == []
