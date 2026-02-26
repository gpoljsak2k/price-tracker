import json
import os


def add_tracked_item(config_path: str, item: dict) -> bool:
    """
    Vrne True če je dodano, False če že obstaja.
    """

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"db": "prices.db", "items": []}

    # preveri duplicate po URL
    for existing in data["items"]:
        if existing["url"] == item["url"]:
            return False

    data["items"].append(item)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True
