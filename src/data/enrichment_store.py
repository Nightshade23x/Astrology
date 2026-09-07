from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"

PLAYERS_PATH = REFERENCE_DIR / "players.csv"
ENRICHMENT_PATH = REFERENCE_DIR / "player_enrichment.csv"


ENRICHMENT_COLUMNS = [
    "player_id",
    "birth_date",
    "zodiac",
    "dob_source",
    "dob_verified",
]


def load_enrichment():
    """
    Load the persistent DOB/zodiac store and make sure
    every player currently in players.csv has a row.
    """

    players = pd.read_csv(PLAYERS_PATH)

    if ENRICHMENT_PATH.exists():
        enrichment = pd.read_csv(ENRICHMENT_PATH)
    else:
        enrichment = pd.DataFrame(
            columns=ENRICHMENT_COLUMNS
        )

    # Normalise player IDs
    enrichment["player_id"] = pd.to_numeric(
        enrichment["player_id"],
        errors="coerce",
    )

    enrichment = enrichment[
        enrichment["player_id"].notna()
    ].copy()

    enrichment["player_id"] = (
        enrichment["player_id"]
        .astype(int)
    )

    # Add newly discovered players
    existing_ids = set(
        enrichment["player_id"]
    )

    missing_ids = players[
        ~players["player_id"].isin(existing_ids)
    ][["player_id"]].copy()

    if not missing_ids.empty:
        missing_ids["birth_date"] = pd.NA
        missing_ids["zodiac"] = pd.NA
        missing_ids["dob_source"] = pd.NA
        missing_ids["dob_verified"] = False

        enrichment = pd.concat(
            [
                enrichment,
                missing_ids,
            ],
            ignore_index=True,
        )

    # Ensure expected columns exist
    for column in ENRICHMENT_COLUMNS:
        if column not in enrichment.columns:
            enrichment[column] = pd.NA

    enrichment["dob_source"] = (
        enrichment["dob_source"]
        .astype("string")
    )

    enrichment["dob_verified"] = (
        enrichment["dob_verified"]
        .apply(
            lambda value: (
                value
                if isinstance(value, bool)
                else (
                    str(value).strip().lower() == "true"
                    if pd.notna(value)
                    else False
                )
            )
        )
    )

    enrichment = (
        enrichment[ENRICHMENT_COLUMNS]
        .drop_duplicates(
            subset=["player_id"],
            keep="last",
        )
        .sort_values("player_id")
        .reset_index(drop=True)
    )

    return enrichment


def save_enrichment(enrichment):
    enrichment = enrichment[
        ENRICHMENT_COLUMNS
    ].copy()

    enrichment = (
        enrichment
        .drop_duplicates(
            subset=["player_id"],
            keep="last",
        )
        .sort_values("player_id")
        .reset_index(drop=True)
    )

    enrichment.to_csv(
        ENRICHMENT_PATH,
        index=False,
        encoding="utf-8",
    )