from fixtures_cache import fetch_and_store_fixtures, load_fixtures
from api_client import get_fixture_player_stats
from processing import load_players, tag_players
import pandas as pd
from pathlib import Path

# --------------------
# CONFIG
# --------------------
SEASON = 2025  # CHANGE HERE: 2024 or 2025
MAX_CALLS = 40

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def season_paths(season):
    return (
        DATA_DIR / f"season_events_{season}.csv",
        DATA_DIR / f"processed_fixtures_{season}.txt"
    )


def load_processed(processed_file):
    if not processed_file.exists():
        return set()
    return set(processed_file.read_text().splitlines())


def save_processed(processed_file, fixture_id):
    with open(processed_file, "a") as f:
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
    csv_path, processed_file = season_paths(SEASON)

    fetch_and_store_fixtures(seasons=[SEASON])
    fixtures = load_fixtures(SEASON)
    players = load_players()

    processed = load_processed(processed_file)
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
        print(f"Fetching PLAYER STATS for fixture {fixture_id}")

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

        save_processed(processed_file, fixture_id)

    if not all_events:
        print("No new fixtures processed")
        return

    new_df = pd.concat(all_events, ignore_index=True)

    if csv_path.exists():
        old_df = pd.read_csv(csv_path)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    final_df.to_csv(csv_path, index=False)
    print(f"Updated {csv_path.name}")


if __name__ == "__main__":
    main()
