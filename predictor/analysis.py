import os
import pandas as pd


def load_data(season):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "data", f"season_events_{season}.csv")
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
    all_scores = []

    for season in seasons:
        df = load_data(season)
        rel = zodiac_reliability(df)
        rel.name = str(season)
        all_scores.append(rel)

    combined = pd.concat(all_scores, axis=1)

    # Average without penalizing missing seasons
    combined["Average"] = combined.mean(axis=1, skipna=True)

    combined = combined.fillna(0)

    return combined.sort_values("Average", ascending=False)


def main():
    SEASONS = [2023, 2024]

    result = multi_season_reliability(SEASONS)

    print("\n=== Cross-Season Zodiac Reliability ===")
    print(result)


if __name__ == "__main__":
    main()
