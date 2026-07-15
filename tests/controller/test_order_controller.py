from datetime import date

from src.controller.order_controller import OrderController
from src.domain.models import Order, OrderStatus, Sample
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


def test_서브메뉴에서_1_선택시_reserve가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "reserve")
    view.get_order_menu_choice.side_effect = ["1", "0"]

    controller.run_submenu()

    controller.reserve.assert_called_once()


def test_서브메뉴에서_0_선택시_바로_루프가_종료된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "reserve")
    view.get_order_menu_choice.side_effect = ["0"]

    controller.run_submenu()

    controller.reserve.assert_not_called()


def test_서브메뉴에서_잘못된_입력시_안내_메시지_출력_후_계속_진행한다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)
    view.get_order_menu_choice.side_effect = ["abc", "0"]

    controller.run_submenu()

    view.show_message.assert_called_once()
    assert "잘못된" in view.show_message.call_args[0][0]


def test_RESERVED_상태_주문만_목록에_표시된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    order_repository.create(
        Order(
            order_id="ORD-20260416-0002",
            sample_id="S-002",
            customer_name="김철수",
            quantity=50,
            status=OrderStatus.CONFIRMED,
        )
    )
    order_repository.create(
        Order(
            order_id="ORD-20260416-0003",
            sample_id="S-003",
            customer_name="이영희",
            quantity=30,
            status=OrderStatus.REJECTED,
        )
    )
    controller = OrderController(view, order_repository, sample_repository)

    controller.list_pending_orders()

    view.show_order_list.assert_called_once()
    orders = view.show_order_list.call_args[0][0]
    assert [o.order_id for o in orders] == ["ORD-20260416-0001"]


def test_접수된_주문이_없으면_안내_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.CONFIRMED,
        )
    )
    controller = OrderController(view, order_repository, sample_repository)

    controller.list_pending_orders()

    view.show_order_list.assert_not_called()
    view.show_message.assert_called_once()
    assert "접수된 주문이 없습니다" in view.show_message.call_args[0][0]


def test_재고가_충분한_주문을_승인하면_CONFIRMED로_전환되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample = Sample(
        sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=100
    )
    sample_repository.create(sample)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    controller = OrderController(view, order_repository, sample_repository)

    controller.approve("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.CONFIRMED
    view.show_message.assert_called_once()
    assert "CONFIRMED" in view.show_message.call_args[0][0]


def test_재고가_부족한_주문을_승인하면_PRODUCING으로_전환되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample = Sample(
        sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=50
    )
    sample_repository.create(sample)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    controller = OrderController(view, order_repository, sample_repository)

    controller.approve("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.PRODUCING
    view.show_message.assert_called_once()
    assert "PRODUCING" in view.show_message.call_args[0][0]


def test_존재하지_않는_주문번호로_승인_시도하면_오류_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)

    controller.approve("ORD-NOT-EXIST")

    view.show_message.assert_called_once()
    assert "존재하지 않는 주문" in view.show_message.call_args[0][0]


def test_RESERVED가_아닌_주문을_승인_시도하면_오류_메시지가_출력되고_상태가_변경되지_않는다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample = Sample(
        sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=100
    )
    sample_repository.create(sample)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.CONFIRMED,
        )
    )
    controller = OrderController(view, order_repository, sample_repository)

    controller.approve("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.CONFIRMED
    view.show_message.assert_called_once()
    assert "승인할 수 없는 상태" in view.show_message.call_args[0][0]


def test_RESERVED_상태_주문을_거절하면_REJECTED로_전환되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    controller = OrderController(view, order_repository, sample_repository)

    controller.reject("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.REJECTED
    view.show_message.assert_called_once()
    assert "REJECTED" in view.show_message.call_args[0][0]


def test_존재하지_않는_주문번호로_거절_시도하면_오류_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)

    controller.reject("ORD-NOT-EXIST")

    view.show_message.assert_called_once()
    assert "존재하지 않는 주문" in view.show_message.call_args[0][0]


def test_RESERVED가_아닌_주문을_거절_시도하면_오류_메시지가_출력되고_상태가_변경되지_않는다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.CONFIRMED,
        )
    )
    controller = OrderController(view, order_repository, sample_repository)

    controller.reject("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.CONFIRMED
    view.show_message.assert_called_once()
    assert "거절할 수 없는 상태" in view.show_message.call_args[0][0]


def test_승인거절_서브메뉴에서_1_선택시_list_pending_orders가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "list_pending_orders")
    view.get_order_approval_menu_choice.side_effect = ["1", "0"]

    controller.run_approval_submenu()

    controller.list_pending_orders.assert_called_once()


def test_승인거절_서브메뉴에서_2_선택시_주문번호를_입력받아_approve가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "approve")
    view.get_order_approval_menu_choice.side_effect = ["2", "0"]
    view.get_order_id_input.return_value = "ORD-20260416-0001"

    controller.run_approval_submenu()

    controller.approve.assert_called_once_with("ORD-20260416-0001")


def test_승인거절_서브메뉴에서_3_선택시_주문번호를_입력받아_reject가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "reject")
    view.get_order_approval_menu_choice.side_effect = ["3", "0"]
    view.get_order_id_input.return_value = "ORD-20260416-0001"

    controller.run_approval_submenu()

    controller.reject.assert_called_once_with("ORD-20260416-0001")


def test_승인거절_서브메뉴에서_0_선택시_바로_루프가_종료된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "list_pending_orders")
    mocker.patch.object(controller, "approve")
    mocker.patch.object(controller, "reject")
    view.get_order_approval_menu_choice.side_effect = ["0"]

    controller.run_approval_submenu()

    controller.list_pending_orders.assert_not_called()
    controller.approve.assert_not_called()
    controller.reject.assert_not_called()


def test_승인거절_서브메뉴에서_잘못된_입력시_안내_메시지_출력_후_계속_진행한다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository)
    view.get_order_approval_menu_choice.side_effect = ["abc", "0"]

    controller.run_approval_submenu()

    view.show_message.assert_called_once()
    assert "잘못된" in view.show_message.call_args[0][0]
