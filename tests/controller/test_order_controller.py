from datetime import date

from src.controller.order_controller import OrderController
from src.domain.models import OrderStatus, Sample
from src.repository.order_repository import OrderRepository
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage


def _make_repositories(tmp_path):
    sample_repository = SampleRepository(JsonStorage(str(tmp_path / "samples.json")))
    order_repository = OrderRepository(JsonStorage(str(tmp_path / "orders.json")))
    return sample_repository, order_repository


def test_등록된_시료로_주문_접수시_RESERVED_상태로_등록되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9)
    )
    view.get_order_reservation_input.return_value = {
        "sample_id": "S-001",
        "customer_name": "홍길동",
        "quantity": 100,
    }
    mocker.patch("src.controller.order_controller.date").today.return_value = date(2026, 4, 16)
    controller = OrderController(view, order_repository, sample_repository)

    controller.reserve()

    orders = order_repository.read_all()
    assert len(orders) == 1
    order = orders[0]
    assert order.order_id == "ORD-20260416-0001"
    assert order.sample_id == "S-001"
    assert order.customer_name == "홍길동"
    assert order.quantity == 100
    assert order.status == OrderStatus.RESERVED
    view.show_message.assert_called_once()
    assert "ORD-20260416-0001" in view.show_message.call_args[0][0]


def test_등록되지_않은_시료_ID로_접수_시도하면_오류_메시지가_출력되고_주문이_생성되지_않는다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    view.get_order_reservation_input.return_value = {
        "sample_id": "S-999",
        "customer_name": "홍길동",
        "quantity": 100,
    }
    controller = OrderController(view, order_repository, sample_repository)

    controller.reserve()

    assert order_repository.read_all() == []
    view.show_message.assert_called_once()
    assert "등록되지 않은 시료" in view.show_message.call_args[0][0]


def test_같은_날_여러_건_접수시_주문번호_순번이_증가한다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9)
    )
    view.get_order_reservation_input.return_value = {
        "sample_id": "S-001",
        "customer_name": "홍길동",
        "quantity": 100,
    }
    mocker.patch("src.controller.order_controller.date").today.return_value = date(2026, 4, 16)
    controller = OrderController(view, order_repository, sample_repository)

    controller.reserve()
    controller.reserve()

    orders = order_repository.read_all()
    assert [o.order_id for o in orders] == ["ORD-20260416-0001", "ORD-20260416-0002"]
