"""Fetch historical international results via ESPN API + fallback synthetic data."""

import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import date, timedelta
from io import StringIO

DATA_DIR = os.path.dirname(__file__)
RESULTS_CSV = os.path.join(DATA_DIR, "results.csv")

FIFA_RANKINGS = {
    # Group A
    "Mexico": 1635, "South Africa": 1325, "South Korea": 1625, "Czech Republic": 1560,
    # Group B
    "Canada": 1545, "Bosnia and Herzegovina": 1480, "Qatar": 1350, "Switzerland": 1600,
    # Group C
    "Brazil": 1782, "Morocco": 1645, "Haiti": 1220, "Scotland": 1540,
    # Group D
    "USA": 1640, "Paraguay": 1400, "Australia": 1540, "Turkey": 1555,
    # Group E
    "Germany": 1720, "Curaçao": 1180, "Ivory Coast": 1490, "Ecuador": 1585,
    # Group F
    "Netherlands": 1736, "Japan": 1620, "Sweden": 1570, "Tunisia": 1455,
    # Group G
    "Belgium": 1742, "Egypt": 1470, "Iran": 1530, "New Zealand": 1338,
    # Group H
    "Spain": 1840, "Cape Verde": 1380, "Saudi Arabia": 1490, "Uruguay": 1700,
    # Group I
    "France": 1851, "Senegal": 1608, "Iraq": 1378, "Norway": 1580,
    # Group J
    "Argentina": 1868, "Algeria": 1478, "Austria": 1550, "Jordan": 1310,
    # Group K
    "Portugal": 1764, "DR Congo": 1420, "Uzbekistan": 1350, "Colombia": 1681,
    # Group L
    "England": 1792, "Croatia": 1655, "Ghana": 1448, "Panama": 1430,
}

ESPN_TEAM_IDS = {
    "Argentina": "7", "Brazil": "6", "France": "17", "England": "10",
    "Spain": "9", "Germany": "12", "Portugal": "11", "Netherlands": "18",
    "Belgium": "4", "Uruguay": "19", "Italy": "15", "Croatia": "49",
    "Morocco": "40", "USA": "20", "Mexico": "21", "Japan": "27",
    "South Korea": "23", "Senegal": "45", "Colombia": "8", "Ecuador": "24",
    "Canada": "22", "Australia": "26", "Poland": "29", "Serbia": "54",
    "Switzerland": "36", "Denmark": "16",
}

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"


def _fetch_espn_range(start: date, end: date) -> list[dict]:
    """Fetch completed international matches from ESPN between two dates."""
    results = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y%m%d")
        try:
            r = requests.get(ESPN_SCOREBOARD, params={"dates": date_str}, timeout=10)
            r.raise_for_status()
            for event in r.json().get("events", []):
                comp = event.get("competitions", [{}])[0]
                status = comp.get("status", {}).get("type", {}).get("name", "")
                if status != "STATUS_FINAL":
                    continue
                competitors = comp.get("competitors", [])
                if len(competitors) < 2:
                    continue
                home = next((c for c in competitors if c.get("homeAway") == "home"), None)
                away = next((c for c in competitors if c.get("homeAway") == "away"), None)
                if home and away:
                    results.append({
                        "date": current,
                        "home_team": home["team"]["displayName"],
                        "away_team": away["team"]["displayName"],
                        "home_score": int(home.get("score", 0)),
                        "away_score": int(away.get("score", 0)),
                        "tournament": event.get("season", {}).get("type", {}).get("name", "Friendly"),
                        "neutral": False,
                    })
        except Exception:
            pass
        current += timedelta(days=1)
        time.sleep(0.05)
    return results


def _build_synthetic() -> pd.DataFrame:
    """
    Ranking-based synthetic data for 18 months.
    Used when no internet access or ESPN returns nothing useful.
    Generates ~2000 plausible matches so the optimizer has data to work with.
    """
    np.random.seed(42)
    teams = list(FIFA_RANKINGS.keys())
    rows = []
    today = date.today()
    # Generate across last 18 months so time-decay filter keeps them
    for i in range(800):
        h, a = np.random.choice(len(teams), 2, replace=False)
        ht, at = teams[h], teams[a]
        rh, ra = FIFA_RANKINGS[ht], FIFA_RANKINGS[at]
        lam_h = max(0.3, 1.2 + (rh - ra) / 2500)
        lam_a = max(0.3, 1.0 + (ra - rh) / 2500)
        hg = int(np.random.poisson(lam_h))
        ag = int(np.random.poisson(lam_a))
        days_ago = np.random.randint(1, 540)
        d = today - timedelta(days=int(days_ago))
        rows.append({
            "date": d, "home_team": ht, "away_team": at,
            "home_score": hg, "away_score": ag,
            "tournament": "Friendly", "neutral": False,
        })
    print(f"Built {len(rows)} synthetic matches (18-month window).")
    return pd.DataFrame(rows)


def fetch_results(force=False) -> pd.DataFrame:
    if os.path.exists(RESULTS_CSV) and not force:
        return pd.read_csv(RESULTS_CSV, parse_dates=["date"])

    today = date.today()
    start = today - timedelta(days=548)

    print(f"Fetching ESPN results {start} → {today} (this may take a minute)...")
    rows = _fetch_espn_range(start, today)

    if len(rows) < 50:
        print(f"ESPN returned only {len(rows)} matches — using synthetic data.")
        df = _build_synthetic()
    else:
        df = pd.DataFrame(rows)
        print(f"Fetched {len(df)} matches from ESPN.")

    df.to_csv(RESULTS_CSV, index=False)
    return df


def get_rankings():
    return pd.DataFrame(
        list(FIFA_RANKINGS.items()), columns=["team", "ranking_points"]
    ).sort_values("ranking_points", ascending=False).reset_index(drop=True)
