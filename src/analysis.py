import pandas as pd


def load_data(season):
    path = f"data/season_events_{season}.csv"
    return pd.read_csv(path)


def zodiac_reliability(df):
    grouped = (
        df.groupby(["date", "Zodiac"])["performed"]
        .sum()
        .reset_index()
    )

    appeared = grouped[grouped["performed"] >= 1].groupby("Zodiac").size()
    clustered = grouped[grouped["performed"] >= 2].groupby("Zodiac").size()

    return (clustered / appeared).fillna(0).sort_values(ascending=False)


def same_day_clustering(df):
    daily = (
        df[df["performed"] == 1]
        .groupby(["date", "Zodiac"])
        .size()
    )

    return daily.groupby("Zodiac").mean().sort_values(ascending=False)


def main():
    SEASON = 2023  # change freely

    df = load_data(SEASON)

    print(f"\n=== Zodiac Reliability ({SEASON}) ===")
    print(zodiac_reliability(df))

    print(f"\n=== Same-Day Clustering ({SEASON}) ===")
    print(same_day_clustering(df))


if __name__ == "__main__":
    main()
