import pandas as pd
import requests
import time

HEADERS = {
    "User-Agent": "ZodiacProject/1.0"
}

def get_dob_from_wikidata(player_name):
    try:
        # Step 1: Search entity on Wikidata
        search_url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": player_name,
            "language": "en",
            "format": "json"
        }

        r = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
        data = r.json()

        if not data.get("search"):
            return None

        entity_id = data["search"][0]["id"]

        # Step 2: Fetch entity details
        entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"

        r2 = requests.get(entity_url, headers=HEADERS, timeout=10)
        entity_data = r2.json()

        claims = entity_data["entities"][entity_id]["claims"]

        # P569 = Date of Birth
        if "P569" in claims:
            dob_raw = claims["P569"][0]["mainsnak"]["datavalue"]["value"]["time"]
            # Format example: "+1997-11-26T00:00:00Z"
            dob_clean = dob_raw[1:11]  # Extract YYYY-MM-DD
            return dob_clean

    except Exception:
        return None

    return None


# IMPORTANT: force birth_date to string
df = pd.read_csv("data/player_dob_batch.csv", dtype={"birth_date": str})
df["birth_date"] = df["birth_date"].astype(str)

for i, row in df.iterrows():

    if pd.notna(row["birth_date"]) and row["birth_date"] != "" and row["birth_date"] != "nan":
        continue

    name = row["player"]
    print("Fetching:", name)

    dob = get_dob_from_wikidata(name)

    if dob:
        df.at[i, "birth_date"] = dob
        print("  Found:", dob)

        # Save immediately after each success
        df.to_csv("data/player_dob_batch.csv", index=False)

    time.sleep(0.5)

    

df.to_csv("data/player_dob_batch.csv", index=False)

print("DOB batch complete.")