"""Persist predictions and actual results to CSV."""

import os
import pandas as pd
import pytz
from datetime import datetime

CEST = pytz.timezone("Europe/Paris")

def _today_cest():
    return datetime.now(CEST).date()

STORE_PATH = os.path.join(os.path.dirname(__file__), "prediction_log.csv")

COLUMNS = [
    "date", "home_team", "away_team", "group",
    "pred_home_xg", "pred_away_xg",
    "pred_home_win_pct", "pred_draw_pct", "pred_away_win_pct",
    "pred_most_likely_home", "pred_most_likely_away",
    "actual_home", "actual_away",
]


def _load() -> pd.DataFrame:
    if os.path.exists(STORE_PATH):
        return pd.read_csv(STORE_PATH, parse_dates=["date"])
    return pd.DataFrame(columns=COLUMNS)


def save_prediction(fixture: dict, pred: dict):
    """Upsert a prediction row (keyed on date+home+away)."""
    df = _load()
    key = (str(fixture["date"]), fixture["home"], fixture["away"])
    mask = (
        (df["date"].astype(str).str[:10] == key[0]) &
        (df["home_team"] == key[1]) &
        (df["away_team"] == key[2])
    )
    row = {
        "date": fixture["date"],
        "home_team": fixture["home"],
        "away_team": fixture["away"],
        "group": fixture.get("group", ""),
        "pred_home_xg": pred["home_xg"],
        "pred_away_xg": pred["away_xg"],
        "pred_home_win_pct": round(pred["home_win_prob"] * 100, 1),
        "pred_draw_pct": round(pred["draw_prob"] * 100, 1),
        "pred_away_win_pct": round(pred["away_win_prob"] * 100, 1),
        "pred_most_likely_home": pred["most_likely_score"][0],
        "pred_most_likely_away": pred["most_likely_score"][1],
        "actual_home": None,
        "actual_away": None,
    }
    if mask.any():
        # Preserve existing actuals
        existing = df[mask].iloc[0]
        row["actual_home"] = existing["actual_home"]
        row["actual_away"] = existing["actual_away"]
        df = df[~mask]

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.sort_values(["date", "home_team"], inplace=True)
    df.to_csv(STORE_PATH, index=False)


def save_actual(match_date: str, home: str, away: str, actual_home: int, actual_away: int):
    df = _load()
    mask = (
        (df["date"].astype(str).str[:10] == str(match_date)) &
        (df["home_team"] == home) &
        (df["away_team"] == away)
    )
    if not mask.any():
        return False
    df.loc[mask, "actual_home"] = actual_home
    df.loc[mask, "actual_away"] = actual_away
    df.to_csv(STORE_PATH, index=False)
    return True


def load_with_actuals() -> pd.DataFrame:
    return _load()


def accuracy_summary(df: pd.DataFrame) -> dict:
    """Compute accuracy metrics over rows that have actuals."""
    scored = df.dropna(subset=["actual_home", "actual_away"]).copy()
    if scored.empty:
        return {}

    scored["actual_home"] = scored["actual_home"].astype(int)
    scored["actual_away"] = scored["actual_away"].astype(int)

    def outcome(h, a):
        return "H" if h > a else ("D" if h == a else "A")

    scored["pred_outcome"] = scored.apply(
        lambda r: outcome(r["pred_most_likely_home"], r["pred_most_likely_away"]), axis=1
    )
    scored["actual_outcome"] = scored.apply(
        lambda r: outcome(r["actual_home"], r["actual_away"]), axis=1
    )
    scored["outcome_correct"] = scored["pred_outcome"] == scored["actual_outcome"]
    scored["exact_score"] = (
        (scored["pred_most_likely_home"] == scored["actual_home"]) &
        (scored["pred_most_likely_away"] == scored["actual_away"])
    )
    # Favourite correct: highest prob outcome matched actual
    def fav_outcome(r):
        probs = {"H": r["pred_home_win_pct"], "D": r["pred_draw_pct"], "A": r["pred_away_win_pct"]}
        return max(probs, key=probs.get)
    scored["fav_outcome"] = scored.apply(fav_outcome, axis=1)
    scored["fav_correct"] = scored["fav_outcome"] == scored["actual_outcome"]

    n = len(scored)
    return {
        "total": n,
        "outcome_accuracy": round(scored["outcome_correct"].sum() / n * 100, 1),
        "favourite_accuracy": round(scored["fav_correct"].sum() / n * 100, 1),
        "exact_score_accuracy": round(scored["exact_score"].sum() / n * 100, 1),
        "detail": scored,
    }
