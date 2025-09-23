from typing import NamedTuple, Optional, List

# --- Новые модели данных для темы Формулы 1 ---

class CarEra(NamedTuple):
    """Эра в Формуле 1 (используется как категория)."""
    id: str
    name: str
    parent: Optional[str]

class Bolid(NamedTuple):
    """Модель гоночного болида (используется как товар)."""
    id: str
    name: str          # Название, например "Mercedes W11 EQ Performance"
    team: str          # Команда
    year: int          # Год
    price: int         # Условная коллекционная цена
    era_id: str        # ID эры (категории)
    tags: List[str]    # Теги, например "Чемпионский", "V10"
    quantity_available: int

class Collector(NamedTuple):
    """Коллекционер (используется как пользователь)."""
    id: str
    name: str
    tier: str  # Уровень, например "Paddock Club", "Grandstand"

# --- Общие модели для "Гаража" и Заказов ---

class GarageItem(NamedTuple):
    """Один болид в гараже."""
    bolid_id: str
    quantity: int

class Garage(NamedTuple):
    """Гараж коллекционера (аналог корзины)."""
    collector_id: str
    items: List[GarageItem]

class PurchaseOrder(NamedTuple):
    """Оформленная покупка (аналог заказа)."""
    id: str
    collector_id: str
    items: List[GarageItem]
    total_price: int
    timestamp: str

class Discount(NamedTuple):
    """Скидка на определенный болид."""
    bolid_id: str
    discount_percent: float