import pandas as pd

# load data
df = pd.read_csv("data/season_events_2023_moon.csv")
dob = pd.read_csv("data/player_dob_batch.csv")

# merge zodiac signs
df = df.merge(
    dob[["player","Zodiac"]],
    on="player",
    how="left"
)

# keep only players who actually played
df = df[df["minutes"] > 0]

# build matrix
matrix = df.groupby(["moon_sign","Zodiac"])["rating"].mean()

# convert to table format
matrix = matrix.unstack()

print(matrix.round(3))