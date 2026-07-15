INVALID_INPUT_MESSAGE = "잘못된 입력입니다. 다시 입력해주세요."


def run_menu_loop(show_menu, get_choice, show_message, handlers: dict) -> None:
    """0을 뒤로가기/종료로 취급하는 공통 메뉴 dispatch 루프.

    handlers에 없는 선택지는 INVALID_INPUT_MESSAGE로 안내하고 계속 진행한다.
    """
    while True:
        show_menu()
        choice = get_choice()

        if choice == "0":
            break

        handler = handlers.get(choice)
        if handler is not None:
            handler()
        else:
            show_message(INVALID_INPUT_MESSAGE)
