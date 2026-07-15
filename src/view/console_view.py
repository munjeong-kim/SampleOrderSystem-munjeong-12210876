class ConsoleView:
    def show_menu(self) -> None:
        print("=== S-Semi 반도체 시료 생산주문관리 시스템 ===")
        print("1. 시료 관리")
        print("2. 시료 주문")
        print("3. 주문 승인/거절")
        print("4. 모니터링")
        print("5. 생산라인 조회")
        print("6. 출고 처리")
        print("0. 종료")

    def get_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def show_message(self, message: str) -> None:
        print(message)
