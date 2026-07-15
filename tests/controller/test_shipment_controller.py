from src.controller.shipment_controller import ShipmentController
from src.domain.models import Order, OrderStatus
from src.repository.order_repository import OrderRepository
from src.storage.json_storage import JsonStorage


def _make_repository(tmp_path):
    return OrderRepository(JsonStorage(str(tmp_path / "orders.json")))


def test_CONFIRMED_주문을_출고하면_RELEASE로_전환되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository = _make_repository(tmp_path)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.CONFIRMED,
        )
    )
    controller = ShipmentController(view, order_repository)

    controller.ship("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.RELEASE
    view.show_message.assert_called_once()
    assert "RELEASE" in view.show_message.call_args[0][0]


def test_존재하지_않는_주문번호로_출고_시도하면_오류_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository = _make_repository(tmp_path)
    controller = ShipmentController(view, order_repository)

    controller.ship("ORD-NOT-EXIST")

    view.show_message.assert_called_once()
    assert "존재하지 않는 주문" in view.show_message.call_args[0][0]


def test_CONFIRMED가_아닌_주문을_출고_시도하면_오류_메시지가_출력되고_상태가_변경되지_않는다(
    tmp_path, mocker
):
    view = mocker.MagicMock()
    order_repository = _make_repository(tmp_path)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.RESERVED,
        )
    )
    controller = ShipmentController(view, order_repository)

    controller.ship("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.RESERVED
    view.show_message.assert_called_once()
    assert "출고할 수 없는 상태" in view.show_message.call_args[0][0]


def test_이미_RELEASE인_주문에_대해_재출고_시도해도_차단된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository = _make_repository(tmp_path)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.RELEASE,
        )
    )
    controller = ShipmentController(view, order_repository)

    controller.ship("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.RELEASE
    view.show_message.assert_called_once()
    assert "출고할 수 없는 상태" in view.show_message.call_args[0][0]


def test_CONFIRMED_상태_주문만_필터링된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository = _make_repository(tmp_path)
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.CONFIRMED)
    )
    order_repository.create(
        Order(order_id="ORD-0002", sample_id="S-002", customer_name="김철수", quantity=20, status=OrderStatus.RESERVED)
    )
    order_repository.create(
        Order(order_id="ORD-0003", sample_id="S-003", customer_name="이영희", quantity=30, status=OrderStatus.PRODUCING)
    )
    order_repository.create(
        Order(order_id="ORD-0004", sample_id="S-004", customer_name="박영수", quantity=40, status=OrderStatus.RELEASE)
    )
    controller = ShipmentController(view, order_repository)

    orders = controller._get_confirmed_orders()

    assert [o.order_id for o in orders] == ["ORD-0001"]
