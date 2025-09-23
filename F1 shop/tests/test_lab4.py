import pytest
from core.ftypes import Maybe, safe_product_find, validate_order
from core.domain import Product, Order, CartItem, Discount
from core.compose import pipe


# Тесты для Maybe
def test_maybe_some():
    maybe = Maybe.Some(10)
    assert maybe.is_some()
    assert not maybe.is_nothing()
    assert maybe.get_or_else(0) == 10


def test_maybe_nothing():
    maybe = Maybe.Nothing()
    assert not maybe.is_some()
    assert maybe.is_nothing()
    assert maybe.get_or_else(0) == 0


def test_maybe_map():
    some = Maybe.Some(5).map(lambda x: x * 2)
    assert some.get_or_else(0) == 10

    nothing = Maybe.Nothing().map(lambda x: x * 2)
    assert nothing.is_nothing()


def test_maybe_bind():
    def half(x):
        return Maybe.Some(x // 2) if x % 2 == 0 else Maybe.Nothing()

    some_even = Maybe.Some(10).bind(half)
    assert some_even.get_or_else(0) == 5

    some_odd = Maybe.Some(5).bind(half)
    assert some_odd.is_nothing()

    nothing = Maybe.Nothing().bind(half)
    assert nothing.is_nothing()


# Тесты для функций с Maybe
def test_safe_product_find():
    products = (Product(id="p1", name="A", price=1, category_id="c1", tags=[], stock=1),)

    found = safe_product_find(products, "p1")
    assert found.is_some()
    assert found.get_or_else(None).id == "p1"

    not_found = safe_product_find(products, "p2")
    assert not_found.is_nothing()


# Тесты для пайплайна
def test_validation_pipeline_success():
    order = Order("o1", "u1", [CartItem("p1", 2)], 200, "")
    stock = {"p1": 5, "p2": 10}
    discounts = tuple()

    def check_stock(o: Order) -> Maybe[Order]:
        for item in o.items:
            if stock.get(item.product_id, 0) < item.quantity:
                return Maybe.Nothing()
        return Maybe.Some(o)

    def process_payment(o: Order) -> Maybe[str]:
        return Maybe.Some(f"Payment successful for order {o.id}")

    pipeline = pipe(check_stock, lambda m: m.bind(process_payment))

    result = pipeline(order)
    assert result.is_some()
    assert result.get_or_else("") == "Payment successful for order o1"


def test_validation_pipeline_failure():
    order = Order("o1", "u1", [CartItem("p1", 10)], 1000, "")  # Хотим 10, на складе 5
    stock = {"p1": 5}

    def check_stock(o: Order) -> Maybe[Order]:
        for item in o.items:
            if stock.get(item.product_id, 0) < item.quantity:
                return Maybe.Nothing()
        return Maybe.Some(o)

    pipeline = pipe(check_stock)

    result = pipeline(order)
    assert result.is_nothing()