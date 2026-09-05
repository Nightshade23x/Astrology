from collections import defaultdict


class DayState:
    """
    Tracks zodiac performance activations for a single calendar day.
    """

    def __init__(self, date):
        self.date = date
        self.activations = defaultdict(int)

    def update_from_match(self, match_df):
        """
        Update zodiac activations from a finished match.

        match_df: DataFrame containing at least:
            - 'Zodiac'
            - 'performed' (1 if performed, 0 otherwise)
        """
        performed = match_df[match_df["performed"] == 1]

        for zodiac in performed["Zodiac"]:
            self.activations[zodiac] += 1

    def get_activation_count(self, zodiac):
        """
        Return how many times this zodiac has activated today.
        """
        return self.activations.get(zodiac, 0)

    def active_zodiacs(self):
        """
        Return all zodiacs that have activated today.
        """
        return list(self.activations.keys())

    def reset(self):
        """
        Clear state (used when moving to a new day).
        """
        self.activations.clear()

    def __repr__(self):
        return f"DayState(date={self.date}, activations={dict(self.activations)})"
