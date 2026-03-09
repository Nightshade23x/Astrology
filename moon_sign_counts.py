import pandas as pd

# load datasets
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

# count matrix
count_matrix = df.groupby(["moon_sign", "Zodiac"]).size()

# convert to table
count_matrix = count_matrix.unstack()

print(count_matrix)