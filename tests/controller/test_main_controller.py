from datetime import datetime

from src.controller.main_controller import MainController
from src.controller.order_controller import OrderController
from src.controller.production_controller import ProductionController
from src.controller.sample_controller import SampleController
from src.domain.models import Order, ProductionJob, Sample
from src.repository.order_repository import OrderRepository
from src.repository.production_queue_repository import ProductionQueueRepository
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage


def test_입력값_0이면_종료_메시지를_출력하고_루프를_종료한다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.return_value = "0"
    controller = MainController(view)

    controller.run()

    view.show_menu.assert_called_once()
    view.get_menu_choice.assert_called_once()
    view.show_message.assert_called_once()
    assert "종료" in view.show_message.call_args[0][0]


def test_구현되지_않은_메뉴_번호_입력시_안내_후_계속_진행하다가_0_입력시_종료한다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["1", "0"]
    controller = MainController(view)

    controller.run()

    assert view.show_menu.call_count == 2
    assert view.get_menu_choice.call_count == 2
    assert view.show_message.call_count == 2
    assert "구현되지 않" in view.show_message.call_args_list[0][0][0]
    assert "종료" in view.show_message.call_args_list[1][0][0]


def test_잘못된_입력시_안내_메시지를_출력하고_계속_진행하다가_0_입력시_종료한다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["abc", "0"]
    controller = MainController(view)

    controller.run()

    assert view.show_menu.call_count == 2
    assert view.get_menu_choice.call_count == 2
    assert view.show_message.call_count == 2
    first_message = view.show_message.call_args_list[0][0][0]
    assert "잘못된" in first_message
    assert "종료" in view.show_message.call_args_list[1][0][0]


def test_1부터_6까지_모든_메뉴_번호는_구현되지_않은_기능_안내_후_계속_진행한다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["1", "2", "3", "4", "5", "6", "0"]
    controller = MainController(view)

    controller.run()

    assert view.show_message.call_count == 7
    for call in view.show_message.call_args_list[:6]:
        assert "구현되지 않" in call[0][0]
    assert "종료" in view.show_message.call_args_list[6][0][0]


def test_시료_컨트롤러가_주어지면_메뉴_1_입력시_서브메뉴가_호출된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["1", "0"]
    sample_controller = mocker.MagicMock()
    controller = MainController(view, sample_controller=sample_controller)

    controller.run()

    sample_controller.run_submenu.assert_called_once()
    view.show_message.assert_called_once()
    assert "종료" in view.show_message.call_args_list[0][0][0]


def test_시료_컨트롤러가_있어도_2부터_6까지는_구현되지_않은_기능_안내가_출력된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["2", "3", "4", "5", "6", "0"]
    sample_controller = mocker.MagicMock()
    controller = MainController(view, sample_controller=sample_controller)

    controller.run()

    sample_controller.run_submenu.assert_not_called()
    assert view.show_message.call_count == 6
    for call in view.show_message.call_args_list[:5]:
        assert "구현되지 않" in call[0][0]
    assert "종료" in view.show_message.call_args_list[5][0][0]


def test_주문_컨트롤러가_주어지면_메뉴_2_입력시_서브메뉴가_호출된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["2", "0"]
    order_controller = mocker.MagicMock()
    controller = MainController(view, order_controller=order_controller)

    controller.run()

    order_controller.run_submenu.assert_called_once()
    view.show_message.assert_called_once()
    assert "종료" in view.show_message.call_args_list[0][0][0]


def test_주문_컨트롤러가_없으면_메뉴_2_입력시_기존_안내가_유지된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["2", "0"]
    controller = MainController(view)

    controller.run()

    assert view.show_message.call_count == 2
    assert "구현되지 않" in view.show_message.call_args_list[0][0][0]
    assert "종료" in view.show_message.call_args_list[1][0][0]


def test_주문_컨트롤러가_주어지면_메뉴_3_입력시_승인거절_서브메뉴가_호출된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["3", "0"]
    order_controller = mocker.MagicMock()
    controller = MainController(view, order_controller=order_controller)

    controller.run()

    order_controller.run_approval_submenu.assert_called_once()
    view.show_message.assert_called_once()
    assert "종료" in view.show_message.call_args_list[0][0][0]


def test_주문_컨트롤러가_없으면_메뉴_3_입력시_기존_안내가_유지된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["3", "0"]
    controller = MainController(view)

    controller.run()

    assert view.show_message.call_count == 2
    assert "구현되지 않" in view.show_message.call_args_list[0][0][0]
    assert "종료" in view.show_message.call_args_list[1][0][0]


def test_생산_컨트롤러가_주어지면_메뉴_5_입력시_서브메뉴가_호출된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["5", "0"]
    production_controller = mocker.MagicMock()
    controller = MainController(view, production_controller=production_controller)

    controller.run()

    production_controller.run_submenu.assert_called_once()
    view.show_message.assert_called_once()
    assert "종료" in view.show_message.call_args_list[0][0][0]


