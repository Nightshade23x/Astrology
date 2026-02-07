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
