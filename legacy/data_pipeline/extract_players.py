import pandas as pd

files = [
    "data/season_events_2023.csv",
    "data/season_events_2024.csv"
]

players = set()

for file in files:
    df = pd.read_csv(file)

    # Only players who actually performed
    performed_df = df[df["performed"] == 1]

    players.update(performed_df["player"].str.strip().str.lower())

players_df = pd.DataFrame(sorted(players), columns=["player"])

# Force birth_date column to string
players_df["birth_date"] = ""
players_df["birth_date"] = players_df["birth_date"].astype(str)

players_df.to_csv("data/player_dob_batch.csv", index=False)

print("Unique impact players extracted:", len(players_df))