import sqlite3
from collections import defaultdict
from typing import Optional, List, Tuple

from services.pricing_service import resolve_pack_id
from repos.price_repo import latest_prices_for_pack_with_packinfo


def basket_totals(
    conn: sqlite3.Connection,
    items: List[Tuple[str, Optional[str], float, str, Optional[str]]],
):
    totals_cents = defaultdict(int)
    coverage = defaultdict(set)   # store -> set(item_index)
    item_count = len(items)

    for idx, (name, brand, size, unit, note) in enumerate(items):
        pack_id = resolve_pack_id(conn, name, brand, size, unit, note)
        if pack_id is None:
            return None, f"Izdelek ali pakiranje ne obstaja: {name}"

        rows = latest_prices_for_pack_with_packinfo(conn, pack_id)

        if not rows:
            continue

        for r in rows:
            store = r["store"]
            totals_cents[store] += r["price_cents"]
            coverage[store].add(idx)

    if not totals_cents:
        return [], None

    results = []

    for store, cents in totals_cents.items():
        covered_indexes = coverage[store]
        missing_indexes = [
            i for i in range(item_count) if i not in covered_indexes
        ]

        missing_items = []
        for i in missing_indexes:
            name, brand, size, unit, note = items[i]
            label = f"{name} {size}{unit}"
            if brand:
                label += f" ({brand})"
            if note:
                label += f" [{note}]"
            missing_items.append(label)

        results.append({
            "store": store,
            "total_cents": cents,
            "covered": len(covered_indexes),
            "missing": missing_items,
        })

    results.sort(key=lambda r: (len(r["missing"]), r["total_cents"]))

    return results, None
