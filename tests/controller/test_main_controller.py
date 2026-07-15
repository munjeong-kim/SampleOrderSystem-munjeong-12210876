from src.controller.main_controller import MainController


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
