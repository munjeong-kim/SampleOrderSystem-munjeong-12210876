from src.controller.shipment_controller import ShipmentController
from src.domain.models import Order, OrderStatus, Sample
from src.repository.order_repository import OrderRepository
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage


def _make_repositories(tmp_path):
    order_repository = OrderRepository(JsonStorage(str(tmp_path / "orders.json")))
    sample_repository = SampleRepository(JsonStorage(str(tmp_path / "samples.json")))
    return order_repository, sample_repository


def test_CONFIRMED_주문을_출고하면_RELEASE로_전환되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(
            sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9,
            stock_quantity=100,
        )
    )
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.CONFIRMED,
        )
    )
    controller = ShipmentController(view, order_repository, sample_repository)

    controller.ship("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.RELEASE
    view.show_message.assert_called_once()
    assert "RELEASE" in view.show_message.call_args[0][0]


def test_CONFIRMED_주문을_출고하면_해당_시료의_재고가_주문수량만큼_차감된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(
            sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9,
            stock_quantity=100,
        )
    )
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=60,
            status=OrderStatus.CONFIRMED,
        )
    )
    controller = ShipmentController(view, order_repository, sample_repository)

    controller.ship("ORD-20260416-0001")

    sample = sample_repository.read_one("S-001")
    assert sample.stock_quantity == 40  # 100 - 60


def test_존재하지_않는_주문번호로_출고_시도하면_오류_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    controller = ShipmentController(view, order_repository, sample_repository)

    controller.ship("ORD-NOT-EXIST")

    view.show_message.assert_called_once()
    assert "존재하지 않는 주문" in view.show_message.call_args[0][0]


def test_CONFIRMED가_아닌_주문을_출고_시도하면_오류_메시지가_출력되고_상태가_변경되지_않는다(
    tmp_path, mocker
):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.RESERVED,
        )
    )
    controller = ShipmentController(view, order_repository, sample_repository)

    controller.ship("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.RESERVED
    view.show_message.assert_called_once()
    assert "출고할 수 없는 상태" in view.show_message.call_args[0][0]


def test_이미_RELEASE인_주문에_대해_재출고_시도해도_차단된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.RELEASE,
        )
    )
    controller = ShipmentController(view, order_repository, sample_repository)

    controller.ship("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.RELEASE
    view.show_message.assert_called_once()
    assert "출고할 수 없는 상태" in view.show_message.call_args[0][0]


def test_CONFIRMED_상태_주문만_필터링된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
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
    controller = ShipmentController(view, order_repository, sample_repository)

    orders = controller._get_confirmed_orders()

    assert [o.order_id for o in orders] == ["ORD-0001"]


def test_서브메뉴_진입시_CONFIRMED_주문이_번호와_함께_자동으로_표시된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.CONFIRMED)
    )
    order_repository.create(
        Order(order_id="ORD-0002", sample_id="S-002", customer_name="김철수", quantity=20, status=OrderStatus.CONFIRMED)
    )
    controller = ShipmentController(view, order_repository, sample_repository)
    view.get_shipment_menu_choice.side_effect = ["0"]

    controller.run_submenu()

    view.show_numbered_order_list.assert_called_once()
    orders = view.show_numbered_order_list.call_args[0][0]
    assert [o.order_id for o in orders] == ["ORD-0001", "ORD-0002"]


def test_출고_가능한_주문이_없으면_안내_메시지만_표시되고_메뉴는_계속_진행된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    controller = ShipmentController(view, order_repository, sample_repository)
    view.get_shipment_menu_choice.side_effect = ["0"]

    controller.run_submenu()

    view.show_numbered_order_list.assert_not_called()
    assert any(
        "출고 가능한 주문이 없습니다" in call.args[0] for call in view.show_message.call_args_list
    )


def test_1_선택_후_유효한_번호를_입력하면_해당_주문이_출고된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.CONFIRMED)
    )
    order_repository.create(
        Order(order_id="ORD-0002", sample_id="S-002", customer_name="김철수", quantity=20, status=OrderStatus.CONFIRMED)
    )
    controller = ShipmentController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "ship")
    view.get_shipment_menu_choice.side_effect = ["1", "0"]
    view.get_order_selection_number.return_value = 2

    controller.run_submenu()

    controller.ship.assert_called_once_with("ORD-0002")


def test_목록_범위를_벗어난_번호_입력시_오류_안내_후_계속_진행된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.CONFIRMED)
    )
    controller = ShipmentController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "ship")
    view.get_shipment_menu_choice.side_effect = ["1", "0"]
    view.get_order_selection_number.return_value = 5

    controller.run_submenu()

    controller.ship.assert_not_called()
    assert any(
        "잘못된 번호" in call.args[0] for call in view.show_message.call_args_list
    )


def test_주문이_없는_상태에서_1을_선택하면_오류_안내_후_계속_진행된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    controller = ShipmentController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "ship")
    view.get_shipment_menu_choice.side_effect = ["1", "0"]

    controller.run_submenu()

    controller.ship.assert_not_called()
    assert any(
        "선택할 주문이 없습니다" in call.args[0] for call in view.show_message.call_args_list
    )


def test_서브메뉴에서_0_선택시_바로_루프가_종료된다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    controller = ShipmentController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "ship")
    view.get_shipment_menu_choice.side_effect = ["0"]

    controller.run_submenu()

    controller.ship.assert_not_called()


def test_서브메뉴에서_잘못된_입력시_안내_메시지_출력_후_계속_진행한다(tmp_path, mocker):
    view = mocker.MagicMock()
    order_repository, sample_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.CONFIRMED)
    )
    controller = ShipmentController(view, order_repository, sample_repository)
    view.get_shipment_menu_choice.side_effect = ["xyz", "0"]

    controller.run_submenu()

    assert any(
        "잘못된 입력입니다" in call.args[0] for call in view.show_message.call_args_list
    )
