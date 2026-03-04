import numpy as np
import pandas as pd
from collections import Counter
from analysis import multi_season_reliability
from coupling import get_cross_season_coupling
from datetime import datetime
import os

SEASONS = [2023, 2024]


def normalize_sign(sign):
    if not isinstance(sign, str):
        return None
    return sign.strip().capitalize()


def predict_same_day(active_signs):

    sign_counts = Counter(active_signs)

    reliability_df = multi_season_reliability(SEASONS)
    base_rates = reliability_df["Average"]

    coupling_df = get_cross_season_coupling(SEASONS)

    dominant_sign = None
    dominant_count = 0

    for sign, count in sign_counts.items():
        if count >= 3:
            dominant_sign = sign
            dominant_count = count
            break

    results = []

    for sign in base_rates.index:

        base_prob = base_rates.get(sign, 0)
        log_prob = np.log(base_prob + 1e-9)

        # -----------------------------
        # STRONG NONLINEAR MOMENTUM
        # -----------------------------
        if sign in sign_counts:
            count = sign_counts[sign]

            if count >= 2:
                momentum_boost = 0.6 * ((count - 1) ** 1.5)
                log_prob += momentum_boost
            else:
                log_prob += 0.1

        # -----------------------------
        # PRESENCE + CLUSTER COUPLING
        # -----------------------------
        for active_sign, trigger_count in sign_counts.items():

            match = coupling_df[
                (coupling_df["Trigger"] == active_sign) &
                (coupling_df["Target"] == sign)
            ]

            if not match.empty:

                presence_lift = match["Presence_Lift"].values[0]
                cluster_lift = match["Cluster_Lift"].values[0]

                # Presence-based lift
                if presence_lift > 0:
                    log_prob += trigger_count * np.log(presence_lift)

                # Cluster-based lift (only if trigger clusters)
                if trigger_count >= 2 and cluster_lift > 0:
                    log_prob += 1.2 * np.log(cluster_lift)

        # -----------------------------
        # DOMINANT SIGN EXTRA BOOST
        # -----------------------------
        if dominant_sign and sign == dominant_sign:
            boost = 1 + 0.25 * (dominant_count - 2)
            log_prob += np.log(boost)

        results.append({
            "Sign": sign,
            "Log_Prob": log_prob
        })

    result_df = pd.DataFrame(results)

    result_df["Raw"] = np.exp(result_df["Log_Prob"])
    total = result_df["Raw"].sum()
    result_df["Probability"] = (result_df["Raw"] / total) * 100

    result_df = result_df.sort_values("Probability", ascending=False)
    result_df["Probability"] = result_df["Probability"].round(2)

    return result_df[["Sign", "Probability"]]


def save_manual_input(active_signs):

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
    print("   Same-Matchday Zodiac Momentum Predictor")
    print("============================================\n")

    print("Enter zodiac signs that have already performed today.")
    print("Repeat signs if multiple players from same zodiac performed.")
    print("Example: Pisces,Pisces,Pisces,Cancer\n")

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

    save_manual_input(active_signs)


if __name__ == "__main__":
    main()