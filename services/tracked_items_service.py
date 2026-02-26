import json
from dataclasses import dataclass
from typing import Optional, Any

@dataclass(frozen=True)
class TrackedMap:
    name: str
    brand: Optional[str]
    size: float
    unit: str
    note: Optional[str]

@dataclass(frozen=True)
class TrackedItem:
    store: str
    scraper: str
    url: str
    map: TrackedMap


def load_tracked_items(path: str) -> tuple[str, list[TrackedItem]]:
    with open(path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    db_path = data.get("db", "prices.db")
    items_raw = data.get("items", [])
    items: list[TrackedItem] = []

    for it in items_raw:
        m = it["map"]
        items.append(
            TrackedItem(
                store=it["store"],
                scraper=it["scraper"],
                url=it["url"].strip(),
                map=TrackedMap(
                    name=m["name"],
                    brand=m.get("brand"),
                    size=float(m["size"]),
                    unit=m["unit"],
                    note=m.get("note"),
                ),
            )
        )

    return db_path, items

