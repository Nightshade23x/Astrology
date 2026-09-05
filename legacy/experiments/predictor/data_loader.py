import pandas as pd
def load_data(season):
    path = f"data/season_events_{season}.csv"
    df = pd.read_csv(path)
    return df