def test_생산_컨트롤러가_없으면_메뉴_5_입력시_기존_안내가_유지된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["5", "0"]
    controller = MainController(view)

    controller.run()

    assert view.show_message.call_count == 2
    assert "구현되지 않" in view.show_message.call_args_list[0][0][0]
    assert "종료" in view.show_message.call_args_list[1][0][0]


def test_모니터링_컨트롤러가_주어지면_메뉴_4_입력시_서브메뉴가_호출된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["4", "0"]
    monitoring_controller = mocker.MagicMock()
    controller = MainController(view, monitoring_controller=monitoring_controller)

    controller.run()

    monitoring_controller.run_submenu.assert_called_once()
    view.show_message.assert_called_once()
    assert "종료" in view.show_message.call_args_list[0][0][0]


def test_모니터링_컨트롤러가_없으면_메뉴_4_입력시_기존_안내가_유지된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["4", "0"]
    controller = MainController(view)

    controller.run()

    assert view.show_message.call_count == 2
    assert "구현되지 않" in view.show_message.call_args_list[0][0][0]
    assert "종료" in view.show_message.call_args_list[1][0][0]


def test_통계가_정확히_계산되어_view에_전달된다(tmp_path, mocker):
    view = mocker.MagicMock()
    sample_repository = SampleRepository(JsonStorage(str(tmp_path / "samples.json")))
    order_repository = OrderRepository(JsonStorage(str(tmp_path / "orders.json")))
    production_queue_repository = ProductionQueueRepository(
        JsonStorage(str(tmp_path / "production_queue.json"))
    )
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9, stock_quantity=30)
    )
    sample_repository.create(
        Sample(sample_id="S-002", name="유리 기판", avg_production_time=1.0, yield_rate=0.9, stock_quantity=20)
    )
    order_repository.create(Order(order_id="ORD-0001", sample_id="S-001", customer_name="홍길동", quantity=10))
    order_repository.create(Order(order_id="ORD-0002", sample_id="S-002", customer_name="김철수", quantity=20))
    order_repository.create(Order(order_id="ORD-0003", sample_id="S-001", customer_name="이영희", quantity=30))
    production_queue_repository.enqueue(
        ProductionJob(order_id="ORD-0003", sample_id="S-001", quantity=5, total_seconds=50.0)
    )
    sample_controller = SampleController(mocker.MagicMock(), sample_repository)
    order_controller = OrderController(
        mocker.MagicMock(), order_repository, sample_repository, production_queue_repository
    )
    production_controller = ProductionController(
        mocker.MagicMock(), production_queue_repository, order_repository, sample_repository
    )
    fixed_now = datetime(2026, 4, 16, 9, 0, 0)
    mocker.patch("src.controller.main_controller.datetime").now.return_value = fixed_now
    controller = MainController(
        view,
        sample_controller=sample_controller,
        order_controller=order_controller,
        production_controller=production_controller,
    )
    view.get_menu_choice.side_effect = ["0"]

    controller.run()

    view.show_system_stats.assert_called_once()
    stats = view.show_system_stats.call_args[0][0]
    assert stats["current_time"] == fixed_now
    assert stats["sample_count"] == 2
    assert stats["total_stock"] == 50
    assert stats["order_count"] == 3
    assert stats["queue_count"] == 1


def test_시료_주문_생산큐가_비어있어도_0으로_정상_표시된다(mocker):
    view = mocker.MagicMock()
    controller = MainController(view)
    view.get_menu_choice.side_effect = ["0"]

    controller.run()

    view.show_system_stats.assert_called_once()
    stats = view.show_system_stats.call_args[0][0]
    assert stats["sample_count"] == 0
    assert stats["total_stock"] == 0
    assert stats["order_count"] == 0
    assert stats["queue_count"] == 0


def test_출고_컨트롤러가_주어지면_메뉴_6_입력시_서브메뉴가_호출된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["6", "0"]
    shipment_controller = mocker.MagicMock()
    controller = MainController(view, shipment_controller=shipment_controller)

    controller.run()

    shipment_controller.run_submenu.assert_called_once()
    view.show_message.assert_called_once()
    assert "종료" in view.show_message.call_args_list[0][0][0]


def test_출고_컨트롤러가_없으면_메뉴_6_입력시_기존_안내가_유지된다(mocker):
    view = mocker.MagicMock()
    view.get_menu_choice.side_effect = ["6", "0"]
    controller = MainController(view)

    controller.run()

    assert view.show_message.call_count == 2
    assert "구현되지 않" in view.show_message.call_args_list[0][0][0]
    assert "종료" in view.show_message.call_args_list[1][0][0]
