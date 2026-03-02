import os
import pandas as pd

MANUAL_WEIGHT = 0.15


# Always get project root (ASTROLOGY folder)
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def load_historical_data(season):

    season_path = os.path.join(DATA_DIR, f"season_events_{season}.csv")
    dob_path = os.path.join(DATA_DIR, "player_dob_batch.csv")

    df = pd.read_csv(season_path)
    dob_df = pd.read_csv(dob_path)

    df.columns = df.columns.str.strip()
    dob_df.columns = dob_df.columns.str.strip()

    if "zodiac" in dob_df.columns:
        dob_df = dob_df.rename(columns={"zodiac": "Zodiac"})

    df = df.merge(
        dob_df[["player", "Zodiac"]],
        on="player",
        how="left"
    )

    df = df.dropna(subset=["Zodiac"])

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    df = df.dropna(subset=["date"])

    return df


def zodiac_reliability(df):

    df = df[df["performed"] == 1]

    grouped = (
        df.groupby(["date", "Zodiac"])
        .size()
        .reset_index(name="count")
    )

    appeared = grouped.groupby("Zodiac").size()
    clustered = grouped[grouped["count"] >= 2].groupby("Zodiac").size()

    reliability = (clustered / appeared).fillna(0)

    return reliability


def multi_season_reliability(seasons):

    all_signs = set()
    season_results = []

    for season in seasons:
        df = load_historical_data(season)
        rel = zodiac_reliability(df)

        all_signs.update(rel.index)
        season_results.append(rel)

    all_signs = sorted(list(all_signs))

    aligned = []

    for rel in season_results:
        aligned.append(rel.reindex(all_signs).fillna(0))

    hist_combined = pd.concat(aligned, axis=1)

    hist_combined["Historical"] = hist_combined.mean(axis=1)

    final = hist_combined["Historical"].fillna(0)

    return final.sort_values(ascending=False).to_frame(name="Average")