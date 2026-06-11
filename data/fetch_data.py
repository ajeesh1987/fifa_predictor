"""Fetch historical international results from martj42/international_results."""

import os
import requests
import pandas as pd
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

MARTJ42_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"


def fetch_results(force=False) -> pd.DataFrame:
    if os.path.exists(RESULTS_CSV) and not force:
        return pd.read_csv(RESULTS_CSV, parse_dates=["date"])

    print("Downloading international results from martj42/international_results...")
    r = requests.get(MARTJ42_URL, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text), parse_dates=["date"])

    # Keep last 4 years — enough signal, not too slow to train
    cutoff = pd.Timestamp(date.today()) - pd.DateOffset(years=4)
    df = df[df["date"] >= cutoff].copy()

    # Normalise column names to match what the rest of the app expects
    df = df.rename(columns={"home_score": "home_score", "away_score": "away_score"})
    df["neutral"] = df["neutral"].astype(str).str.upper() == "TRUE"

    df.to_csv(RESULTS_CSV, index=False)
    print(f"Saved {len(df)} matches to {RESULTS_CSV}")
    return df


def get_rankings():
    return pd.DataFrame(
        list(FIFA_RANKINGS.items()), columns=["team", "ranking_points"]
    ).sort_values("ranking_points", ascending=False).reset_index(drop=True)
