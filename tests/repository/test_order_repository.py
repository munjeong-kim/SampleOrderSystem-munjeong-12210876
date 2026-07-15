from src.domain.models import Order, OrderStatus
from src.repository.order_repository import OrderRepository
from src.storage.json_storage import JsonStorage


def _make_repository(tmp_path):
    storage = JsonStorage(str(tmp_path / "orders.json"))
    return OrderRepository(storage)


def test_주문_생성_후_read_all로_조회된다(tmp_path):
    repository = _make_repository(tmp_path)
    order = Order(
        order_id="ORD-20260416-0043",
        sample_id="S-001",
        customer_name="홍길동",
        quantity=100,
    )

    repository.create(order)

    assert repository.read_all() == [order]


def test_주문_생성_후_read_one으로_조회된다(tmp_path):
    repository = _make_repository(tmp_path)
    order = Order(
        order_id="ORD-20260416-0043",
        sample_id="S-001",
        customer_name="홍길동",
        quantity=100,
    )

    repository.create(order)

    assert repository.read_one("ORD-20260416-0043") == order


def test_존재하지_않는_주문번호로_read_one하면_None을_반환한다(tmp_path):
    repository = _make_repository(tmp_path)

    assert repository.read_one("ORD-NOT-EXIST") is None


def test_update로_주문_상태를_변경하면_반영된다(tmp_path):
    repository = _make_repository(tmp_path)
    order = Order(
        order_id="ORD-20260416-0043",
        sample_id="S-001",
        customer_name="홍길동",
        quantity=100,
    )
    repository.create(order)

    order.status = OrderStatus.CONFIRMED
    repository.update(order)

    assert repository.read_one("ORD-20260416-0043").status == OrderStatus.CONFIRMED


def test_저장소를_새로_생성해도_기존에_저장된_주문이_유지된다(tmp_path):
    storage = JsonStorage(str(tmp_path / "orders.json"))
    order = Order(
        order_id="ORD-20260416-0043",
        sample_id="S-001",
        customer_name="홍길동",
        quantity=100,
    )
    OrderRepository(storage).create(order)

    new_repository = OrderRepository(JsonStorage(str(tmp_path / "orders.json")))

    assert new_repository.read_one("ORD-20260416-0043") == order
