import pandas as pd

def load_players(path="players/players.csv"):
    """
    Load player zodiac data.
    """
    df = pd.read_csv(path, encoding="latin1")

    # Ensure Player column is string-safe
    df["Player"] = df["Player"].astype(str).str.lower().str.strip()

    return df


def tag_players(events_df: pd.DataFrame, players_df: pd.DataFrame) -> pd.DataFrame:
    """
    Safely attach zodiac info to events.
    """

    # Some API rows have NaN / floats in player column → fix permanently
    events_df["player"] = (
        events_df["player"]
        .astype(str)          # convert everything to string
        .str.lower()
        .str.strip()
    )

    merged = events_df.merge(
        players_df,
        left_on="player",
        right_on="Player",
        how="left"
    )

    return merged
