from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REFERENCE_DATA_DIR = PROJECT_ROOT / "data" / "reference"

REFERENCE_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ---------------------------------------------------------
# LOAD PLAYER-MATCH DATA
# ---------------------------------------------------------

def load_player_match_data():
    """
    Load every currently available player-match dataset.

    This means the script can be rerun later as additional
    seasons are collected.
    """

    files = sorted(
        PROCESSED_DATA_DIR.glob(
            "player_match_stats_*.csv"
        )
    )

    if not files:
        raise FileNotFoundError(
            "No player_match_stats_*.csv files found."
        )

    print("Player-match files found:")

    dataframes = []

    for file in files:
        print(f"  {file.name}")

        df = pd.read_csv(file)

        dataframes.append(df)

    combined = pd.concat(
        dataframes,
        ignore_index=True,
    )

    return combined


# ---------------------------------------------------------
# BUILD PLAYER REFERENCE
# ---------------------------------------------------------

def build_player_reference(df):
    """
    Create one row for every unique API-Football player ID.
    """

    # Player IDs are essential
    df = df[
        df["player_id"].notna()
    ].copy()

    df["kickoff_datetime"] = pd.to_datetime(
        df["kickoff_datetime"],
        utc=True,
        errors="coerce",
    )

    # Sort chronologically so first/last observations
    # are meaningful
    df = df.sort_values(
        "kickoff_datetime"
    )

    rows = []

    for player_id, player_df in df.groupby(
        "player_id"
    ):

        # Most commonly occurring API name
        name_counts = (
            player_df["player_name"]
            .dropna()
            .value_counts()
        )

        if len(name_counts) > 0:
            player_name = name_counts.index[0]
        else:
            player_name = None

        teams = sorted(
            player_df["team_name"]
            .dropna()
            .unique()
        )

        positions = sorted(
            player_df["position"]
            .dropna()
            .unique()
        )

        appearances = int(
            player_df["appeared"].sum()
        )

        starts = int(
            player_df["starter"].sum()
        )

        rows.append(
            {
                "player_id": int(player_id),
                "player_name": player_name,

                "teams": " | ".join(teams),

                "positions":
                    " | ".join(positions),

                "first_seen":
                    player_df[
                        "kickoff_datetime"
                    ].min(),

                "last_seen":
                    player_df[
                        "kickoff_datetime"
                    ].max(),

                "appearances":
                    appearances,

                "starts":
                    starts,

                # Filled later
                "birth_date": None,
                "zodiac": None,

                # Useful for checking DOB source
                "dob_source": None,
                "dob_verified": False,
            }
        )

    reference = pd.DataFrame(rows)

    reference = reference.sort_values(
        ["player_name", "player_id"]
    ).reset_index(drop=True)

    return reference


# ---------------------------------------------------------
# VALIDATE
# ---------------------------------------------------------

def validate(reference):
    print("\n==============================")
    print("PLAYER REFERENCE VALIDATION")
    print("==============================")

    print(
        f"Unique players: "
        f"{len(reference)}"
    )

    print(
        "Duplicate player IDs:",
        reference[
            "player_id"
        ].duplicated().sum(),
    )

    print(
        "Missing player names:",
        reference[
            "player_name"
        ].isna().sum(),
    )

    print("\nPositions:")

    print(
        reference["positions"]
        .value_counts()
        .head(15)
        .to_string()
    )

    print("==============================\n")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    df = load_player_match_data()

    reference = build_player_reference(df)

    validate(reference)

    output_path = (
        REFERENCE_DATA_DIR
        / "players.csv"
    )

    reference.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
    )

    print(
        f"Player reference saved to:\n"
        f"{output_path}"
    )


if __name__ == "__main__":
    main()