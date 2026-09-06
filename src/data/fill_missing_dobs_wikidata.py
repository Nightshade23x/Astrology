import argparse
import json
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
RAW_WIKIDATA_DIR = PROJECT_ROOT / "data" / "raw" / "wikidata"

REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
RAW_WIKIDATA_DIR.mkdir(parents=True, exist_ok=True)

PLAYERS_PATH = REFERENCE_DIR / "players.csv"
LOOKUP_LOG_PATH = REFERENCE_DIR / "wikidata_lookup_log.csv"


# ---------------------------------------------------------
# WIKIDATA CONFIG
# ---------------------------------------------------------

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "StarsVsStatsThesis/1.0 "
        "(Bachelor's thesis football data project)"
    )
}


def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)

    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retries)

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


SESSION = create_session()


# ---------------------------------------------------------
# NAME NORMALISATION
# ---------------------------------------------------------

def normalize_name(value):
    if value is None:
        return ""

    value = str(value).strip().lower()

    # Remove accents:
    # André -> andre
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    # Keep only letters/numbers/spaces
    cleaned = []

    for char in value:
        if char.isalnum():
            cleaned.append(char)
        else:
            cleaned.append(" ")

    return " ".join(
        "".join(cleaned).split()
    )


def name_similarity(name_a, name_b):
    a = normalize_name(name_a)
    b = normalize_name(name_b)

    if not a or not b:
        return 0

    if a == b:
        return 100

    # Allow cases such as:
    # Jaden Philogene-Bidace -> Jaden Philogene
    tokens_a = a.split()
    tokens_b = b.split()

    if (
        len(tokens_a) >= 2
        and len(tokens_b) >= 2
        and (a in b or b in a)
    ):
        return 94

    ratio = SequenceMatcher(
        None,
        a,
        b,
    ).ratio()

    return round(ratio * 100)


# ---------------------------------------------------------
# FOOTBALL CHECK
# ---------------------------------------------------------

def football_description(description):
    if not description:
        return False

    description = description.lower()

    football_terms = [
        "footballer",
        "football player",
        "association football",
        "soccer player",
    ]

    return any(
        term in description
        for term in football_terms
    )


# ---------------------------------------------------------
# SEARCH WIKIDATA
# ---------------------------------------------------------

