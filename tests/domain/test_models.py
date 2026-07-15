from src.domain.models import Order, OrderStatus, Sample


def test_시료_생성_시_속성이_올바르게_저장된다():
    sample = Sample(
        sample_id="S-001",
        name="실리콘 웨이퍼-8인치",
        avg_production_time=10.5,
        yield_rate=0.9,
    )

    assert sample.sample_id == "S-001"
    assert sample.name == "실리콘 웨이퍼-8인치"
    assert sample.avg_production_time == 10.5
    assert sample.yield_rate == 0.9


def test_시료_생성_시_재고_기본값은_0이다():
    sample = Sample(
        sample_id="S-001",
        name="실리콘 웨이퍼-8인치",
        avg_production_time=10.5,
        yield_rate=0.9,
    )

    assert sample.stock_quantity == 0


def test_주문상태는_5개의_값을_모두_가진다():
    assert {status.name for status in OrderStatus} == {
        "RESERVED",
        "REJECTED",
        "PRODUCING",
        "CONFIRMED",
        "RELEASE",
    }


def test_주문_생성_시_속성이_올바르게_저장된다():
    order = Order(
        order_id="ORD-20260416-0043",
        sample_id="S-001",
        customer_name="홍길동",
        quantity=100,
    )

    assert order.order_id == "ORD-20260416-0043"
    assert order.sample_id == "S-001"
    assert order.customer_name == "홍길동"
    assert order.quantity == 100


def test_주문_생성_시_기본_상태는_RESERVED이다():
    order = Order(
        order_id="ORD-20260416-0043",
        sample_id="S-001",
        customer_name="홍길동",
        quantity=100,
    )

    assert order.status == OrderStatus.RESERVED
