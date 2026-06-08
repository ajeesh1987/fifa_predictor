"""Fetch historical international results and FIFA rankings."""

import os
import pandas as pd
import requests
from io import StringIO

DATA_DIR = os.path.dirname(__file__)
RESULTS_CSV = os.path.join(DATA_DIR, "results.csv")
RANKINGS_CSV = os.path.join(DATA_DIR, "rankings.csv")

# Historical international results from martj42/international-football-results (public domain)
RESULTS_URL = "https://raw.githubusercontent.com/martj42/international-football-results/master/results.csv"


def fetch_results(force=False):
    if os.path.exists(RESULTS_CSV) and not force:
        return pd.read_csv(RESULTS_CSV, parse_dates=["date"])
    print("Downloading historical results...")
    r = requests.get(RESULTS_URL, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text), parse_dates=["date"])
    df.to_csv(RESULTS_CSV, index=False)
    print(f"Saved {len(df)} matches to {RESULTS_CSV}")
    return df


# FIFA rankings (approximate — based on latest available ranking points)
# Source: fifa.com rankings Dec 2024 (top 48 WC teams)
FIFA_RANKINGS = {
    "Argentina": 1868, "France": 1851, "Spain": 1840, "England": 1792,
    "Brazil": 1782, "Portugal": 1764, "Belgium": 1742, "Netherlands": 1736,
    "Germany": 1720, "Uruguay": 1700, "Colombia": 1681, "Italy": 1665,
    "Croatia": 1655, "Morocco": 1645, "USA": 1640, "Mexico": 1635,
    "South Korea": 1625, "Japan": 1620, "Senegal": 1608, "Switzerland": 1600,
    "Ecuador": 1585, "Chile": 1578, "Serbia": 1570, "Denmark": 1565,
    "Poland": 1555, "Canada": 1545, "Australia": 1540, "Iran": 1530,
    "Peru": 1518, "Nigeria": 1505, "Saudi Arabia": 1490, "Cameroon": 1485,
    "Algeria": 1478, "Egypt": 1470, "Mali": 1455, "Ghana": 1448,
    "Costa Rica": 1440, "Panama": 1430, "Honduras": 1415, "Venezuela": 1408,
    "Paraguay": 1400, "Bolivia": 1390, "Iraq": 1378, "Jamaica": 1365,
    "Qatar": 1350, "New Zealand": 1338, "South Africa": 1325, "Indonesia": 1265,
    "Fiji": 1120, "Thailand": 1205,
}


def get_rankings():
    return pd.DataFrame(
        list(FIFA_RANKINGS.items()), columns=["team", "ranking_points"]
    ).sort_values("ranking_points", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    fetch_results(force=True)
    print(get_rankings().head(10))
