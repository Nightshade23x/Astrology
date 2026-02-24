import os
import pandas as pd

MANUAL_WEIGHT = 0.15


def load_historical_data(season):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "data", f"season_events_{season}.csv")
    return pd.read_csv(path)


def load_manual_data():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "data", "manual_day_events.csv")

    if not os.path.exists(path):
        return pd.DataFrame(columns=["date", "Zodiac", "performed"])

    return pd.read_csv(path)


def zodiac_reliability(df):
    grouped = (
        df.groupby(["date", "Zodiac"])["performed"]
        .sum()
        .reset_index()
    )

    appeared = grouped[grouped["performed"] >= 1].groupby("Zodiac").size()
    clustered = grouped[grouped["performed"] >= 2].groupby("Zodiac").size()

    reliability = (clustered / appeared)

    return reliability


def multi_season_reliability(seasons):

    # Historical
    hist_scores = []

    for season in seasons:
        df = load_historical_data(season)
        rel = zodiac_reliability(df)
        hist_scores.append(rel)

    hist_combined = pd.concat(hist_scores, axis=1)
    hist_combined["Historical"] = hist_combined.mean(axis=1, skipna=True)

    # Manual
    manual_df = load_manual_data()

    if not manual_df.empty:
        manual_rel = zodiac_reliability(manual_df)
    else:
        manual_rel = pd.Series(dtype=float)

    # Combine weighted
    combined = hist_combined["Historical"].copy()

    for sign in manual_rel.index:
        hist_val = combined.get(sign, 0)
        manual_val = manual_rel.get(sign, 0)

        combined[sign] = (
            (1 - MANUAL_WEIGHT) * hist_val +
            MANUAL_WEIGHT * manual_val
        )

    combined = combined.fillna(0)

    return combined.sort_values(ascending=False).to_frame(name="Average")