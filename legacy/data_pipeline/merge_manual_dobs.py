import pandas as pd

# Load main DOB file
main_df = pd.read_csv("data/player_dob_batch.csv", encoding="latin1")

# Load manual fixes
manual_df = pd.read_csv("data/manual_dob_fix.csv", encoding="latin1")

# Clean column names (removes hidden spaces from Excel)
main_df.columns = main_df.columns.str.strip()
manual_df.columns = manual_df.columns.str.strip()

# Ensure required columns exist
if "player" not in manual_df.columns or "birth_date" not in manual_df.columns:
    raise ValueError("manual_dob_fix.csv must contain columns: player, birth_date")

# Clean string formatting
main_df["player"] = main_df["player"].str.strip().str.lower()
manual_df["player"] = manual_df["player"].str.strip().str.lower()

# Merge using update logic (safer than loop)
main_df = main_df.set_index("player")
manual_df = manual_df.set_index("player")

main_df.update(manual_df)

main_df = main_df.reset_index()

# Save cleaned master file
main_df.to_csv("data/player_dob_batch.csv", index=False)

print("Manual DOBs merged successfully.")
print("Total players:", len(main_df))