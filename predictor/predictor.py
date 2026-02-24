import numpy as np
import pandas as pd
from collections import Counter
from analysis import multi_season_reliability
from coupling import get_cross_season_coupling
from datetime import datetime
import os

SEASONS = [2023, 2024]


def normalize_sign(sign):
    """
    Clean and standardize zodiac input.
    """
    if not isinstance(sign, str):
        return None
    return sign.strip().capitalize()


def predict_same_day(active_signs):
    """
    Compute same-day conditional probabilities using:
    - Historical reliability (prior)
    - Coupling lift (conditional)
    - Momentum amplification (count-based)
    """

    # Count occurrences (momentum strength)
    sign_counts = Counter(active_signs)

    # Load reliability (prior probability)
    reliability_df = multi_season_reliability(SEASONS)
    base_rates = reliability_df["Average"]

    # Load coupling matrix
    coupling_df = get_cross_season_coupling(SEASONS)

    results = []

    for sign in base_rates.index:

        base_prob = base_rates.get(sign, 0)

        # Avoid log(0)
        log_prob = np.log(base_prob + 1e-9)

        # Apply momentum-based coupling
        for active_sign, count in sign_counts.items():

            match = coupling_df[
                (coupling_df["Trigger"] == active_sign) &
                (coupling_df["Target"] == sign)
            ]

            if not match.empty:
                lift = match["Avg_Lift"].values[0]
                if lift > 0:
                    log_prob += count * np.log(lift)

        results.append({
            "Sign": sign,
            "Log_Prob": log_prob
        })

    result_df = pd.DataFrame(results)

    # Convert back from log-space
    result_df["Raw"] = np.exp(result_df["Log_Prob"])

    # Normalize to probability distribution
    total = result_df["Raw"].sum()
    result_df["Probability"] = (result_df["Raw"] / total) * 100

    result_df = result_df.sort_values("Probability", ascending=False)
    result_df["Probability"] = result_df["Probability"].round(2)

    return result_df[["Sign", "Probability"]]


def save_manual_input(active_signs):
    """
    Save today's manual input as a synthetic matchday.
    This reinforces future predictions.
    """

    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "data", "manual_day_events.csv")

    today = datetime.now().strftime("%Y-%m-%d")

    rows = []

    for sign in active_signs:
        rows.append({
            "date": today,
            "Zodiac": sign,
            "performed": 1
        })

    df_new = pd.DataFrame(rows)

    if os.path.exists(path):
        df_existing = pd.read_csv(path)
        df_new = pd.concat([df_existing, df_new], ignore_index=True)

    df_new.to_csv(path, index=False)


def main():
    print("\n============================================")
    print("  Same-Matchday Zodiac Momentum Predictor")
    print("============================================\n")

    print("Enter zodiac signs that have already performed today.")
    print("Separate with commas (example: Cancer,Pisces)\n")
    print("IMPORTANT:")
    print("- If a sign has performed multiple times,")
    print("  repeat it multiple times in your input.")
    print("  Example: Pisces,Pisces,Pisces,Cancer\n")

    user_input = input("Active signs: ")

    raw_signs = user_input.split(",")

    active_signs = []
    for s in raw_signs:
        norm = normalize_sign(s)
        if norm is not None:
            active_signs.append(norm)

    if len(active_signs) == 0:
        print("\nNo valid zodiac signs entered.\n")
        return

    prediction = predict_same_day(active_signs)

    print("\n==============================")
    print("Predicted Sign Probabilities")
    print("==============================\n")
    print(prediction.to_string(index=False))

    # Save AFTER prediction (affects future runs only)
    save_manual_input(active_signs)


if __name__ == "__main__":
    main()