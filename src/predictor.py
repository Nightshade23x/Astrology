import pandas as pd


class ZodiacPredictor:
    """
    Core prediction engine.
    Computes zodiac and player-level performance probabilities
    using baseline strength + same-day activation.
    """

    def __init__(
        self,
        reliability,
        clustering,
        activation_power=1.0,
        min_baseline=0.01
    ):
        """
        reliability: Series indexed by Zodiac (baseline probability)
        clustering: Series indexed by Zodiac (same-day clustering strength)
        activation_power: exponent applied per same-day activation
        min_baseline: floor probability to avoid zeroing out
        """
        self.reliability = reliability
        self.clustering = clustering
        self.activation_power = activation_power
        self.min_baseline = min_baseline

    def zodiac_score(self, zodiac, day_state):
        """
        Compute today's score for a zodiac sign.
        """
        base = self.reliability.get(zodiac, self.min_baseline)
        cluster = self.clustering.get(zodiac, 1.0)
        activations = day_state.get_activation_count(zodiac)

        score = base * (cluster ** (activations * self.activation_power))
        return score

    def score_players(self, match_df, day_state):
        """
        Score players in an upcoming match.

        match_df must contain:
            - 'player'
            - 'Zodiac'
        """
        scores = []

        for _, row in match_df.iterrows():
            zodiac = row["Zodiac"]
            score = self.zodiac_score(zodiac, day_state)

            scores.append({
                "player": row["player"],
                "Zodiac": zodiac,
                "score": score
            })

        return pd.DataFrame(scores).sort_values("score", ascending=False)

    def top_zodiacs(self, day_state, n=3):
        """
        Return top-N zodiac signs for the current day.
        """
        rows = []

        for zodiac in self.reliability.index:
            rows.append({
                "Zodiac": zodiac,
                "score": self.zodiac_score(zodiac, day_state)
            })

        df = pd.DataFrame(rows)
        return df.sort_values("score", ascending=False).head(n)
