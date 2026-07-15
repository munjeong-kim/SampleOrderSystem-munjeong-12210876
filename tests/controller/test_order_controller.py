from datetime import date, datetime

from src.controller.order_controller import OrderController
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


def test_등록된_시료로_주문_접수시_RESERVED_상태로_등록되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9)
    )
    view.get_order_reservation_input.return_value = {
        "sample_id": "S-001",
        "customer_name": "홍길동",
        "quantity": 100,
    }
    mocker.patch("src.controller.order_controller.date").today.return_value = date(2026, 4, 16)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

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
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    view.get_order_reservation_input.return_value = {
        "sample_id": "S-999",
        "customer_name": "홍길동",
        "quantity": 100,
    }
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.reserve()

    assert order_repository.read_all() == []
    view.show_message.assert_called_once()
    assert "등록되지 않은 시료" in view.show_message.call_args[0][0]


def test_같은_날_여러_건_접수시_주문번호_순번이_증가한다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9)
    )
    view.get_order_reservation_input.return_value = {
        "sample_id": "S-001",
        "customer_name": "홍길동",
        "quantity": 100,
    }
    mocker.patch("src.controller.order_controller.date").today.return_value = date(2026, 4, 16)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.reserve()
    controller.reserve()

    orders = order_repository.read_all()
    assert [o.order_id for o in orders] == ["ORD-20260416-0001", "ORD-20260416-0002"]


def test_서브메뉴에서_1_선택시_reserve가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    mocker.patch.object(controller, "reserve")
    view.get_order_menu_choice.side_effect = ["1", "0"]

    controller.run_submenu()

    controller.reserve.assert_called_once()


def test_서브메뉴에서_0_선택시_바로_루프가_종료된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    mocker.patch.object(controller, "reserve")
    view.get_order_menu_choice.side_effect = ["0"]

    controller.run_submenu()

    controller.reserve.assert_not_called()


def test_서브메뉴에서_잘못된_입력시_안내_메시지_출력_후_계속_진행한다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    view.get_order_menu_choice.side_effect = ["abc", "0"]

    controller.run_submenu()

    view.show_message.assert_called_once()
    assert "잘못된" in view.show_message.call_args[0][0]


def test_RESERVED_상태_주문만_목록에_표시된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
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
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.list_pending_orders()

    view.show_order_list.assert_called_once()
    orders = view.show_order_list.call_args[0][0]
    assert [o.order_id for o in orders] == ["ORD-20260416-0001"]


def test_접수된_주문이_없으면_안내_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.CONFIRMED,
        )
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.list_pending_orders()

    view.show_order_list.assert_not_called()
    view.show_message.assert_called_once()
    assert "접수된 주문이 없습니다" in view.show_message.call_args[0][0]


