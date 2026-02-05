from fixtures_cache import fetch_and_store_fixtures, load_fixtures
from api_client import get_fixture_player_stats
from processing import load_players, tag_players
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

PROCESSED_FILE = DATA_DIR / "processed_fixtures.txt"
CSV_PATH = DATA_DIR / "season_events.csv"

MAX_CALLS = 54   # use what you have left


def load_processed():
    if not PROCESSED_FILE.exists():
        return set()
    return set(PROCESSED_FILE.read_text().splitlines())


def save_processed(fixture_id):
    with open(PROCESSED_FILE, "a") as f:
        f.write(str(fixture_id) + "\n")


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
                "match_id": fixture_id,
                "date": date
            })

    return pd.DataFrame(rows)


def main():
    fetch_and_store_fixtures()
    fixtures = load_fixtures()
    players = load_players()

    processed = load_processed()
    all_events = []
    calls = 0

    for fx in fixtures:
        if fx["fixture"]["status"]["short"] != "FT":
            continue

        fixture_id = str(fx["fixture"]["id"])
        if fixture_id in processed:
            continue

        if calls >= MAX_CALLS:
            print("API limit reached for today")
            break

        date = fx["fixture"]["date"][:10]
        print("Fetching PLAYER STATS for fixture:", fixture_id)

        response = get_fixture_player_stats(fixture_id)
        calls += 1

        if not response:
            continue

        events = extract_players_from_stats(response, fixture_id, date)

        events["performed"] = (
            (events["goals"] > 0) |
            (events["assists"] > 0) |
            (events["rating"] >= 7.0)
        ).astype(int)

        tagged = tag_players(events, players)
        all_events.append(tagged)

        save_processed(fixture_id)

    if not all_events:
        print("No new fixtures processed")
        return

    new_df = pd.concat(all_events, ignore_index=True)

    if CSV_PATH.exists():
        old_df = pd.read_csv(CSV_PATH)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    final_df.to_csv(CSV_PATH, index=False)
    print("Updated season_events.csv")


if __name__ == "__main__":
    main()
