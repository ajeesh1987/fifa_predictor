"""Head-to-head historical offset for match predictions."""

import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.dirname(__file__)
RESULTS_CSV = os.path.join(DATA_DIR, "results.csv")

H2H_SCALE = 0.008   # log-scale per avg goal-difference unit; cap ±0.04
H2H_MIN_MATCHES = 3
H2H_LOOKBACK = 10   # most recent N meetings

_cache: dict = {}


def get_h2h_offset(home: str, away: str) -> float:
    """
    Small log-scale offset (+ve favours home) based on historical H2H results.
    Looks at last H2H_LOOKBACK meetings regardless of venue. Capped at ±0.04.
    Returns 0.0 if fewer than H2H_MIN_MATCHES meetings found.
    """
    key = (home, away)
    if key in _cache:
        return _cache[key]

    if not os.path.exists(RESULTS_CSV):
        _cache[key] = 0.0
        return 0.0

    try:
        df = pd.read_csv(
            RESULTS_CSV,
            usecols=["date", "home_team", "away_team", "home_score", "away_score"],
        )
        df["date"] = pd.to_datetime(df["date"])
        mask = (
            ((df["home_team"] == home) & (df["away_team"] == away)) |
            ((df["home_team"] == away) & (df["away_team"] == home))
        )
        h2h = df[mask].sort_values("date").tail(H2H_LOOKBACK)
        if len(h2h) < H2H_MIN_MATCHES:
            _cache[key] = 0.0
            return 0.0

        def _gd_from_home_perspective(row):
            if row["home_team"] == home:
                return int(row["home_score"]) - int(row["away_score"])
            return int(row["away_score"]) - int(row["home_score"])

        avg_gd = h2h.apply(_gd_from_home_perspective, axis=1).mean()
        offset = float(np.clip(avg_gd * H2H_SCALE, -0.04, 0.04))
    except Exception:
        offset = 0.0

    _cache[key] = offset
    return offset


def clear_cache():
    _cache.clear()
