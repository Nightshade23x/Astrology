import json
import time
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# --------------------
# ENV SETUP
# --------------------
load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
if not API_KEY:
    raise RuntimeError("API_FOOTBALL_KEY not loaded")

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

# --------------------
# DATA SETUP
# --------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def fixtures_file_for_season(season):
    return DATA_DIR / f"fixtures_{season}.json"


# --------------------
# SEASON DISCOVERY
# --------------------
def get_league_seasons(league_id=39):
    """
    Ask API-Football which seasons actually exist for this league.
    Returns a list like: [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    """
    url = f"{BASE_URL}/leagues"
    params = {"id": league_id}

    try:
        r = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=30,
            verify=False
        )
        r.raise_for_status()
    except Exception as e:
        print("Failed to fetch league metadata:", e)
        return []

    response = r.json().get("response", [])
    if not response:
        return []

    seasons = response[0].get("seasons", [])
    return sorted([s["year"] for s in seasons if "year" in s])


# --------------------
# FIXTURE FETCHING
# --------------------
def fetch_and_store_fixtures(league_id=39, seasons=None):
    """
    Fetch fixtures for valid seasons and store them separately.
    If seasons=None, automatically discovers seasons via API.
    """
    if seasons is None:
        seasons = get_league_seasons(league_id)
        print(f"Discovered seasons from API: {seasons}")

    for season in seasons:
        fixtures_file = fixtures_file_for_season(season)

        if fixtures_file.exists():
            print(f"Fixtures for season {season} already cached")
            continue

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
                    verify=False
                )
                r.raise_for_status()

                fixtures = r.json().get("response", [])

                with open(fixtures_file, "w", encoding="utf-8") as f:
                    json.dump(fixtures, f)

                print(f"Saved {len(fixtures)} fixtures for season {season}")
                break

            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/5): {e}")
                time.sleep(2)

        time.sleep(1)


# --------------------
# LOAD FIXTURES
# --------------------
def load_fixtures(season):
    fixtures_file = fixtures_file_for_season(season)

    if not fixtures_file.exists():
        raise FileNotFoundError(
            f"No cached fixtures found for season {season}. "
            "Run fetch_and_store_fixtures() first."
        )

    with open(fixtures_file, "r", encoding="utf-8") as f:
        return json.load(f)
