"""2026 FIFA World Cup — real fixtures from official draw."""

from datetime import date

GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["USA", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

GROUP_FIXTURES = [
    # Group A
    {"date": date(2026, 6, 11), "home": "Mexico",       "away": "South Africa",  "group": "A"},
    {"date": date(2026, 6, 11), "home": "South Korea",  "away": "Czech Republic","group": "A"},
    {"date": date(2026, 6, 18), "home": "Czech Republic","away": "South Africa", "group": "A"},
    {"date": date(2026, 6, 18), "home": "Mexico",       "away": "South Korea",   "group": "A"},
    {"date": date(2026, 6, 24), "home": "Czech Republic","away": "Mexico",       "group": "A"},
    {"date": date(2026, 6, 24), "home": "South Africa", "away": "South Korea",   "group": "A"},

    # Group B
    {"date": date(2026, 6, 12), "home": "Canada",               "away": "Bosnia and Herzegovina", "group": "B"},
    {"date": date(2026, 6, 13), "home": "Qatar",                "away": "Switzerland",            "group": "B"},
    {"date": date(2026, 6, 18), "home": "Switzerland",          "away": "Bosnia and Herzegovina", "group": "B"},
    {"date": date(2026, 6, 18), "home": "Canada",               "away": "Qatar",                  "group": "B"},
    {"date": date(2026, 6, 24), "home": "Switzerland",          "away": "Canada",                 "group": "B"},
    {"date": date(2026, 6, 24), "home": "Bosnia and Herzegovina","away": "Qatar",                 "group": "B"},

    # Group C
    {"date": date(2026, 6, 13), "home": "Brazil",   "away": "Morocco",  "group": "C"},
    {"date": date(2026, 6, 13), "home": "Haiti",    "away": "Scotland", "group": "C"},
    {"date": date(2026, 6, 19), "home": "Scotland", "away": "Morocco",  "group": "C"},
    {"date": date(2026, 6, 19), "home": "Brazil",   "away": "Haiti",    "group": "C"},
    {"date": date(2026, 6, 24), "home": "Scotland", "away": "Brazil",   "group": "C"},
    {"date": date(2026, 6, 24), "home": "Morocco",  "away": "Haiti",    "group": "C"},

    # Group D
    {"date": date(2026, 6, 12), "home": "USA",       "away": "Paraguay",  "group": "D"},
    {"date": date(2026, 6, 13), "home": "Australia", "away": "Turkey",    "group": "D"},
    {"date": date(2026, 6, 19), "home": "USA",       "away": "Australia", "group": "D"},
    {"date": date(2026, 6, 19), "home": "Turkey",    "away": "Paraguay",  "group": "D"},
    {"date": date(2026, 6, 25), "home": "Turkey",    "away": "USA",       "group": "D"},
    {"date": date(2026, 6, 25), "home": "Paraguay",  "away": "Australia", "group": "D"},

    # Group E
    {"date": date(2026, 6, 14), "home": "Germany",     "away": "Curaçao",      "group": "E"},
    {"date": date(2026, 6, 14), "home": "Ivory Coast", "away": "Ecuador",      "group": "E"},
    {"date": date(2026, 6, 20), "home": "Germany",     "away": "Ivory Coast",  "group": "E"},
    {"date": date(2026, 6, 20), "home": "Ecuador",     "away": "Curaçao",      "group": "E"},
    {"date": date(2026, 6, 25), "home": "Curaçao",     "away": "Ivory Coast",  "group": "E"},
    {"date": date(2026, 6, 25), "home": "Ecuador",     "away": "Germany",      "group": "E"},

    # Group F
    {"date": date(2026, 6, 14), "home": "Netherlands", "away": "Japan",        "group": "F"},
    {"date": date(2026, 6, 14), "home": "Sweden",      "away": "Tunisia",      "group": "F"},
    {"date": date(2026, 6, 20), "home": "Netherlands", "away": "Sweden",       "group": "F"},
    {"date": date(2026, 6, 20), "home": "Tunisia",     "away": "Japan",        "group": "F"},
    {"date": date(2026, 6, 25), "home": "Japan",       "away": "Sweden",       "group": "F"},
    {"date": date(2026, 6, 25), "home": "Tunisia",     "away": "Netherlands",  "group": "F"},

    # Group G
    {"date": date(2026, 6, 15), "home": "Belgium",     "away": "Egypt",        "group": "G"},
    {"date": date(2026, 6, 15), "home": "Iran",        "away": "New Zealand",  "group": "G"},
    {"date": date(2026, 6, 21), "home": "Belgium",     "away": "Iran",         "group": "G"},
    {"date": date(2026, 6, 21), "home": "New Zealand", "away": "Egypt",        "group": "G"},
    {"date": date(2026, 6, 26), "home": "Egypt",       "away": "Iran",         "group": "G"},
    {"date": date(2026, 6, 26), "home": "New Zealand", "away": "Belgium",      "group": "G"},

    # Group H
    {"date": date(2026, 6, 15), "home": "Spain",       "away": "Cape Verde",   "group": "H"},
    {"date": date(2026, 6, 15), "home": "Saudi Arabia","away": "Uruguay",      "group": "H"},
    {"date": date(2026, 6, 21), "home": "Spain",       "away": "Saudi Arabia", "group": "H"},
    {"date": date(2026, 6, 21), "home": "Uruguay",     "away": "Cape Verde",   "group": "H"},
    {"date": date(2026, 6, 26), "home": "Cape Verde",  "away": "Saudi Arabia", "group": "H"},
    {"date": date(2026, 6, 26), "home": "Uruguay",     "away": "Spain",        "group": "H"},

    # Group I
    {"date": date(2026, 6, 16), "home": "France",  "away": "Senegal", "group": "I"},
    {"date": date(2026, 6, 16), "home": "Iraq",    "away": "Norway",  "group": "I"},
    {"date": date(2026, 6, 22), "home": "France",  "away": "Iraq",    "group": "I"},
    {"date": date(2026, 6, 22), "home": "Norway",  "away": "Senegal", "group": "I"},
    {"date": date(2026, 6, 26), "home": "Norway",  "away": "France",  "group": "I"},
    {"date": date(2026, 6, 26), "home": "Senegal", "away": "Iraq",    "group": "I"},

    # Group J
    {"date": date(2026, 6, 16), "home": "Argentina", "away": "Algeria", "group": "J"},
    {"date": date(2026, 6, 16), "home": "Austria",   "away": "Jordan",  "group": "J"},
    {"date": date(2026, 6, 22), "home": "Argentina", "away": "Austria", "group": "J"},
    {"date": date(2026, 6, 22), "home": "Jordan",    "away": "Algeria", "group": "J"},
    {"date": date(2026, 6, 27), "home": "Algeria",   "away": "Austria", "group": "J"},
    {"date": date(2026, 6, 27), "home": "Jordan",    "away": "Argentina","group": "J"},

    # Group K
    {"date": date(2026, 6, 17), "home": "Portugal",  "away": "DR Congo",   "group": "K"},
    {"date": date(2026, 6, 17), "home": "Uzbekistan","away": "Colombia",   "group": "K"},
    {"date": date(2026, 6, 23), "home": "Portugal",  "away": "Uzbekistan", "group": "K"},
    {"date": date(2026, 6, 23), "home": "Colombia",  "away": "DR Congo",   "group": "K"},
    {"date": date(2026, 6, 27), "home": "Colombia",  "away": "Portugal",   "group": "K"},
    {"date": date(2026, 6, 27), "home": "DR Congo",  "away": "Uzbekistan", "group": "K"},

    # Group L
    {"date": date(2026, 6, 17), "home": "England", "away": "Croatia", "group": "L"},
    {"date": date(2026, 6, 17), "home": "Ghana",   "away": "Panama",  "group": "L"},
    {"date": date(2026, 6, 23), "home": "England", "away": "Ghana",   "group": "L"},
    {"date": date(2026, 6, 23), "home": "Panama",  "away": "Croatia", "group": "L"},
    {"date": date(2026, 6, 27), "home": "Panama",  "away": "England", "group": "L"},
    {"date": date(2026, 6, 27), "home": "Croatia", "away": "Ghana",   "group": "L"},
]