def test_재고가_충분한_주문을_승인하면_CONFIRMED로_전환되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    sample = Sample(
        sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=100
    )
    sample_repository.create(sample)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.approve("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.CONFIRMED
    view.show_message.assert_called_once()
    assert "CONFIRMED" in view.show_message.call_args[0][0]


def test_재고가_부족한_주문을_승인하면_PRODUCING으로_전환되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    sample = Sample(
        sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=50
    )
    sample_repository.create(sample)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.approve("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.PRODUCING
    view.show_message.assert_called_once()
    assert "PRODUCING" in view.show_message.call_args[0][0]


def test_존재하지_않는_주문번호로_승인_시도하면_오류_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.approve("ORD-NOT-EXIST")

    view.show_message.assert_called_once()
    assert "존재하지 않는 주문" in view.show_message.call_args[0][0]


def test_RESERVED가_아닌_주문을_승인_시도하면_오류_메시지가_출력되고_상태가_변경되지_않는다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
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
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.approve("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.CONFIRMED
    view.show_message.assert_called_once()
    assert "승인할 수 없는 상태" in view.show_message.call_args[0][0]


def test_RESERVED_상태_주문을_거절하면_REJECTED로_전환되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.reject("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.REJECTED
    view.show_message.assert_called_once()
    assert "REJECTED" in view.show_message.call_args[0][0]


def test_존재하지_않는_주문번호로_거절_시도하면_오류_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.reject("ORD-NOT-EXIST")

    view.show_message.assert_called_once()
    assert "존재하지 않는 주문" in view.show_message.call_args[0][0]


def test_RESERVED가_아닌_주문을_거절_시도하면_오류_메시지가_출력되고_상태가_변경되지_않는다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(
            order_id="ORD-20260416-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=100,
            status=OrderStatus.CONFIRMED,
        )
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.reject("ORD-20260416-0001")

    order = order_repository.read_one("ORD-20260416-0001")
    assert order.status == OrderStatus.CONFIRMED
    view.show_message.assert_called_once()
    assert "거절할 수 없는 상태" in view.show_message.call_args[0][0]


def test_서브메뉴_진입시_RESERVED_주문이_번호와_함께_자동으로_표시된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    order_repository.create(
        Order(order_id="ORD-20260416-0002", sample_id="S-002", customer_name="김철수", quantity=50)
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    view.get_order_approval_menu_choice.side_effect = ["0"]

    controller.run_approval_submenu()

    view.show_numbered_order_list.assert_called_once()
    orders = view.show_numbered_order_list.call_args[0][0]
    assert [o.order_id for o in orders] == ["ORD-20260416-0001", "ORD-20260416-0002"]


def test_접수된_주문이_없으면_안내_메시지만_표시되고_메뉴는_계속_진행된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    view.get_order_approval_menu_choice.side_effect = ["0"]

    controller.run_approval_submenu()

    view.show_numbered_order_list.assert_not_called()
    assert any(
        "접수된 주문이 없습니다" in call.args[0] for call in view.show_message.call_args_list
    )


def test_1_선택_후_유효한_번호를_입력하면_해당_주문이_승인된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    order_repository.create(
        Order(order_id="ORD-20260416-0002", sample_id="S-002", customer_name="김철수", quantity=50)
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    mocker.patch.object(controller, "approve")
    view.get_order_approval_menu_choice.side_effect = ["1", "0"]
    view.get_order_selection_number.return_value = 2

    controller.run_approval_submenu()

    controller.approve.assert_called_once_with("ORD-20260416-0002")


def test_2_선택_후_유효한_번호를_입력하면_해당_주문이_거절된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    mocker.patch.object(controller, "reject")
    view.get_order_approval_menu_choice.side_effect = ["2", "0"]
    view.get_order_selection_number.return_value = 1

    controller.run_approval_submenu()

    controller.reject.assert_called_once_with("ORD-20260416-0001")


def test_목록_범위를_벗어난_번호_입력시_오류_안내_후_계속_진행된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    mocker.patch.object(controller, "approve")
    view.get_order_approval_menu_choice.side_effect = ["1", "0"]
    view.get_order_selection_number.return_value = 5

    controller.run_approval_submenu()

    controller.approve.assert_not_called()
    assert any(
        "잘못된 번호" in call.args[0] for call in view.show_message.call_args_list
    )


def test_주문이_없는_상태에서_1을_선택하면_오류_안내_후_계속_진행된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    mocker.patch.object(controller, "approve")
    view.get_order_approval_menu_choice.side_effect = ["1", "0"]

    controller.run_approval_submenu()

    controller.approve.assert_not_called()
    assert any(
        "선택할 주문이 없습니다" in call.args[0] for call in view.show_message.call_args_list
    )


def test_승인거절_서브메뉴에서_0_선택시_바로_루프가_종료된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    mocker.patch.object(controller, "approve")
    mocker.patch.object(controller, "reject")
    view.get_order_approval_menu_choice.side_effect = ["0"]

    controller.run_approval_submenu()

    controller.approve.assert_not_called()
    controller.reject.assert_not_called()


def test_승인거절_서브메뉴에서_잘못된_입력시_안내_메시지_출력_후_계속_진행한다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)
    view.get_order_approval_menu_choice.side_effect = ["xyz", "0"]

    controller.run_approval_submenu()

    assert any(
        "잘못된 입력입니다" in call.args[0] for call in view.show_message.call_args_list
    )


def test_재고_부족으로_승인된_주문의_생산_작업이_큐에_등록된다(tmp_path, mocker):
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
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    mocker.patch(
        "src.controller.order_controller.datetime"
    ).now.return_value = datetime(2026, 4, 16, 9, 0, 0)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.approve("ORD-20260416-0001")

    jobs = production_queue_repository.read_all()
    assert len(jobs) == 1
    job = jobs[0]
    assert job.order_id == "ORD-20260416-0001"
    assert job.sample_id == "S-001"
    assert job.quantity == 63  # ceil((100-50)/0.8) == 63
    assert job.total_seconds == 630.0  # 10.0 * 63


def test_큐가_비어있을_때_승인하면_즉시_시작된다(tmp_path, mocker):
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
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    fixed_now = datetime(2026, 4, 16, 9, 0, 0)
    mocker.patch("src.controller.order_controller.datetime").now.return_value = fixed_now
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.approve("ORD-20260416-0001")

    job = production_queue_repository.read_head()
    assert job.started_at == fixed_now.isoformat()


def test_이미_큐에_작업이_있을_때_승인하면_새_작업은_대기로_등록된다(tmp_path, mocker):
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
    production_queue_repository.enqueue(
        ProductionJob(
            order_id="ORD-20260416-9999",
            sample_id="S-999",
            quantity=10,
            total_seconds=100.0,
            started_at="2026-04-16T08:00:00",
        )
    )
    order_repository.create(
        Order(order_id="ORD-20260416-0001", sample_id="S-001", customer_name="홍길동", quantity=100)
    )
    mocker.patch(
        "src.controller.order_controller.datetime"
    ).now.return_value = datetime(2026, 4, 16, 9, 0, 0)
    controller = OrderController(view, order_repository, sample_repository, production_queue_repository)

    controller.approve("ORD-20260416-0001")

    jobs = production_queue_repository.read_all()
    assert len(jobs) == 2
    new_job = jobs[1]
    assert new_job.order_id == "ORD-20260416-0001"
    assert new_job.started_at is None
