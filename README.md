# price-tracker

A modular CLI price tracking system built in Python.

Tracks product prices across stores, normalizes them to **unit price**, supports trend analysis, basket comparison, and CSV exports.

[![tests](https://github.com/gpoljsak2k/price-tracker/actions/workflows/tests.yml/badge.svg)](https://github.com/gpoljsak2k/price-tracker/actions/workflows/tests.yml)

---

## Features

- SQLite-backed data model (Stores / Products / Packs / Prices)
- **Unit price normalization** (€/kg, €/l, €/pcs)
- `latest` – latest prices per store
- `cheapest-now` – ranking by lowest unit price
- `history` – historical price tracking (optional store filter)
- `trend` – price change over time (absolute + %)
- `basket` – multi-item basket comparison across stores (with coverage + missing items)
- CSV export:
  - `export-latest`
  - `export-history`
  - `export-basket`
- Automated test suite (pytest)
- CI pipeline via GitHub Actions (Python 3.10 / 3.11)

---

## Architecture

- `repos/` – database access (no business logic)
- `services/` – calculations & domain logic
- `app.py` – CLI / controller layer
- `tests/` – pytest suite

Designed with clear separation of concerns and testability in mind.

---

## Quickstart


```bash
python app.py init-db
python app.py add-store Mercator
python app.py add-store Spar

python app.py add-product --name "Mleko 3.5%" --brand Alpsko
python app.py add-pack --name "Mleko 3.5%" --brand Alpsko --size 1 --unit l --note tetrapak

python app.py add-price --store Mercator --name "Mleko 3.5%" --brand Alpsko --size 1 --unit l --note tetrapak --price 1.19
python app.py add-price --store Spar --name "Mleko 3.5%" --brand Alpsko --size 1 --unit l --note tetrapak --price 1.09

python app.py latest --name "Mleko 3.5%" --brand Alpsko --size 1 --unit l --note tetrapak
python app.py cheapest-now --name "Mleko 3.5%" --brand Alpsko --size 1 --unit l --note tetrapak
```

## CSV Export
```bash
python app.py export-latest --out latest.csv --name "Mleko 3.5%" --brand Alpsko --size 1 --unit l --note tetrapak

python app.py export-history --out history.csv --name "Mleko 3.5%" --brand Alpsko --size 1 --unit l --note tetrapak

python app.py export-basket --out basket.csv \
  --item "Mleko 3.5%,Alpsko,1,l,tetrapak" \
  --item "Jajca,,10,pcs,"
```

## Development
```bash
pip install -r requirements.txt
pytest -q
```