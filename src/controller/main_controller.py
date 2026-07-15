IMPLEMENTED_MENU_CHOICES = {"1", "2", "3", "4", "5", "6"}


class MainController:
    def __init__(
        self,
        view,
        sample_controller=None,
        order_controller=None,
        production_controller=None,
        monitoring_controller=None,
        shipment_controller=None,
    ):
        self.view = view
        self.sample_controller = sample_controller
        self.order_controller = order_controller
        self.production_controller = production_controller
        self.monitoring_controller = monitoring_controller
        self.shipment_controller = shipment_controller

    def run(self) -> None:
        handlers = {}
        if self.sample_controller is not None:
            handlers["1"] = self.sample_controller.run_submenu
        if self.order_controller is not None:
            handlers["2"] = self.order_controller.run_submenu
            handlers["3"] = self.order_controller.run_approval_submenu
        if self.monitoring_controller is not None:
            handlers["4"] = self.monitoring_controller.run_submenu
        if self.production_controller is not None:
            handlers["5"] = self.production_controller.run_submenu
        if self.shipment_controller is not None:
            handlers["6"] = self.shipment_controller.run_submenu

        while True:
            self.view.show_menu()
            choice = self.view.get_menu_choice()

            if choice == "0":
                self.view.show_message("프로그램을 종료합니다.")
                break

            handler = handlers.get(choice)
            if handler is not None:
                handler()
            elif choice in IMPLEMENTED_MENU_CHOICES:
                self.view.show_message("아직 구현되지 않은 기능입니다.")
            else:
                self.view.show_message("잘못된 입력입니다. 다시 입력해주세요.")
