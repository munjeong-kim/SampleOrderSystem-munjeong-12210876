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

    def get_sample_registration_input(self) -> dict:
        sample_id = input("시료 ID: ")
        name = input("이름: ")
        avg_production_time = float(input("평균 생산시간(sec/ea): "))
        yield_rate = float(input("수율: "))

        return {
            "sample_id": sample_id,
            "name": name,
            "avg_production_time": avg_production_time,
            "yield_rate": yield_rate,
        }

    def show_sample_list(self, samples: list, page: int, total_pages: int) -> None:
        for sample in samples:
            print(
                f"{sample.sample_id} | {sample.name} | "
                f"평균 생산시간: {sample.avg_production_time} | 수율: {sample.yield_rate} | "
                f"재고: {sample.stock_quantity}"
            )
        print(f"{page}/{total_pages} 페이지")
