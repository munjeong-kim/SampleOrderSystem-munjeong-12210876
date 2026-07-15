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

    def get_order_reservation_input(self) -> dict:
        sample_id = input("시료 ID: ")
        customer_name = input("고객명: ")
        quantity = int(input("주문 수량: "))

        return {
            "sample_id": sample_id,
            "customer_name": customer_name,
            "quantity": quantity,
        }

    def show_order_menu(self) -> None:
        print("=== 시료 주문 ===")
        print("1. 주문 접수")
        print("0. 뒤로가기")

    def get_order_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def show_order_list(self, orders: list) -> None:
        for order in orders:
            print(
                f"{order.order_id} | {order.sample_id} | "
                f"{order.customer_name} | 수량: {order.quantity}"
            )

    def show_order_approval_menu(self) -> None:
        print("=== 주문 승인/거절 ===")
        print("1. 승인")
        print("2. 거절")
        print("0. 뒤로가기")

    def get_order_approval_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def show_numbered_order_list(self, orders: list) -> None:
        for number, order in enumerate(orders, start=1):
            print(
                f"{number}. {order.order_id} | {order.customer_name} | "
                f"{order.sample_id} | 수량: {order.quantity}"
            )

    def get_order_selection_number(self) -> int:
        return int(input("번호를 선택하세요: "))

    def show_current_production(self, job) -> None:
        print(
            f"현재 생산 중: {job.order_id} | {job.sample_id} | "
            f"실생산량: {job.quantity} | 시작 시각: {job.started_at} | "
            f"총 생산 시간: {job.total_seconds}초"
        )

    def show_production_queue(self, jobs: list) -> None:
        for number, job in enumerate(jobs, start=1):
            status = "생산 중" if job.started_at is not None else "대기 중"
            print(
                f"{number}. {job.order_id} | {job.sample_id} | "
                f"실생산량: {job.quantity} | {status}"
            )

    def show_production_menu(self) -> None:
        print("=== 생산 라인 ===")
        print("1. 생산 현황 조회")
        print("2. 대기 큐 목록 확인")
        print("0. 뒤로가기")

    def get_production_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def show_order_status_summary(self, counts: dict) -> None:
        for status, count in counts.items():
            print(f"{status}: {count}건")

    def show_stock_status(self, rows: list) -> None:
        for sample, required, status in rows:
            print(
                f"{sample.sample_id} | {sample.name} | 재고: {sample.stock_quantity} | "
                f"필요 수량: {required} | 상태: {status}"
            )

    def show_monitoring_menu(self) -> None:
        print("=== 모니터링 ===")
        print("1. 주문량 확인")
        print("2. 재고량 확인")
        print("0. 뒤로가기")

    def get_monitoring_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def show_shipment_menu(self) -> None:
        print("=== 출고 처리 ===")
        print("1. 출고 처리")
        print("0. 뒤로가기")

    def get_shipment_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")
