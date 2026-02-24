import numpy as np
import pandas as pd
from collections import Counter
from analysis import multi_season_reliability
from coupling import get_cross_season_coupling

SEASONS = [2023, 2024]


def normalize_sign(sign):
    if not isinstance(sign, str):
        return None
    return sign.strip().capitalize()


def predict_same_day(active_signs):

    # -------------------------
    # Clean and normalize input
    # -------------------------
    cleaned = []
    for s in active_signs:
        norm = normalize_sign(s)
        if norm is not None:
            cleaned.append(norm)

    active_signs = cleaned

    # Count occurrences (momentum strength)
    sign_counts = Counter(active_signs)

    # -------------------------
    # Load base reliability (prior probability)
    # -------------------------
    reliability_df = multi_season_reliability(SEASONS)
    base_rates = reliability_df["Average"]

    # -------------------------
    # Load coupling matrix (conditional lift)
    # -------------------------
    coupling_df = get_cross_season_coupling(SEASONS)

    results = []

    # -------------------------
    # Compute probabilities
    # -------------------------
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
                    # Count-based amplification
                    log_prob += count * np.log(lift)

        results.append({
            "Sign": sign,
            "Log_Prob": log_prob
        })

    result_df = pd.DataFrame(results)

    # Convert back from log-space
    result_df["Raw"] = np.exp(result_df["Log_Prob"])

    # Normalize into probability distribution
    total = result_df["Raw"].sum()
    result_df["Probability"] = (result_df["Raw"] / total) * 100

    result_df = result_df.sort_values("Probability", ascending=False)
    result_df["Probability"] = result_df["Probability"].round(2)

    return result_df[["Sign", "Probability"]]


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

    active_signs = user_input.split(",")

    prediction = predict_same_day(active_signs)

    print("\n==============================")
    print("Predicted Sign Probabilities")
    print("==============================\n")

    print(prediction.to_string(index=False))


if __name__ == "__main__":
    main()