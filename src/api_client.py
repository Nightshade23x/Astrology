# src/api_client.py

import os
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

def get_fixtures(league_id=39, season=2024):
    url = f"{BASE_URL}/fixtures"
    params = {"league": league_id, "season": season}
    r = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=20,
        verify=False   # 👈 KEY LINE
    )
    r.raise_for_status()
    return r.json()["response"]

def get_fixture_events(fixture_id):
    url = f"{BASE_URL}/fixtures/events"
    params = {"fixture": fixture_id}
    r = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=20,
        verify=False   # 👈 KEY LINE
    )
    r.raise_for_status()
    return r.json()["response"]
