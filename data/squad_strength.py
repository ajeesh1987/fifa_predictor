"""
Squad strength per team: base FIFA rating for key players.
Injury adjustments are applied on top at prediction time.

strength_offset() returns a log-scale offset added to both attack params:
  +0.10 = ~10% more goals expected  (full-strength elite team)
  -0.15 = ~14% fewer goals          (key striker + midfielder out)

Key players are the top 3 contributors per team (striker, CM, keeper).
Weights: striker=0.50, midfielder=0.30, keeper=0.20 (keeper affects defence).
"""

import os
import json

DATA_DIR = os.path.dirname(__file__)
INJURIES_FILE = os.path.join(DATA_DIR, "injuries.json")

# Top-3 key players per WC 2026 team.
# rating: FIFA 25 overall (0-99). role: ATK / MID / GK.
# These are the players whose absence meaningfully shifts xG.
KEY_PLAYERS: dict[str, list[dict]] = {
    "Argentina":    [{"name": "L. Messi",       "rating": 93, "role": "ATK"},
                     {"name": "J. Álvarez",      "rating": 83, "role": "ATK"},
                     {"name": "R. De Paul",      "rating": 85, "role": "MID"}],
    "France":       [{"name": "K. Mbappé",       "rating": 91, "role": "ATK"},
                     {"name": "A. Griezmann",    "rating": 86, "role": "ATK"},
                     {"name": "A. Tchouaméni",   "rating": 84, "role": "MID"}],
    "Brazil":       [{"name": "Vinicius Jr.",    "rating": 91, "role": "ATK"},
                     {"name": "Rodrygo",         "rating": 85, "role": "ATK"},
                     {"name": "Casemiro",        "rating": 85, "role": "MID"}],
    "England":      [{"name": "J. Bellingham",  "rating": 89, "role": "MID"},
                     {"name": "H. Kane",         "rating": 90, "role": "ATK"},
                     {"name": "B. Saka",         "rating": 87, "role": "ATK"}],
    "Spain":        [{"name": "Y. Yamal",        "rating": 87, "role": "ATK"},
                     {"name": "P. Pedri",        "rating": 87, "role": "MID"},
                     {"name": "A. Morata",       "rating": 83, "role": "ATK"}],
    "Portugal":     [{"name": "C. Ronaldo",      "rating": 88, "role": "ATK"},
                     {"name": "B. Fernandes",    "rating": 87, "role": "MID"},
                     {"name": "R. Leão",         "rating": 86, "role": "ATK"}],
    "Germany":      [{"name": "J. Musiala",      "rating": 87, "role": "MID"},
                     {"name": "K. Havertz",      "rating": 85, "role": "ATK"},
                     {"name": "F. Wirtz",        "rating": 87, "role": "MID"}],
    "Netherlands":  [{"name": "V. van Dijk",     "rating": 88, "role": "MID"},
                     {"name": "C. Gakpo",        "rating": 84, "role": "ATK"},
                     {"name": "X. Simons",       "rating": 84, "role": "MID"}],
    "Belgium":      [{"name": "K. De Bruyne",    "rating": 90, "role": "MID"},
                     {"name": "R. Lukaku",       "rating": 84, "role": "ATK"},
                     {"name": "J. Doku",         "rating": 82, "role": "ATK"}],
    "Morocco":      [{"name": "H. Ziyech",       "rating": 82, "role": "MID"},
                     {"name": "Y. En-Nesyri",    "rating": 82, "role": "ATK"},
                     {"name": "A. Hakimi",       "rating": 85, "role": "MID"}],
    "Croatia":      [{"name": "L. Modrić",       "rating": 85, "role": "MID"},
                     {"name": "M. Kovačić",      "rating": 84, "role": "MID"},
                     {"name": "A. Kramarić",     "rating": 82, "role": "ATK"}],
    "Uruguay":      [{"name": "F. Valverde",     "rating": 87, "role": "MID"},
                     {"name": "D. Núñez",        "rating": 85, "role": "ATK"},
                     {"name": "R. Bentancur",    "rating": 83, "role": "MID"}],
    "Colombia":     [{"name": "L. Díaz",         "rating": 85, "role": "ATK"},
                     {"name": "J. Cuadrado",     "rating": 80, "role": "MID"},
                     {"name": "R. Falcao",       "rating": 79, "role": "ATK"}],
    "USA":          [{"name": "C. Pulisic",      "rating": 83, "role": "ATK"},
                     {"name": "W. McKennie",     "rating": 79, "role": "MID"},
                     {"name": "G. Reyna",        "rating": 78, "role": "ATK"}],
    "Mexico":       [{"name": "H. Lozano",       "rating": 80, "role": "ATK"},
                     {"name": "A. Guardado",     "rating": 77, "role": "MID"},
                     {"name": "R. Jiménez",      "rating": 78, "role": "ATK"}],
    "Japan":        [{"name": "T. Minamino",     "rating": 80, "role": "ATK"},
                     {"name": "W. Endo",         "rating": 81, "role": "MID"},
                     {"name": "K. Mitoma",       "rating": 81, "role": "ATK"}],
    "South Korea":  [{"name": "Son Heung-min",   "rating": 87, "role": "ATK"},
                     {"name": "H. Hwang",        "rating": 79, "role": "ATK"},
                     {"name": "J. Hwang",        "rating": 78, "role": "MID"}],
    "Senegal":      [{"name": "S. Mané",         "rating": 84, "role": "ATK"},
                     {"name": "I. Gueye",        "rating": 80, "role": "MID"},
                     {"name": "K. Kouyaté",      "rating": 78, "role": "MID"}],
    "Italy":        [{"name": "F. Chiesa",       "rating": 83, "role": "ATK"},
                     {"name": "N. Barella",      "rating": 87, "role": "MID"},
                     {"name": "L. Pellegrini",   "rating": 82, "role": "MID"}],
    "Poland":       [{"name": "R. Lewandowski",  "rating": 87, "role": "ATK"},
                     {"name": "P. Zieliński",    "rating": 82, "role": "MID"},
                     {"name": "K. Piątek",       "rating": 78, "role": "ATK"}],
    "Australia":    [{"name": "M. Leckie",       "rating": 76, "role": "ATK"},
                     {"name": "A. Hrustic",      "rating": 75, "role": "MID"},
                     {"name": "M. Sainsbury",    "rating": 72, "role": "MID"}],
    "Ecuador":      [{"name": "E. Valencia",     "rating": 77, "role": "ATK"},
                     {"name": "M. Caicedo",      "rating": 83, "role": "MID"},
                     {"name": "A. Preciado",     "rating": 76, "role": "MID"}],
    "Serbia":       [{"name": "D. Vlahović",     "rating": 84, "role": "ATK"},
                     {"name": "N. Milinković-Savić","rating": 83, "role": "MID"},
                     {"name": "A. Mitrović",     "rating": 82, "role": "ATK"}],
    "Canada":       [{"name": "A. Davies",       "rating": 84, "role": "MID"},
                     {"name": "J. David",        "rating": 83, "role": "ATK"},
                     {"name": "T. Buchanan",     "rating": 78, "role": "ATK"}],
    "Iran":         [{"name": "M. Taremi",       "rating": 81, "role": "ATK"},
                     {"name": "A. Jahanbakhsh",  "rating": 78, "role": "ATK"},
                     {"name": "S. Azmoun",       "rating": 80, "role": "ATK"}],
    "Saudi Arabia": [{"name": "S. Al-Dawsari",   "rating": 76, "role": "ATK"},
                     {"name": "M. Al-Buraikan",  "rating": 74, "role": "ATK"},
                     {"name": "F. Al-Bulayhi",   "rating": 73, "role": "MID"}],
    "Nigeria":      [{"name": "V. Osimhen",      "rating": 86, "role": "ATK"},
                     {"name": "A. Iwobi",        "rating": 79, "role": "MID"},
                     {"name": "K. Lookman",      "rating": 82, "role": "ATK"}],
    "Ghana":        [{"name": "J. Ayew",         "rating": 76, "role": "ATK"},
                     {"name": "M. Kudus",        "rating": 81, "role": "MID"},
                     {"name": "I. Sulemana",     "rating": 77, "role": "ATK"}],
    "Egypt":        [{"name": "M. Salah",        "rating": 89, "role": "ATK"},
                     {"name": "T. Mohamed",      "rating": 75, "role": "MID"},
                     {"name": "O. Kamal",        "rating": 73, "role": "ATK"}],
    "Chile":        [{"name": "A. Vidal",        "rating": 78, "role": "MID"},
                     {"name": "E. Vargas",       "rating": 77, "role": "ATK"},
                     {"name": "B. Brereton",     "rating": 75, "role": "ATK"}],
    "Peru":         [{"name": "G. Lapadula",     "rating": 74, "role": "ATK"},
                     {"name": "C. Cueva",        "rating": 76, "role": "MID"},
                     {"name": "Y. Pineau",       "rating": 72, "role": "MID"}],
    "Venezuela":    [{"name": "S. Rondón",       "rating": 74, "role": "ATK"},
                     {"name": "T. Brekalo",      "rating": 75, "role": "ATK"},
                     {"name": "Y. Herrera",      "rating": 73, "role": "MID"}],
    "Paraguay":     [{"name": "M. Almirón",      "rating": 80, "role": "MID"},
                     {"name": "Ángel Romero",    "rating": 75, "role": "ATK"},
                     {"name": "R. Sánchez",      "rating": 73, "role": "ATK"}],
    "Bolivia":      [{"name": "M. Martins",      "rating": 70, "role": "ATK"},
                     {"name": "R. Justiniano",   "rating": 68, "role": "MID"},
                     {"name": "G. Antelo",       "rating": 67, "role": "ATK"}],
    "Cameroon":     [{"name": "V. Aboubakar",    "rating": 79, "role": "ATK"},
                     {"name": "A. Onana",        "rating": 86, "role": "GK"},
                     {"name": "N. Nkoulou",      "rating": 77, "role": "MID"}],
    "Mali":         [{"name": "A. Traoré",       "rating": 77, "role": "ATK"},
                     {"name": "D. Samaké",       "rating": 72, "role": "MID"},
                     {"name": "M. Haïdara",      "rating": 74, "role": "MID"}],
    "Algeria":      [{"name": "R. Mahrez",       "rating": 83, "role": "ATK"},
                     {"name": "I. Bennacer",     "rating": 82, "role": "MID"},
                     {"name": "Y. Brahimi",      "rating": 77, "role": "ATK"}],
    "Iraq":         [{"name": "A. Mohanad",      "rating": 70, "role": "ATK"},
                     {"name": "A. Karrar",       "rating": 68, "role": "MID"},
                     {"name": "B. Nassir",       "rating": 67, "role": "ATK"}],
    "Qatar":        [{"name": "A. Afif",         "rating": 76, "role": "ATK"},
                     {"name": "A. Al-Haydos",    "rating": 74, "role": "MID"},
                     {"name": "A. Ali",          "rating": 72, "role": "ATK"}],
    "Costa Rica":   [{"name": "K. Navas",        "rating": 82, "role": "GK"},
                     {"name": "J. Campbell",     "rating": 75, "role": "ATK"},
                     {"name": "B. Ruiz",         "rating": 73, "role": "ATK"}],
    "Panama":       [{"name": "R. Torres",       "rating": 73, "role": "MID"},
                     {"name": "G. Torres",       "rating": 74, "role": "ATK"},
                     {"name": "M. Murillo",      "rating": 74, "role": "MID"}],
    "Honduras":     [{"name": "R. Aceituno",     "rating": 68, "role": "MID"},
                     {"name": "J. Benguché",     "rating": 69, "role": "ATK"},
                     {"name": "M. Elis",         "rating": 71, "role": "ATK"}],
    "Jamaica":      [{"name": "L. Bailey",       "rating": 78, "role": "ATK"},
                     {"name": "M. Antonio",      "rating": 76, "role": "ATK"},
                     {"name": "R. Lowe",         "rating": 72, "role": "MID"}],
    "New Zealand":  [{"name": "C. Wood",         "rating": 75, "role": "ATK"},
                     {"name": "R. De Vries",     "rating": 70, "role": "MID"},
                     {"name": "J. Garuccio",     "rating": 67, "role": "MID"}],
    "South Africa": [{"name": "P. Grobler",      "rating": 70, "role": "ATK"},
                     {"name": "K. Dolly",        "rating": 72, "role": "ATK"},
                     {"name": "T. Zungu",        "rating": 71, "role": "MID"}],
    "Indonesia":    [{"name": "E. Haaland",      "rating": 65, "role": "ATK"},
                     {"name": "T. Arhan",        "rating": 63, "role": "MID"},
                     {"name": "M. Ferarri",      "rating": 64, "role": "MID"}],
    "Fiji":         [{"name": "R. Kumar",        "rating": 58, "role": "ATK"},
                     {"name": "J. Singh",        "rating": 56, "role": "MID"},
                     {"name": "P. Brown",        "rating": 55, "role": "ATK"}],
    "Thailand":     [{"name": "T. Dangda",       "rating": 65, "role": "ATK"},
                     {"name": "C. Supachai",     "rating": 63, "role": "MID"},
                     {"name": "P. Atirat",       "rating": 60, "role": "ATK"}],
}

