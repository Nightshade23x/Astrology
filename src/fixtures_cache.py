import json
import time
import requests
from pathlib import Path

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": "YOUR_API_KEY_HERE"
}

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

FIXTURES_FILE = DATA_DIR / "fixtures.json"

SEASONS = [2024]   # add future seasons here


def fetch_and_store_fixtures(league_id=39):
    """
    Fetch fixtures for multiple seasons and cache them.
    """
    if FIXTURES_FILE.exists():
        print("Fixtures already cached")
        return

    all_fixtures = []

    for season in SEASONS:
        print(f"Fetching fixtures for season {season}…")

        url = f"{BASE_URL}/fixtures"
        params = {
            "league": league_id,
            "season": season
        }

        for attempt in range(5):
            try:
                r = requests.get(
                    url,
                    headers=HEADERS,
                    params=params,
                    timeout=30,
                    verify=False  # Windows SSL stability
                )
                r.raise_for_status()

                data = r.json()["response"]
                all_fixtures.extend(data)

                print(f"  → Retrieved {len(data)} fixtures")
                break

            except requests.exceptions.RequestException:
                print(f"Request failed (attempt {attempt + 1}/5). Retrying...")
                time.sleep(2)

        else:
            raise RuntimeError(f"Failed to fetch fixtures for season {season}")

        # polite pause between seasons
        time.sleep(1)

    with open(FIXTURES_FILE, "w", encoding="utf-8") as f:
        json.dump(all_fixtures, f)

    print(f"Saved {len(all_fixtures)} fixtures total")


def load_fixtures():
    with open(FIXTURES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
