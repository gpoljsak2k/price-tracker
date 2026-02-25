import argparse
import sqlite3
from datetime import date
from typing import Optional

from db import connect, init_db

# repos (CRUD only)
from repos.store_repo import add_store, list_stores, find_store_id
from repos.product_repo import (
    add_product,
    list_products_with_pack_status,
    find_product_id,
    delete_product,
)
from repos.pack_repo import add_pack, list_packs
from repos.price_repo import add_price

# services (business logic)
from services.pricing_service import (
    resolve_pack_id_or_reason,
    latest_with_unit_price,
    cheapest_now,
    history_with_unit_price,
    trend,
)
from services.analytics_service import basket_totals
from services.export_service import write_csv

from utils import euros_to_cents, cents_to_euros

# scrapers
from services.ingest_service import ingest_price_observation
from services.tracked_items_service import load_tracked_items
from services.scrape_service import scrape_one
from scrapers.mercator import fetch_mercator_offer, infer_map_from_mercator_url

# --------------------------------------------------
# CLI
# --------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(prog="price-tracker")
    parser.add_argument("--db", default="prices.db", help="Pot do SQLite baze (privzeto prices.db)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-db", help="Ustvari DB schema")

    # store
    s_add = sub.add_parser("add-store", help="Dodaj trgovino")
    s_add.add_argument("name")
    sub.add_parser("list-stores", help="Izpiši trgovine")

    # product
    p_add = sub.add_parser("add-product", help="Dodaj izdelek")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--brand")

    lp = sub.add_parser("list-products", help="Izpiši izdelke")
    lp.add_argument("--packed", choices=["all", "yes", "no"], default="all")

    p_del = sub.add_parser("delete-product", help="Pobriši izdelek (CASCADE)")
    p_del.add_argument("--name", required=True)
    p_del.add_argument("--brand")

    # pack
    pk = sub.add_parser("add-pack", help="Dodaj pakiranje")
    pk.add_argument("--name", required=True)
    pk.add_argument("--brand")
    pk.add_argument("--size", required=True, type=float)
    pk.add_argument("--unit", required=True, choices=["g", "kg", "ml", "l", "pcs"])
    pk.add_argument("--note")

    sub.add_parser("list-packs", help="Izpiši vsa pakiranja")

    # price
    pr = sub.add_parser("add-price", help="Dodaj ceno (EUR)")
    pr.add_argument("--store", required=True)
    pr.add_argument("--name", required=True)
    pr.add_argument("--brand")
    pr.add_argument("--size", required=True, type=float)
    pr.add_argument("--unit", required=True, choices=["g", "kg", "ml", "l", "pcs"])
    pr.add_argument("--note")
    pr.add_argument("--price", required=True, help='Cena v EUR, npr. "1.19"')
    pr.add_argument("--date", help="Datum YYYY-MM-DD (privzeto danes)")

    la = sub.add_parser("latest", help="Zadnje cene po trgovinah (+ unit price)")
    la.add_argument("--name", required=True)
    la.add_argument("--brand")
    la.add_argument("--size", required=True, type=float)
    la.add_argument("--unit", required=True, choices=["g", "kg", "ml", "l", "pcs"])
    la.add_argument("--note")

    h = sub.add_parser("history", help="Zgodovina cen (+ unit price)")
    h.add_argument("--name", required=True)
    h.add_argument("--brand")
    h.add_argument("--size", required=True, type=float)
    h.add_argument("--unit", required=True, choices=["g", "kg", "ml", "l", "pcs"])
    h.add_argument("--note")
    h.add_argument("--store", help="Filtriraj po trgovini (ime)")

    ch = sub.add_parser("cheapest-now", help="Uredi trgovine po najnižjem unit price")
    ch.add_argument("--name", required=True)
    ch.add_argument("--brand")
    ch.add_argument("--size", required=True, type=float)
    ch.add_argument("--unit", required=True, choices=["g", "kg", "ml", "l", "pcs"])
    ch.add_argument("--note")

    tr = sub.add_parser("trend", help="Trend cene za pakiranje v trgovini")
    tr.add_argument("--store", required=True)
    tr.add_argument("--name", required=True)
    tr.add_argument("--brand")
    tr.add_argument("--size", required=True, type=float)
    tr.add_argument("--unit", required=True, choices=["g", "kg", "ml", "l", "pcs"])
    tr.add_argument("--note")

    bs = sub.add_parser("basket", help="Košarica: seštej zadnje cene po trgovinah")
    bs.add_argument(
        "--item",
        action="append",
        required=True,
        help="Format: name,brand,size,unit,note (brand/note lahko prazna).",
    )

    # CSV exports
    exb = sub.add_parser("export-basket", help="Export basket rezultata v CSV")
    exb.add_argument("--out", required=True, help="Pot do CSV datoteke")
    exb.add_argument("--item", action="append", required=True, help="Format: name,brand,size,unit,note")

    exl = sub.add_parser("export-latest", help="Export 'latest' v CSV")
    exl.add_argument("--out", required=True, help="Pot do CSV datoteke")
    exl.add_argument("--name", required=True)
    exl.add_argument("--brand")
    exl.add_argument("--size", required=True, type=float)
    exl.add_argument("--unit", required=True, choices=["g", "kg", "ml", "l", "pcs"])
    exl.add_argument("--note")

    exh = sub.add_parser("export-history", help="Export 'history' v CSV")
    exh.add_argument("--out", required=True, help="Pot do CSV datoteke")
    exh.add_argument("--name", required=True)
    exh.add_argument("--brand")
    exh.add_argument("--size", required=True, type=float)
    exh.add_argument("--unit", required=True, choices=["g", "kg", "ml", "l", "pcs"])
    exh.add_argument("--note")
    exh.add_argument("--store", help="Filtriraj po trgovini (ime)")

    sm = sub.add_parser("scrape-mercator", help="Scrape Mercator product URL in shrani ceno v DB")
    sm.add_argument("--url", required=True)
    sm.add_argument("--map-from-url", action="store_true")
    sm.add_argument("--name")
    sm.add_argument("--brand")
    sm.add_argument("--size", type=float)
    sm.add_argument("--unit", choices=["g", "kg", "ml", "l", "pcs"])
    sm.add_argument("--note")

    sa = sub.add_parser("scrape-all", help="Scrape vse tracked_items iz JSON configa")
    sa.add_argument("--config", default="tracked_items.json", help="Pot do tracked_items.json")

    return parser.parse_args()


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def resolve_or_print(conn, name, brand, size, unit, note) -> Optional[int]:
    pack_id, reason = resolve_pack_id_or_reason(conn, name, brand, size, unit, note)
    if pack_id is None:
        if reason == "product_missing":
            print("NAPAKA: izdelek ne obstaja. Najprej add-product.")
        elif reason == "pack_missing":
            print("NAPAKA: pakiranje ne obstaja. Najprej add-pack.")
        else:
            print("NAPAKA: izdelek ali pakiranje ne obstaja.")
        return None
    return pack_id


