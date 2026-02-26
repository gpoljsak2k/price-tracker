import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from urllib.request import Request, urlopen
from scrapers.html_utils import extract_title


@dataclass(frozen=True)
class HoferOffer:
    store: str
    title: str
    price_eur: Decimal
    source_url: str
    observed_on: str


# ujame tudi NBSP in običajne presledke: "2,54 €"
_PRICE_RE = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*€")


def _to_decimal_eur(s: str) -> Decimal:
    return Decimal(s.replace(".", "").replace(",", "."))


def parse_hofer_product_html(html: str, url: str) -> HoferOffer:
    title = extract_title(html)

    m = re.search(
        r'class="base-price__regular"[^>]*>\s*<span>\s*([\d.,]+)\s*€\s*</span>',
        html,
        re.IGNORECASE,
    )

    if m:
        price = _to_decimal_eur(m.group(1))
        return HoferOffer(
            store="Hofer",
            title=title,
            price_eur=price,
            source_url=url.strip(),
            observed_on=date.today().isoformat(),
        )

    prices = _PRICE_RE.findall(html)
    if not prices:
        raise ValueError("Ne najdem cene v HTML (layout se je verjetno spremenil).")

    dec_prices = [_to_decimal_eur(p) for p in prices]

    # Zadnja cena je ponavadi main price
    price = dec_prices[-1]

    return HoferOffer(
        store="Hofer",
        title=title,
        price_eur=price,
        source_url=url.strip(),
        observed_on=date.today().isoformat(),
    )


def fetch_hofer_offer(url: str, timeout_s: int = 20) -> HoferOffer:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (price-tracker; educational project)",
            "Accept-Language": "sl,en;q=0.8",
        },
    )
    with urlopen(req, timeout=timeout_s) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return parse_hofer_product_html(html, url)
