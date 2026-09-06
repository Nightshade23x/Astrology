import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PROFILE_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "player_profiles"
)

REFERENCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "reference"
)

RAW_PROFILE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REFERENCE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ---------------------------------------------------------
# API CONFIG
# ---------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("API_FOOTBALL_KEY")

BASE_URL = "https://v3.football.api-sports.io"
PREMIER_LEAGUE_ID = 39


def create_session():

    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(
        max_retries=retries
    )

    session.mount(
        "https://",
        adapter,
    )

    return session


SESSION = create_session()


# ---------------------------------------------------------
# API CALL
# ---------------------------------------------------------

def fetch_page(season, page):

    if not API_KEY:
        raise RuntimeError(
            "API_FOOTBALL_KEY not found."
        )

    url = f"{BASE_URL}/players"

    headers = {
        "x-apisports-key": API_KEY,
    }

    params = {
        "league": PREMIER_LEAGUE_ID,
        "season": season,
        "page": page,
    }

    response = SESSION.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("errors"):
        raise RuntimeError(
            f"API returned errors: "
            f"{payload['errors']}"
        )

    return payload


# ---------------------------------------------------------
# RAW CACHE
# ---------------------------------------------------------

def page_path(season, page):

    season_dir = (
        RAW_PROFILE_DIR
        / str(season)
    )

    season_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return (
        season_dir
        / f"page_{page}.json"
    )


