# price-tracker

CLI aplikacija za sledenje cen izdelkov po trgovinah z normalizacijo na **unit price**, trendi, košarico in CSV exportom.

[![tests](https://github.com/gpoljsak2k/price-tracker/actions/workflows/tests.yml/badge.svg)]
(https://github.com/gpoljsak2k/price-tracker/actions/workflows/tests.yml)


## Features
- Stores / Products / Packs / Prices (SQLite)
- `latest`: zadnje cene po trgovinah + unit price
- `cheapest-now`: ranking po najnižji unit price
- `history`: zgodovina cen (+ filter po trgovini)
- `trend`: sprememba cene v trgovini (€/%) med prvo in zadnjo meritvijo
- `basket`: seštevek “zadnjih cen” po trgovinah + coverage + seznam manjkajočih itemov
- CSV export: `export-latest`, `export-history`, `export-basket`
- Tests + GitHub Actions CI (Python 3.10 / 3.11)

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

## CSV export
python app.py export-latest --out latest.csv --name "Mleko 3.5%" --brand Alpsko --size 1 --unit l --note tetrapak
python app.py export-history --out history.csv --name "Mleko 3.5%" --brand Alpsko --size 1 --unit l --note tetrapak
python app.py export-basket --out basket.csv \
  --item "Mleko 3.5%,Alpsko,1,l,tetrapak" \
  --item "Jajca,,10,pcs,"

## Dev ->zagon testov
pip install -r requirements.txt
pytest -q

## Project structure

repos/ – SQL-only access layer
services/ – business logic (unit price, trend, basket, exports)
app.py – CLI/controller
tests/ – pytest suite