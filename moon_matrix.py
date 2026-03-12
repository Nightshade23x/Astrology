import pandas as pd

# load both seasons
df1 = pd.read_csv("data/season_events_2023_moon.csv")   # 2023 season
df2 = pd.read_csv("data/season_events_2024_moon.csv")   # 2024 season

# combine seasons
df = pd.concat([df1, df2], ignore_index=True)

# load player zodiac data
dob = pd.read_csv("data/player_dob_batch.csv")

# merge zodiac signs
df = df.merge(
    dob[["player", "Zodiac"]],   # attach zodiac sign to each player
    on="player",
    how="left"
)

# keep only players who actually played
df = df[df["minutes"] > 0]

# build moon vs player zodiac matrix
matrix = df.groupby(["moon_sign", "Zodiac"])["rating"].mean()

# convert to table format
matrix = matrix.unstack()

# round values for readability
matrix = matrix.round(3)

# print matrix
print(matrix)

# save matrix for later analysis
matrix.to_csv("data/moon_player_matrix.csv")