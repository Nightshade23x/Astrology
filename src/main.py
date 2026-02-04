# src/main.py

from api_client import get_fixtures, get_fixture_events
from processing import load_players

def main():
    players_df = load_players("players/players.csv")

    fixtures = get_fixtures()

    performed_rows = []

    # ⚠️ Start small: only first 5 fixtures
    for fixture in fixtures[:5]:
        fixture_id = fixture["fixture"]["id"]
        match_date = fixture["fixture"]["date"]
        home = fixture["teams"]["home"]["name"]
        away = fixture["teams"]["away"]["name"]

        events = get_fixture_events(fixture_id)

        for event in events:
            if event["type"] == "Goal":
                scorer = event["player"]["name"]
                assister = event["assist"]["name"]

                performed_rows.append({
                    "fixture_id": fixture_id,
                    "date": match_date,
                    "team_home": home,
                    "team_away": away,
                    "player": scorer,
                    "action": "goal"
                })

                if assister:
                    performed_rows.append({
                        "fixture_id": fixture_id,
                        "date": match_date,
                        "team_home": home,
                        "team_away": away,
                        "player": assister,
                        "action": "assist"
                    })

    print("\nPlayers who performed (sample):")
    for row in performed_rows[:10]:
        print(row)

if __name__ == "__main__":
    main()
