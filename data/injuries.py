"""
Injury / suspension store + ESPN auto-detection.

Storage: data/injuries.json
  {
    "Argentina": {
      "injured":   ["L. Messi"],
      "suspended": ["R. De Paul"],
      "notes":     {"L. Messi": "hamstring, est. return 2026-06-18"}
    }
  }

Auto-detection: scrapes ESPN WC injury news headlines and fuzzy-matches
player names from KEY_PLAYERS against headline text.
"""

import os
import json
import re
import time
import requests
import pytz
from datetime import datetime

DATA_DIR = os.path.dirname(__file__)
INJURIES_FILE = os.path.join(DATA_DIR, "injuries.json")
LAST_INJURY_FETCH = os.path.join(DATA_DIR, ".last_injury_fetch")
CEST = pytz.timezone("Europe/Paris")

# ESPN news endpoint for FIFA World Cup
ESPN_NEWS_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/news"

INJURY_KEYWORDS = [
    "injured", "injury", "out", "doubt", "suspended", "suspension",
    "ruled out", "misses", "sidelined", "hamstring", "knee", "ankle",
    "muscle", "ban", "red card", "yellow card", "unavailable",
]
SUSPENSION_KEYWORDS = ["suspended", "suspension", "ban", "red card", "yellow card", "bookings"]


def _load() -> dict:
    if not os.path.exists(INJURIES_FILE):
        return {}
    with open(INJURIES_FILE) as f:
        return json.load(f)


def _save(data: dict):
    with open(INJURIES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def set_injury(team: str, player: str, note: str = ""):
    data = _load()
    t = data.setdefault(team, {"injured": [], "suspended": [], "notes": {}})
    if player not in t["injured"]:
        t["injured"].append(player)
    if note:
        t["notes"][player] = note
    _save(data)


def set_suspension(team: str, player: str, note: str = ""):
    data = _load()
    t = data.setdefault(team, {"injured": [], "suspended": [], "notes": {}})
    if player not in t["suspended"]:
        t["suspended"].append(player)
    if note:
        t["notes"][player] = note
    _save(data)


def clear_player(team: str, player: str):
    data = _load()
    if team not in data:
        return
    data[team]["injured"] = [p for p in data[team].get("injured", []) if p != player]
    data[team]["suspended"] = [p for p in data[team].get("suspended", []) if p != player]
    data[team].get("notes", {}).pop(player, None)
    _save(data)


def get_all() -> dict:
    return _load()


def should_fetch_injuries() -> bool:
    if not os.path.exists(LAST_INJURY_FETCH):
        return True
    with open(LAST_INJURY_FETCH) as f:
        last = float(f.read().strip())
    return (time.time() - last) > 86400


def auto_detect_injuries(force: bool = False) -> list[str]:
    """
    Fetch ESPN WC news, scan for injury/suspension mentions alongside
    player names from KEY_PLAYERS. Returns list of detection messages.
    Auto-adds confirmed mentions to injuries.json.
    """
    from data.squad_strength import KEY_PLAYERS

    if not force and not should_fetch_injuries():
        return []

    with open(LAST_INJURY_FETCH, "w") as f:
        f.write(str(time.time()))

    try:
        r = requests.get(ESPN_NEWS_URL, params={"limit": 50}, timeout=10)
        r.raise_for_status()
        articles = r.json().get("articles", [])
    except Exception as e:
        return [f"ESPN injury news fetch failed: {e}"]

    detections = []
    data = _load()

    for article in articles:
        headline = article.get("headline", "").lower()
        description = article.get("description", "").lower()
        text = headline + " " + description

        if not any(kw in text for kw in INJURY_KEYWORDS):
            continue

        is_suspension = any(kw in text for kw in SUSPENSION_KEYWORDS)

        for team, players in KEY_PLAYERS.items():
            for p in players:
                # Match on last name (more reliable in headlines)
                last_name = p["name"].split(".")[-1].strip().lower()
                if len(last_name) < 4:
                    continue
                if last_name in text:
                    t_data = data.setdefault(team, {"injured": [], "suspended": [], "notes": {}})
                    already_tracked = (
                        p["name"] in t_data.get("injured", []) or
                        p["name"] in t_data.get("suspended", [])
                    )
                    if not already_tracked:
                        category = "suspended" if is_suspension else "injured"
                        t_data[category].append(p["name"])
                        t_data.setdefault("notes", {})[p["name"]] = f"Auto-detected: {article.get('headline', '')[:80]}"
                        detections.append(
                            f"[AUTO] {p['name']} ({team}) flagged as {category} — {article.get('headline', '')[:60]}"
                        )

    _save(data)
    return detections
