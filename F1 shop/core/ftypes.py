from typing import TypeVar, Generic, Callable, Optional, Any

T = TypeVar('T')
U = TypeVar('U')


class Maybe(Generic[T]):
    """Контейнер Maybe для обработки возможных отсутствующих значений."""

    def __init__(self, value: Optional[T]):
        self._value = value

    @staticmethod
    def Some(value: T) -> 'Maybe[T]':
        if value is None:
            raise ValueError("Some value cannot be None.")
        return Maybe(value)

    @staticmethod
    def Nothing() -> 'Maybe[Any]':
        return Maybe(None)

    def is_some(self) -> bool:
        return self._value is not None

    def is_nothing(self) -> bool:
        return self._value is None

    def bind(self, func: Callable[[T], 'Maybe[U]']) -> 'Maybe[U]':
        """Применяет функцию к значению, если оно есть."""
        if self.is_nothing():
            return Maybe.Nothing()
        return func(self._value)

    def map(self, func: Callable[[T], U]) -> 'Maybe[U]':
        """Применяет функцию к значению и оборачивает результат в Maybe."""
        if self.is_nothing():
            return Maybe.Nothing()
        return Maybe.Some(func(self._value))

    def get_or_else(self, default: T) -> T:
        """Возвращает значение или значение по умолчанию."""
        return self._value if self.is_some() else default

    def __repr__(self) -> str:
        return f"Some({self._value})" if self.is_some() else "Nothing"


# --- Функции для Лабы №4 ---

from .domain import Order, Product, Discount, Cart


def safe_product_find(products: Tuple[Product, ...], pid: str) -> Maybe[Product]:
    """Безопасный поиск товара по ID."""
    product = next((p for p in products if p.id == pid), None)
    return Maybe.Some(product) if product else Maybe.Nothing()


def validate_order(order: Order, stock: Dict[str, int], discounts: Tuple[Discount, ...]) -> Maybe[Dict[str, Any]]:
    """
    Проверяет заказ: наличие товаров на складе и применяет скидки.
    Возвращает Maybe с информацией о заказе или Nothing, если проверка не пройдена.
    """
    validated_items = []
    total_price = 0.0

    product_discounts = {d.product_id: d.discount_percent for d in discounts}

    for item in order.items:
        # Проверка наличия на складе
        if stock.get(item.product_id, 0) < item.quantity:
            return Maybe.Nothing()  # Товара нет на складе в нужном количестве

        # Намеренно не используем safe_product_find, т.к. в этой логике
        # предполагается, что товар существует, если он есть в заказе.
        # Цена будет взята из `order.total_price` после всех расчетов.

        # Просто собираем информацию
        validated_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "discount": product_discounts.get(item.product_id, 0.0)
        })

    # Эта функция просто валидирует, а не пересчитывает цену.
    # Для простоты вернем словарь с проверенными данными.
    return Maybe.Some({
        "order_id": order.id,
        "user_id": order.user_id,
        "items": validated_items,
        "is_valid": True
    })
