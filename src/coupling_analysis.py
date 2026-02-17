import pandas as pd
from collections import defaultdict


# --------------------
# CONFIG
# --------------------
SEASONS = [2023, 2024]
ZODIAC_COL = "Zodiac"
DATE_COL = "date"
PERFORMED_COL = "performed"


def load_data(season):
    path = f"data/season_events_{season}.csv"
    df = pd.read_csv(path)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df[df[ZODIAC_COL].notna()]
    return df


def build_daily_zodiac_sets(df):
    performed = df[df[PERFORMED_COL] == 1]

    daily_sets = (
        performed
        .groupby(DATE_COL)[ZODIAC_COL]
        .apply(lambda x: set(x))
    )

    return daily_sets


def compute_lift_matrix(daily_sets):
    appearance_counts = defaultdict(int)
    coappearance_counts = defaultdict(int)

    total_days = len(daily_sets)

    # Count appearances
    for zodiac_set in daily_sets:
        for z in zodiac_set:
            appearance_counts[z] += 1

    # Count co-appearances
    for zodiac_set in daily_sets:
        for a in zodiac_set:
            for b in zodiac_set:
                if a != b:
                    coappearance_counts[(a, b)] += 1

    rows = []

    for (a, b), co_count in coappearance_counts.items():
        p_a = appearance_counts[a] / total_days
        p_b = appearance_counts[b] / total_days
        p_b_given_a = co_count / appearance_counts[a]

        lift = p_b_given_a / p_b if p_b > 0 else None

        rows.append({
            "Trigger": a,
            "Target": b,
            "P(B|A)": round(p_b_given_a, 3),
            "Baseline_P(B)": round(p_b, 3),
            "Lift": round(lift, 3) if lift else None
        })

    result_df = pd.DataFrame(rows)

    return result_df.sort_values("Lift", ascending=False)


def main():
    for season in SEASONS:
        print("\n======================================")
        print(f"=== Zodiac Coupling Analysis: {season} ===")
        print("======================================")

        df = load_data(season)
        daily_sets = build_daily_zodiac_sets(df)

        lift_df = compute_lift_matrix(daily_sets)

        print("\n--- Strongest Positive Couplings ---")
        print(lift_df.head(15).to_string(index=False))

        print("\n--- Strongest Negative Couplings ---")
        print(lift_df.sort_values("Lift").head(15).to_string(index=False))


if __name__ == "__main__":
    main()
