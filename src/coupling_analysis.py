import pandas as pd
from itertools import combinations
from collections import defaultdict

# --------------------
# CONFIG
# --------------------
CSV_PATH = "data/season_events.csv"
ZODIAC_COL = "Zodiac"
DATE_COL = "date"
PERFORMED_COL = "performed"


def load_data():
    df = pd.read_csv(CSV_PATH)
    return df


def build_daily_zodiac_sets(df):
    """
    For each date, collect the set of zodiac signs
    that had at least one performing player.
    """
    performed = df[df[PERFORMED_COL] == 1]

    daily_sets = (
        performed
        .groupby(DATE_COL)[ZODIAC_COL]
        .apply(lambda x: set(x.dropna()))
    )

    return daily_sets


def compute_pair_counts(daily_sets):
    """
    Count how often each zodiac pair appears on the same day.
    """
    pair_counts = defaultdict(int)

    for zodiac_set in daily_sets:
        if len(zodiac_set) < 2:
            continue

        for a, b in combinations(sorted(zodiac_set), 2):
            pair_counts[(a, b)] += 1

    return pd.Series(pair_counts).sort_values(ascending=False)


def compute_conditional_probabilities(daily_sets):
    """
    Compute P(B | A):
    On days where A appears, how often does B also appear?
    """
    appearance_counts = defaultdict(int)
    coappearance_counts = defaultdict(int)

    for zodiac_set in daily_sets:
        for a in zodiac_set:
            appearance_counts[a] += 1

        for a, b in combinations(zodiac_set, 2):
            coappearance_counts[(a, b)] += 1
            coappearance_counts[(b, a)] += 1

    conditional = {}

    for (a, b), count in coappearance_counts.items():
        conditional[(a, b)] = count / appearance_counts[a]

    return (
        pd.Series(conditional)
        .sort_values(ascending=False)
    )


def main():
    df = load_data()
    daily_sets = build_daily_zodiac_sets(df)

    print("\n=== Zodiac Pair Co-occurrence Counts ===")
    pair_counts = compute_pair_counts(daily_sets)
    print(pair_counts.head(15))

    print("\n=== Conditional Probabilities P(B | A) ===")
    conditional_probs = compute_conditional_probabilities(daily_sets)
    print(conditional_probs.head(15))


if __name__ == "__main__":
    main()
