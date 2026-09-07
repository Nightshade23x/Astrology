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

from src.data.fetch_player_profiles import zodiac_from_date


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PLAYERS_PATH = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "players.csv"
)

LOOKUP_LOG_PATH = (
    PROJECT_ROOT
    / "data"
    / "reference"
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

    return session


SESSION = create_session()


# ---------------------------------------------------------
# CACHE
# ---------------------------------------------------------

def cache_path(season, player_id):

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


def load_cache(season, player_id):

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

def fetch_player(player_id, season):

    if not API_KEY:
        raise RuntimeError(
            "API_FOOTBALL_KEY not found."
        )

    url = f"{BASE_URL}/players"

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
# PARSE PROFILE
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

        if not birth_date:
            return {
                "player_name_api":
                    player.get("name"),

                "birth_date":
                    None,
            }, "no_birth_date"

        return {
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
        }, "matched"

    return None, "player_id_not_found"


# ---------------------------------------------------------
# SAVE LOG
# ---------------------------------------------------------

def save_log(results):

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
# RESOLVE MISSING PLAYERS
# ---------------------------------------------------------

def resolve_missing(
    season,
    max_requests,
):

    players = pd.read_csv(
        PLAYERS_PATH
    )

    # Fix column types
    players["dob_source"] = (
        players["dob_source"]
        .astype("string")
    )

    missing = players[
        players["birth_date"].isna()
    ].copy()

    # Most important players first
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
    results = []

    for number, (
        index,
        row,
    ) in enumerate(
        missing.iterrows(),
        start=1,
    ):

        if requests_made >= max_requests:
            break

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

        payload = load_cache(
            season,
            player_id,
        )

        if payload is None:

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

                # Respect 10 requests/minute
                time.sleep(6.5)

            except Exception as exc:

                print(
                    f"    -> error: {exc}"
                )

                results.append(
                    {
                        "player_id":
                            player_id,

                        "player_name":
                            player_name,

                        "status":
                            "error",

                        "birth_date":
                            None,
                    }
                )

                continue

        else:

            cached_count += 1

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
            profile.get("player_name_api")
            if profile
            else None
        )

        print(
            f"    -> {status}"
        )

        if status == "matched":

            players.at[
                index,
                "birth_date"
            ] = birth_date

            players.at[
                index,
                "zodiac"
            ] = zodiac_from_date(
                birth_date
            )

            players.at[
                index,
                "dob_source"
            ] = "API-Football-ID"

            # Exact API player ID match
            players.at[
                index,
                "dob_verified"
            ] = True

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

    players.to_csv(
        PLAYERS_PATH,
        index=False,
        encoding="utf-8",
    )

    save_log(
        results
    )

    # ---------------------------------------------
    # SUMMARY
    # ---------------------------------------------

    total = len(players)

    with_dob = (
        players["birth_date"]
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
            .value_counts()
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
    )

    parser.add_argument(
        "--max-requests",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    resolve_missing(
        season=args.season,
        max_requests=args.max_requests,
    )


if __name__ == "__main__":
    main()