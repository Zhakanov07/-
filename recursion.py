from typing import Tuple, List, Optional
from core.domain import CarEra, Bolid


def get_children(eras: Tuple[CarEra, ...], era_id: Optional[str]) -> Tuple[CarEra, ...]:
    return tuple(e for e in eras if e.parent == era_id)


def flatten_eras(eras: Tuple[CarEra, ...], root_id: Optional[str]) -> Tuple[CarEra, ...]:
    flat_list = []

    def recurse(current_id: Optional[str]):
        children = get_children(eras, current_id)
        for child in children:
            flat_list.append(child)
            recurse(child.id)

    root_era = next((e for e in eras if e.id == root_id), None)
    if root_era:
        flat_list.append(root_era)

    recurse(root_id)
    return tuple(flat_list)


def collect_bolids_recursive(eras: Tuple[CarEra, ...], bolids: Tuple[Bolid, ...], root_id: str) -> Tuple[Bolid, ...]:
    target_eras = flatten_eras(eras, root_id)
    target_era_ids = {e.id for e in target_eras}
    return tuple(b for b in bolids if b.era_id in target_era_ids)