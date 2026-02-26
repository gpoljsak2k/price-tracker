import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from urllib.request import  Request, urlopen
from urllib.parse import urlparse


@dataclass(frozen=True)
class MercatorOffer:
    store: str
    title: str
    price_eur: Decimal
    source_url: str
    observed_on: str


_PRICE_RE = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*€")
_URL_SIZE_RE = re.compile(r"-(\d+(?:[.,]\d+)?)-(ml|l|g|kg|pcs)$", re.IGNORECASE)

def _to_decimal_eur(s: str) -> Decimal:
    # "11,99" -> Decimal("11.99")
    return Decimal(s.replace(".", "").replace(",", "."))

def _extract_title(html: str) -> str:
    # 1) og:title (atributi niso vedno v istem vrstnem redu)
    m = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if not m:
        m = re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
            html,
            re.IGNORECASE,
        )
    if m:
        return m.group(1).strip()

    # 2) <title> fallback
    m = re.search(r"<title>\s*(.*?)\s*</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()

    return "(unknown title)"

def parse_mercator_product_html(html: str, url: str) -> MercatorOffer:
    title = _extract_title(html)

    # Strategy: find the "Cena na enoto:" block, then pick the next EUR price occurrence (main price).
    idx = html.find("Cena na enoto")
    if idx == -1:
        raise ValueError("Na strani ne najdem 'Cena na enoto' bloka (layout se je verjetno spremenil).")

    tail = html[idx: idx + 2000]  # enough to include unit price + main price

    prices = _PRICE_RE.findall(tail)
    if not prices:
        raise ValueError("Ne najdem cen v HTML (layout se je verjetno spremenil).")

    dec_prices = [_to_decimal_eur(p) for p in prices]

    # Glavna cena je praviloma najnižja (unit price je višji)
    main_price = min(dec_prices)

    return MercatorOffer(
        store="Mercator",
        title=title,
        price_eur=main_price,
        source_url=url,
        observed_on=date.today().isoformat(),
    )

def fetch_mercator_offer(url: str, timeout_s: int = 20) -> MercatorOffer:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (price-tracker; educational project)",
            "Accept-Language": "sl,en;q=0.8",
        },
    )
    with urlopen(req, timeout=timeout_s) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return parse_mercator_product_html(html, url)

def infer_map_from_mercator_url(url: str):
    """
    Vrne predlog:
    (name, brand, size, unit, note)
    Heuristika:
      - zadnji segment URL-ja (slug) razbijemo po '-'
      - zadnja dva tokena sta pogosto <size>-<unit>
      - brand je pogosto token tik pred size/unit (npr. 'monini')
      - name je ostalo, title-cased + nekaj popravkov
    """

    path = urlparse(url).path.strip("/")
    slug = path.split("/")[-1]  # ekstra-devisko-oljcno-olje-classico-monini-750-ml


    # size/unit
    m = _URL_SIZE_RE.search(slug)
    if not m:
        return None

    size_raw = m.group(1).replace(",", ".")
    unit = m.group(2).lower()
    size = float(size_raw)

    base = slug[: m.start()]  # brez "-750-ml"
    tokens = [t for t in base.split("-") if t]

    if not tokens:
        return None

    # brand: zadnji token pred size/unit (heuristika)
    brand = tokens[-1]
    name_tokens = tokens[:-1]

    # basic prettify
    def prettify(tok: str) -> str:
        # nekaj slovenskih posebnosti (URL nima šumnikov)
        # to je minimalna v1; kasneje lahko razširimo
        repl = {
            "oljcno": "oljčno",
            "devisko": "deviško",
            "ekstra": "Ekstra",
            "cena": "cena",
        }
        return repl.get(tok, tok)

    name = " ".join(prettify(t) for t in name_tokens).strip()
    if name:
        name = name[0].upper() + name[1:]

    # brand prettify (Monini)
    brand = brand.capitalize()

    note = None
    return (name, brand, size, unit, note)