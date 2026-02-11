# src/processing.py

import pandas as pd
from datetime import datetime


def load_players(path="players/players.csv"):
    df = pd.read_csv(path, encoding="latin1")

    # Standardize column names
    df = df.rename(columns={
        "Player": "player",
        "DOB": "birth_date"
    })

    # Normalize names for matching
    df["player"] = df["player"].str.strip().str.lower()

    # Extract surname for fallback matching
    df["surname"] = df["player"].apply(lambda x: x.split()[-1])

    return df


def calculate_zodiac(date_str):
    from datetime import datetime

    # Try multiple date formats safely
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            date = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue
    else:
        return None  # if no format works

    day = date.day
    month = date.month

    if (month == 3 and day >= 21) or (month == 4 and day <= 19):
        return "Aries"
    elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
        return "Taurus"
    elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
        return "Gemini"
    elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
        return "Cancer"
    elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return "Leo"
    elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return "Virgo"
    elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
        return "Libra"
    elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
        return "Scorpio"
    elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
        return "Sagittarius"
    elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
        return "Capricorn"
    elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
        return "Aquarius"
    else:
        return "Pisces"



def tag_players(events_df, players_df):
    events_df["player"] = events_df["player"].str.strip().str.lower()
    events_df["surname"] = events_df["player"].apply(lambda x: x.split()[-1])

    # First try full-name merge
    merged = events_df.merge(
        players_df[["player", "birth_date"]],
        on="player",
        how="left"
    )

    # For unmatched rows → try surname match
    unmatched = merged[merged["birth_date"].isna()]

    if not unmatched.empty:
        surname_merge = unmatched.drop(columns=["birth_date"]).merge(
            players_df[["surname", "birth_date"]],
            on="surname",
            how="left"
        )

        merged.loc[merged["birth_date"].isna(), "birth_date"] = surname_merge["birth_date"].values

    # Calculate zodiac
    merged["Zodiac"] = merged["birth_date"].apply(
        lambda x: calculate_zodiac(x) if pd.notna(x) else None
    )

    return merged
