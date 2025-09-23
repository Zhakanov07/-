import pytest
from datetime import datetime
from core.domain import Cart, CartItem, Product, Order
from core.transforms import add_to_cart, remove_from_cart, checkout, total_sales

# Фикстуры для тестов
@pytest.fixture
def sample_cart() -> Cart:
    return Cart(user_id="user_1", items=[
        CartItem(product_id="prod_1", quantity=2),
        CartItem(product_id="prod_2", quantity=1)
    ])

@pytest.fixture
def sample_products() -> tuple[Product, ...]:
    return (
        Product(id="prod_1", name="Laptop", price=1000, category_id="cat_1", tags=[], stock=10),
        Product(id="prod_2", name="Mouse", price=25, category_id="cat_1", tags=[], stock=10),
        Product(id="prod_3", name="Keyboard", price=75, category_id="cat_1", tags=[], stock=10),
    )

@pytest.fixture
def sample_orders() -> tuple[Order, ...]:
    return (
        Order(id="order_1", user_id="user_1", items=[], total_price=1500, timestamp="..."),
        Order(id="order_2", user_id="user_2", items=[], total_price=500, timestamp="..."),
        Order(id="order_3", user_id="user_1", items=[], total_price=2000, timestamp="..."),
    )

# Тесты для Лабы №1
def test_add_to_cart_new_item(sample_cart):
    new_cart = add_to_cart(sample_cart, "prod_3", 1)
    assert len(new_cart.items) == 3
    assert new_cart is not sample_cart  # Проверка иммутабельности
    assert any(item.product_id == "prod_3" and item.quantity == 1 for item in new_cart.items)

def test_add_to_cart_existing_item(sample_cart):
    new_cart = add_to_cart(sample_cart, "prod_1", 1)
    assert len(new_cart.items) == 2
    item = next(item for item in new_cart.items if item.product_id == "prod_1")
    assert item.quantity == 3

def test_remove_from_cart(sample_cart):
    new_cart = remove_from_cart(sample_cart, "prod_1")
    assert len(new_cart.items) == 1
    assert new_cart is not sample_cart # Проверка иммутабельности
    assert all(item.product_id != "prod_1" for item in new_cart.items)

def test_checkout(sample_cart, sample_products):
    ts = datetime.now().isoformat()
    order = checkout(sample_cart, sample_products, ts)
    assert order.user_id == "user_1"
    assert len(order.items) == 2
    # 2 * 1000 (Laptop) + 1 * 25 (Mouse) = 2025
    assert order.total_price == 2025
    assert order.timestamp == ts

def test_total_sales(sample_orders):
    total = total_sales(sample_orders)
    assert total == 1500 + 500 + 2000

def test_total_sales_empty():
    assert total_sales(tuple()) == 0