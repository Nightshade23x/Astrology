import pandas as pd

DATA_PATH = "data/season_events.csv"


def load_data():
    df = pd.read_csv(DATA_PATH)
    return df


def zodiac_reliability(df):
    """
    Reliability = days with >=2 performers / days with >=1 appearance
    """
    grouped = (
        df.groupby(["date", "Zodiac"])["performed"]
        .sum()
        .reset_index()
    )

    appeared = grouped[grouped["performed"] >= 1].groupby("Zodiac").size()
    clustered = grouped[grouped["performed"] >= 2].groupby("Zodiac").size()

    reliability = (clustered / appeared).fillna(0)

    return reliability.sort_values(ascending=False)


def same_day_clustering(df):
    """
    Average number of same-sign performers per day
    """
    daily = (
        df[df["performed"] == 1]
        .groupby(["date", "Zodiac"])
        .size()
    )

    return daily.groupby("Zodiac").mean().sort_values(ascending=False)


def cancer_sagittarius_coupling(df):
    """
    P(Sagittarius | Cancer) vs baseline
    """
    daily = (
        df[df["performed"] == 1]
        .groupby(["date", "Zodiac"])
        .size()
        .unstack(fill_value=0)
    )

    if "Cancer" not in daily.columns or "Sagittarius" not in daily.columns:
        return None

    cancer_days = daily[daily["Cancer"] > 0]
    no_cancer_days = daily[daily["Cancer"] == 0]

    p_sag_given_cancer = (cancer_days["Sagittarius"] > 0).mean()
    p_sag_given_no_cancer = (no_cancer_days["Sagittarius"] > 0).mean()

    return {
        "P(Sagittarius | Cancer)": p_sag_given_cancer,
        "P(Sagittarius | no Cancer)": p_sag_given_no_cancer,
        "Lift": (
            p_sag_given_cancer / p_sag_given_no_cancer
            if p_sag_given_no_cancer > 0
            else None
        ),
    }


def main():
    df = load_data()

    print("\n=== Zodiac Reliability ===")
    print(zodiac_reliability(df))

    print("\n=== Same-Day Clustering ===")
    print(same_day_clustering(df))

    print("\n=== Cancer ↔ Sagittarius Coupling ===")
    coupling = cancer_sagittarius_coupling(df)
    if coupling:
        for k, v in coupling.items():
            print(f"{k}: {v:.3f}")
    else:
        print("Not enough data yet")


if __name__ == "__main__":
    main()
