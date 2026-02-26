import pandas as pd

df = pd.read_csv("data/player_dob_batch.csv")

df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
df["year"] = df["birth_date"].dt.year

MIN_YEAR = 1950
MAX_YEAR = 2010

invalid = df[
    (df["year"].isna()) |
    (df["year"] < MIN_YEAR) |
    (df["year"] > MAX_YEAR)
]

print("\nTotal players:", len(df))
print("Valid DOBs:", len(df) - len(invalid))
print("Invalid or Missing:", len(invalid))

# Export for manual fixing
invalid[["player"]].to_csv("data/manual_dob_fix.csv", index=False)

print("\nManual fix file created: data/manual_dob_fix.csv")