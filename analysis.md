## Zodiac Pair Coupling Analysis (Same-Day Performance)

**Dataset:**  
- Premier League (8 teams)
- Match stats from previous season
- Player zodiac data from current season
- Incomplete player representation

**Method:**  
- Filtered to players with `performed = 1` (goal, assist, or rating ≥ 7)
- Grouped by match date
- For each date, collected zodiac signs with at least one performing player
- Generated unordered zodiac pairs per day
- Computed:
  - Raw co-occurrence counts
  - Conditional probabilities P(B | A)

---

### Key Observations

**1. Raw Co-occurrence**
- Capricorn appears as a hub sign, pairing frequently with many others.
- Virgo co-occurs with many signs but lacks individual reliability.
- High raw counts alone are not sufficient evidence due to base-rate effects.

**2. Conditional Coupling**
- Strong directional relationships observed:
  - Cancer → Capricorn ≈ 0.96
  - Pisces → Capricorn ≈ 0.95
  - Taurus → Capricorn ≈ 0.95
- Pisces and Sagittarius show strong coupling *toward* Virgo, despite Virgo’s weak standalone reliability.
- Aries → Sagittarius (~0.81) appears as a clean, asymmetric pair.

**3. Small-Sample Artifacts**
- Libra shows perfect (1.0) conditional probabilities due to very low appearance frequency.
- These cases are treated as unreliable and excluded from interpretation.

---

### Interpretation

- Zodiac interactions are **directional**, not symmetric.
- Certain signs act as **anchors** (e.g., Capricorn), while others act as **followers**.
- The presence of structured coupling despite a small, noisy dataset suggests the effect is not purely random, but requires validation with larger and cleaner data.

---

### Next Steps
- Normalize by number of players per zodiac.
- Compare against randomized zodiac labels (null model).
- Extend analysis to additional teams or leagues to test robustness.



## Null Model Validation (Zodiac Pair Coupling)

**Objective:**  
Evaluate whether observed zodiac pair couplings exceed what would be expected by chance.

---

### Method
- Used the existing `season_events.csv`
- Preserved match dates and performance labels
- Randomly shuffled zodiac labels across rows
- Recomputed same-day zodiac pair conditional probabilities P(B | A)
- Repeated for 10 independent shuffles

---

### Results

**Real Data (Top Conditional Pairs):**
- Multiple pairs with P(B | A) ≈ 0.95–1.00
- Strong directional pairs observed (e.g., Cancer → Capricorn, Pisces → Capricorn)

**Null Model:**
- Average max P(B | A): ~0.936
- Maximum observed P(B | A): 1.000
- Perfect conditional probabilities frequently observed under random labeling

---

### Interpretation

- High conditional probabilities (including perfect 1.0 values) are **common under random zodiac assignments** at the current dataset size.
- Therefore, raw P(B | A) magnitude alone is **not sufficient evidence** of non-random coupling.
- The null test indicates that the current metric is too permissive given:
  - small sample size
  - uneven zodiac frequencies
  - set-based “at least one performer per day” logic

---

### Conclusion

- The observed coupling structure does **not significantly exceed** what is expected under a null model.
- This does not invalidate the analysis pipeline, but shows that stronger constraints or more data are required.
- Future work should either:
  - refine coupling metrics, or
  - expand the dataset to improve statistical power.



## Minimum Support Coupling (MSC) Analysis

**MSC Rule:**  
A zodiac is considered active on a given day only if **≥2 players of that zodiac performed**.

This constraint was introduced to reduce small-sample artifacts observed in earlier analyses.

---

### Dataset Impact
- Days retained after MSC filtering: **35**
- Many weak or one-off zodiac appearances removed
- Analysis focuses on genuinely strong same-day signals

---

### MSC Pair Co-occurrence (Raw Counts)
Top recurring same-day pairs:
- Capricorn – Pisces (11 days)
- Pisces – Virgo (10)
- Sagittarius – Virgo (10)
- Pisces – Sagittarius (9)
- Capricorn – Virgo (9)

These pairs represent days where **both zodiacs had at least two performing players**, making random occurrence unlikely.

---

### MSC Conditional Probabilities P(B | A)
Notable directional couplings:
- Virgo → Pisces ≈ 0.77
- Pisces → Capricorn ≈ 0.73
- Sagittarius → Virgo ≈ 0.71
- Leo → Capricorn ≈ 0.73

Perfect (1.0) probabilities still occur for rare signs (e.g., Cancer, Aries) but are treated as small-sample effects.

---

### Interpretation
- The MSC constraint significantly reduces noise seen in earlier analyses.
- Core zodiac structure persists:
  - **Anchor signs:** Capricorn, Pisces
  - **Amplifier signs:** Virgo, Sagittarius
  - **Noise signs:** Libra (absent under MSC)
- Directional (asymmetric) coupling remains, suggesting non-random structure.

---

### Conclusion
Introducing minimum support strengthens the coupling analysis.
The surviving patterns are more robust and provide a stronger foundation for dataset expansion.




PREDICTOR BEGINNINGS

# Astrology-Based Same-Day Performance Analysis

## Motivation

The goal of this project was **not** to claim that astrology deterministically predicts football performance.  
Instead, the objective was to test a personal intuition:

> *Given that footballers are human and subject to mood, rhythm, and contextual factors, could grouping players by zodiac reveal small but measurable same-day performance biases?*

In particular:
- Does early-day performance influence later matches on the **same calendar day**?
- Is this influence visible when players are grouped by zodiac signs?
- Is the intuition completely random, or does it show structured signal?

---

## Data Collection

- Fixtures were fetched from the **Premier League (2024 season)** using the API-Football API.
- For each finished match:
  - Player statistics were collected.
  - A player was marked as **performed** if **any** of the following held:
    - Goals > 0
    - Assists > 0
    - Match rating ≥ 7.0
- Player birthdates were mapped to zodiac signs via a static `players.csv`.

All match events were stored in:



Calendar D+1 Zodiac Continuation Test (2024 – 10 Teams)
What We Tested

We checked whether a zodiac sign that performed on one calendar day (e.g., Saturday) was more likely to perform again on the very next calendar day (e.g., Sunday).
So if Scorpio performed on Saturday, we tested whether another Scorpio performed on Sunday.
We compared this “next-day continuation rate” to the normal baseline rate of that zodiac appearing on any random day.

Results
No zodiac sign had a higher next-day continuation rate than its normal baseline rate.
All Lift values were below 1.
This means there was no evidence of a two-day persistence effect.
In fact, continuation was slightly weaker than baseline in most cases.

Conclusion
Based on the 2024 data (10 teams), there is no statistical support for the idea that zodiac performance carries over to the next calendar day.
