from decimal import Decimal
from scrapers.hofer import parse_hofer_product_html


def test_parse_hofer_html_extracts_price_and_title():
    html = """
<title>Slovensko čajno maslo</title>

0,25 kg (10,16 €/1 kg)

2,54 €vključen DDV
"""
    offer = parse_hofer_product_html(html, "https://example.com")
    assert offer.store == "Hofer"
    assert offer.title == "Slovensko čajno maslo"
    assert offer.price_eur == Decimal("2.54")
