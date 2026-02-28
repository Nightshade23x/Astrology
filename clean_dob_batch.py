import pandas as pd

# Load file
df = pd.read_csv("data/player_dob_batch.csv", encoding="latin1")

# Clean column names
df.columns = df.columns.str.strip()

# Replace empty strings and "nan" with actual NaN
df["birth_date"] = df["birth_date"].replace(["", "nan"], pd.NA)

# Sort so filled dates come first
df = df.sort_values(by="birth_date", ascending=False)

# Drop duplicates, keeping the first (which will be the filled one)
df = df.drop_duplicates(subset=["player"], keep="first")

# Save cleaned file
df.to_csv("data/player_dob_batch.csv", index=False)

print("Duplicates cleaned.")
print("Total unique players:", len(df))