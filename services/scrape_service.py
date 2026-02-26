import sqlite3
from dataclasses import dataclass
from typing import Optional, Literal

from scrapers.mercator import fetch_mercator_offer
from scrapers.hofer import fetch_hofer_offer

from services.ingest_service import ingest_price_observation
from services.tracked_items_service import TrackedItem


Status = Literal["new", "skipped", "fail"]


@dataclass(frozen=True)
class ScrapeResult:
    ok: bool
    status: Status
    message: str
    observation_id: Optional[int] = None


def scrape_one(conn: sqlite3.Connection, item: TrackedItem) -> ScrapeResult:
    try:
        if item.scraper == "mercator_url":
            offer = fetch_mercator_offer(item.url)
        elif item.scraper == "hofer_url":
            offer = fetch_hofer_offer(item.url)
        else:
            return ScrapeResult(False, "fail", f"{item.store}: unknown scraper '{item.scraper}'")

        obs_id = ingest_price_observation(
            conn,
            store_name=offer.store,
            name=item.map.name,
            brand=item.map.brand,
            size=item.map.size,
            unit=item.map.unit,
            note=item.map.note,
            price_eur=offer.price_eur,
            observed_on=offer.observed_on,
            source=f"scrape:{item.store.lower()}:{item.url}",
        )

        if obs_id == 0:
            return ScrapeResult(
                True,
                "skipped",
                f"{item.store}: already scraped for {offer.observed_on} ({offer.price_eur} €) | "
                f"DB='{item.map.name}'",
                None,
            )

        return ScrapeResult(
            True,
            "new",
            f"{item.store}: {offer.price_eur} € | "
            f"DB='{item.map.name}' ({item.map.brand}) {item.map.size}{item.map.unit} | "
            f"Title='{offer.title}'",
            obs_id,
        )

    except Exception as e:
        return ScrapeResult(False, "fail", f"{item.store}: ERROR: {e}")
