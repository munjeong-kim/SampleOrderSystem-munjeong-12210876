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
            self._print_sample_line(sample)
        print(f"{page}/{total_pages} 페이지")

    def show_search_results(self, results: list) -> None:
        for sample in results:
            self._print_sample_line(sample)

    def _print_sample_line(self, sample) -> None:
        print(
            f"{sample.sample_id} | {sample.name} | "
            f"평균 생산시간: {sample.avg_production_time} | 수율: {sample.yield_rate} | "
            f"재고: {sample.stock_quantity}"
        )

    def show_sample_menu(self) -> None:
        print("=== 시료 관리 ===")
        print("1. 시료 등록")
        print("2. 시료 목록 조회")
        print("3. 시료 검색")
        print("0. 뒤로가기")

    def get_sample_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def get_page_number(self) -> int:
        return int(input("조회할 페이지 번호를 입력하세요: "))

    def get_list_navigation_choice(self) -> str:
        return input("다음 페이지(n) / 이전 페이지(p) / 뒤로가기(b): ")

    def get_search_keyword(self) -> str:
        return input("검색어를 입력하세요: ")