ROLE_WEIGHTS = {"ATK": 0.50, "MID": 0.30, "GK": 0.20}
AVG_RATING = 78  # baseline "average" player


def _load_injuries() -> dict:
    if not os.path.exists(INJURIES_FILE):
        return {}
    with open(INJURIES_FILE) as f:
        return json.load(f)


def strength_offset(team: str, injuries: dict | None = None) -> tuple[float, float]:
    """
    Returns (attack_offset, defence_offset) as log-scale values to add to xG params.

    For each key player that is injured/suspended:
      - ATK player out → reduces attack
      - MID player out → reduces attack slightly + defence slightly
      - GK player out  → reduces defence

    Scale: a rating-90 striker is worth +0.08 attack offset when present.
    If injured, that offset is lost.
    """
    if injuries is None:
        injuries = _load_injuries()

    players = KEY_PLAYERS.get(team, [])
    if not players:
        return 0.0, 0.0

    injured_names = {p.lower() for p in injuries.get(team, {}).get("injured", [])}
    suspended_names = {p.lower() for p in injuries.get(team, {}).get("suspended", [])}
    out = injured_names | suspended_names

    atk_offset = 0.0
    def_offset = 0.0

    for p in players:
        r = p["rating"]
        role = p["role"]
        # How much above/below average this player is, scaled to log-goal contribution
        contribution = (r - AVG_RATING) / 100  # e.g. rating 90 → +0.12, rating 70 → -0.08

        if role == "ATK":
            atk_offset += contribution * ROLE_WEIGHTS["ATK"]
        elif role == "MID":
            atk_offset += contribution * ROLE_WEIGHTS["MID"] * 0.5
            def_offset += contribution * ROLE_WEIGHTS["MID"] * 0.5
        elif role == "GK":
            def_offset += contribution * ROLE_WEIGHTS["GK"]

    # Subtract contribution of injured/suspended players
    for p in players:
        if p["name"].lower() in out:
            r = p["rating"]
            role = p["role"]
            contribution = (r - AVG_RATING) / 100
            if role == "ATK":
                atk_offset -= contribution * ROLE_WEIGHTS["ATK"]
            elif role == "MID":
                atk_offset -= contribution * ROLE_WEIGHTS["MID"] * 0.5
                def_offset -= contribution * ROLE_WEIGHTS["MID"] * 0.5
            elif role == "GK":
                def_offset -= contribution * ROLE_WEIGHTS["GK"]

    return round(atk_offset, 4), round(def_offset, 4)


def get_all_teams() -> list[str]:
    return sorted(KEY_PLAYERS.keys())


def get_key_players(team: str) -> list[dict]:
    return KEY_PLAYERS.get(team, [])
