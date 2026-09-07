import io
import subprocess
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"

PLAYERS_PATH = REFERENCE_DIR / "players.csv"
API_LOG_PATH = REFERENCE_DIR / "api_dob_lookup_log.csv"


def zodiac_from_date(date_value):
    if pd.isna(date_value):
        return None

    date = pd.to_datetime(date_value, errors="coerce")

    if pd.isna(date):
        return None

    month = date.month
    day = date.day

    if (month == 3 and day >= 21) or (month == 4 and day <= 19):
        return "Aries"
    if (month == 4 and day >= 20) or (month == 5 and day <= 20):
        return "Taurus"
    if (month == 5 and day >= 21) or (month == 6 and day <= 20):
        return "Gemini"
    if (month == 6 and day >= 21) or (month == 7 and day <= 22):
        return "Cancer"
    if (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return "Leo"
    if (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return "Virgo"
    if (month == 9 and day >= 23) or (month == 10 and day <= 22):
        return "Libra"
    if (month == 10 and day >= 23) or (month == 11 and day <= 21):
        return "Scorpio"
    if (month == 11 and day >= 22) or (month == 12 and day <= 21):
        return "Sagittarius"
    if (month == 12 and day >= 22) or (month == 1 and day <= 19):
        return "Capricorn"
    if (month == 1 and day >= 20) or (month == 2 and day <= 18):
        return "Aquarius"

    return "Pisces"


def load_last_committed_players():
    """
    Read players.csv exactly as it existed at HEAD,
    before today's accidental overwrite.
    """

    result = subprocess.run(
        [
            "git",
            "show",
            "HEAD:data/reference/players.csv",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=True,
    )

    text = result.stdout.decode("utf-8-sig")

    return pd.read_csv(io.StringIO(text))


def main():
    # Current file contains the newest 584-player population.
    current = pd.read_csv(PLAYERS_PATH)

    print(f"Current players: {len(current)}")
    print(
        "Current DOBs before recovery:",
        current["birth_date"].notna().sum(),
    )

    # Last committed version contains our earlier enrichment.
    old = load_last_committed_players()

    print(f"Players in committed reference: {len(old)}")
    print(
        "DOBs in committed reference:",
        old["birth_date"].notna().sum(),
    )

    enrichment_columns = [
        "player_id",
        "birth_date",
        "zodiac",
        "dob_source",
        "dob_verified",
    ]

    old_enrichment = old[enrichment_columns].copy()

    # Remove wiped enrichment columns from the newly built table.
    current = current.drop(
        columns=[
            "birth_date",
            "zodiac",
            "dob_source",
            "dob_verified",
        ],
        errors="ignore",
    )

    # Restore previously committed enrichment by exact API player ID.
    recovered = current.merge(
        old_enrichment,
        on="player_id",
        how="left",
    )

    # -----------------------------------------------------
    # Reapply any exact-ID API DOBs obtained after the
    # last commit.
    # -----------------------------------------------------

    if API_LOG_PATH.exists():
        api_log = pd.read_csv(API_LOG_PATH)

        matched = api_log[
            (api_log["status"] == "matched")
            & api_log["birth_date"].notna()
        ].copy()

        matched = matched.drop_duplicates(
            subset=["player_id"],
            keep="last",
        )

        lookup = matched.set_index("player_id")

        for index, row in recovered.iterrows():
            player_id = row["player_id"]

            if player_id not in lookup.index:
                continue

            info = lookup.loc[player_id]
            birth_date = info["birth_date"]

            recovered.at[index, "birth_date"] = birth_date
            recovered.at[index, "zodiac"] = zodiac_from_date(
                birth_date
            )
            recovered.at[index, "dob_source"] = "API-Football-ID"
            recovered.at[index, "dob_verified"] = True

    recovered["dob_source"] = recovered[
        "dob_source"
    ].astype("string")

    recovered["dob_verified"] = (
        recovered["dob_verified"]
        .fillna(False)
        .apply(
            lambda x: (
                x
                if isinstance(x, bool)
                else str(x).strip().lower() == "true"
            )
        )
    )

    recovered.to_csv(
        PLAYERS_PATH,
        index=False,
        encoding="utf-8",
    )

    total = len(recovered)
    with_dob = recovered["birth_date"].notna().sum()

    print("\n==============================")
    print("PLAYER ENRICHMENT RECOVERY")
    print("==============================")
    print(f"Players: {total}")
    print(f"DOBs recovered: {with_dob}")
    print(f"Still missing: {total - with_dob}")
    print(
        "Duplicate player IDs:",
        recovered["player_id"].duplicated().sum(),
    )
    print("==============================")


if __name__ == "__main__":
    main()