import pandas as pd
import ephem

# Zodiac signs in order
ZODIAC = [
    "Aries","Taurus","Gemini","Cancer",
    "Leo","Virgo","Libra","Scorpio",
    "Sagittarius","Capricorn","Aquarius","Pisces"
]

# Function to compute moon sign for a given date
def get_moon_sign(date):

    moon = ephem.Moon(date)                     # create moon object for that date

    lon = moon.hlon                             # get moon longitude

    degree = float(lon) * 180 / ephem.pi        # convert radians to degrees

    sign_index = int(degree / 30)               # each zodiac sign spans 30 degrees

    return ZODIAC[sign_index]                   # return zodiac sign


# seasons we want to process
SEASONS = [2023, 2024]


for season in SEASONS:

    print("Processing season:", season)

    # load season data
    df = pd.read_csv(f"data/season_events_{season}.csv")

    # convert date format
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)

    # get unique match dates
    unique_dates = df["date"].drop_duplicates()

    moon_map = {}

    for d in unique_dates:

        moon_map[d] = get_moon_sign(d.strftime("%Y/%m/%d"))   # compute moon sign for that date

    # map moon sign back to dataframe
    df["moon_sign"] = df["date"].map(moon_map)

    # save new file
    df.to_csv(f"data/season_events_{season}_moon.csv", index=False)

    print(f"Moon signs added for {season}")