import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ListItem:
    label: str
    keywords: list[str]
    size: float
    unit: str


def load_shopping_list(path: str) -> list[ListItem]:
    with open(path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    items_raw = data.get("items", [])
    items: list[ListItem] = []
    for it in items_raw:
        items.append(
            ListItem(
                label=it["label"],
                keywords=[k.lower().strip() for k in it.get("keywords", [])],
                size=float(it["size"]),
                unit=it["unit"],
            )
        )
    return items