class ConsoleView:
    DIVIDER = "-" * 60

    def _print_title(self, title: str) -> None:
        print()
        print(f"=== {title} ===")

    def show_system_stats(self, stats: dict) -> None:
        print(self.DIVIDER)
        print(f"현재 시각: {stats['current_time']}")
        print(
            f"등록 시료 종수: {stats['sample_count']} | "
            f"총 재고 수량: {stats['total_stock']} | "
            f"전체 주문 건수: {stats['order_count']} | "
            f"생산 라인 대기 건수: {stats['queue_count']}"
        )
        print(self.DIVIDER)

    def show_menu(self) -> None:
        self._print_title("S-Semi 반도체 시료 생산주문관리 시스템")
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
        print(f">> {message}")

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
        self._print_sample_table_header()
        for sample in samples:
            self._print_sample_line(sample)
        print(self.DIVIDER)
        print(f"{page}/{total_pages} 페이지")

    def show_search_results(self, results: list) -> None:
        self._print_sample_table_header()
        for sample in results:
            self._print_sample_line(sample)
        print(self.DIVIDER)

    def _print_sample_table_header(self) -> None:
        print(self.DIVIDER)
        print(
            f"{'시료 ID':<10} {'이름':<20} {'생산시간(초/ea)':>14} "
            f"{'수율':>6} {'재고':>6}"
        )
        print(self.DIVIDER)

    def _print_sample_line(self, sample) -> None:
        print(
            f"{sample.sample_id:<10} {sample.name:<20} "
            f"{sample.avg_production_time:>14} {sample.yield_rate:>6} "
            f"{sample.stock_quantity:>6}"
        )

    def show_sample_menu(self) -> None:
        self._print_title("시료 관리")
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
        self._print_title("시료 주문")
        print("1. 주문 접수")
        print("0. 뒤로가기")

    def get_order_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def show_order_list(self, orders: list) -> None:
        print(self.DIVIDER)
        print(f"{'주문번호':<20} {'시료 ID':<10} {'고객명':<10} {'수량':>6}")
        print(self.DIVIDER)
        for order in orders:
            self._print_order_line(order)
        print(self.DIVIDER)

    def show_order_approval_menu(self) -> None:
        self._print_title("주문 승인/거절")
        print("1. 승인")
        print("2. 거절")
        print("0. 뒤로가기")

    def get_order_approval_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def show_numbered_order_list(self, orders: list) -> None:
        print(self.DIVIDER)
        print(f"{'번호':>4} {'주문번호':<20} {'고객명':<10} {'시료 ID':<10} {'수량':>6}")
        print(self.DIVIDER)
        for number, order in enumerate(orders, start=1):
            print(
                f"{number:>4} {order.order_id:<20} {order.customer_name:<10} "
                f"{order.sample_id:<10} {order.quantity:>6}"
            )
        print(self.DIVIDER)

    def _print_order_line(self, order) -> None:
        print(
            f"{order.order_id:<20} {order.sample_id:<10} "
            f"{order.customer_name:<10} {order.quantity:>6}"
        )

    def get_order_selection_number(self) -> int:
        return int(input("번호를 선택하세요: "))

    def show_current_production(self, job) -> None:
        print(self.DIVIDER)
        print(
            f"현재 생산 중: {job.order_id} | {job.sample_id} | "
            f"실생산량: {job.quantity} | 시작 시각: {job.started_at} | "
            f"총 생산 시간: {job.total_seconds}초"
        )
        print(self.DIVIDER)

    def show_production_queue(self, jobs: list) -> None:
        print(self.DIVIDER)
        print(f"{'번호':>4} {'주문번호':<20} {'시료 ID':<10} {'실생산량':>8} {'상태':<6}")
        print(self.DIVIDER)
        for number, job in enumerate(jobs, start=1):
            status = "생산 중" if job.started_at is not None else "대기 중"
            print(
                f"{number:>4} {job.order_id:<20} {job.sample_id:<10} "
                f"{job.quantity:>8} {status:<6}"
            )
        print(self.DIVIDER)

    def show_production_menu(self) -> None:
        self._print_title("생산 라인")
        print("1. 생산 현황 조회")
        print("2. 대기 큐 목록 확인")
        print("0. 뒤로가기")

    def get_production_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def show_order_status_summary(self, counts: dict) -> None:
        print(self.DIVIDER)
        for status, count in counts.items():
            print(f"{status:<10}: {count}건")
        print(self.DIVIDER)

    def show_stock_status(self, rows: list) -> None:
        print(self.DIVIDER)
        print(f"{'시료 ID':<10} {'이름':<20} {'재고':>6} {'필요 수량':>8} {'상태':<6}")
        print(self.DIVIDER)
        for sample, required, status in rows:
            print(
                f"{sample.sample_id:<10} {sample.name:<20} "
                f"{sample.stock_quantity:>6} {required:>8} {status:<6}"
            )
        print(self.DIVIDER)

    def show_monitoring_menu(self) -> None:
        self._print_title("모니터링")
        print("1. 주문량 확인")
        print("2. 재고량 확인")
        print("0. 뒤로가기")

    def get_monitoring_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")

    def show_shipment_menu(self) -> None:
        self._print_title("출고 처리")
        print("1. 출고 처리")
        print("0. 뒤로가기")

    def get_shipment_menu_choice(self) -> str:
        return input("메뉴를 선택하세요: ")
