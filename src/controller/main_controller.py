IMPLEMENTED_MENU_CHOICES = {"1", "2", "3", "4", "5", "6"}


class MainController:
    def __init__(self, view):
        self.view = view

    def run(self) -> None:
        while True:
            self.view.show_menu()
            choice = self.view.get_menu_choice()

            if choice == "0":
                self.view.show_message("프로그램을 종료합니다.")
                break
            elif choice in IMPLEMENTED_MENU_CHOICES:
                self.view.show_message("아직 구현되지 않은 기능입니다.")
            else:
                self.view.show_message("잘못된 입력입니다. 다시 입력해주세요.")
