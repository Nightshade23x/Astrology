import pandas as pd

DATA_PATH = "data/season_events_2024.csv"


def same_sign_continuation():
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])

    # Remove NaN zodiacs
    df = df[df["Zodiac"].notna()]

    zodiacs = sorted(df["Zodiac"].unique())

    results = []

    # Baseline: probability a zodiac appears on a random day
    daily_presence = (
        df[df["performed"] == 1]
        .groupby(["date", "Zodiac"])
        .size()
        .unstack(fill_value=0)
    )

    baseline_rate = (daily_presence > 0).mean()

    for zodiac in zodiacs:
        activation_days = 0
        continuation_days = 0

        for date, day_df in df.groupby("date"):
            day_df = day_df.sort_values("match_id")

            matches = day_df.groupby("match_id")

            appeared_early = False

            for _, match_df in matches:
                performed_zodiacs = set(
                    match_df[
                        (match_df["performed"] == 1) &
                        (match_df["Zodiac"].notna())
                    ]["Zodiac"]
                )

                if not appeared_early:
                    if zodiac in performed_zodiacs:
                        appeared_early = True
                        activation_days += 1
                else:
                    if zodiac in performed_zodiacs:
                        continuation_days += 1
                        break  # only count once per day

        if activation_days > 0:
            continuation_rate = continuation_days / activation_days
            lift = (
                continuation_rate / baseline_rate.get(zodiac, 0)
                if baseline_rate.get(zodiac, 0) > 0
                else None
            )
        else:
            continuation_rate = 0
            lift = None

        results.append({
            "Zodiac": zodiac,
            "Activation_days": activation_days,
            "Continuation_days": continuation_days,
            "Continuation_rate": round(continuation_rate, 3),
            "Baseline_rate": round(baseline_rate.get(zodiac, 0), 3),
            "Lift": round(lift, 3) if lift else None
        })

    result_df = pd.DataFrame(results).sort_values(
        "Lift", ascending=False, na_position="last"
    )

    print("\n=== Same-Sign Continuation Test ===")
    print(result_df.to_string(index=False))


if __name__ == "__main__":
    same_sign_continuation()
