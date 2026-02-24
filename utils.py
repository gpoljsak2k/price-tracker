from decimal import Decimal, ROUND_HALF_UP
from datetime import date

TWOPLACES = Decimal("0.01")

def resolve_date(date_str: str | None) -> str:
    return date_str.strip() if date_str else date.today().isoformat()

def euros_to_cents(eur: str) -> int:
    d = Decimal(eur).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    if d < 0:
        raise ValueError("Cena ne sme biti negativna.")
    return int(d * 100)

def cents_to_euros(cents: int) -> str:
    d = (Decimal(cents) / Decimal(100)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return f"{d:.2f}"

def unit_price_eur(price_cents: int, pack_size: float, base_unit: str):
    """
    Vrne (unit_price: Decimal, label: str)
    label: €/kg, €/l, €/pcs, €/100g, €/100ml ...
    """
    if pack_size <= 0:
        raise ValueError("pack_size mora biti > 0")

    price = (Decimal(price_cents) / Decimal(100))

    # normalizacija na "glavne" enote
    if base_unit == "g":
        size_base = Decimal(pack_size) / Decimal(1000)
        unit_label = "€/kg"
    elif base_unit == "kg":
        size_base = Decimal(pack_size)
        unit_label = "€/kg"
    elif base_unit == "ml":
        size_base = Decimal(pack_size) / Decimal(1000)
        unit_label = "€/l"
    elif base_unit == "l":
        size_base = Decimal(pack_size)
        unit_label = "€/l"
    elif base_unit == "pcs":
        size_base = Decimal(pack_size)
        unit_label = "€/pcs"
    else:
        raise ValueError(f"Neznana enota: {base_unit}")

    unit_price = (price / size_base).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return unit_price, unit_label
