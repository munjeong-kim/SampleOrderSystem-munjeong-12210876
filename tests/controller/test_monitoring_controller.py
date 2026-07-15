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


def _find_row(rows, sample_id):
    for sample, required, status in rows:
        if sample.sample_id == sample_id:
            return sample, required, status
    raise AssertionError(f"{sample_id}에 대한 행을 찾을 수 없습니다")


def test_재고가_0이면_필요_수량과_무관하게_고갈로_표기된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=0)
    )
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.RESERVED)
    )
    controller = MonitoringController(view, order_repository, sample_repository)

    controller.show_stock_status()

    rows = view.show_stock_status.call_args[0][0]
    sample, required, status = _find_row(rows, "S-001")
    assert required == 10
    assert status == "고갈"


def test_재고가_0보다_크고_필요수량보다_적으면_부족으로_표기된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=5)
    )
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.RESERVED)
    )
    controller = MonitoringController(view, order_repository, sample_repository)

    controller.show_stock_status()

    rows = view.show_stock_status.call_args[0][0]
    sample, required, status = _find_row(rows, "S-001")
    assert required == 10
    assert status == "부족"


def test_재고가_0보다_크고_필요수량_이상이면_여유로_표기된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=10)
    )
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.RESERVED)
    )
    controller = MonitoringController(view, order_repository, sample_repository)

    controller.show_stock_status()

    rows = view.show_stock_status.call_args[0][0]
    sample, required, status = _find_row(rows, "S-001")
    assert required == 10
    assert status == "여유"


def test_RESERVED_주문이_없는_시료는_필요수량_0으로_간주되어_재고가_있으면_여유로_표기된다(
    tmp_path, mocker
):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=10)
    )
    controller = MonitoringController(view, order_repository, sample_repository)

    controller.show_stock_status()

    rows = view.show_stock_status.call_args[0][0]
    sample, required, status = _find_row(rows, "S-001")
    assert required == 0
    assert status == "여유"


def test_필요_수량은_해당_시료의_RESERVED_주문_수량만_합산한다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=5)
    )
    sample_repository.create(
        Sample(sample_id="S-002", name="유리 기판", avg_production_time=1.0, yield_rate=0.9, stock_quantity=5)
    )
    order_repository.create(
        Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10, status=OrderStatus.RESERVED)
    )
    order_repository.create(
        Order(order_id="ORD-0002", sample_id="S-001", customer_name="김철수", quantity=20, status=OrderStatus.RESERVED)
    )
    order_repository.create(
        Order(order_id="ORD-0003", sample_id="S-001", customer_name="이영희", quantity=100, status=OrderStatus.CONFIRMED)
    )
    order_repository.create(
        Order(order_id="ORD-0004", sample_id="S-002", customer_name="박영수", quantity=5, status=OrderStatus.RESERVED)
    )
    controller = MonitoringController(view, order_repository, sample_repository)

    controller.show_stock_status()

    rows = view.show_stock_status.call_args[0][0]
    _, required_s001, _ = _find_row(rows, "S-001")
    _, required_s002, _ = _find_row(rows, "S-002")
    assert required_s001 == 30
    assert required_s002 == 5


def test_서브메뉴에서_1_선택시_show_order_status_summary가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = MonitoringController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "show_order_status_summary")
    view.get_monitoring_menu_choice.side_effect = ["1", "0"]

    controller.run_submenu()

    controller.show_order_status_summary.assert_called_once()


def test_서브메뉴에서_2_선택시_show_stock_status가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = MonitoringController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "show_stock_status")
    view.get_monitoring_menu_choice.side_effect = ["2", "0"]

    controller.run_submenu()

    controller.show_stock_status.assert_called_once()


def test_서브메뉴에서_0_선택시_바로_루프가_종료된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = MonitoringController(view, order_repository, sample_repository)
    mocker.patch.object(controller, "show_order_status_summary")
    mocker.patch.object(controller, "show_stock_status")
    view.get_monitoring_menu_choice.side_effect = ["0"]

    controller.run_submenu()

    controller.show_order_status_summary.assert_not_called()
    controller.show_stock_status.assert_not_called()


def test_서브메뉴에서_잘못된_입력시_안내_메시지_출력_후_계속_진행한다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository, order_repository = _make_repositories(tmp_path)
    controller = MonitoringController(view, order_repository, sample_repository)
    view.get_monitoring_menu_choice.side_effect = ["xyz", "0"]

    controller.run_submenu()

    assert any(
        "잘못된 입력입니다" in call.args[0] for call in view.show_message.call_args_list
    )
