import pandas as pd
from collections import defaultdict
from predictor.predictor import normalize_sign

SEASONS = [2023, 2024]


# -------------------------
# Reliability (past only)
# -------------------------
def compute_reliability(df):
    grouped = (
        df.groupby(["date", "Zodiac"])["performed"]
        .sum()
        .reset_index()
    )

    appeared = grouped[grouped["performed"] >= 1].groupby("Zodiac").size()
    clustered = grouped[grouped["performed"] >= 2].groupby("Zodiac").size()

    reliability = (clustered / appeared)

    return reliability


# -------------------------
# Coupling (past only)
# -------------------------
def compute_coupling(df):
    appearance_counts = defaultdict(int)
    coappearance_counts = defaultdict(int)

    performed = df[df["performed"] == 1]

    daily_sets = (
        performed.groupby("date")["Zodiac"]
        .apply(lambda x: set(x.dropna()))
    )

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
        if appearance_counts[a] == 0:
            continue

        p_b = appearance_counts[b] / total_days
        p_b_given_a = co_count / appearance_counts[a]

        lift = p_b_given_a / p_b if p_b > 0 else None

        rows.append({
            "Trigger": a,
            "Target": b,
            "Lift": lift
        })

    return pd.DataFrame(rows)


# -------------------------
# Strict Prediction
# -------------------------
def predict_from_past(past_df, active_signs):
    reliability = compute_reliability(past_df)
    coupling_df = compute_coupling(past_df)

    results = []

    for sign in reliability.index:

        base_score = reliability.get(sign, 0)

        lifts = []

        for active in active_signs:
            match = coupling_df[
                (coupling_df["Trigger"] == active) &
                (coupling_df["Target"] == sign)
            ]

            if not match.empty:
                lifts.append(match["Lift"].values[0])

        coupling_score = sum(lifts) / len(lifts) if lifts else 1

        final_score = 0.6 * base_score + 0.4 * coupling_score

        results.append((sign, final_score))

    if not results:
        return None

    results.sort(key=lambda x: x[1], reverse=True)

    return results[0][0]  # top predicted sign


# -------------------------
# Strict Walk-forward
# -------------------------
def backtest_season(season):
    df = pd.read_csv(f"data/season_events_{season}.csv")
    df["date"] = pd.to_datetime(df["date"])

    df = df[df["performed"] == 1]

    total_tests = 0
    correct = 0

    all_dates = sorted(df["date"].unique())

    for date in all_dates:

        past_df = df[df["date"] < date]

        if len(past_df) < 50:
            continue

        day_df = df[df["date"] == date]

        if len(day_df) < 3:
            continue

        day_df = day_df.sort_values("minutes", ascending=False)

        midpoint = len(day_df) // 2

        early = day_df.iloc[:midpoint]
        late = day_df.iloc[midpoint:]

        early_signs = [normalize_sign(s) for s in early["Zodiac"].dropna().unique()]

        if not early_signs:
            continue

        # Determine dominant later sign
        late_counts = late["Zodiac"].value_counts()

        if late_counts.empty:
            continue

        dominant_late_sign = late_counts.idxmax()

        predicted = predict_from_past(past_df, early_signs)

        if predicted is None:
            continue

        total_tests += 1

        if predicted == dominant_late_sign:
            correct += 1

    accuracy = correct / total_tests if total_tests > 0 else 0

    return {
        "Season": season,
        "Tests": total_tests,
        "Top1_Correct": correct,
        "Accuracy": round(accuracy, 3)
    }


def main():
    print("\nRunning STRICT Walk-Forward Backtest...\n")

    results = []

    for season in SEASONS:
        results.append(backtest_season(season))

    print(pd.DataFrame(results).to_string(index=False))


if __name__ == "__main__":
    main()
