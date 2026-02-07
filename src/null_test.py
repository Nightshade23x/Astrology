import pandas as pd
import random
from itertools import combinations
from collections import defaultdict

# --------------------
# CONFIG
# --------------------
CSV_PATH = "data/season_events.csv"
ZODIAC_COL = "Zodiac"
DATE_COL = "date"
PERFORMED_COL = "performed"
N_SHUFFLES = 10   # start small; increase later if needed


def build_daily_sets(df):
    """
    For each date, return the set of zodiac signs
    that had at least one performing player.
    """
    performed = df[df[PERFORMED_COL] == 1]

    daily_sets = (
        performed
        .groupby(DATE_COL)[ZODIAC_COL]
        .apply(lambda x: set(x.dropna()))
    )

    return daily_sets


def compute_conditional_probs(daily_sets):
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


def run_null_test():
    df = pd.read_csv(CSV_PATH)

    print("\n=== REAL DATA (Top Conditional Pairs) ===")
    real_sets = build_daily_sets(df)
    real_probs = compute_conditional_probs(real_sets)
    print(real_probs.head(10))

    max_random_values = []

    print("\n=== NULL MODEL (Shuffled Zodiac Labels) ===")
    for i in range(N_SHUFFLES):
        shuffled_df = df.copy()
        shuffled_df[ZODIAC_COL] = random.sample(
            list(shuffled_df[ZODIAC_COL]),
            len(shuffled_df)
        )

        shuffled_sets = build_daily_sets(shuffled_df)
        shuffled_probs = compute_conditional_probs(shuffled_sets)

        max_val = shuffled_probs.max()
        max_random_values.append(max_val)

        print(f"Shuffle {i+1}: max P(B|A) = {max_val:.3f}")

    print("\n=== NULL SUMMARY ===")
    print(f"Average max P(B|A): {sum(max_random_values) / len(max_random_values):.3f}")
    print(f"Max observed P(B|A): {max(max_random_values):.3f}")


if __name__ == "__main__":
    run_null_test()
