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
    mock_datetime = mocker.patch("src.controller.production_controller.datetime")
    mock_datetime.now.return_value = datetime(2026, 4, 16, 9, 10, 30)
    mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )

    controller.process_queue()

    sample = sample_repository.read_one("S-001")
    assert sample.stock_quantity == 13  # 50 + 63(실생산량) - 100(주문 수량)

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
    # 재고 = 0(초기) + job.quantity(실생산량) - order.quantity(주문수량, 셋 다 10)
    assert sample_repository.read_one("S-001").stock_quantity == 0  # 0 + 10 - 10
    assert sample_repository.read_one("S-002").stock_quantity == 10  # 0 + 20 - 10
    assert sample_repository.read_one("S-003").stock_quantity == 20  # 0 + 30 - 10
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


def test_생산_현황_조회_시_process_queue가_먼저_실행된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    mocker.patch.object(controller, "process_queue")

    controller.show_status()

    controller.process_queue.assert_called_once()


def test_현재_생산_중인_작업이_없으면_안내_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    mocker.patch.object(controller, "process_queue")

    controller.show_status()

    view.show_current_production.assert_not_called()
    view.show_message.assert_called_once()
    assert "현재 생산 중인 작업이 없습니다" in view.show_message.call_args[0][0]


def test_현재_생산_중인_작업이_있으면_view로_표시된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    job = ProductionJob(
        order_id="ORD-0001",
        sample_id="S-001",
        quantity=63,
        total_seconds=630.0,
        started_at="2026-04-16T09:00:00",
    )
    production_queue_repository.enqueue(job)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    mocker.patch.object(controller, "process_queue")

    controller.show_status()

    view.show_message.assert_not_called()
    view.show_current_production.assert_called_once()
    shown_job = view.show_current_production.call_args[0][0]
    assert shown_job.order_id == "ORD-0001"


def test_대기_큐_목록_조회_시_process_queue가_먼저_실행된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    mocker.patch.object(controller, "process_queue")

    controller.show_waiting_queue()

    controller.process_queue.assert_called_once()


def test_대기_큐가_비어있으면_안내_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    mocker.patch.object(controller, "process_queue")

    controller.show_waiting_queue()

    view.show_production_queue.assert_not_called()
    view.show_message.assert_called_once()
    assert "대기 중인 생산 작업이 없습니다" in view.show_message.call_args[0][0]


def test_대기_큐_목록이_FIFO_순서로_표시된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
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
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    mocker.patch.object(controller, "process_queue")

    controller.show_waiting_queue()

    view.show_production_queue.assert_called_once()
    jobs = view.show_production_queue.call_args[0][0]
    assert [job.order_id for job in jobs] == ["ORD-0001", "ORD-0002"]


def test_서브메뉴에서_1_선택시_show_status가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    mocker.patch.object(controller, "show_status")
    view.get_production_menu_choice.side_effect = ["1", "0"]

    controller.run_submenu()

    controller.show_status.assert_called_once()


def test_서브메뉴에서_2_선택시_show_waiting_queue가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    mocker.patch.object(controller, "show_waiting_queue")
    view.get_production_menu_choice.side_effect = ["2", "0"]

    controller.run_submenu()

    controller.show_waiting_queue.assert_called_once()


def test_서브메뉴에서_0_선택시_바로_루프가_종료된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    mocker.patch.object(controller, "show_status")
    mocker.patch.object(controller, "show_waiting_queue")
    view.get_production_menu_choice.side_effect = ["0"]

    controller.run_submenu()

    controller.show_status.assert_not_called()
    controller.show_waiting_queue.assert_not_called()


def test_서브메뉴에서_잘못된_입력시_안내_메시지_출력_후_계속_진행한다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository, production_queue_repository = _make_repositories(tmp_path)
    controller = ProductionController(
        view, production_queue_repository, order_repository, sample_repository
    )
    view.get_production_menu_choice.side_effect = ["xyz", "0"]

    controller.run_submenu()

    assert any(
        "잘못된 입력입니다" in call.args[0] for call in view.show_message.call_args_list
    )
