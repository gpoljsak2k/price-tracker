from decimal import Decimal
from scrapers.mercator import parse_mercator_product_html

def test_parse_mercator_html_extracts_main_price():
    html = """
# Ekstra deviško oljčno olje Classico, Monini, 750 ml

Cena na enoto: 15,99€ / 1l

11,99€

kos
"""
    offer = parse_mercator_product_html(html, "https://example.com")
    assert offer.store == "Mercator"
    assert offer.price_eur == Decimal("11.99")

