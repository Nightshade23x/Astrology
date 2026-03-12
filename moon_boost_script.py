import pandas as pd

# -----------------------------
# LOAD DATA
# -----------------------------

df1 = pd.read_csv("data/season_events_2023_moon.csv")
df2 = pd.read_csv("data/season_events_2024_moon.csv")
dob = pd.read_csv("data/player_dob_batch.csv")

# combine seasons
df = pd.concat([df1, df2], ignore_index=True)

# attach zodiac signs
df = df.merge(dob[["player","Zodiac"]], on="player", how="left")

# keep players who played
df = df[df["minutes"] > 0]

# -----------------------------
# BASELINE PLAYER PERFORMANCE
# -----------------------------

baseline = df.groupby("Zodiac")["rating"].mean()

# -----------------------------
# MOON + SIGN PERFORMANCE
# -----------------------------

moon_avg = df.groupby(["moon_sign","Zodiac"])["rating"].mean()

boost = (moon_avg / baseline).unstack()

# -----------------------------
# FIND STRONG BOOSTS
# -----------------------------

print("\nStrong Moon Boosts:\n")

for moon in boost.index:
    for sign in boost.columns:

        value = boost.loc[moon, sign]

        if value > 1.03:   # >3% boost threshold
            print(f"{sign} boosted under {moon} moon → {round(value,3)}")

print("\nStrong Suppressions:\n")

for moon in boost.index:
    for sign in boost.columns:

        value = boost.loc[moon, sign]

        if value < 0.97:   # >3% suppression
            print(f"{sign} suppressed under {moon} moon → {round(value,3)}")