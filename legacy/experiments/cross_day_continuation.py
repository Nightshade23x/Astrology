import pandas as pd


SEASON = 2024
DATA_PATH = f"data/season_events_{SEASON}.csv"


def calendar_next_day_continuation():
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])

    # Only keep performed rows
    performed = df[df["performed"] == 1]

    # Daily presence matrix (1 if zodiac appears that day)
    daily_presence = (
        performed
        .groupby(["date", "Zodiac"])
        .size()
        .unstack(fill_value=0)
    )

    daily_presence = (daily_presence > 0).astype(int)

    zodiacs = daily_presence.columns
    results = []

    baseline_rate = daily_presence.mean()

    for zodiac in zodiacs:
        activation_days = 0
        continuation_days = 0

        for date in daily_presence.index:
            next_day = date + pd.Timedelta(days=1)

            if zodiac in daily_presence.columns:
                if daily_presence.loc[date, zodiac] == 1:
                    # Only count if next calendar day exists in dataset
                    if next_day in daily_presence.index:
                        activation_days += 1

                        if daily_presence.loc[next_day, zodiac] == 1:
                            continuation_days += 1

        if activation_days > 0:
            continuation_rate = continuation_days / activation_days
            lift = (
                continuation_rate / baseline_rate[zodiac]
                if baseline_rate[zodiac] > 0
                else None
            )
        else:
            continuation_rate = 0
            lift = None

        results.append({
            "Zodiac": zodiac,
            "Activation_days": activation_days,
            "Next_day_hits": continuation_days,
            "Continuation_rate": round(continuation_rate, 3),
            "Baseline_rate": round(baseline_rate[zodiac], 3),
            "Lift": round(lift, 3) if lift else None
        })

    result_df = pd.DataFrame(results).sort_values(
        "Lift", ascending=False, na_position="last"
    )

    print("\n=== Calendar D+1 Zodiac Continuation Test ===")
    print(result_df.to_string(index=False))


if __name__ == "__main__":
    calendar_next_day_continuation()
