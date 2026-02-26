import sqlite3
from dataclasses import dataclass
from typing import Optional
import unicodedata

from repos.price_repo import latest_prices_by_store_with_packinfo
from services.shopping_list_service import ListItem


def _norm(s: str) -> str:
    s = (s or "").lower()
    # odstrani šumnike
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


@dataclass(frozen=True)
class Chosen:
    item_label: str
    product_name: str
    brand: str
    pack_size: float
    unit: str
    price_cents: int
    observed_on: str


@dataclass(frozen=True)
class StoreResult:
    store: str
    total_cents: int
    covered: int
    missing: list[str]
    chosen: list[Chosen]


def compare_list_total_price(conn: sqlite3.Connection, items: list[ListItem]) -> list[StoreResult]:
    rows = latest_prices_by_store_with_packinfo(conn)

    # group rows by store
    by_store: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        by_store.setdefault(r["store"], []).append(r)

    results: list[StoreResult] = []

    for store, store_rows in by_store.items():
        total = 0
        covered = 0
        missing: list[str] = []
        chosen: list[Chosen] = []

        for it in items:
            # candidates: same size+unit AND keywords match in name/brand
            candidates = []
            for r in store_rows:
                if float(r["pack_size"]) != float(it.size):
                    continue
                if r["base_unit"] != it.unit:
                    continue

                hay = _norm(r["product_name"]) + " " + _norm(r["brand"]) + " " + _norm(r["note"])
                if all(k in hay for k in it.keywords):
                    candidates.append(r)

            if not candidates:
                missing.append(it.label)
                continue

            # total price mode: pick cheapest price_cents
            best = min(candidates, key=lambda x: x["price_cents"])
            total += int(best["price_cents"])
            covered += 1
            chosen.append(
                Chosen(
                    item_label=it.label,
                    product_name=best["product_name"],
                    brand=best["brand"] or "",
                    pack_size=float(best["pack_size"]),
                    unit=best["base_unit"],
                    price_cents=int(best["price_cents"]),
                    observed_on=best["observed_on"],
                )
            )

        results.append(
            StoreResult(
                store=store,
                total_cents=total,
                covered=covered,
                missing=missing,
                chosen=chosen,
            )
        )

    # sort by total price, but put stores with 0 covered at end
    results.sort(key=lambda r: (r.covered == 0, r.total_cents))
    return results