import pandas as pd
from analysis import multi_season_reliability
from coupling_analysis import get_cross_season_coupling

# --------------------
# CONFIG
# --------------------
SEASONS = [2023, 2024]
RELIABILITY_WEIGHT = 0.6
COUPLING_WEIGHT = 0.4


def predict_next_signs(active_signs):
    # Load reliability
    reliability_df = multi_season_reliability(SEASONS)
    reliability = reliability_df["Average"]

    # Load coupling matrix
    coupling_df = get_cross_season_coupling(SEASONS)

    results = []

    for sign in reliability.index:
        # Skip already active signs
        if sign in active_signs:
            continue

        # Base reliability
        base_score = reliability.get(sign, 0)

        # Coupling score from active signs
        lifts = []

        for active in active_signs:
            match = coupling_df[
                (coupling_df["Trigger"] == active) &
                (coupling_df["Target"] == sign)
            ]

            if not match.empty:
                lifts.append(match["Avg_Lift"].values[0])

        coupling_score = sum(lifts) / len(lifts) if lifts else 1

        final_score = (
            RELIABILITY_WEIGHT * base_score +
            COUPLING_WEIGHT * coupling_score
        )

        results.append({
            "Sign": sign,
            "Reliability": round(base_score, 3),
            "Coupling": round(coupling_score, 3),
            "Final_Score": round(final_score, 3)
        })

    result_df = pd.DataFrame(results)

    return result_df.sort_values("Final_Score", ascending=False)


def main():
    print("\nEnter zodiac signs that performed today.")
    print("Separate by comma (example: Virgo,Pisces,Cancer)\n")

    user_input = input("Active signs: ")

    active_signs = [s.strip() for s in user_input.split(",")]

    prediction = predict_next_signs(active_signs)

    print("\n===============================")
    print("Predicted Next Best Signs")
    print("===============================\n")

    print(prediction.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
