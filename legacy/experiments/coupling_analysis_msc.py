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
MIN_SUPPORT = 2   # require >=2 performers per zodiac per day


def load_data():
    return pd.read_csv(CSV_PATH)


def build_daily_zodiac_sets_msc(df):
    """
    For each date, include a zodiac ONLY IF
    it has at least MIN_SUPPORT performing players that day.
    """
    performed = df[df[PERFORMED_COL] == 1]

    # Count performers per (date, zodiac)
    counts = (
        performed
        .groupby([DATE_COL, ZODIAC_COL])
        .size()
        .reset_index(name="count")
    )

    # Keep only zodiac-days meeting minimum support
    strong = counts[counts["count"] >= MIN_SUPPORT]

    # Build zodiac sets per day
    daily_sets = (
        strong
        .groupby(DATE_COL)[ZODIAC_COL]
        .apply(lambda x: set(x.dropna()))
    )

    return daily_sets


def compute_pair_counts(daily_sets):
    """
    Raw co-occurrence counts for zodiac pairs.
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
    Conditional probability P(B | A) under MSC:
    On days where A is active (>= MIN_SUPPORT), how often is B also active?
    """
    appearance = defaultdict(int)
    coappearance = defaultdict(int)

    for zodiac_set in daily_sets:
        for a in zodiac_set:
            appearance[a] += 1
        for a, b in combinations(zodiac_set, 2):
            coappearance[(a, b)] += 1
            coappearance[(b, a)] += 1

    conditional = {}
    for (a, b), count in coappearance.items():
        conditional[(a, b)] = count / appearance[a]

    return pd.Series(conditional).sort_values(ascending=False)


def main():
    df = load_data()
    daily_sets = build_daily_zodiac_sets_msc(df)

    print(f"\n=== MSC DAILY SETS (min {MIN_SUPPORT} performers) ===")
    print(f"Days retained: {len(daily_sets)}")

    print("\n=== MSC Zodiac Pair Co-occurrence Counts ===")
    pair_counts = compute_pair_counts(daily_sets)
    if len(pair_counts) == 0:
        print("No pairs meet the minimum support criteria.")
    else:
        print(pair_counts.head(15))

    print("\n=== MSC Conditional Probabilities P(B | A) ===")
    conditional_probs = compute_conditional_probabilities(daily_sets)
    if len(conditional_probs) == 0:
        print("No conditional pairs meet the minimum support criteria.")
    else:
        print(conditional_probs.head(15))


if __name__ == "__main__":
    main()