def save_page(payload, season, page):

    path = page_path(
        season,
        page,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_page(season, page):

    path = page_path(
        season,
        page,
    )

    if not path.exists():
        return None

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ---------------------------------------------------------
# COLLECT
# ---------------------------------------------------------

def collect_profiles(season):

    print(
        f"\nFetching Premier League "
        f"player profiles for {season}..."
    )

    # First page tells us how many pages exist.
    first = load_page(
        season,
        1,
    )

    if first is None:

        print("Fetching page 1...")

        first = fetch_page(
            season,
            1,
        )

        save_page(
            first,
            season,
            1,
        )

        time.sleep(6.5)

    paging = first.get(
        "paging",
        {}
    )

    total_pages = paging.get(
        "total",
        1,
    )
    # API-Football free plan only allows pages 1-3
    FREE_PLAN_MAX_PAGE = 3

    available_pages = total_pages

    total_pages = min(
        total_pages,
        FREE_PLAN_MAX_PAGE,
    )

    print(
        f"Pages available from API: {available_pages}"
    )

    print(
        f"Pages accessible on current plan: {total_pages}"
    )
    print(
        f"Total pages: {total_pages}"
    )

    for page in range(
        2,
        total_pages + 1,
    ):

        if load_page(
            season,
            page,
        ) is not None:

            print(
                f"Page {page} already cached."
            )

            continue

        print(
            f"Fetching page "
            f"{page}/{total_pages}..."
        )

        payload = fetch_page(
            season,
            page,
        )

        save_page(
            payload,
            season,
            page,
        )

        time.sleep(6.5)

    print(
        "\nProfile collection complete."
    )


# ---------------------------------------------------------
# BUILD PROFILE TABLE
# ---------------------------------------------------------

def build_profile_table(season):

    season_dir = (
        RAW_PROFILE_DIR
        / str(season)
    )

    files = sorted(
        season_dir.glob(
            "page_*.json"
        )
    )

    rows = []

    for file in files:

        with open(
            file,
            "r",
            encoding="utf-8",
        ) as f:

            payload = json.load(f)

        for entry in payload.get(
            "response",
            []
        ):

            player = (
                entry.get("player")
                or {}
            )

            birth = (
                player.get("birth")
                or {}
            )

            rows.append(
                {
                    "player_id":
                        player.get("id"),

                    "player_name_api":
                        player.get("name"),

                    "firstname":
                        player.get(
                            "firstname"
                        ),

                    "lastname":
                        player.get(
                            "lastname"
                        ),

                    "birth_date":
                        birth.get("date"),

                    "birth_place":
                        birth.get("place"),

                    "birth_country":
                        birth.get("country"),

                    "nationality":
                        player.get(
                            "nationality"
                        ),
                }
            )

    df = pd.DataFrame(rows)

    if not df.empty:

        df = (
            df
            .drop_duplicates(
                subset=["player_id"]
            )
            .sort_values(
                "player_id"
            )
            .reset_index(drop=True)
        )

    return df


# ---------------------------------------------------------
# ZODIAC
# ---------------------------------------------------------

def zodiac_from_date(date_value):

    if pd.isna(date_value):
        return None

    date = pd.to_datetime(
        date_value,
        errors="coerce",
    )

    if pd.isna(date):
        return None

    month = date.month
    day = date.day

    if (
        (month == 3 and day >= 21)
        or
        (month == 4 and day <= 19)
    ):
        return "Aries"

    if (
        (month == 4 and day >= 20)
        or
        (month == 5 and day <= 20)
    ):
        return "Taurus"

    if (
        (month == 5 and day >= 21)
        or
        (month == 6 and day <= 20)
    ):
        return "Gemini"

    if (
        (month == 6 and day >= 21)
        or
        (month == 7 and day <= 22)
    ):
        return "Cancer"

    if (
        (month == 7 and day >= 23)
        or
        (month == 8 and day <= 22)
    ):
        return "Leo"

    if (
        (month == 8 and day >= 23)
        or
        (month == 9 and day <= 22)
    ):
        return "Virgo"

    if (
        (month == 9 and day >= 23)
        or
        (month == 10 and day <= 22)
    ):
        return "Libra"

    if (
        (month == 10 and day >= 23)
        or
        (month == 11 and day <= 21)
    ):
        return "Scorpio"

    if (
        (month == 11 and day >= 22)
        or
        (month == 12 and day <= 21)
    ):
        return "Sagittarius"

    if (
        (month == 12 and day >= 22)
        or
        (month == 1 and day <= 19)
    ):
        return "Capricorn"

    if (
        (month == 1 and day >= 20)
        or
        (month == 2 and day <= 18)
    ):
        return "Aquarius"

    return "Pisces"


# ---------------------------------------------------------
# UPDATE MASTER REFERENCE
# ---------------------------------------------------------

def update_reference(profiles):

    players_path = (
        REFERENCE_DIR
        / "players.csv"
    )

    players = pd.read_csv(players_path)

    profile_subset = profiles[
        [
            "player_id",
            "birth_date",
        ]
    ].copy()

    profile_subset = profile_subset.rename(
        columns={
            "birth_date": "new_birth_date"
        }
    )

    players = players.merge(
        profile_subset,
        on="player_id",
        how="left",
    )

    # Keep an existing DOB if we already have one.
    # Otherwise use the newly retrieved API DOB.
    if "birth_date" not in players.columns:
        players["birth_date"] = None

    players["birth_date"] = (
        players["birth_date"]
        .combine_first(
            players["new_birth_date"]
        )
    )

    players = players.drop(
        columns=["new_birth_date"]
    )

    # Recalculate zodiac from the preserved DOB
    players["zodiac"] = (
        players["birth_date"]
        .apply(zodiac_from_date)
    )

    # Preserve an existing source where possible
    if "dob_source" not in players.columns:
        players["dob_source"] = pd.Series(
            pd.NA,
            index=players.index,
            dtype="string",
        )
    else:
        players["dob_source"] = (
            players["dob_source"]
            .astype("string")
        )

    new_api_dob = (
        players["birth_date"].notna()
        & players["dob_source"].isna()
    )

    players.loc[
        new_api_dob,
        "dob_source"
    ] = "API-Football"

    if "dob_verified" not in players.columns:
        players["dob_verified"] = False
    else:
        players["dob_verified"] = (
            players["dob_verified"]
            .apply(
                lambda x: (
                    str(x).strip().lower() == "true"
                    if pd.notna(x)
                    else False
                )
            )
        )
    players.to_csv(
        players_path,
        index=False,
        encoding="utf-8",
    )

    return players


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate(players):

    total = len(players)

    with_dob = (
        players["birth_date"]
        .notna()
        .sum()
    )

    with_zodiac = (
        players["zodiac"]
        .notna()
        .sum()
    )

    print("\n==============================")
    print("DOB / ZODIAC VALIDATION")
    print("==============================")

    print(
        f"Players in reference: {total}"
    )

    print(
        f"Players with DOB: "
        f"{with_dob}/{total}"
    )

    print(
        f"Players with zodiac: "
        f"{with_zodiac}/{total}"
    )

    print(
        f"Missing DOBs: "
        f"{total - with_dob}"
    )

    print("\nZodiac distribution:")

    print(
        players["zodiac"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print("==============================\n")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--season",
        required=True,
        type=int,
    )

    args = parser.parse_args()

    collect_profiles(
        args.season
    )

    profiles = build_profile_table(
        args.season
    )

    players = update_reference(
        profiles
    )

    validate(players)


if __name__ == "__main__":
    main()