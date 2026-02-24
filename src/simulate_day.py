import pandas as pd

from predictor.day_state import DayState
from predictor.predictor import ZodiacPredictor
from predictor.analysis import zodiac_reliability, same_day_clustering


DATA_PATH = "data/season_events_2024.csv"

CONFIDENCE_MULTIPLIER = 1.2   # try 1.1–1.4 later


def simulate_day_predictions():
    # --------------------
    # LOAD DATA
    # --------------------
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])

    # --------------------
    # BASELINE STATS
    # --------------------
    reliability = zodiac_reliability(df)
    clustering = same_day_clustering(df)

    predictor = ZodiacPredictor(
        reliability=reliability,
        clustering=clustering,
        activation_power=1.0
    )

    mean_baseline = reliability.mean()

    # --------------------
    # GROUP BY DAY
    # --------------------
    grouped_days = df.groupby("date")

    total_predictions = 0
    correct_predictions = 0
    skipped_no_signal = 0
    skipped_low_confidence = 0

    # --------------------
    # SIMULATION LOOP
    # --------------------
    for date, day_df in grouped_days:
        print(f"\n=== Simulating {date.date()} ===")

        day_state = DayState(date=str(date.date()))
        day_df = day_df.sort_values("match_id")

        matches = day_df.groupby("match_id")

        for match_id, match_df in matches:
            # --------------------
            # PREDICT BEFORE MATCH
            # --------------------
            if len(day_state.activations) > 0:
                zodiac_scores = predictor.top_zodiacs(day_state, n=2)
                top_score = zodiac_scores.iloc[0]["score"]

                # Confidence gate
                if top_score < CONFIDENCE_MULTIPLIER * mean_baseline:
                    skipped_low_confidence += 1
                else:
                    predicted_signs = set(zodiac_scores["Zodiac"])

                    actual_performers = set(
                        match_df[
                            (match_df["performed"] == 1) &
                            (match_df["Zodiac"].notna())
                        ]["Zodiac"]
                    )


                    # Skip matches with no performers
                    if len(actual_performers) == 0:
                        skipped_no_signal += 1
                    else:
                        total_predictions += 1
                        hit = len(predicted_signs & actual_performers) > 0

                        if hit:
                            correct_predictions += 1

                        print(f"\nMatch {match_id}")
                        print("Predicted:", list(predicted_signs))
                        print("Actual:", list(actual_performers))
                        print("Hit:", hit)

            # --------------------
            # UPDATE DAY STATE
            # --------------------
            day_state.update_from_match(match_df)

    # --------------------
    # FINAL RESULTS
    # --------------------
    accuracy = (
        correct_predictions / total_predictions
        if total_predictions > 0
        else 0
    )

    print("\n==============================")
    print("Simulation complete")
    print(f"Predictions evaluated: {total_predictions}")
    print(f"Correct predictions: {correct_predictions}")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"Skipped (no performers): {skipped_no_signal}")
    print(f"Skipped (low confidence): {skipped_low_confidence}")
    print("==============================\n")


if __name__ == "__main__":
    simulate_day_predictions()
