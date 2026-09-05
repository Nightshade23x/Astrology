import json
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# API CONFIGURATION
# ---------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

PREMIER_LEAGUE_ID = 39


def create_session():
    """
    Create an HTTP session with automatic retry handling.
    """
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retries)

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


SESSION = create_session()


# ---------------------------------------------------------
# FETCH FIXTURES
# ---------------------------------------------------------

def fetch_fixtures(season, league_id=PREMIER_LEAGUE_ID):
    """
    Fetch every fixture for one Premier League season.

    API-Football uses the starting year of the season.
    For example:
        2023 = 2023/24
        2024 = 2024/25
    """

    if not API_KEY:
        raise RuntimeError(
            "API_FOOTBALL_KEY was not found. "
            "Add it to the project's .env file."
        )

    url = f"{BASE_URL}/fixtures"

    params = {
        "league": league_id,
        "season": season,
    }

    headers = {
        "x-apisports-key": API_KEY,
    }

    print(f"Fetching Premier League fixtures for season {season}...")

    response = SESSION.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("errors"):
        raise RuntimeError(f"API returned errors: {payload['errors']}")

    fixtures = payload.get("response", [])

    print(f"Fixtures returned: {len(fixtures)}")

    return payload


# ---------------------------------------------------------
# SAVE RAW RESPONSE
# ---------------------------------------------------------

def save_raw_fixtures(payload, season):
    """
    Save the complete API response unchanged.

    This gives us a permanent raw copy of the source data.
    """

    output_path = RAW_DATA_DIR / f"fixtures_{season}.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    print(f"Raw fixture data saved to:")
    print(output_path)


# ---------------------------------------------------------
# CREATE CLEAN FIXTURE INDEX
# ---------------------------------------------------------

def build_fixture_index(payload):
    """
    Convert the API response into one clean row per fixture.

    Crucially, kickoff_datetime and kickoff_timestamp are kept
    so matches can later be processed in true chronological order.
    """

    rows = []

    for item in payload.get("response", []):

        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        venue = fixture.get("venue") or {}
        status = fixture.get("status") or {}

        rows.append(
            {
                "fixture_id": fixture.get("id"),

                # Essential for same-day chronological prediction
                "kickoff_datetime": fixture.get("date"),
                "kickoff_timestamp": fixture.get("timestamp"),
                "timezone": fixture.get("timezone"),

                "season": league.get("season"),
                "round": league.get("round"),

                "status": status.get("short"),

                "home_team_id": (teams.get("home") or {}).get("id"),
                "home_team": (teams.get("home") or {}).get("name"),

                "away_team_id": (teams.get("away") or {}).get("id"),
                "away_team": (teams.get("away") or {}).get("name"),

                "home_goals": goals.get("home"),
                "away_goals": goals.get("away"),

                "venue_id": venue.get("id"),
                "venue_name": venue.get("name"),
                "venue_city": venue.get("city"),
            }
        )

    df = pd.DataFrame(rows)

    if not df.empty:
        df["kickoff_datetime"] = pd.to_datetime(
            df["kickoff_datetime"],
            utc=True,
            errors="coerce",
        )

        df = df.sort_values(
            ["kickoff_datetime", "fixture_id"]
        ).reset_index(drop=True)

    return df


def save_fixture_index(df, season):
    output_path = PROCESSED_DATA_DIR / f"fixtures_{season}.csv"

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
    )

    print(f"Clean fixture index saved to:")
    print(output_path)


# ---------------------------------------------------------
# BASIC VALIDATION
# ---------------------------------------------------------

def validate_fixture_index(df):
    print("\n==============================")
    print("FIXTURE VALIDATION")
    print("==============================")

    print(f"Rows: {len(df)}")
    print(f"Unique fixture IDs: {df['fixture_id'].nunique()}")

    duplicate_ids = df["fixture_id"].duplicated().sum()
    missing_kickoffs = df["kickoff_datetime"].isna().sum()

    print(f"Duplicate fixture IDs: {duplicate_ids}")
    print(f"Missing kickoff times: {missing_kickoffs}")

    if not df.empty:
        print(f"Earliest fixture: {df['kickoff_datetime'].min()}")
        print(f"Latest fixture:   {df['kickoff_datetime'].max()}")

        print("\nFixture status counts:")
        print(df["status"].value_counts(dropna=False).to_string())

    print("==============================\n")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    seasons = [2022, 2023, 2024]

    for season in seasons:

        print("\n")
        print("=" * 60)
        print(f"PROCESSING PREMIER LEAGUE SEASON {season}/{str(season + 1)[-2:]}")
        print("=" * 60)

        payload = fetch_fixtures(season)

        save_raw_fixtures(
            payload=payload,
            season=season,
        )

        fixture_df = build_fixture_index(payload)

        validate_fixture_index(fixture_df)

        save_fixture_index(
            df=fixture_df,
            season=season,
        )


if __name__ == "__main__":
    main()