def search_wikidata(player_name):
    params = {
        "action": "wbsearchentities",
        "search": player_name,
        "language": "en",
        "format": "json",
        "limit": 10,
        "type": "item",
    }

    response = SESSION.get(
        WIKIDATA_API,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------
# FETCH ENTITY
# ---------------------------------------------------------

def fetch_entity(qid):
    params = {
        "action": "wbgetentities",
        "ids": qid,
        "props": "claims|labels|descriptions",
        "languages": "en",
        "format": "json",
    }

    response = SESSION.get(
        WIKIDATA_API,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    return (
        payload
        .get("entities", {})
        .get(qid, {})
    )


# ---------------------------------------------------------
# DOB EXTRACTION
# ---------------------------------------------------------

def extract_birth_date(entity):
    claims = entity.get("claims", {})

    birth_claims = claims.get("P569", [])

    if not birth_claims:
        return None, "no_birth_date"

    for claim in birth_claims:
        mainsnak = claim.get(
            "mainsnak",
            {}
        )

        datavalue = mainsnak.get(
            "datavalue"
        )

        if not datavalue:
            continue

        value = datavalue.get(
            "value",
            {}
        )

        time_value = value.get("time")
        precision = value.get("precision")

        if not time_value:
            continue

        # For zodiac we require the exact day.
        # Wikidata precision 11 = day precision.
        if precision is None or precision < 11:
            return None, "insufficient_date_precision"

        try:
            # Example:
            # +1997-05-10T00:00:00Z
            date_text = (
                time_value
                .lstrip("+")
                .split("T")[0]
            )

            parsed = pd.to_datetime(
                date_text,
                errors="coerce",
            )

            if pd.isna(parsed):
                continue

            return (
                parsed.strftime("%Y-%m-%d"),
                "ok",
            )

        except Exception:
            continue

    return None, "invalid_birth_date"


# ---------------------------------------------------------
# ZODIAC
# ---------------------------------------------------------

def zodiac_from_date(date_value):
    if pd.isna(date_value):
        return None

    date = pd.to_datetime(
        date_value,
        errors="coerce",
    )

    if pd.isna(date):
        return None

    month = date.month
    day = date.day

    if (
        (month == 3 and day >= 21)
        or
        (month == 4 and day <= 19)
    ):
        return "Aries"

    if (
        (month == 4 and day >= 20)
        or
        (month == 5 and day <= 20)
    ):
        return "Taurus"

    if (
        (month == 5 and day >= 21)
        or
        (month == 6 and day <= 20)
    ):
        return "Gemini"

    if (
        (month == 6 and day >= 21)
        or
        (month == 7 and day <= 22)
    ):
        return "Cancer"

    if (
        (month == 7 and day >= 23)
        or
        (month == 8 and day <= 22)
    ):
        return "Leo"

    if (
        (month == 8 and day >= 23)
        or
        (month == 9 and day <= 22)
    ):
        return "Virgo"

    if (
        (month == 9 and day >= 23)
        or
        (month == 10 and day <= 22)
    ):
        return "Libra"

    if (
        (month == 10 and day >= 23)
        or
        (month == 11 and day <= 21)
    ):
        return "Scorpio"

    if (
        (month == 11 and day >= 22)
        or
        (month == 12 and day <= 21)
    ):
        return "Sagittarius"

    if (
        (month == 12 and day >= 22)
        or
        (month == 1 and day <= 19)
    ):
        return "Capricorn"

    if (
        (month == 1 and day >= 20)
        or
        (month == 2 and day <= 18)
    ):
        return "Aquarius"

    return "Pisces"


# ---------------------------------------------------------
# CACHE
# ---------------------------------------------------------

def cache_path(player_id):
    return (
        RAW_WIKIDATA_DIR
        / f"player_{int(player_id)}.json"
    )


def load_cache(player_id):
    path = cache_path(player_id)

    if not path.exists():
        return None

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_cache(player_id, data):
    path = cache_path(player_id)

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ---------------------------------------------------------
# CHOOSE CANDIDATE
# ---------------------------------------------------------

def choose_candidate(
    player_name,
    search_payload,
):
    results = search_payload.get(
        "search",
        [],
    )

    candidates = []

    for result in results:
        label = result.get(
            "label",
            ""
        )

        description = result.get(
            "description",
            ""
        )

        if not football_description(
            description
        ):
            continue

        similarity = name_similarity(
            player_name,
            label,
        )

        if similarity < 90:
            continue

        candidates.append(
            {
                "qid": result.get("id"),
                "label": label,
                "description": description,
                "similarity": similarity,
            }
        )

    candidates = sorted(
        candidates,
        key=lambda x: x["similarity"],
        reverse=True,
    )

    if not candidates:
        return None, "no_confident_football_candidate", []

    # Single-word names such as "Beto" or "André"
    # are too risky to auto-match.
    if len(normalize_name(player_name).split()) < 2:
        return None, "single_name_manual_review", candidates

    top = candidates[0]

    if len(candidates) == 1:
        return top, "candidate_selected", candidates

    second = candidates[1]

    # Require the best result to be clearly better.
    if (
        top["similarity"] >= 95
        and
        top["similarity"]
        - second["similarity"] >= 8
    ):
        return top, "candidate_selected", candidates

    return None, "ambiguous_candidates", candidates


# ---------------------------------------------------------
# PROCESS ONE PLAYER
# ---------------------------------------------------------

def resolve_player(player_id, player_name):
    cached = load_cache(
        player_id
    )

    if cached is None:
        search_payload = search_wikidata(
            player_name
        )

        cached = {
            "player_id": int(player_id),
            "player_name": player_name,
            "search": search_payload,
        }

        save_cache(
            player_id,
            cached,
        )

        time.sleep(0.7)

    else:
        search_payload = cached["search"]

    candidate, status, candidates = choose_candidate(
        player_name,
        search_payload,
    )

    if candidate is None:
        return {
            "player_id": int(player_id),
            "player_name": player_name,
            "status": status,
            "wikidata_id": None,
            "wikidata_label": None,
            "birth_date": None,
            "candidate_count": len(candidates),
        }

    qid = candidate["qid"]

    if cached.get("entity") is None:
        entity = fetch_entity(
            qid
        )

        cached["entity"] = entity
        cached["selected_qid"] = qid

        save_cache(
            player_id,
            cached,
        )

        time.sleep(0.7)

    else:
        entity = cached["entity"]

    birth_date, dob_status = extract_birth_date(
        entity
    )

    if dob_status != "ok":
        return {
            "player_id": int(player_id),
            "player_name": player_name,
            "status": dob_status,
            "wikidata_id": qid,
            "wikidata_label": candidate["label"],
            "birth_date": None,
            "candidate_count": len(candidates),
        }

    return {
        "player_id": int(player_id),
        "player_name": player_name,
        "status": "matched",
        "wikidata_id": qid,
        "wikidata_label": candidate["label"],
        "birth_date": birth_date,
        "candidate_count": len(candidates),
    }


# ---------------------------------------------------------
# SAVE LOOKUP LOG
# ---------------------------------------------------------

def save_lookup_log(new_results):
    new_df = pd.DataFrame(
        new_results
    )

    if LOOKUP_LOG_PATH.exists():
        old_df = pd.read_csv(
            LOOKUP_LOG_PATH
        )

        combined = pd.concat(
            [old_df, new_df],
            ignore_index=True,
        )

        combined = (
            combined
            .drop_duplicates(
                subset=["player_id"],
                keep="last",
            )
        )

    else:
        combined = new_df

    combined = combined.sort_values(
        "player_id"
    )

    combined.to_csv(
        LOOKUP_LOG_PATH,
        index=False,
        encoding="utf-8",
    )


# ---------------------------------------------------------
# UPDATE PLAYERS.CSV
# ---------------------------------------------------------

def update_players(
    players,
    results,
):
    result_df = pd.DataFrame(
        results
    )

    matched = result_df[
        result_df["status"] == "matched"
    ].copy()

    if matched.empty:
        return players

    lookup = matched.set_index(
        "player_id"
    )

    for index, row in players.iterrows():
        player_id = row["player_id"]

        if player_id not in lookup.index:
            continue

        # Never overwrite an existing DOB
        if pd.notna(
            row.get("birth_date")
        ):
            continue

        info = lookup.loc[
            player_id
        ]

        birth_date = info[
            "birth_date"
        ]

        qid = info[
            "wikidata_id"
        ]

        players.at[
            index,
            "birth_date"
        ] = birth_date

        players.at[
            index,
            "zodiac"
        ] = zodiac_from_date(
            birth_date
        )

        players.at[
            index,
            "dob_source"
        ] = f"Wikidata:{qid}"

        # Automatically matched,
        # but not independently verified.
        players.at[
            index,
            "dob_verified"
        ] = False

    return players


# ---------------------------------------------------------
# MAIN COLLECTION
# ---------------------------------------------------------

def process_missing(limit):
    players = pd.read_csv(
        PLAYERS_PATH
    )

    missing = players[
        players["birth_date"].isna()
    ].copy()

    # Prioritise players who actually appear most often.
    missing = missing.sort_values(
        "appearances",
        ascending=False,
    )

    if limit is not None:
        missing = missing.head(
            limit
        )

    print(
        f"Players currently missing DOB: "
        f"{players['birth_date'].isna().sum()}"
    )

    print(
        f"Players to process this run: "
        f"{len(missing)}"
    )

    results = []

    for number, (_, row) in enumerate(
        missing.iterrows(),
        start=1,
    ):
        player_id = int(
            row["player_id"]
        )

        player_name = row[
            "player_name"
        ]

        print(
            f"[{number}/{len(missing)}] "
            f"{player_name} "
            f"(ID {player_id})"
        )

        try:
            result = resolve_player(
                player_id,
                player_name,
            )

        except Exception as exc:
            result = {
                "player_id": player_id,
                "player_name": player_name,
                "status": "error",
                "wikidata_id": None,
                "wikidata_label": None,
                "birth_date": None,
                "candidate_count": 0,
                "error": str(exc),
            }

        results.append(
            result
        )

        print(
            f"    -> {result['status']}"
        )

    save_lookup_log(
        results
    )

    players = update_players(
        players,
        results,
    )

    players.to_csv(
        PLAYERS_PATH,
        index=False,
        encoding="utf-8",
    )

    print("\n==============================")
    print("WIKIDATA LOOKUP SUMMARY")
    print("==============================")

    result_df = pd.DataFrame(
        results
    )

    print(
        result_df["status"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    total = len(players)

    with_dob = (
        players["birth_date"]
        .notna()
        .sum()
    )

    print()
    print(
        f"Total DOB coverage: "
        f"{with_dob}/{total}"
    )

    print(
        f"Still missing: "
        f"{total - with_dob}"
    )

    print("==============================\n")


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help=(
            "Maximum number of missing players "
            "to process in this run."
        ),
    )

    args = parser.parse_args()

    process_missing(
        args.limit
    )


if __name__ == "__main__":
    main()