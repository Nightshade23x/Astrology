import pandas as pd
import requests
import time
import re

HEADERS = {
    "User-Agent": "ZodiacProject/1.0 (contact@example.com)"
}

def get_dob_from_wikipedia(player_name):
    try:
        # Direct page summary endpoint
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{player_name.replace(' ', '_')}"
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()

        # Try to extract birth date from description
        extract = data.get("extract", "")

        # Pattern like: born 11 August 1995
        match = re.search(r"born\s+(\d{1,2}\s\w+\s\d{4})", extract, re.IGNORECASE)

        if match:
            return match.group(1)

    except Exception:
        return None

    return None


df = pd.read_csv("data/player_dob_batch.csv")

for i, row in df.iterrows():

    if pd.notna(row["birth_date"]) and row["birth_date"] != "":
        continue

    name = row["player"]
    print("Fetching:", name)

    dob = get_dob_from_wikipedia(name)

    if dob:
        df.at[i, "birth_date"] = dob

    time.sleep(0.8)  # lighter delay

    # Save progress every 25 players
    if i % 25 == 0:
        df.to_csv("data/player_dob_batch.csv", index=False)

df.to_csv("data/player_dob_batch.csv", index=False)

print("DOB batch complete.")