"""Fetch actual WC 2026 scores from ESPN public API and update prediction log."""

import os
import json
import time
import requests
import pandas as pd
import pytz
from datetime import datetime, timedelta

DATA_DIR = os.path.dirname(__file__)
LAST_FETCH_FILE = os.path.join(DATA_DIR, ".last_score_fetch")
CEST = pytz.timezone("Europe/Paris")

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"


def _now_cest() -> datetime:
    return datetime.now(CEST)


def _fetch_espn_date(date_cest: datetime) -> list[dict]:
    """Fetch ESPN scoreboard for a given CEST date. Returns list of match dicts."""
    date_str = date_cest.strftime("%Y%m%d")
    try:
        r = requests.get(ESPN_URL, params={"dates": date_str}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"ESPN fetch error for {date_str}: {e}")
        return []

    matches = []
    for event in data.get("events", []):
        comp = event.get("competitions", [{}])[0]
        status_type = comp.get("status", {}).get("type", {})
        status = status_type.get("name", "")
        completed = status_type.get("completed", False)
        if not completed and status not in ("STATUS_FINAL", "STATUS_FULL_TIME"):
            continue
        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            continue
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue
        matches.append({
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_score": int(home.get("score", 0)),
            "away_score": int(away.get("score", 0)),
        })
    return matches


# ESPN uses full country names; map to our short names
TEAM_NAME_MAP = {
    "United States": "USA",
    "South Korea": "South Korea",
    "Korea Republic": "South Korea",
    "Czechia": "Czech Republic",
    "Czech Rep.": "Czech Republic",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Ivory Coast": "Ivory Coast",
    "Côte d'Ivoire": "Ivory Coast",
    "DR Congo": "DR Congo",
    "Democratic Republic of Congo": "DR Congo",
    "Iran": "Iran",
    "Saudi Arabia": "Saudi Arabia",
    "New Zealand": "New Zealand",
    "South Africa": "South Africa",
    "Costa Rica": "Costa Rica",
    "Cape Verde": "Cape Verde",
    "Cape Verde Islands": "Cape Verde",
}


def _normalize(name: str) -> str:
    return TEAM_NAME_MAP.get(name, name)


def should_fetch() -> bool:
    """True if >24h since last fetch or never fetched."""
    if not os.path.exists(LAST_FETCH_FILE):
        return True
    with open(LAST_FETCH_FILE) as f:
        last = float(f.read().strip())
    return (time.time() - last) > 86400


def fetch_and_update_actuals(force=False) -> tuple[int, list[str]]:
    """
    Fetch scores for the past 3 days (CEST) and update prediction log.
    Looks back 3 days so missed results (e.g. due to status bugs) are caught.
    Returns (matches_updated, messages).
    """
    from data.predictions_store import save_actual, load_with_actuals

    if not force and not should_fetch():
        return 0, []

    now = _now_cest()

    # Stamp fetch time regardless of results
    with open(LAST_FETCH_FILE, "w") as f:
        f.write(str(time.time()))

    all_matches_by_date = {}
    for days_ago in range(0, 4):
        day = now - timedelta(days=days_ago)
        day_matches = _fetch_espn_date(day)
        if day_matches:
            all_matches_by_date[day.date()] = day_matches

    if not all_matches_by_date:
        yesterday = (now - timedelta(days=1)).date()
        return 0, [f"No completed matches found for {yesterday} (CEST)."]

    updated = 0
    messages = []

    for match_date, matches in all_matches_by_date.items():
        for m in matches:
            home = _normalize(m["home_team"])
            away = _normalize(m["away_team"])
            # Try ESPN date, then ±1 day (handles late-night UTC/CEST offset mismatches)
            candidate_dates = [
                match_date,
                match_date - timedelta(days=1),
                match_date + timedelta(days=1),
            ]
            saved = False
            for d in candidate_dates:
                if save_actual(str(d), home, away, m["home_score"], m["away_score"]):
                    updated += 1
                    messages.append(f"{home} {m['home_score']}–{m['away_score']} {away}")
                    saved = True
                    break
                if save_actual(str(d), away, home, m["away_score"], m["home_score"]):
                    updated += 1
                    messages.append(f"{away} {m['away_score']}–{m['home_score']} {home} (flipped)")
                    saved = True
                    break

    if updated:
        retrain_msg = retrain_with_wc_results()
        messages.append(retrain_msg)

    return updated, messages


def _surprise_weight(pred_home_win_pct: float, pred_draw_pct: float, pred_away_win_pct: float,
                     actual_home: int, actual_away: int) -> float:
    """
    Return a weight multiplier based on how surprising the result was.
    Favourite probability × inverse = surprise. Capped at 4.0.

    e.g. model gave home team 80% win chance but away won → weight = 1/0.20 = 5 → capped at 4.0
         model gave 50/25/25 and home won → weight = 1/0.50 = 2.0
    """
    if actual_home > actual_away:
        p_actual = pred_home_win_pct / 100
    elif actual_home == actual_away:
        p_actual = pred_draw_pct / 100
    else:
        p_actual = pred_away_win_pct / 100
    p_actual = max(p_actual, 0.05)  # floor to avoid divide-by-zero
    return min(1.0 / p_actual, 4.0)


def retrain_with_wc_results() -> str:
    """Build WC results dataframe with surprise weights and retrain model."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from data.predictions_store import load_with_actuals
    from data.fetch_data import fetch_results, FIFA_RANKINGS
    from model.dixon_coles import train
    import pandas as pd

    log = load_with_actuals()
    scored = log.dropna(subset=["actual_home", "actual_away"]).copy()

    if scored.empty:
        return "No WC results to retrain on yet."

    scored["surprise_weight"] = scored.apply(
        lambda r: _surprise_weight(
            r["pred_home_win_pct"], r["pred_draw_pct"], r["pred_away_win_pct"],
            int(r["actual_home"]), int(r["actual_away"])
        ), axis=1
    )
    wc_matches = scored.rename(columns={
        "home_team": "home_team", "away_team": "away_team",
        "actual_home": "home_score", "actual_away": "away_score",
    })[["date", "home_team", "away_team", "home_score", "away_score", "surprise_weight"]]

    print("Retraining model with WC results...")
    hist = fetch_results(force=False)
    known_teams = list(FIFA_RANKINGS.keys())

    from data.elo import build_elo, save_elo
    # Append WC actuals so Elo reflects tournament performance, not just pre-tournament form
    wc_for_elo = wc_matches[["date", "home_team", "away_team", "home_score", "away_score"]].copy()
    wc_for_elo["tournament"] = "FIFA World Cup"
    hist_with_wc = pd.concat([hist, wc_for_elo], ignore_index=True)
    ratings = build_elo(hist_with_wc)
    save_elo(ratings)

    train(hist, known_teams, wc_matches=wc_matches)

    from data.h2h import clear_cache
    clear_cache()

    n_surprise = (scored["surprise_weight"] > 1.5).sum()
    return f"Model retrained on {len(wc_matches)} WC match(es) ({n_surprise} surprise(s) boosted)."
