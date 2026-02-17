from fixtures_cache import fetch_and_store_fixtures, load_fixtures
from api_client import get_fixture_player_stats
from processing import load_players, tag_players
import pandas as pd
from pathlib import Path

# --------------------
# CONFIG
# --------------------
SEASON = 2023
MAX_CALLS = 20

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

CSV_PATH = DATA_DIR / f"season_events_{SEASON}.csv"



def extract_players_from_stats(fixture_response, fixture_id, date):
    rows = []

    for team in fixture_response:
        for p in team["players"]:
            stats = p["statistics"][0]

            rows.append({
                "player": p["player"]["name"],
                "goals": stats["goals"]["total"] or 0,
                "assists": stats["goals"]["assists"] or 0,
                "rating": float(stats["games"]["rating"]) if stats["games"]["rating"] else 0,
                "minutes": stats["games"]["minutes"] or 0,
                "match_id": str(fixture_id),
                "date": date
            })

    return pd.DataFrame(rows)


def main():
    # Fetch fixtures (only if not already cached)
    fetch_and_store_fixtures(seasons=[SEASON])
    fixtures = load_fixtures(SEASON)
    players = load_players()

    # Load existing CSV if exists
    if CSV_PATH.exists():
        existing_df = pd.read_csv(CSV_PATH)
        processed_ids = set(existing_df["match_id"].astype(str))
    else:
        existing_df = None
        processed_ids = set()

    all_events = []
    calls = 0

    for fx in fixtures:
        if fx["fixture"]["status"]["short"] != "FT":
            continue

        fixture_id = str(fx["fixture"]["id"])

        # Skip fixtures already stored
        if fixture_id in processed_ids:
            continue

        if calls >= MAX_CALLS:
            print("API limit reached for today")
            break

        date = fx["fixture"]["date"][:10]
        print(f"Fetching PLAYER STATS for fixture {fixture_id}")

        response = get_fixture_player_stats(fixture_id)
        calls += 1

        if not response:
            continue

        events = extract_players_from_stats(response, fixture_id, date)

        # Performance logic
        events["performed"] = (
            (events["goals"] > 0) |
            (events["assists"] > 0) |
            (events["rating"] >= 7.0)
        ).astype(int)

        tagged = tag_players(events, players)
        all_events.append(tagged)

    if not all_events:
        print("No new fixtures processed")
        return

    new_df = pd.concat(all_events, ignore_index=True)

    if existing_df is not None:
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    final_df.to_csv(CSV_PATH, index=False)
    print(f"Updated {CSV_PATH.name}")


if __name__ == "__main__":
    main()
