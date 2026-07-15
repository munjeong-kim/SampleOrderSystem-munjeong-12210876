from src.controller.monitoring_controller import MonitoringController
from src.domain.models import Order, OrderStatus, Sample
from src.repository.order_repository import OrderRepository
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage


def _make_repositories(tmp_path):
    sample_repository = SampleRepository(JsonStorage(str(tmp_path / "samples.json")))
    order_repository = OrderRepository(JsonStorage(str(tmp_path / "orders.json")))
    return sample_repository, order_repository


def test_상태별_주문_건수가_정확히_집계된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.RESERVED)
    )
    order_repository.create(
        Order(order_id="ORD-0002", sample_id="S-001", customer_name="김철수", quantity=20, status=OrderStatus.RESERVED)
    )
    order_repository.create(
        Order(order_id="ORD-0003", sample_id="S-001", customer_name="이영희", quantity=30, status=OrderStatus.CONFIRMED)
    )
    order_repository.create(
        Order(order_id="ORD-0004", sample_id="S-001", customer_name="박영수", quantity=40, status=OrderStatus.PRODUCING)
    )
    order_repository.create(
        Order(order_id="ORD-0005", sample_id="S-001", customer_name="최민지", quantity=50, status=OrderStatus.RELEASE)
    )
    controller = MonitoringController(view, order_repository, sample_repository)

    controller.show_order_status_summary()

    view.show_order_status_summary.assert_called_once()
    counts = view.show_order_status_summary.call_args[0][0]
    assert counts["RESERVED"] == 2
    assert counts["CONFIRMED"] == 1
    assert counts["PRODUCING"] == 1
    assert counts["RELEASE"] == 1


def test_REJECTED는_집계에서_제외된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.REJECTED)
    )
    controller = MonitoringController(view, order_repository, sample_repository)

    controller.show_order_status_summary()

    counts = view.show_order_status_summary.call_args[0][0]
    assert "REJECTED" not in counts
    assert sum(counts.values()) == 0


def test_특정_상태의_주문이_0건이어도_결과에_포함된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.RESERVED)
    )
    controller = MonitoringController(view, order_repository, sample_repository)

    controller.show_order_status_summary()

    counts = view.show_order_status_summary.call_args[0][0]
    assert counts == {"RESERVED": 1, "CONFIRMED": 0, "PRODUCING": 0, "RELEASE": 0}


def test_주문이_없어도_모든_상태가_0으로_집계된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = MonitoringController(view, order_repository, sample_repository)

    controller.show_order_status_summary()

    counts = view.show_order_status_summary.call_args[0][0]
    assert counts == {"RESERVED": 0, "CONFIRMED": 0, "PRODUCING": 0, "RELEASE": 0}
