import argparse
import json
import os
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

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "player_stats"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# API
# ---------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"


def create_session():
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
# HELPERS
# ---------------------------------------------------------

def zero_if_none(value):
    return 0 if value is None else value


def to_float(value):
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value):
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------
# FETCH ONE FIXTURE
# ---------------------------------------------------------

def fetch_fixture_players(fixture_id):
    if not API_KEY:
        raise RuntimeError(
            "API_FOOTBALL_KEY was not found in .env."
        )

    url = f"{BASE_URL}/fixtures/players"

    headers = {
        "x-apisports-key": API_KEY,
    }

    params = {
        "fixture": int(fixture_id),
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
            f"API returned errors for fixture "
            f"{fixture_id}: {payload['errors']}"
        )

    return payload, response.headers


# ---------------------------------------------------------
# RAW CACHE
# ---------------------------------------------------------

def raw_fixture_path(season, fixture_id):
    season_dir = RAW_DATA_DIR / str(season)
    season_dir.mkdir(parents=True, exist_ok=True)

    return season_dir / f"fixture_{fixture_id}.json"


def save_raw_fixture(payload, season, fixture_id):
    path = raw_fixture_path(season, fixture_id)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_raw_fixture(season, fixture_id):
    path = raw_fixture_path(season, fixture_id)

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------
# FLATTEN API RESPONSE
# ---------------------------------------------------------

