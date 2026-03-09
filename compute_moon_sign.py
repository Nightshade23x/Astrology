import ephem

# zodiac list
ZODIAC = [
    "Aries","Taurus","Gemini","Cancer",
    "Leo","Virgo","Libra","Scorpio",
    "Sagittarius","Capricorn","Aquarius","Pisces"
]

def get_moon_sign(date):

    moon = ephem.Moon(date)

    lon = moon.hlon  # moon longitude

    degree = float(lon) * 180 / ephem.pi

    sign_index = int(degree / 30)

    return ZODIAC[sign_index]


# test example
date = "2023/08/12"

print(get_moon_sign(date))