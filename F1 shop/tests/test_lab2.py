import pytest
from core.domain import Product, Category
from core.transforms import by_category, by_price_range, by_tag
from core.recursion import flatten_categories, collect_products_recursive

@pytest.fixture
def products_for_filtering() -> tuple[Product, ...]:
    return (
        Product(id="p1", name="A", price=100, category_id="c1", tags=['new'], stock=1),
        Product(id="p2", name="B", price=200, category_id="c2", tags=['sale'], stock=1),
        Product(id="p3", name="C", price=300, category_id="c1", tags=['new', 'eco'], stock=1),
        Product(id="p4", name="D", price=400, category_id="c3", tags=['eco'], stock=1),
    )

def test_filter_by_category(products_for_filtering):
    filter_c1 = by_category("c1")
    result = list(filter(filter_c1, products_for_filtering))
    assert len(result) == 2
    assert all(p.category_id == "c1" for p in result)

def test_filter_by_price_range(products_for_filtering):
    filter_price = by_price_range(150, 350)
    result = list(filter(filter_price, products_for_filtering))
    assert len(result) == 2
    assert {p.id for p in result} == {"p2", "p3"}

def test_filter_by_tag(products_for_filtering):
    filter_eco = by_tag("eco")
    result = list(filter(filter_eco, products_for_filtering))
    assert len(result) == 2
    assert {p.id for p in result} == {"p3", "p4"}

@pytest.fixture
def category_tree() -> tuple[Category, ...]:
    return (
        Category(id="c1", name="Электроника", parent=None),
        Category(id="c2", name="Смартфоны", parent="c1"),
        Category(id="c3", name="Ноутбуки", parent="c1"),
        Category(id="c4", name="Аксессуары", parent="c2"),
        Category(id="c5", name="Одежда", parent=None),
    )

def test_flatten_categories_recursive(category_tree):
    # Уплощаем все подкатегории "Электроники"
    flat_list = flatten_categories(category_tree, "c1")
    # Должны быть c1, c2, c3, c4
    assert len(flat_list) == 4
    assert {c.id for c in flat_list} == {"c1", "c2", "c3", "c4"}

def test_collect_products_recursive(category_tree):
    products = (
        Product(id="p1", name="Смартфон X", price=1, category_id="c2", tags=[], stock=1),
        Product(id="p2", name="Чехол для X", price=1, category_id="c4", tags=[], stock=1),
        Product(id="p3", name="Ноутбук Y", price=1, category_id="c3", tags=[], stock=1),
        Product(id="p4", name="Футболка Z", price=1, category_id="c5", tags=[], stock=1),
    )
    # Собираем все товары из категории "Электроника" и ее подкатегорий
    collected = collect_products_recursive(category_tree, products, "c1")
    assert len(collected) == 3
    assert {p.id for p in collected} == {"p1", "p2", "p3"}