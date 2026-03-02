import os
import pandas as pd

SEASONS = [2023, 2024]


def load_and_merge(season):
    season_path = os.path.join("data", f"season_events_{season}.csv")
    dob_path = os.path.join("data", "player_dob_batch.csv")

    df = pd.read_csv(season_path)
    dob_df = pd.read_csv(dob_path)

    # Clean column names
    df.columns = df.columns.str.strip()
    dob_df.columns = dob_df.columns.str.strip()

    # Normalize zodiac column
    if "zodiac" in dob_df.columns:
        dob_df = dob_df.rename(columns={"zodiac": "Zodiac"})

    # Merge zodiac into season data
    df = df.merge(
        dob_df[["player", "Zodiac"]],
        on="player",
        how="left"
    )

    # Remove rows without zodiac
    df = df.dropna(subset=["Zodiac"])

    # Convert date (DD-MM-YYYY format)
    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

    df = df.dropna(subset=["date"])

    return df


def main():
    print("\n=======================================")
    print(" SAME-DAY ZODIAC CLUSTERING ANALYSIS")
    print("=======================================\n")

    all_data = []

    for season in SEASONS:
        df = load_and_merge(season)
        all_data.append(df)

    df_all = pd.concat(all_data, ignore_index=True)

    # Keep only players who performed
    df_all = df_all[df_all["performed"] == 1]

    # Count performers per day per zodiac
    daily_counts = (
        df_all.groupby(["date", "Zodiac"])
        .size()
        .reset_index(name="count")
    )

    # Days appeared (>=1 performer)
    appeared_days = daily_counts.groupby("Zodiac").size()

    # Days clustered (>=2 performers)
    clustered_days = daily_counts[daily_counts["count"] >= 2].groupby("Zodiac").size()

    # Average performers per appearance day
    avg_performers = daily_counts.groupby("Zodiac")["count"].mean()

    # Maximum performers in a single day
    max_performers = daily_counts.groupby("Zodiac")["count"].max()

    result = pd.DataFrame({
        "Appeared_Days": appeared_days,
        "Clustered_Days_(2+)": clustered_days,
        "Avg_Performers_Per_Day": avg_performers,
        "Max_Performers_In_A_Day": max_performers
    }).fillna(0)

    result["Cluster_Rate"] = (
        result["Clustered_Days_(2+)"] / result["Appeared_Days"]
    ).fillna(0)

    result = result.sort_values("Clustered_Days_(2+)", ascending=False)

    print(result.to_string())
    print("\nDone.\n")


if __name__ == "__main__":
    main()