def flatten_fixture_players(payload, fixture_row):
    rows = []

    for team_entry in payload.get("response", []):

        team = team_entry.get("team") or {}

        for player_entry in team_entry.get("players", []):

            player = player_entry.get("player") or {}

            statistics_list = (
                player_entry.get("statistics") or []
            )

            if not statistics_list:
                continue

            stats = statistics_list[0]

            games = stats.get("games") or {}
            shots = stats.get("shots") or {}
            goals = stats.get("goals") or {}
            passes = stats.get("passes") or {}
            tackles = stats.get("tackles") or {}
            duels = stats.get("duels") or {}
            dribbles = stats.get("dribbles") or {}
            fouls = stats.get("fouls") or {}
            cards = stats.get("cards") or {}
            penalty = stats.get("penalty") or {}

            minutes = to_int(games.get("minutes"))
            substitute = games.get("substitute")

            passes_total = zero_if_none(
                to_int(passes.get("total"))
            )

            passes_accurate = zero_if_none(
                to_int(passes.get("accuracy"))
            )

            if passes_total > 0:
                passes_accuracy_pct = (
                    passes_accurate
                    / passes_total
                    * 100
                )
            else:
                passes_accuracy_pct = None

            rows.append(
                {
                    # -------------------------------------
                    # MATCH
                    # -------------------------------------

                    "fixture_id":
                        fixture_row["fixture_id"],

                    "kickoff_datetime":
                        fixture_row["kickoff_datetime"],

                    "season":
                        fixture_row["season"],

                    "round":
                        fixture_row["round"],

                    "home_team_id":
                        fixture_row["home_team_id"],

                    "home_team":
                        fixture_row["home_team"],

                    "away_team_id":
                        fixture_row["away_team_id"],

                    "away_team":
                        fixture_row["away_team"],

                    # -------------------------------------
                    # TEAM
                    # -------------------------------------

                    "team_id":
                        team.get("id"),

                    "team_name":
                        team.get("name"),

                    # -------------------------------------
                    # PLAYER
                    # -------------------------------------

                    "player_id":
                        player.get("id"),

                    "player_name":
                        player.get("name"),

                    "shirt_number":
                        games.get("number"),

                    "position":
                        games.get("position"),

                    "captain":
                        games.get("captain"),

                    "substitute":
                        substitute,

                    "starter":
                        substitute is False,

                    "minutes":
                        minutes,

                    "appeared":
                        minutes is not None
                        and minutes > 0,

                    "rating":
                        to_float(
                            games.get("rating")
                        ),

                    # -------------------------------------
                    # ATTACKING
                    # -------------------------------------

                    "goals":
                        zero_if_none(
                            goals.get("total")
                        ),

                    "assists":
                        zero_if_none(
                            goals.get("assists")
                        ),

                    "shots_total":
                        zero_if_none(
                            shots.get("total")
                        ),

                    "shots_on_target":
                        zero_if_none(
                            shots.get("on")
                        ),

                    "offsides":
                        zero_if_none(
                            stats.get("offsides")
                        ),

                    # -------------------------------------
                    # PASSING
                    # -------------------------------------

                    "passes_total":
                        passes_total,

                    "passes_accurate":
                        passes_accurate,

                    "passes_accuracy_pct":
                        passes_accuracy_pct,

                    "key_passes":
                        zero_if_none(
                            passes.get("key")
                        ),

                    # -------------------------------------
                    # DEFENDING
                    # -------------------------------------

                    "tackles":
                        zero_if_none(
                            tackles.get("total")
                        ),

                    "blocks":
                        zero_if_none(
                            tackles.get("blocks")
                        ),

                    "interceptions":
                        zero_if_none(
                            tackles.get(
                                "interceptions"
                            )
                        ),

                    # -------------------------------------
                    # DUELS / DRIBBLING
                    # -------------------------------------

                    "duels_total":
                        zero_if_none(
                            duels.get("total")
                        ),

                    "duels_won":
                        zero_if_none(
                            duels.get("won")
                        ),

                    "dribbles_attempted":
                        zero_if_none(
                            dribbles.get("attempts")
                        ),

                    "dribbles_successful":
                        zero_if_none(
                            dribbles.get("success")
                        ),

                    "dribbled_past":
                        zero_if_none(
                            dribbles.get("past")
                        ),

                    # -------------------------------------
                    # FOULS
                    # -------------------------------------

                    "fouls_drawn":
                        zero_if_none(
                            fouls.get("drawn")
                        ),

                    "fouls_committed":
                        zero_if_none(
                            fouls.get("committed")
                        ),

                    # -------------------------------------
                    # CARDS
                    # -------------------------------------

                    "yellow_cards":
                        zero_if_none(
                            cards.get("yellow")
                        ),

                    "red_cards":
                        zero_if_none(
                            cards.get("red")
                        ),

                    # -------------------------------------
                    # GOALKEEPING
                    # -------------------------------------

                    "goals_conceded":
                        zero_if_none(
                            goals.get("conceded")
                        ),

                    "saves":
                        zero_if_none(
                            goals.get("saves")
                        ),

                    # -------------------------------------
                    # PENALTIES
                    # -------------------------------------

                    "penalties_won":
                        zero_if_none(
                            penalty.get("won")
                        ),

                    # API-Football uses "commited"
                    "penalties_committed":
                        zero_if_none(
                            penalty.get("commited")
                        ),

                    "penalties_scored":
                        zero_if_none(
                            penalty.get("scored")
                        ),

                    "penalties_missed":
                        zero_if_none(
                            penalty.get("missed")
                        ),

                    "penalties_saved":
                        zero_if_none(
                            penalty.get("saved")
                        ),
                }
            )

    return rows


# ---------------------------------------------------------
# BUILD DATASET FROM CACHE
# ---------------------------------------------------------

