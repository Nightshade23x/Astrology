import pandas as pd
import ephem

ZODIAC = [
    "Aries","Taurus","Gemini","Cancer",
    "Leo","Virgo","Libra","Scorpio",
    "Sagittarius","Capricorn","Aquarius","Pisces"
]

def get_moon_sign(date):

    moon = ephem.Moon(date)

    lon = moon.hlon
    degree = float(lon) * 180 / ephem.pi

    sign_index = int(degree / 30)

    return ZODIAC[sign_index]


# load season data
df = pd.read_csv("data/season_events_2023.csv")

# convert date format
df["date"] = pd.to_datetime(df["date"], dayfirst=True)

# get unique match dates
unique_dates = df["date"].drop_duplicates()

moon_map = {}

for d in unique_dates:

    moon_map[d] = get_moon_sign(d.strftime("%Y/%m/%d"))

# map moon sign back
df["moon_sign"] = df["date"].map(moon_map)

df.to_csv("data/season_events_2023_moon.csv", index=False)

print("Moon signs added.")