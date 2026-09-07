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
from src.data.fetch_player_profiles import zodiac_from_date


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REFERENCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "reference"
)

PLAYERS_PATH = (
    REFERENCE_DIR
    / "players.csv"
)

LOOKUP_LOG_PATH = (
    REFERENCE_DIR
    / "api_dob_lookup_log.csv"
)

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "player_profiles_by_id"
)

RAW_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ---------------------------------------------------------
# API CONFIGURATION
# ---------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("API_FOOTBALL_KEY")

BASE_URL = "https://v3.football.api-sports.io"


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

    session.mount(
        "http://",
        adapter,
    )

    return session


SESSION = create_session()


# ---------------------------------------------------------
# CACHE
# ---------------------------------------------------------

def cache_path(
    season,
    player_id,
):

    season_dir = (
        RAW_DIR
        / str(season)
    )

    season_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return (
        season_dir
        / f"player_{int(player_id)}.json"
    )


def load_cache(
    season,
    player_id,
):

    path = cache_path(
        season,
        player_id,
    )

    if not path.exists():
        return None

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def save_cache(
    payload,
    season,
    player_id,
):

    path = cache_path(
        season,
        player_id,
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

def fetch_player(
    player_id,
    season,
):

    if not API_KEY:
        raise RuntimeError(
            "API_FOOTBALL_KEY not found."
        )

    url = (
        f"{BASE_URL}/players"
    )

    headers = {
        "x-apisports-key": API_KEY,
    }

    params = {
        "id": int(player_id),
        "season": int(season),
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
# PARSE PLAYER PROFILE
# ---------------------------------------------------------

def parse_profile(
    payload,
    expected_player_id,
):

    response = payload.get(
        "response",
        [],
    )

    if not response:
        return None, "no_response"

    for entry in response:

        player = (
            entry.get("player")
            or {}
        )

        player_id = player.get(
            "id"
        )

        if player_id is None:
            continue

        if int(player_id) != int(
            expected_player_id
        ):
            continue

        birth = (
            player.get("birth")
            or {}
        )

        birth_date = birth.get(
            "date"
        )

        profile = {
            "player_name_api":
                player.get("name"),

            "birth_date":
                birth_date,

            "birth_place":
                birth.get("place"),

            "birth_country":
                birth.get("country"),

            "nationality":
                player.get("nationality"),
        }

        if not birth_date:
            return (
                profile,
                "no_birth_date",
            )

        return (
            profile,
            "matched",
        )

    return (
        None,
        "player_id_not_found",
    )


# ---------------------------------------------------------
# LOOKUP LOG
# ---------------------------------------------------------

def save_log(results):

    if not results:
        return

    new_df = pd.DataFrame(
        results
    )

    if LOOKUP_LOG_PATH.exists():

        old_df = pd.read_csv(
            LOOKUP_LOG_PATH
        )

        combined = pd.concat(
            [
                old_df,
                new_df,
            ],
            ignore_index=True,
        )

        combined = (
            combined
            .drop_duplicates(
                subset=["player_id"],
                keep="last",
            )
        )

    else:

        combined = new_df

    combined = combined.sort_values(
        "player_id"
    )

    combined.to_csv(
        LOOKUP_LOG_PATH,
        index=False,
        encoding="utf-8",
    )


# ---------------------------------------------------------
# UPDATE ENRICHMENT
# ---------------------------------------------------------

def update_enrichment(
    enrichment,
    player_id,
    birth_date,
):

    matching_rows = enrichment[
        enrichment["player_id"]
        == int(player_id)
    ].index

    if len(matching_rows) != 1:
        return False

    index = matching_rows[0]

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
    ] = "API-Football-ID"

    # Exact API-Football player ID match,
    # so we consider this identity verified.
    enrichment.at[
        index,
        "dob_verified"
    ] = True

    return True


# ---------------------------------------------------------
# RESOLVE MISSING DOBs
# ---------------------------------------------------------

def resolve_missing(
    season,
    max_requests,
):

    # players.csv is generated data.
    # We only use it for names, teams,
    # appearances, etc.
    players = pd.read_csv(
        PLAYERS_PATH
    )

    # player_enrichment.csv is the persistent
    # DOB/zodiac source of truth.
    enrichment = load_enrichment()

    # -----------------------------------------------------
    # FIND PLAYERS WITHOUT DOB
    # -----------------------------------------------------

    missing_ids = set(
        enrichment[
            enrichment["birth_date"].isna()
        ]["player_id"]
    )

    missing = players[
        players["player_id"].isin(
            missing_ids
        )
    ].copy()

    # Prioritise players with more appearances.
    missing = missing.sort_values(
        "appearances",
        ascending=False,
    )

    print(
        f"Players currently missing DOB: "
        f"{len(missing)}"
    )

    requests_made = 0
    cached_count = 0
    skipped_due_limit = 0

    results = []

    # -----------------------------------------------------
    # PROCESS PLAYERS
    # -----------------------------------------------------

    for number, (
        _,
        row,
    ) in enumerate(
        missing.iterrows(),
        start=1,
    ):

        player_id = int(
            row["player_id"]
        )

        player_name = row[
            "player_name"
        ]

        print(
            f"[{number}] "
            f"{player_name} "
            f"(ID {player_id})"
        )

        # ---------------------------------------------
        # TRY CACHE FIRST
        # ---------------------------------------------

        payload = load_cache(
            season,
            player_id,
        )

        if payload is not None:

            cached_count += 1

        else:

            # No cache and we've reached the
            # allowed number of new API requests.
            if requests_made >= max_requests:

                skipped_due_limit += 1

                print(
                    "    -> skipped "
                    "(request limit reached)"
                )

                continue

            # -----------------------------------------
            # NEW API REQUEST
            # -----------------------------------------

            try:

                payload = fetch_player(
                    player_id,
                    season,
                )

                save_cache(
                    payload,
                    season,
                    player_id,
                )

                requests_made += 1

                # API-Football free plan:
                # maximum ~10 requests/minute.
                time.sleep(6.5)

            except Exception as exc:

                print(
                    f"    -> error: "
                    f"{exc}"
                )

                results.append(
                    {
                        "player_id":
                            player_id,

                        "player_name":
                            player_name,

                        "player_name_api":
                            None,

                        "status":
                            "error",

                        "birth_date":
                            None,

                        "error":
                            str(exc),
                    }
                )

                continue

        # ---------------------------------------------
        # PARSE PROFILE
        # ---------------------------------------------

        profile, status = parse_profile(
            payload,
            player_id,
        )

        birth_date = (
            profile.get("birth_date")
            if profile
            else None
        )

        api_name = (
            profile.get(
                "player_name_api"
            )
            if profile
            else None
        )

        print(
            f"    -> {status}"
        )

        # ---------------------------------------------
        # SAVE DOB TO ENRICHMENT ONLY
        # ---------------------------------------------

        if status == "matched":

            updated = update_enrichment(
                enrichment,
                player_id,
                birth_date,
            )

            if not updated:

                print(
                    "    -> warning: "
                    "player_id not uniquely "
                    "present in enrichment"
                )

        results.append(
            {
                "player_id":
                    player_id,

                "player_name":
                    player_name,

                "player_name_api":
                    api_name,

                "status":
                    status,

                "birth_date":
                    birth_date,
            }
        )

    # -----------------------------------------------------
    # SAVE PERSISTENT ENRICHMENT
    # -----------------------------------------------------

    save_enrichment(
        enrichment
    )

    # Save lookup history separately.
    save_log(
        results
    )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    total = len(
        enrichment
    )

    with_dob = (
        enrichment[
            "birth_date"
        ]
        .notna()
        .sum()
    )

    print("\n==============================")
    print("API DOB LOOKUP SUMMARY")
    print("==============================")

    if results:

        result_df = pd.DataFrame(
            results
        )

        print(
            result_df["status"]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

        print()

    print(
        f"New API requests: "
        f"{requests_made}"
    )

    print(
        f"Cached profiles used: "
        f"{cached_count}"
    )

    print(
        f"Skipped due request limit: "
        f"{skipped_due_limit}"
    )

    print(
        f"Total DOB coverage: "
        f"{with_dob}/{total}"
    )

    print(
        f"Still missing: "
        f"{total - with_dob}"
    )

    print("==============================\n")


# ---------------------------------------------------------
# CLI
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
        "--max-requests",
        type=int,
        default=5,
        help=(
            "Maximum number of NEW API "
            "requests during this run."
        ),
    )

    args = parser.parse_args()

    resolve_missing(
        season=args.season,
        max_requests=args.max_requests,
    )


if __name__ == "__main__":
    main()