def build_season_dataset(season, fixtures_df):
    all_rows = []

    for _, fixture_row in fixtures_df.iterrows():

        fixture_id = int(
            fixture_row["fixture_id"]
        )

        payload = load_raw_fixture(
            season,
            fixture_id,
        )

        if payload is None:
            continue

        rows = flatten_fixture_players(
            payload,
            fixture_row,
        )

        all_rows.extend(rows)

    return pd.DataFrame(all_rows)


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_dataset(df):
    print("\n==============================")
    print("PLAYER DATA VALIDATION")
    print("==============================")

    print(f"Player rows: {len(df)}")

    if df.empty:
        print("No player data available.")
        print("==============================\n")
        return

    print(
        "Fixtures represented:",
        df["fixture_id"].nunique(),
    )

    print(
        "Unique players:",
        df["player_id"].nunique(),
    )

    duplicates = df.duplicated(
        subset=["fixture_id", "player_id"]
    ).sum()

    print(
        "Duplicate fixture/player rows:",
        duplicates,
    )

    print(
        "Missing player IDs:",
        df["player_id"].isna().sum(),
    )

    print(
        "Missing kickoff times:",
        df["kickoff_datetime"].isna().sum(),
    )

    print(
        "Players who appeared:",
        df["appeared"].sum(),
    )

    starters_per_fixture = (
        df[df["starter"]]
        .groupby("fixture_id")
        .size()
    )

    if not starters_per_fixture.empty:
        print(
            "Starters per fixture "
            f"(min/max): "
            f"{starters_per_fixture.min()}/"
            f"{starters_per_fixture.max()}"
        )

    print("\nPositions among appearances:")

    print(
        df[df["appeared"]]["position"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("==============================\n")


# ---------------------------------------------------------
# COLLECT
# ---------------------------------------------------------

def collect_season(season, max_requests):
    fixtures_path = (
        PROCESSED_DATA_DIR
        / f"fixtures_{season}.csv"
    )

    if not fixtures_path.exists():
        raise FileNotFoundError(
            f"Missing fixture file: "
            f"{fixtures_path}"
        )

    fixtures_df = pd.read_csv(
        fixtures_path
    )

    fixtures_df = fixtures_df.sort_values(
        "kickoff_datetime"
    )

    requests_made = 0
    cached = 0

    print(
        f"\nCollecting player data "
        f"for season {season}..."
    )

    for _, fixture_row in fixtures_df.iterrows():

        fixture_id = int(
            fixture_row["fixture_id"]
        )

        existing = load_raw_fixture(
            season,
            fixture_id,
        )

        if existing is not None:
            cached += 1
            continue

        if requests_made >= max_requests:
            print(
                "\nRequest limit for this run reached."
            )
            break

        print(
            f"Fetching fixture {fixture_id}..."
        )

        payload, headers = fetch_fixture_players(
            fixture_id
        )

        save_raw_fixture(
            payload,
            season,
            fixture_id,
        )

        requests_made += 1

        remaining = headers.get(
            "x-ratelimit-requests-remaining"
        )

        if remaining is not None:
            print(
                f"API requests remaining today: "
                f"{remaining}"
            )

            try:
                if int(remaining) <= 2:
                    print(
                        "Stopping to avoid exhausting "
                        "the daily API quota."
                    )
                    break
            except ValueError:
                pass

    # Rebuild CSV from everything currently cached
    dataset = build_season_dataset(
        season,
        fixtures_df,
    )

    output_path = (
        PROCESSED_DATA_DIR
        / f"player_match_stats_{season}.csv"
    )

    dataset.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
    )

    print("\nCollection summary")
    print("------------------")
    print(f"Previously cached: {cached}")
    print(f"New API requests: {requests_made}")
    print(
        f"Fixtures currently collected: "
        f"{dataset['fixture_id'].nunique() if not dataset.empty else 0}"
        f"/{len(fixtures_df)}"
    )

    print(
        f"Saved dataset to:\n{output_path}"
    )

    validate_dataset(dataset)


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--season",
        type=int,
        required=True,
        help=(
            "Premier League starting year, "
            "e.g. 2024 for 2024/25"
        ),
    )

    parser.add_argument(
        "--max-requests",
        type=int,
        default=20,
        help=(
            "Maximum new API requests "
            "during this run"
        ),
    )

    args = parser.parse_args()

    collect_season(
        season=args.season,
        max_requests=args.max_requests,
    )


if __name__ == "__main__":
    main()