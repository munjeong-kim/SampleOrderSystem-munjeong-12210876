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


def select_order_by_number(view, orders: list):
    """번호와 함께 표시된 목록(orders)에서 view.get_order_selection_number()로 입력받은
    번호에 대응하는 Order를 반환한다.

    orders가 비어있거나 번호가 범위를 벗어나면 view.show_message로 안내하고 None을 반환한다.
    """
    if not orders:
        view.show_message("선택할 주문이 없습니다.")
        return None

    number = view.get_order_selection_number()
    if number < 1 or number > len(orders):
        view.show_message("잘못된 번호입니다.")
        return None

    return orders[number - 1]
