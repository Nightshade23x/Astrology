import pandas as pd
import numpy as np
from predictor.predictor import predict_same_day

# -----------------------------
# LOAD DATA
# -----------------------------

train = pd.read_csv("data/season_events_2023_moon.csv")
test = pd.read_csv("data/season_events_2024_moon.csv")
dob = pd.read_csv("data/player_dob_batch.csv")

# attach zodiac signs
train = train.merge(dob[["player","Zodiac"]], on="player", how="left")
test = test.merge(dob[["player","Zodiac"]], on="player", how="left")

# keep players who played
train = train[train["minutes"] > 0]
test = test[test["minutes"] > 0]

# -----------------------------
# BUILD MOON MULTIPLIERS (2023)
# -----------------------------

player_avg = train.groupby("Zodiac")["rating"].mean()

moon_avg = train.groupby(["moon_sign","Zodiac"])["rating"].mean()

moon_multiplier = (moon_avg / player_avg).unstack().fillna(1.0)

# -----------------------------
# EVALUATION
# -----------------------------

moon_correct = 0
model_correct = 0
model_moon_correct = 0
total_matches = 0

matches = test["match_id"].unique()

for match in matches:

    match_df = test[test["match_id"] == match]

    moon = match_df["moon_sign"].iloc[0]

    performers = match_df[match_df["performed"] == 1]["Zodiac"].unique()

    if len(performers) == 0:
        continue

    # -----------------------------
    # MOON ONLY PREDICTION
    # -----------------------------

    if moon in moon_multiplier.index:
        moon_scores = moon_multiplier.loc[moon]
        moon_top3 = moon_scores.sort_values(ascending=False).head(3).index.tolist()
    else:
        moon_top3 = []

    if any(sign in performers for sign in moon_top3):
        moon_correct += 1

    # -----------------------------
    # MODEL PREDICTION
    # -----------------------------

    active_signs = match_df[match_df["performed"] == 1]["Zodiac"].tolist()

    model_pred = predict_same_day(active_signs)

    model_top3 = model_pred.head(3)["Sign"].tolist()

    if any(sign in performers for sign in model_top3):
        model_correct += 1

    # -----------------------------
    # MODEL + MOON
    # -----------------------------

    model_pred_moon = model_pred.copy()

    if moon in moon_multiplier.index:

        for i, row in model_pred_moon.iterrows():

            sign = row["Sign"]

            if sign in moon_multiplier.columns:

                multiplier = moon_multiplier.loc[moon, sign]

                model_pred_moon.loc[i,"Probability"] *= multiplier

    model_pred_moon = model_pred_moon.sort_values("Probability", ascending=False)

    model_moon_top3 = model_pred_moon.head(3)["Sign"].tolist()

    if any(sign in performers for sign in model_moon_top3):
        model_moon_correct += 1

    total_matches += 1


# -----------------------------
# RESULTS
# -----------------------------

print("\n==============================")
print("Moon Signal Validation")
print("==============================\n")

print("Total matches tested:", total_matches)

print("\nMoon Only Accuracy:",
      round(moon_correct / total_matches, 3))

print("Predictor Accuracy:",
      round(model_correct / total_matches, 3))

print("Predictor + Moon Accuracy:",
      round(model_moon_correct / total_matches, 3))