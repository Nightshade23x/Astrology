# src/api_client.py

import os
import time
import requests
import urllib3
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings (Windows / uni network issue)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

def create_session():
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session

session = create_session()


def get_fixtures(league_id=39, season=2024):
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_id,
        "season": season
    }

    r = session.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30,
        verify=False
    )
    r.raise_for_status()
    return r.json()["response"]


def get_fixture_events(fixture_id):
    url = f"{BASE_URL}/fixtures/events"
    params = {"fixture": fixture_id}

    r = session.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30,
        verify=False
    )
    r.raise_for_status()

    # Rate limiting protection
    time.sleep(1.2)

    return r.json()["response"]

def get_fixture_player_stats(fixture_id):
    url = f"{BASE_URL}/fixtures/players"
    params = {"fixture": fixture_id}

    r = session.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30,
        verify=False
    )
    r.raise_for_status()

    time.sleep(1.2)  # stay safe with rate limits

    return r.json()["response"]