def parse_items(raw_items: list[str]):
    parsed = []
    for item in raw_items:
        parts = [p.strip() for p in item.split(",")]
        if len(parts) < 4:
            raise ValueError("napačen format --item. Rabiš vsaj: name,brand,size,unit,note")

        name = parts[0]
        brand = parts[1] if len(parts) > 1 and parts[1] else None
        size = float(parts[2])
        unit = parts[3]
        note = parts[4] if len(parts) > 4 and parts[4] else None
        parsed.append((name, brand, size, unit, note))
    return parsed


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    args = parse_args()
    conn = connect(args.db)

    try:
        # --- init ---
        if args.cmd == "init-db":
            init_db(conn)
            print("OK: baza ustvarjena.")
            return

        # --------------------------------------------------
        # STORE
        # --------------------------------------------------

        if args.cmd == "add-store":
            try:
                store_id = add_store(conn, args.name)
                print(f"OK: dodano #{store_id} - {args.name.strip()}")
            except sqlite3.IntegrityError:
                print("NAPAKA: trgovina že obstaja.")
            except ValueError as e:
                print(f"NAPAKA: {e}")
            return

        if args.cmd == "list-stores":
            rows = list_stores(conn)
            if not rows:
                print("(ni trgovin)")
                return
            for r in rows:
                print(f"{r['id']:>3}  {r['name']}")
            return

        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------

        if args.cmd == "add-product":
            try:
                product_id = add_product(conn, args.name, args.brand)
                print(f"OK: dodano #{product_id}")
            except sqlite3.IntegrityError:
                print("NAPAKA: izdelek že obstaja.")
            except ValueError as e:
                print(f"NAPAKA: {e}")
            return

        if args.cmd == "list-products":
            rows = list_products_with_pack_status(conn)
            if not rows:
                print("(ni izdelkov)")
                return

            for r in rows:
                packed = bool(r["packed"])
                if args.packed == "yes" and not packed:
                    continue
                if args.packed == "no" and packed:
                    continue
                brand = r["brand"] if r["brand"] else "-"
                flag = "PACKED" if packed else "UNPACKED"
                print(f"{r['id']:>3}  {r['name']} | {brand} | {flag}")
            return

        if args.cmd == "delete-product":
            product_id = find_product_id(conn, args.name, args.brand)
            if product_id is None:
                print("NAPAKA: izdelek ne obstaja.")
                return
            delete_product(conn, product_id)
            print("OK: izdelek pobrisan.")
            return

        # --------------------------------------------------
        # PACK
        # --------------------------------------------------

        if args.cmd == "add-pack":
            product_id = find_product_id(conn, args.name, args.brand)
            if product_id is None:
                print("NAPAKA: izdelek ne obstaja. Najprej add-product.")
                return

            try:
                pack_id = add_pack(conn, product_id, args.size, args.unit, args.note)
                print(f"OK: dodano pakiranje #{pack_id}")
            except sqlite3.IntegrityError:
                print("NAPAKA: pakiranje že obstaja.")
            except ValueError as e:
                print(f"NAPAKA: {e}")
            return

        if args.cmd == "list-packs":
            rows = list_packs(conn)
            if not rows:
                print("(ni pakiranj)")
                return
            for r in rows:
                brand = r["brand"] if r["brand"] else "-"
                note = f" | {r['note']}" if r["note"] else ""
                print(
                    f"{r['pack_id']:>3}  {r['product_name']} | {brand} | "
                    f"{r['pack_size']} {r['base_unit']}{note}"
                )
            return

        # --------------------------------------------------
        # PRICE
        # --------------------------------------------------

        if args.cmd == "add-price":
            store_id = find_store_id(conn, args.store)
            if store_id is None:
                print("NAPAKA: trgovina ne obstaja. Najprej add-store.")
                return

            pack_id = resolve_or_print(conn, args.name, args.brand, args.size, args.unit, args.note)
            if pack_id is None:
                return

            observed_on = args.date.strip() if args.date else date.today().isoformat()
            price_cents = euros_to_cents(args.price)

            try:
                obs_id = add_price(conn, store_id, pack_id, price_cents, observed_on)
                print(f"OK: dodana cena #{obs_id}")
            except sqlite3.IntegrityError:
                print("NAPAKA: cena za ta datum/trgovino/pakiranje že obstaja.")
            except ValueError as e:
                print(f"NAPAKA: {e}")
            return

        # --------------------------------------------------
        # LATEST
        # --------------------------------------------------

        if args.cmd == "latest":
            pack_id = resolve_or_print(conn, args.name, args.brand, args.size, args.unit, args.note)
            if pack_id is None:
                return

            rows = latest_with_unit_price(conn, pack_id)
            if not rows:
                print("(ni cen za to pakiranje)")
                return

            for r in rows:
                eur = cents_to_euros(r["price_cents"])
                print(
                    f"{r['store']:<15} {eur} € ({r['observed_on']}) | "
                    f"{r['unit_price']} {r['unit_label']}"
                )
            return

        # --------------------------------------------------
        # CHEAPEST
        # --------------------------------------------------

        if args.cmd == "cheapest-now":
            pack_id = resolve_or_print(conn, args.name, args.brand, args.size, args.unit, args.note)
            if pack_id is None:
                return

            rows = cheapest_now(conn, pack_id)
            if not rows:
                print("(ni cen za to pakiranje)")
                return

            for r in rows:
                eur = cents_to_euros(r["price_cents"])
                print(
                    f"{r['store']:<15} {eur} € ({r['observed_on']}) | "
                    f"{r['unit_price']} {r['unit_label']}"
                )
            return

        # --------------------------------------------------
        # HISTORY
        # --------------------------------------------------

        if args.cmd == "history":
            pack_id = resolve_or_print(conn, args.name, args.brand, args.size, args.unit, args.note)
            if pack_id is None:
                return

            store_id = None
            if args.store:
                store_id = find_store_id(conn, args.store)
                if store_id is None:
                    print("NAPAKA: trgovina ne obstaja.")
                    return

            rows = history_with_unit_price(conn, pack_id, args.size, args.unit, store_id)
            if not rows:
                print("(ni cen za to pakiranje)")
                return

            for r in rows:
                eur = cents_to_euros(r["price_cents"])
                print(
                    f"{r['observed_on']} | {r['store']:<15} | {eur} € | "
                    f"{r['unit_price']} {r['unit_label']}"
                )
            return

        # --------------------------------------------------
        # TREND
        # --------------------------------------------------

        if args.cmd == "trend":
            pack_id = resolve_or_print(conn, args.name, args.brand, args.size, args.unit, args.note)
            if pack_id is None:
                return

            result = trend(conn, pack_id, args.store)
            if result is None:
                print("NAPAKA: trgovina ne obstaja.")
                return
            if result == "not_enough":
                print("Ni dovolj podatkov za trend (rabiš vsaj 2 datuma).")
                return

            first = cents_to_euros(result["first"])
            last = cents_to_euros(result["last"])
            sign = "+" if result["diff"] > 0 else ""

            print(result["store"])
            print(f"Od: {first} €")
            print(f"Do: {last} €")
            print(f"Sprememba: {sign}{result['diff']} € ({sign}{result['percent']}%)")
            return

        # --------------------------------------------------
        # BASKET
        # --------------------------------------------------

        if args.cmd == "basket":
            try:
                parsed_items = parse_items(args.item)
            except ValueError as e:
                print(f"NAPAKA: {e}")
                return

            results, error = basket_totals(conn, parsed_items)
            if error:
                print(f"NAPAKA: {error}")
                return
            if not results:
                print("Ni podatkov za košarico.")
                return

            for r in results:
                total_eur = cents_to_euros(r["total_cents"])
                coverage = f"{r['covered']}/{len(parsed_items)}"
                print(f"{r['store']:<15} {total_eur} €   [{coverage}]")

                if r["missing"]:
                    print("   Manjkajo:")
                    for item in r["missing"]:
                        print(f"     - {item}")
            return

        # --------------------------------------------------
        # EXPORT: BASKET
        # --------------------------------------------------

        if args.cmd == "export-basket":
            try:
                parsed_items = parse_items(args.item)
            except ValueError as e:
                print(f"NAPAKA: {e}")
                return

            results, error = basket_totals(conn, parsed_items)
            if error:
                print(f"NAPAKA: {error}")
                return
            if not results:
                print("Ni podatkov za košarico.")
                return

            csv_rows = []
            for r in results:
                csv_rows.append({
                    "store": r["store"],
                    "total_eur": str(cents_to_euros(r["total_cents"])),
                    "total_cents": r["total_cents"],
                    "covered": r["covered"],
                    "missing_count": len(r["missing"]),
                    "missing_items": "; ".join(r["missing"]),
                })

            write_csv(
                args.out,
                csv_rows,
                fieldnames=["store", "total_eur", "total_cents", "covered", "missing_count", "missing_items"],
            )
            print(f"OK: zapisano v {args.out}")
            return

        # --------------------------------------------------
        # EXPORT: LATEST
        # --------------------------------------------------
        if args.cmd == "export-latest":
            pack_id = resolve_or_print(conn, args.name, args.brand, args.size, args.unit, args.note)
            if pack_id is None:
                return

            rows = latest_with_unit_price(conn, pack_id)
            if not rows:
                print("(ni cen za to pakiranje)")
                return

            csv_rows = []
            for r in rows:
                csv_rows.append({
                    "store": r["store"],
                    "observed_on": r["observed_on"],
                    "price_eur": str(cents_to_euros(r["price_cents"])),
                    "price_cents": r["price_cents"],
                    "unit_price": str(r["unit_price"]),
                    "unit_label": r["unit_label"],
                })

            write_csv(
                args.out,
                csv_rows,
                fieldnames=["store", "observed_on", "price_eur", "price_cents", "unit_price", "unit_label"],
            )
            print(f"OK: zapisano v {args.out}")
            return

        # --------------------------------------------------
        # EXPORT: HISTORY
        # --------------------------------------------------
        if args.cmd == "export-history":
            pack_id = resolve_or_print(conn, args.name, args.brand, args.size, args.unit, args.note)
            if pack_id is None:
                return

            store_id = None
            if args.store:
                store_id = find_store_id(conn, args.store)
                if store_id is None:
                    print(f"NAPAKA: trgovina '{args.store.strip()}' ne obstaja.")
                    return

            rows = history_with_unit_price(conn, pack_id, args.size, args.unit, store_id)
            if not rows:
                print("(ni cen za to pakiranje)")
                return

            csv_rows = []
            for r in rows:
                csv_rows.append({
                    "observed_on": r["observed_on"],
                    "store": r["store"],
                    "price_eur": str(cents_to_euros(r["price_cents"])),
                    "price_cents": r["price_cents"],
                    "unit_price": str(r["unit_price"]),
                    "unit_label": r["unit_label"],
                })

            write_csv(
                args.out,
                csv_rows,
                fieldnames=["observed_on", "store", "price_eur", "price_cents", "unit_price", "unit_label"],
            )
            print(f"OK: zapisano v {args.out}")
            return

        # --------------------------------------------------
        # SCRAPE-MERCATOR
        # --------------------------------------------------
        if args.cmd == "scrape-mercator":
            # 1) optional infer mapping from URL
            if getattr(args, "map_from_url", False):
                inferred = infer_map_from_mercator_url(args.url)
                if inferred is None:
                    print("NAPAKA: Ne morem razbrati mapiranja iz URL-ja. Podaj --name/--brand/--size/--unit ročno.")
                    return

                inf_name, inf_brand, inf_size, inf_unit, inf_note = inferred

                # user-provided args override inferred values
                if not args.name:
                    print(
                        f"INFO: inferred title from URL: '{inf_name}' (uporabi --name za mapiranje na tvoj DB product)")
                args.brand = args.brand or inf_brand
                args.size = args.size if args.size is not None else inf_size
                args.unit = args.unit or inf_unit
                args.note = args.note or inf_note

                print(
                    "INFO: inferred map -> "
                    f"name='{args.name or '-'}', brand='{args.brand}', size={args.size}{args.unit}, note='{args.note}'"
                )

            # 2) validate mapping (either provided or inferred)
            if not args.name or args.size is None or not args.unit:
                print("NAPAKA: Manjka --name (DB product name) ali --size/--unit (ali uporabi --map-from-url).")
                return

            # 3) scrape + ingest
            try:
                offer = fetch_mercator_offer(args.url)

                obs_id = ingest_price_observation(
                    conn,
                    store_name=offer.store,
                    name=args.name,
                    brand=args.brand,
                    size=args.size,
                    unit=args.unit,
                    note=args.note,
                    price_eur=offer.price_eur,
                    observed_on=offer.observed_on,
                    source=f"scrape:mercator:{offer.source_url}",
                )

                # Duplikati
                if obs_id == 0:
                    print(f"OK: already scraped for {offer.observed_on} ({offer.price_eur} €) — no new row")
                    return

                print(f"OK: scraped {offer.price_eur} € ({offer.title})")
                print(f"OK: saved observation #{obs_id} ({offer.observed_on})")
                return

            except ValueError as e:
                if str(e) == "product_missing":
                    print("NAPAKA: izdelek ne obstaja. Najprej add-product.")
                elif str(e) == "pack_missing":
                    print("NAPAKA: pakiranje ne obstaja. Najprej add-pack.")
                else:
                    print(f"NAPAKA: {e}")
            except sqlite3.IntegrityError:
                print("OK: cena za ta izdelek/trgovino je za danes že shranjena (ni spremembe).")
            except Exception as e:
                print(f"NAPAKA: scrape failed: {e}")
            return

        # --------------------------------------------------
        # SCRAPE-ALL
        # --------------------------------------------------
        if args.cmd == "scrape-all":
            db_path, items = load_tracked_items(args.config)

            if db_path != args.db:
                conn.close()
                conn = connect(db_path)

            if not items:
                print("Ni tracked items.")
                return

            new_count = 0
            skipped_count = 0
            fail_count = 0

            for it in items:
                res = scrape_one(conn, it)

                if res.status == "new":
                    new_count += 1
                    print("NEW: " + res.message)
                elif res.status == "skipped":
                    skipped_count += 1
                    print("SKIP: " + res.message)
                else:
                    fail_count += 1
                    print("FAIL: " + res.message)

            print(f"Done. NEW={new_count}, SKIP={skipped_count}, FAIL={fail_count}, TOTAL={len(items)}")

            if fail_count > 0:
                raise SystemExit(1)

            return

    finally:
        conn.close()

if __name__ == "__main__":
    main()
