import os
import pandas as pd
from collections import defaultdict

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


# -----------------------------
# PRESENCE-LEVEL DAILY SETS
# -----------------------------
def build_presence_sets(df):

    df = df[df["performed"] == 1]

    return (
        df.groupby("date")["Zodiac"]
        .apply(lambda x: set(x))
    )


# -----------------------------
# CLUSTER-LEVEL DAILY SETS
# (2+ performers)
# -----------------------------
def build_cluster_sets(df):

    df = df[df["performed"] == 1]

    grouped = (
        df.groupby(["date", "Zodiac"])
        .size()
        .reset_index(name="count")
    )

    clustered = grouped[grouped["count"] >= 2]

    return (
        clustered.groupby("date")["Zodiac"]
        .apply(lambda x: set(x))
    )


# -----------------------------
# GENERIC LIFT CALCULATION
# -----------------------------
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
            "Lift": lift
        })

    return pd.DataFrame(rows)


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def get_cross_season_coupling(seasons):

    presence_sets = []
    cluster_sets = []

    for season in seasons:
        df = load_historical_data(season)

        presence_sets.append(build_presence_sets(df))
        cluster_sets.append(build_cluster_sets(df))

    combined_presence = pd.concat(presence_sets)
    combined_cluster = pd.concat(cluster_sets)

    presence_lift = compute_lift(combined_presence)
    cluster_lift = compute_lift(combined_cluster)

    presence_lift = presence_lift.rename(columns={"Lift": "Presence_Lift"})
    cluster_lift = cluster_lift.rename(columns={"Lift": "Cluster_Lift"})

    merged = presence_lift.merge(
        cluster_lift,
        on=["Trigger", "Target"],
        how="outer"
    )

    merged["Presence_Lift"] = merged["Presence_Lift"].fillna(1)
    merged["Cluster_Lift"] = merged["Cluster_Lift"].fillna(1)

    return merged