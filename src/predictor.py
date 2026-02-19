import pandas as pd
from analysis import multi_season_reliability
from coupling_analysis import get_cross_season_coupling

SEASONS = [2023, 2024]

RELIABILITY_WEIGHT = 0.5
COUPLING_WEIGHT = 0.3
SELF_WEIGHT = 0.2


def normalize_sign(sign):
    if not isinstance(sign, str):
        return None
    return sign.strip().capitalize()



def predict_next_signs(active_signs):
    active_signs = [
        normalize_sign(s)
        for s in active_signs
        if normalize_sign(s) is not None
    ]


    reliability_df = multi_season_reliability(SEASONS)
    reliability = reliability_df["Average"]

    coupling_df = get_cross_season_coupling(SEASONS)

    results = []

    for sign in reliability.index:

        base_score = reliability.get(sign, 0)

        # Coupling from OTHER active signs
        lifts = []

        for active in active_signs:
            if active == sign:
                continue

            match = coupling_df[
                (coupling_df["Trigger"] == active) &
                (coupling_df["Target"] == sign)
            ]

            if not match.empty:
                lifts.append(match["Avg_Lift"].values[0])

        coupling_score = sum(lifts) / len(lifts) if lifts else 1

        # Self-reinforcement
        if sign in active_signs:
            self_match = coupling_df[
                (coupling_df["Trigger"] == sign) &
                (coupling_df["Target"] == sign)
            ]

            if not self_match.empty:
                self_score = self_match["Avg_Lift"].values[0]
            else:
                self_score = reliability.get(sign, 0)
        else:
            self_score = 1

        final_score = (
            RELIABILITY_WEIGHT * base_score +
            COUPLING_WEIGHT * coupling_score +
            SELF_WEIGHT * self_score
        )

        results.append({
            "Sign": sign,
            "Reliability": round(base_score, 3),
            "Coupling": round(coupling_score, 3),
            "Self": round(self_score, 3),
            "Final_Score": round(final_score, 3)
        })

    result_df = pd.DataFrame(results)

    return result_df.sort_values("Final_Score", ascending=False)


def main():
    print("\nEnter zodiac signs that performed today.")
    print("Separate by comma (example: Virgo,Pisces,Cancer)\n")

    user_input = input("Active signs: ")
    active_signs = user_input.split(",")

    prediction = predict_next_signs(active_signs)

    print("\n===============================")
    print("Predicted Strongest Signs")
    print("===============================\n")

    print(prediction.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
