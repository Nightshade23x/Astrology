import os
import pandas as pd
from collections import defaultdict

# -----------------------------
# Trine Mapping (120° apart)
# -----------------------------
TRINE_MAP = {
    "Aries": ["Leo", "Sagittarius"],
    "Leo": ["Aries", "Sagittarius"],
    "Sagittarius": ["Aries", "Leo"],

    "Taurus": ["Virgo", "Capricorn"],
    "Virgo": ["Taurus", "Capricorn"],
    "Capricorn": ["Taurus", "Virgo"],

    "Gemini": ["Libra", "Aquarius"],
    "Libra": ["Gemini", "Aquarius"],
    "Aquarius": ["Gemini", "Libra"],

    "Cancer": ["Scorpio", "Pisces"],
    "Scorpio": ["Cancer", "Pisces"],
    "Pisces": ["Cancer", "Scorpio"]
}

SEASONS = [2023, 2024]

PROJECT_ROOT = os.path.abspath(".")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def load_data(season):

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
    df = df[df["performed"] == 1]

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    df = df.dropna(subset=["date"])

    return df


def build_daily_sign_sets(df):

    return (
        df.groupby("date")["Zodiac"]
        .apply(lambda x: set(x))
    )


def compute_trine_lift(daily_sets):

    appearance_counts = defaultdict(int)
    coappearance_counts = defaultdict(int)

    total_days = len(daily_sets)

    # Count how often each sign appears
    for sign_set in daily_sets:
        for s in sign_set:
            appearance_counts[s] += 1

    # Count co-appearances
    for sign_set in daily_sets:
        for a in sign_set:

            if a not in TRINE_MAP:
                continue

            for b in TRINE_MAP[a]:
                if b in sign_set:
                    coappearance_counts[(a, b)] += 1

    print("\n=== TRINE LIFT MATRIX ===\n")

    for (a, b), co_count in coappearance_counts.items():

        p_b = appearance_counts[b] / total_days
        p_b_given_a = co_count / appearance_counts[a]

        lift = p_b_given_a / p_b if p_b > 0 else 1

        print(f"{a} → {b} | Lift: {round(lift, 3)}")


def main():

    all_sets = []

    for season in SEASONS:
        df = load_data(season)
        daily_sets = build_daily_sign_sets(df)
        all_sets.append(daily_sets)

    combined = pd.concat(all_sets)

    compute_trine_lift(combined)


if __name__ == "__main__":
    main()