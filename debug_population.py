import os
import pandas as pd

# Path to data folder
DATA_DIR = os.path.join("data")

def main():
    print("\n=====================================")
    print("   ZODIAC POPULATION DISTRIBUTION")
    print("=====================================\n")

    dob_path = os.path.join(DATA_DIR, "player_dob_batch.csv")

    df = pd.read_csv(dob_path)

    df.columns = df.columns.str.strip()

    # Normalize column name
    if "zodiac" in df.columns:
        df = df.rename(columns={"zodiac": "Zodiac"})

    total_players = len(df)

    counts = df["Zodiac"].value_counts().sort_values(ascending=False)

    percentages = (counts / total_players) * 100

    result = pd.DataFrame({
        "Player_Count": counts,
        "Percentage_%": percentages.round(2)
    })

    print(f"Total Players: {total_players}\n")
    print(result.to_string())
    print("\nDone.\n")

if __name__ == "__main__":
    main()