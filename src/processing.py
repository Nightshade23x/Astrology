# src/processing.py

import pandas as pd

def load_players(path="players/players.csv"):
    return pd.read_csv(path, encoding="latin1")
