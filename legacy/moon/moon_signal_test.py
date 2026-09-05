import pandas as pd

df = pd.read_csv("data/season_events_2023_moon.csv")
dob = pd.read_csv("data/player_dob_batch.csv")

df = df.merge(
    dob[["player","Zodiac"]],
    on="player",
    how="left"
)

# remove players who didn't play
df = df[df["minutes"] > 0]

df["moon_match"] = df["Zodiac"] == df["moon_sign"]

match_perf = df[df["moon_match"]]["rating"].mean()
non_match_perf = df[~df["moon_match"]]["rating"].mean()

print("Moon sign matches player sign:", match_perf)
print("Moon sign different:", non_match_perf)

print("\nNumber of matches:")
print(df["moon_match"].value_counts())