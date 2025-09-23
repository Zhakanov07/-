import json
from functools import reduce, lru_cache
from typing import Tuple, Callable
import time
import uuid

from core.domain import CarEra, Bolid, Collector, PurchaseOrder, Garage, GarageItem


def load_seed_data(path: str) -> Tuple[
    Tuple[CarEra, ...], Tuple[Bolid, ...], Tuple[Collector, ...], Tuple[PurchaseOrder, ...]]:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    eras = tuple(CarEra(**e) for e in data.get('eras', []))
    bolids = tuple(Bolid(**b) for b in data.get('bolids', []))
    collectors = tuple(Collector(**c) for c in data.get('collectors', []))
    orders = tuple(PurchaseOrder(**o) for o in data.get('purchase_orders', []))

    return eras, bolids, collectors, orders


def add_to_garage(garage: Garage, bolid_id: str, quantity: int) -> Garage:
    new_items = list(garage.items)
    item_found = False
    for i, item in enumerate(new_items):
        if item.bolid_id == bolid_id:
            new_items[i] = GarageItem(bolid_id, item.quantity + quantity)
            item_found = True
            break
    if not item_found:
        new_items.append(GarageItem(bolid_id, quantity))
    return Garage(collector_id=garage.collector_id, items=new_items)


def finalize_purchase(garage: Garage, bolids: Tuple[Bolid, ...], timestamp: str) -> PurchaseOrder:
    bolid_map = {b.id: b for b in bolids}
    total_price = sum(bolid_map[item.bolid_id].price * item.quantity for item in garage.items)
    return PurchaseOrder(
        id=str(uuid.uuid4()),
        collector_id=garage.collector_id,
        items=list(garage.items),
        total_price=total_price,
        timestamp=timestamp
    )


def total_sales(orders: Tuple[PurchaseOrder, ...]) -> int:
    if not orders:
        return 0
    return reduce(lambda acc, order: acc + order.total_price, orders, 0)


def by_era(era_id: str) -> Callable[[Bolid], bool]:
    return lambda bolid: bolid.era_id == era_id


def by_price_range(min_price: int, max_price: int) -> Callable[[Bolid], bool]:
    return lambda bolid: min_price <= bolid.price <= max_price


def by_tag(tag: str) -> Callable[[Bolid], bool]:
    return lambda bolid: tag in bolid.tags


def by_team(team: str) -> Callable[[Bolid], bool]:
    return lambda bolid: bolid.team == team


@lru_cache(maxsize=128)
def top_selling_bolids(orders: Tuple[PurchaseOrder, ...], bolids: Tuple[Bolid, ...], k: int = 10) -> Tuple[Bolid, ...]:
    time.sleep(2)
    sales_count = {}
    for order in orders:
        for item in order.items:
            sales_count[item.bolid_id] = sales_count.get(item.bolid_id, 0) + item.quantity

    sorted_bolid_ids = sorted(sales_count.keys(), key=lambda bid: sales_count.get(bid, 0), reverse=True)[:k]

    bolid_map = {b.id: b for b in bolids}
    return tuple(bolid_map[bid] for bid in sorted_bolid_ids if bid in bolid_map)