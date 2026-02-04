# src/main.py

import pandas as pd
from api_client import get_fixtures, get_fixture_events
from processing import load_players

# --------------------
# CONSTANTS
# --------------------
BIG_6 = {
    "Arsenal",
    "Chelsea",
    "Liverpool",
    "Manchester City",
    "Manchester United",
    "Tottenham"
}

# --------------------
# MAIN
# --------------------
def main():

    # Load astrology player data
    players_df = load_players("players/players.csv")
    player_names = set(players_df["Player"])

    print("Players loaded:")
    print(players_df.head(), "\n")

    # Fetch fixtures
    fixtures = get_fixtures()
    print(f"Total fixtures fetched: {len(fixtures)}")

    performed_rows = []

    # 🔒 LIMIT FIXTURES (increase later if stable)
    for fixture in fixtures[:25]:

        fixture_id = fixture["fixture"]["id"]
        match_date = fixture["fixture"]["date"]

        home = fixture["teams"]["home"]["name"]
        away = fixture["teams"]["away"]["name"]

        # Only Big 6 matches
        if home not in BIG_6 and away not in BIG_6:
            continue

        # Fetch events safely
        try:
            events = get_fixture_events(fixture_id)
        except Exception:
            print(f"Skipping fixture {fixture_id} due to connection issue")
            continue

        for event in events:
            if event["type"] == "Goal":

                scorer = event["player"]["name"]
                assister = event["assist"]["name"]

                if scorer in player_names:
                    performed_rows.append({
                        "fixture_id": fixture_id,
                        "date": match_date,
                        "player": scorer,
                        "action": "goal"
                    })

                if assister and assister in player_names:
                    performed_rows.append({
                        "fixture_id": fixture_id,
                        "date": match_date,
                        "player": assister,
                        "action": "assist"
                    })

    if not performed_rows:
        print("No performances collected.")
        return

    # --------------------
    # BUILD DATAFRAME
    # --------------------
    performed_df = pd.DataFrame(performed_rows)

    # Normalize to calendar day
    performed_df["match_day"] = pd.to_datetime(
        performed_df["date"]
    ).dt.date

    # Join astrology data
    merged_df = performed_df.merge(
        players_df,
        left_on="player",
        right_on="Player",
        how="inner"
    )

    # Save processed data
    merged_df.to_csv(
        "data/processed/big6_performances.csv",
        index=False
    )

    print("\nSaved data to data/processed/big6_performances.csv")

    # --------------------
    # SAME-DAY ZODIAC TEST
    # --------------------
    daily_zodiac_counts = (
        merged_df
        .groupby(["match_day", "Zodiac"])
        .size()
        .reset_index(name="performances")
    )

    daily_zodiac_counts["reinforced"] = (
        daily_zodiac_counts["performances"] >= 2
    )

    reinforcement_rate = (
        daily_zodiac_counts
        .groupby("Zodiac")["reinforced"]
        .mean()
        .sort_values(ascending=False)
    )

    print("\nSame-day zodiac reinforcement rate:")
    print(reinforcement_rate)


if __name__ == "__main__":
    main()
