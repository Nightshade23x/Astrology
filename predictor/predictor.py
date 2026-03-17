import numpy as np
import pandas as pd
from collections import Counter
from analysis import multi_season_reliability
from coupling import get_cross_season_coupling
from datetime import datetime
from moon import get_moon_sign
import os


SEASONS = [2023, 2024]

DEBUG = False


# ---------------------------------------------------
# NORMALIZE SIGN INPUT
# ---------------------------------------------------

def normalize_sign(sign):

    if not isinstance(sign, str):
        return None

    return sign.strip().capitalize()


# ---------------------------------------------------
# COMPUTE MOON BOOST TABLE
# ---------------------------------------------------

def compute_moon_boosts():

    base_dir = os.path.dirname(os.path.dirname(__file__))

    df1 = pd.read_csv(os.path.join(base_dir, "data", "season_events_2023.csv"))
    df2 = pd.read_csv(os.path.join(base_dir, "data", "season_events_2024.csv"))
    dob = pd.read_csv(os.path.join(base_dir, "data", "player_dob_batch.csv"))

    df = pd.concat([df1, df2], ignore_index=True)

    df = df.merge(dob[["player", "Zodiac"]], on="player", how="left")

    df = df[df["minutes"] > 0]

    df["moon_sign"] = df["date"].apply(
        lambda d: get_moon_sign(pd.to_datetime(d, dayfirst=True).strftime("%Y/%m/%d"))
    )

    baseline = df.groupby("Zodiac")["rating"].mean()

    moon_avg = df.groupby(["moon_sign", "Zodiac"])["rating"].mean()

    boost = (moon_avg / baseline).unstack().fillna(1.0)

    return boost


MOON_BOOST_TABLE = compute_moon_boosts()


# ---------------------------------------------------
# MAIN PREDICTION FUNCTION
# ---------------------------------------------------

def predict_same_day(active_signs):

    sign_counts = Counter(active_signs)

    reliability_df = multi_season_reliability(SEASONS)
    base_rates = reliability_df["Average"]

    coupling_df = get_cross_season_coupling(SEASONS)
    moon_boost_table = MOON_BOOST_TABLE

    today = datetime.now().strftime("%Y/%m/%d")
    moon_sign = get_moon_sign(today)

    if DEBUG:
        print("\nBaseline reliability:")
        print(base_rates.sort_values(ascending=False))


    results = []

    for sign in base_rates.index:

        log_prob = 0
        debug_components = {}

        # ---------------------------------------------------
        # 1. INPUT PRIOR (MOST IMPORTANT FIX)
        # ---------------------------------------------------

        if sign in sign_counts:
            prior = 0.8 * sign_counts[sign]   # strong influence
            log_prob += prior

            if DEBUG:
                debug_components["prior"] = prior


        # ---------------------------------------------------
        # 2. BASELINE (WEAKENED)
        # ---------------------------------------------------

        mean_base = base_rates.mean()

        base_prob = base_rates.get(sign, 0) / mean_base

        baseline_effect = np.log(base_prob + 1e-9) * 0.3   # reduced weight

        log_prob += baseline_effect

        if DEBUG:
            debug_components["baseline"] = baseline_effect


        # ---------------------------------------------------
        # 3. COUPLING (CONTROLLED BUT USEFUL)
        # ---------------------------------------------------

        for active_sign, count in sign_counts.items():

            match = coupling_df[
                (coupling_df["Trigger"] == active_sign) &
                (coupling_df["Target"] == sign)
            ]

            if not match.empty:

                presence_lift = match["Presence_Lift"].values[0]

                if presence_lift > 0:

                    effect = 0.5 * count * np.log(presence_lift)

                    effect = np.clip(effect, -0.5, 0.5)

                    log_prob += effect

                    if DEBUG:
                        debug_components[f"coupling_{active_sign}"] = effect


        # ---------------------------------------------------
        # 4. MOON BOOST (SMALL)
        # ---------------------------------------------------

        if moon_sign in moon_boost_table.index and sign in moon_boost_table.columns:

            multiplier = moon_boost_table.loc[moon_sign, sign]
            multiplier = np.clip(multiplier, 0.9, 1.1)

            moon_effect = np.log(multiplier)

            log_prob += moon_effect

            if DEBUG:
                debug_components["moon"] = moon_effect


        if DEBUG:
            print(f"\n{sign} breakdown:", debug_components)


        results.append({
            "Sign": sign,
            "Log_Prob": log_prob
        })


    result_df = pd.DataFrame(results)

    # ---------------------------------------------------
    # SOFTMAX
    # ---------------------------------------------------

    result_df["Raw"] = np.exp(result_df["Log_Prob"])

    total = result_df["Raw"].sum()

    result_df["Probability"] = (result_df["Raw"] / total) * 100

    result_df = result_df.sort_values("Probability", ascending=False)

    result_df["Probability"] = result_df["Probability"].round(2)

    return result_df[["Sign", "Probability"]]


# ---------------------------------------------------
# SAVE INPUT
# ---------------------------------------------------

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


# ---------------------------------------------------
# CLI
# ---------------------------------------------------

def main():

    print("\n============================================")
    print("   Same-Matchday Zodiac Momentum Predictor")
    print("============================================\n")

    print("Enter zodiac signs that have already performed today.")
    print("Example: Pisces,Pisces,Cancer\n")

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