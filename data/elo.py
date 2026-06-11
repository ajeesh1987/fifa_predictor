"""
Compute Elo ratings from scratch using historical results.
Standard Elo with competition-weighted K-factor.
Cached to elo_ratings.csv — rebuilt on each retrain.
"""

import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.dirname(__file__)
ELO_CSV = os.path.join(DATA_DIR, "elo_ratings.csv")

BASE_ELO = 1500

COMPETITION_K = {
    # High-stakes
    "FIFA World Cup": 60,
    "Copa América": 50,
    "UEFA Euro": 50,
    "Africa Cup of Nations": 45,
    "AFC Asian Cup": 45,
    "CONCACAF Gold Cup": 40,
    # Qualifiers
    "FIFA World Cup qualification": 40,
    "UEFA Euro qualification": 35,
    "Copa América qualification": 35,
    # Confederations / Nations League
    "UEFA Nations League": 35,
    "CONCACAF Nations League": 30,
    "Confederations Cup": 45,
    # Friendlies — low signal
    "Friendly": 15,
}
DEFAULT_K = 30  # for unlisted tournaments


def _k(tournament: str) -> float:
    for key, k in COMPETITION_K.items():
        if key.lower() in tournament.lower():
            return k
    return DEFAULT_K


def _expected(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))


def _goal_index(home_goals: int, away_goals: int) -> float:
    """Multiplier based on goal difference — rewards dominant wins."""
    diff = abs(home_goals - away_goals)
    if diff <= 1:
        return 1.0
    if diff == 2:
        return 1.5
    return (11 + diff) / 8


def build_elo(df: pd.DataFrame) -> dict[str, float]:
    """
    Iterate chronologically through all matches, update Elo.
    Returns final dict: team → elo_rating.
    Seeded from FIFA_RANKINGS so synthetic/sparse data can't invert
    well-known team strength (e.g. Portugal >> USA).
    """
    from data.fetch_data import FIFA_RANKINGS
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    ratings: dict[str, float] = dict(FIFA_RANKINGS)

    for _, row in df.iterrows():
        h, a = row["home_team"], row["away_team"]
        hg, ag = int(row["home_score"]), int(row["away_score"])
        tournament = row.get("tournament", "Friendly")

        rh = ratings.get(h, BASE_ELO)
        ra = ratings.get(a, BASE_ELO)

        # Actual score for home team (1=win, 0.5=draw, 0=loss)
        if hg > ag:
            s_h, s_a = 1.0, 0.0
        elif hg == ag:
            s_h = s_a = 0.5
        else:
            s_h, s_a = 0.0, 1.0

        e_h = _expected(rh, ra)
        e_a = 1 - e_h
        k = _k(tournament) * _goal_index(hg, ag)

        ratings[h] = rh + k * (s_h - e_h)
        ratings[a] = ra + k * (s_a - e_a)

    return ratings


def save_elo(ratings: dict[str, float]):
    df = pd.DataFrame(list(ratings.items()), columns=["team", "elo"])
    df.sort_values("elo", ascending=False, inplace=True)
    df.to_csv(ELO_CSV, index=False)


def load_elo() -> dict[str, float]:
    if not os.path.exists(ELO_CSV):
        return {}
    df = pd.read_csv(ELO_CSV)
    return dict(zip(df["team"], df["elo"]))


def get_elo_delta(home: str, away: str, ratings: dict[str, float]) -> float:
    """Normalised Elo delta in [-1, +1] range. Used as feature in xG calculation."""
    rh = ratings.get(home, BASE_ELO)
    ra = ratings.get(away, BASE_ELO)
    return (rh - ra) / 400  # ~[-2, +2] in practice, bounded by real rating spreads
