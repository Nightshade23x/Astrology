import json
from pathlib import Path
from api_client import get_fixtures

FIXTURES_FILE = Path("data/fixtures_2024.json")

def fetch_and_store_fixtures():
    if FIXTURES_FILE.exists():
        print("Fixtures already cached")
        return

    fixtures = get_fixtures()
    FIXTURES_FILE.parent.mkdir(exist_ok=True)

    with open(FIXTURES_FILE, "w", encoding="utf-8") as f:
        json.dump(fixtures, f, indent=2)

    print(f"Saved {len(fixtures)} fixtures")


def load_fixtures():
    with open(FIXTURES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
