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

from src.data.enrichment_store import (
    load_enrichment,
    save_enrichment,
)


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "player_profiles"
)

RAW_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REFERENCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "reference"
)


# ---------------------------------------------------------
# API CONFIGURATION
# ---------------------------------------------------------

load_dotenv(
    PROJECT_ROOT / ".env"
)

API_KEY = os.getenv(
    "API_FOOTBALL_KEY"
)

BASE_URL = (
    "https://v3.football.api-sports.io"
)

LEAGUE_ID = 39

# API-Football free plan currently allows
# only pages 1–3 for this endpoint.
FREE_PLAN_MAX_PAGE = 3


# ---------------------------------------------------------
# ZODIAC
# ---------------------------------------------------------

def zodiac_from_date(
    birth_date,
):

    if (
        birth_date is None
        or pd.isna(birth_date)
    ):
        return None

    date = pd.to_datetime(
        birth_date,
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
# HTTP SESSION
# ---------------------------------------------------------

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
# CACHE
# ---------------------------------------------------------

def season_cache_dir(
    season,
):

    directory = (
        RAW_DIR
        / str(season)
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def page_cache_path(
    season,
    page,
):

    return (
        season_cache_dir(season)
        / f"page_{page}.json"
    )


def load_cached_page(
    season,
    page,
):

    path = page_cache_path(
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


def save_cached_page(
    season,
    page,
    payload,
):

    path = page_cache_path(
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


# ---------------------------------------------------------
# API REQUEST
# ---------------------------------------------------------

def fetch_page(
    season,
    page,
):

    if not API_KEY:
        raise RuntimeError(
            "API_FOOTBALL_KEY not found."
        )

    url = (
        f"{BASE_URL}/players"
    )

    headers = {
        "x-apisports-key":
            API_KEY,
    }

    params = {
        "league":
            LEAGUE_ID,

        "season":
            int(season),

        "page":
            int(page),
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
# PARSE API PROFILE PAGE
# ---------------------------------------------------------

def parse_page(
    payload,
):

    rows = []

    response = payload.get(
        "response",
        [],
    )

    for entry in response:

        player = (
            entry.get("player")
            or {}
        )

        birth = (
            player.get("birth")
            or {}
        )

        player_id = player.get(
            "id"
        )

        if player_id is None:
            continue

        rows.append(
            {
                "player_id":
                    int(player_id),

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
                    birth.get(
                        "date"
                    ),

                "birth_place":
                    birth.get(
                        "place"
                    ),

                "birth_country":
                    birth.get(
                        "country"
                    ),

                "nationality":
                    player.get(
                        "nationality"
                    ),
            }
        )

    return rows


# ---------------------------------------------------------
# UPDATE PERSISTENT ENRICHMENT
# ---------------------------------------------------------

def apply_profiles_to_enrichment(
    enrichment,
    profiles,
):

    added = 0
    already_present = 0
    missing_birth_date = 0
    player_not_in_reference = 0

    enrichment_ids = set(
        enrichment[
            "player_id"
        ].astype(int)
    )

    for _, profile in profiles.iterrows():

        player_id = int(
            profile["player_id"]
        )

        if (
            player_id
            not in enrichment_ids
        ):

            player_not_in_reference += 1
            continue

        birth_date = profile[
            "birth_date"
        ]

        if pd.isna(
            birth_date
        ):
            missing_birth_date += 1
            continue

        matching_rows = enrichment[
            enrichment["player_id"]
            == player_id
        ].index

        if len(matching_rows) != 1:
            continue

        index = matching_rows[0]

        # Never overwrite a DOB from another source.
        if pd.notna(
            enrichment.at[
                index,
                "birth_date"
            ]
        ):
            already_present += 1
            continue

        enrichment.at[
            index,
            "birth_date"
        ] = birth_date

        enrichment.at[
            index,
            "zodiac"
        ] = zodiac_from_date(
            birth_date
        )

        enrichment.at[
            index,
            "dob_source"
        ] = "API-Football-Profile"

        # Exact API player ID.
        enrichment.at[
            index,
            "dob_verified"
        ] = True

        added += 1

    return {
        "added":
            added,

        "already_present":
            already_present,

        "missing_birth_date":
            missing_birth_date,

        "player_not_in_reference":
            player_not_in_reference,
    }


# ---------------------------------------------------------
# COLLECT PROFILES
# ---------------------------------------------------------

def collect_profiles(
    season,
    max_pages,
    cache_only,
):

    max_pages = min(
        max_pages,
        FREE_PLAN_MAX_PAGE,
    )

    all_rows = []

    new_requests = 0
    cached_pages = 0

    for page in range(
        1,
        max_pages + 1,
    ):

        print(
            f"Page {page}/{max_pages}"
        )

        payload = load_cached_page(
            season,
            page,
        )

        if payload is not None:

            cached_pages += 1

            print(
                "    -> using cache"
            )

        else:

            if cache_only:

                print(
                    "    -> no cache, skipped"
                )

                continue

            print(
                "    -> requesting API"
            )

            payload = fetch_page(
                season,
                page,
            )

            save_cached_page(
                season,
                page,
                payload,
            )

            new_requests += 1

            time.sleep(6.5)

        rows = parse_page(
            payload
        )

        all_rows.extend(
            rows
        )

    return (
        pd.DataFrame(all_rows),
        new_requests,
        cached_pages,
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--season",
        type=int,
        default=2024,
        help=(
            "API-Football season, "
            "e.g. 2024 for 2024/25."
        ),
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help=(
            "Maximum number of API profile "
            "pages to process."
        ),
    )

    parser.add_argument(
        "--cache-only",
        action="store_true",
        help=(
            "Use already cached pages only. "
            "Makes zero new API requests."
        ),
    )

    args = parser.parse_args()

    print(
        f"Season: {args.season}"
    )

    profiles, new_requests, cached_pages = (
        collect_profiles(
            season=args.season,
            max_pages=args.max_pages,
            cache_only=args.cache_only,
        )
    )

    if profiles.empty:

        print(
            "\nNo player profiles found."
        )

        return

    profiles = (
        profiles
        .drop_duplicates(
            subset=["player_id"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    enrichment = load_enrichment()

    before = (
        enrichment[
            "birth_date"
        ]
        .notna()
        .sum()
    )

    result = (
        apply_profiles_to_enrichment(
            enrichment,
            profiles,
        )
    )

    save_enrichment(
        enrichment
    )

    after = (
        enrichment[
            "birth_date"
        ]
        .notna()
        .sum()
    )

    total = len(
        enrichment
    )

    print("\n==============================")
    print("PLAYER PROFILE SUMMARY")
    print("==============================")

    print(
        f"Profiles processed: "
        f"{len(profiles)}"
    )

    print(
        f"Cached pages used: "
        f"{cached_pages}"
    )

    print(
        f"New API requests: "
        f"{new_requests}"
    )

    print()

    print(
        f"New DOBs added: "
        f"{result['added']}"
    )

    print(
        f"Already had DOB: "
        f"{result['already_present']}"
    )

    print(
        f"API profiles without DOB: "
        f"{result['missing_birth_date']}"
    )

    print(
        f"Players outside reference: "
        f"{result['player_not_in_reference']}"
    )

    print()

    print(
        f"DOB coverage before: "
        f"{before}/{total}"
    )

    print(
        f"DOB coverage after: "
        f"{after}/{total}"
    )

    print(
        f"Still missing: "
        f"{total - after}"
    )

    print("==============================\n")


if __name__ == "__main__":
    main()