import os
import pandas as pd
from collections import defaultdict

MANUAL_WEIGHT = 0.15
ZODIAC_COL = "Zodiac"
DATE_COL = "date"
PERFORMED_COL = "performed"


def load_historical_data(season):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "data", f"season_events_{season}.csv")
    df = pd.read_csv(path)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    return df


def load_manual_data():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "data", "manual_day_events.csv")

    if not os.path.exists(path):
        return pd.DataFrame(columns=[DATE_COL, ZODIAC_COL, PERFORMED_COL])

    df = pd.read_csv(path)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    return df


def build_daily_sets(df):
    performed = df[df[PERFORMED_COL] == 1]

    return (
        performed
        .groupby(DATE_COL)[ZODIAC_COL]
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

        p_b = appearance_counts[b] / total_days
        p_b_given_a = co_count / appearance_counts[a]
        lift = p_b_given_a / p_b if p_b > 0 else None

        rows.append({
            "Trigger": a,
            "Target": b,
            "Lift": lift
        })

    return pd.DataFrame(rows)


def get_cross_season_coupling(seasons):

    # Historical
    hist_sets = []

    for season in seasons:
        df = load_historical_data(season)
        hist_sets.append(build_daily_sets(df))

    hist_daily = pd.concat(hist_sets)
    hist_lift = compute_lift(hist_daily)

    # Manual
    manual_df = load_manual_data()

    if not manual_df.empty:
        manual_sets = build_daily_sets(manual_df)
        manual_lift = compute_lift(manual_sets)
    else:
        manual_lift = pd.DataFrame(columns=["Trigger", "Target", "Lift"])

    # Merge weighted
    combined = hist_lift.copy()
    combined = combined.rename(columns={"Lift": "Hist_Lift"})

    combined = combined.merge(
        manual_lift.rename(columns={"Lift": "Manual_Lift"}),
        on=["Trigger", "Target"],
        how="outer"
    )

    combined["Hist_Lift"] = combined["Hist_Lift"].fillna(1)
    combined["Manual_Lift"] = combined["Manual_Lift"].fillna(1)

    combined["Avg_Lift"] = (
        (1 - MANUAL_WEIGHT) * combined["Hist_Lift"] +
        MANUAL_WEIGHT * combined["Manual_Lift"]
    )

    return combined[["Trigger", "Target", "Avg_Lift"]]