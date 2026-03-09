import pandas as pd

# load data
df = pd.read_csv("data/season_events_2023_moon.csv")
dob = pd.read_csv("data/player_dob_batch.csv")

# merge zodiac
df = df.merge(
    dob[["player", "Zodiac"]],
    on="player",
    how="left"
)

# only players who played
df = df[df["minutes"] > 0]

# compute each player's average rating
player_avg = df.groupby("player")["rating"].mean()

# map player averages back to dataset
df["player_avg"] = df["player"].map(player_avg)

# compute relative performance
df["relative_rating"] = df["rating"] - df["player_avg"]

# build moon × player sign matrix
matrix = df.groupby(["moon_sign","Zodiac"])["relative_rating"].mean()

# convert to table
matrix = matrix.unstack()

print(matrix.round(3))