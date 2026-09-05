import pandas as pd
from processing import load_players, tag_players

path = "data/season_events.csv"

df = pd.read_csv(path)
players = load_players()

updated = tag_players(df, players)

updated.to_csv(path, index=False)

print("Retagging complete.")
