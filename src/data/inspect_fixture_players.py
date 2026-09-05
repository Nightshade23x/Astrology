import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("API_FOOTBALL_KEY")

BASE_URL = "https://v3.football.api-sports.io"
FIXTURE_ID = 1208021


def main():
    if not API_KEY:
        raise RuntimeError("API_FOOTBALL_KEY not found.")

    url = f"{BASE_URL}/fixtures/players"

    headers = {
        "x-apisports-key": API_KEY
    }

    params = {
        "fixture": FIXTURE_ID
    }

    print(f"Fetching player statistics for fixture {FIXTURE_ID}...")

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("errors"):
        raise RuntimeError(
            f"API returned errors: {payload['errors']}"
        )

    print(f"Teams returned: {len(payload.get('response', []))}")

    output_path = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / f"fixture_players_{FIXTURE_ID}.json"
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved raw response to:\n{output_path}")

    # -------------------------------------------------
    # PRINT A SMALL SUMMARY
    # -------------------------------------------------

    for team in payload.get("response", []):
        team_info = team.get("team", {})

        print("\n" + "=" * 60)
        print(
            f"{team_info.get('name')} "
            f"(team_id={team_info.get('id')})"
        )
        print("=" * 60)

        players = team.get("players", [])

        print(f"Players returned: {len(players)}")

        for entry in players[:3]:

            player = entry.get("player", {})
            statistics = entry.get("statistics", [])

            print("\nPlayer:")
            print(
                f"  {player.get('name')} "
                f"(player_id={player.get('id')})"
            )

            if statistics:
                print(
                    json.dumps(
                        statistics[0],
                        indent=2,
                        ensure_ascii=False
                    )
                )


if __name__ == "__main__":
    main()