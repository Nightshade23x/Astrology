import os
import pandas as pd
from collections import defaultdict

MANUAL_WEIGHT = 0.15


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


def build_daily_sets(df):

    df = df[df["performed"] == 1]

    return (
        df.groupby("date")["Zodiac"]
        .apply(lambda x: set(x))
    )


def compute_lift(daily_sets):

    appearance_counts = defaultdict(int)
    coappearance_counts = defaultdict(int)

    total_days = len(daily_sets)

    for zodiac_set in daily_sets:
        for z in zodiac_set:
            appearance_counts[z] += 1

    for zodiac_set in daily_sets:
        for a in zodiac_set:
            for b in zodiac_set:
                if a != b:
                    coappearance_counts[(a, b)] += 1

    rows = []

    for (a, b), co_count in coappearance_counts.items():

        if appearance_counts[a] == 0:
            continue

        p_b = appearance_counts[b] / total_days
        p_b_given_a = co_count / appearance_counts[a]

        lift = p_b_given_a / p_b if p_b > 0 else 1

        rows.append({
            "Trigger": a,
            "Target": b,
            "Avg_Lift": lift
        })

    return pd.DataFrame(rows)


def get_cross_season_coupling(seasons):

    all_sets = []

    for season in seasons:
        df = load_historical_data(season)
        daily_sets = build_daily_sets(df)
        all_sets.append(daily_sets)

    combined_sets = pd.concat(all_sets)

    return compute_lift(combined_sets)