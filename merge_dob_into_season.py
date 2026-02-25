import pandas as pd

dob_df = pd.read_csv("data/player_dob_batch.csv")

files = [
    "data/season_events_2023.csv",
    "data/season_events_2024.csv"
]

for file in files:
    df = pd.read_csv(file)

    df = df.merge(
        dob_df,
        on="player",
        how="left"
    )

    df.to_csv(file, index=False)

    print(f"Updated {file}")