import pytest
import time
from core.domain import Order, Product, CartItem
from core.transforms import top_products_memoized


@pytest.fixture
def orders_for_top() -> tuple[Order, ...]:
    return (
        Order(id="o1", user_id="u1", items=[CartItem("p1", 5), CartItem("p2", 2)], total_price=1, timestamp=""),
        Order(id="o2", user_id="u2", items=[CartItem("p2", 3), CartItem("p3", 10)], total_price=1, timestamp=""),
        Order(id="o3", user_id="u1", items=[CartItem("p3", 8), CartItem("p1", 2)], total_price=1, timestamp=""),
    )
    # Итоги продаж:
    # p1: 5 + 2 = 7
    # p2: 2 + 3 = 5
    # p3: 10 + 8 = 18
    # Ожидаемый порядок: p3, p1, p2


@pytest.fixture
def products_for_top() -> tuple[Product, ...]:
    return (
        Product(id="p1", name="A", price=1, category_id="c1", tags=[], stock=1),
        Product(id="p2", name="B", price=1, category_id="c1", tags=[], stock=1),
        Product(id="p3", name="C", price=1, category_id="c1", tags=[], stock=1),
    )


def test_top_products_logic(orders_for_top, products_for_top):
    top_products_memoized.cache_clear()
    top_2 = top_products_memoized(orders_for_top, products_for_top, k=2)
    assert len(top_2) == 2
    assert top_2[0].id == "p3"
    assert top_2[1].id == "p1"


def test_top_products_memoization_speed(orders_for_top, products_for_top):
    top_products_memoized.cache_clear()

    # Первый вызов - медленный
    start_first = time.monotonic()
    top_products_memoized(orders_for_top, products_for_top, k=3)
    end_first = time.monotonic()
    duration_first = end_first - start_first

    # Второй вызов - быстрый (из кеша)
    start_second = time.monotonic()
    top_products_memoized(orders_for_top, products_for_top, k=3)
    end_second = time.monotonic()
    duration_second = end_second - start_second

    # Проверяем, что первый вызов был "дорогим" (дольше 2 сек)
    assert duration_first > 2.0
    # Проверяем, что второй вызов был значительно быстрее
    assert duration_second < 0.01


def test_top_products_immutable_keys(products_for_top):
    """Проверяет, что функция работает с иммутабельными ключами (кортежами)."""
    top_products_memoized.cache_clear()

    # Создаем изменяемый список заказов
    mutable_orders = [
        Order(id="o1", user_id="u1", items=[CartItem("p1", 5)], total_price=1, timestamp="")
    ]

    # Ожидаем ошибку, если передать изменяемый список
    with pytest.raises(TypeError):
        top_products_memoized(mutable_orders, products_for_top, k=1)

    # Проверяем, что с кортежем все работает
    immutable_orders = tuple(mutable_orders)
    result = top_products_memoized(immutable_orders, products_for_top, k=1)
    assert len(result) == 1
    assert result[0].id == "p1"


def test_top_products_k_parameter(orders_for_top, products_for_top):
    top_products_memoized.cache_clear()
    top_1 = top_products_memoized(orders_for_top, products_for_top, k=1)
    assert len(top_1) == 1
    assert top_1[0].id == "p3"


def test_top_products_empty_orders(products_for_top):
    top_products_memoized.cache_clear()
    result = top_products_memoized(tuple(), products_for_top, k=5)
    assert len(result) == 0