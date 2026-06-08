"""2026 FIFA World Cup fixtures — 48 teams, 3 groups of 4 → expanded to 12 groups of 4."""

from datetime import date

GROUPS = {
    "A": ["USA", "Panama", "Honduras", "Bolivia"],
    "B": ["Mexico", "Jamaica", "Costa Rica", "Canada"],
    "C": ["Brazil", "Colombia", "Paraguay", "Ecuador"],
    "D": ["Argentina", "Chile", "Peru", "Venezuela"],
    "E": ["Spain", "Morocco", "Portugal", "Uruguay"],
    "F": ["France", "Belgium", "Netherlands", "England"],
    "G": ["Germany", "Japan", "South Korea", "Australia"],
    "H": ["Italy", "Poland", "Croatia", "Serbia"],
    "I": ["Senegal", "Cameroon", "Mali", "Algeria"],
    "J": ["Iran", "Saudi Arabia", "Qatar", "Iraq"],
    "K": ["New Zealand", "Fiji", "Indonesia", "Thailand"],
    "L": ["Egypt", "South Africa", "Nigeria", "Ghana"],
}

# Group stage fixtures — each team plays 3 matches
# Dates are approximate based on official schedule windows
GROUP_FIXTURES = [
    # Group A
    {"date": date(2026, 6, 11), "home": "USA", "away": "Bolivia", "group": "A"},
    {"date": date(2026, 6, 11), "home": "Panama", "away": "Honduras", "group": "A"},
    {"date": date(2026, 6, 15), "home": "USA", "away": "Panama", "group": "A"},
    {"date": date(2026, 6, 15), "home": "Bolivia", "away": "Honduras", "group": "A"},
    {"date": date(2026, 6, 19), "home": "Honduras", "away": "USA", "group": "A"},
    {"date": date(2026, 6, 19), "home": "Bolivia", "away": "Panama", "group": "A"},
    # Group B
    {"date": date(2026, 6, 12), "home": "Mexico", "away": "Canada", "group": "B"},
    {"date": date(2026, 6, 12), "home": "Jamaica", "away": "Costa Rica", "group": "B"},
    {"date": date(2026, 6, 16), "home": "Mexico", "away": "Jamaica", "group": "B"},
    {"date": date(2026, 6, 16), "home": "Canada", "away": "Costa Rica", "group": "B"},
    {"date": date(2026, 6, 20), "home": "Costa Rica", "away": "Mexico", "group": "B"},
    {"date": date(2026, 6, 20), "home": "Canada", "away": "Jamaica", "group": "B"},
    # Group C
    {"date": date(2026, 6, 12), "home": "Brazil", "away": "Ecuador", "group": "C"},
    {"date": date(2026, 6, 12), "home": "Colombia", "away": "Paraguay", "group": "C"},
    {"date": date(2026, 6, 16), "home": "Brazil", "away": "Colombia", "group": "C"},
    {"date": date(2026, 6, 16), "home": "Ecuador", "away": "Paraguay", "group": "C"},
    {"date": date(2026, 6, 20), "home": "Paraguay", "away": "Brazil", "group": "C"},
    {"date": date(2026, 6, 20), "home": "Ecuador", "away": "Colombia", "group": "C"},
    # Group D
    {"date": date(2026, 6, 13), "home": "Argentina", "away": "Venezuela", "group": "D"},
    {"date": date(2026, 6, 13), "home": "Chile", "away": "Peru", "group": "D"},
    {"date": date(2026, 6, 17), "home": "Argentina", "away": "Chile", "group": "D"},
    {"date": date(2026, 6, 17), "home": "Venezuela", "away": "Peru", "group": "D"},
    {"date": date(2026, 6, 21), "home": "Peru", "away": "Argentina", "group": "D"},
    {"date": date(2026, 6, 21), "home": "Venezuela", "away": "Chile", "group": "D"},
    # Group E
    {"date": date(2026, 6, 13), "home": "Spain", "away": "Uruguay", "group": "E"},
    {"date": date(2026, 6, 13), "home": "Morocco", "away": "Portugal", "group": "E"},
    {"date": date(2026, 6, 17), "home": "Spain", "away": "Morocco", "group": "E"},
    {"date": date(2026, 6, 17), "home": "Uruguay", "away": "Portugal", "group": "E"},
    {"date": date(2026, 6, 21), "home": "Portugal", "away": "Spain", "group": "E"},
    {"date": date(2026, 6, 21), "home": "Uruguay", "away": "Morocco", "group": "E"},
    # Group F
    {"date": date(2026, 6, 14), "home": "France", "away": "England", "group": "F"},
    {"date": date(2026, 6, 14), "home": "Belgium", "away": "Netherlands", "group": "F"},
    {"date": date(2026, 6, 18), "home": "France", "away": "Belgium", "group": "F"},
    {"date": date(2026, 6, 18), "home": "England", "away": "Netherlands", "group": "F"},
    {"date": date(2026, 6, 22), "home": "Netherlands", "away": "France", "group": "F"},
    {"date": date(2026, 6, 22), "home": "England", "away": "Belgium", "group": "F"},
    # Group G
    {"date": date(2026, 6, 14), "home": "Germany", "away": "Australia", "group": "G"},
    {"date": date(2026, 6, 14), "home": "Japan", "away": "South Korea", "group": "G"},
    {"date": date(2026, 6, 18), "home": "Germany", "away": "Japan", "group": "G"},
    {"date": date(2026, 6, 18), "home": "Australia", "away": "South Korea", "group": "G"},
    {"date": date(2026, 6, 22), "home": "South Korea", "away": "Germany", "group": "G"},
    {"date": date(2026, 6, 22), "home": "Australia", "away": "Japan", "group": "G"},
    # Group H
    {"date": date(2026, 6, 15), "home": "Italy", "away": "Serbia", "group": "H"},
    {"date": date(2026, 6, 15), "home": "Poland", "away": "Croatia", "group": "H"},
    {"date": date(2026, 6, 19), "home": "Italy", "away": "Poland", "group": "H"},
    {"date": date(2026, 6, 19), "home": "Serbia", "away": "Croatia", "group": "H"},
    {"date": date(2026, 6, 23), "home": "Croatia", "away": "Italy", "group": "H"},
    {"date": date(2026, 6, 23), "home": "Serbia", "away": "Poland", "group": "H"},
    # Group I
    {"date": date(2026, 6, 15), "home": "Senegal", "away": "Algeria", "group": "I"},
    {"date": date(2026, 6, 15), "home": "Cameroon", "away": "Mali", "group": "I"},
    {"date": date(2026, 6, 19), "home": "Senegal", "away": "Cameroon", "group": "I"},
    {"date": date(2026, 6, 19), "home": "Algeria", "away": "Mali", "group": "I"},
    {"date": date(2026, 6, 23), "home": "Mali", "away": "Senegal", "group": "I"},
    {"date": date(2026, 6, 23), "home": "Algeria", "away": "Cameroon", "group": "I"},
    # Group J
    {"date": date(2026, 6, 16), "home": "Iran", "away": "Iraq", "group": "J"},
    {"date": date(2026, 6, 16), "home": "Saudi Arabia", "away": "Qatar", "group": "J"},
    {"date": date(2026, 6, 20), "home": "Iran", "away": "Saudi Arabia", "group": "J"},
    {"date": date(2026, 6, 20), "home": "Iraq", "away": "Qatar", "group": "J"},
    {"date": date(2026, 6, 24), "home": "Qatar", "away": "Iran", "group": "J"},
    {"date": date(2026, 6, 24), "home": "Iraq", "away": "Saudi Arabia", "group": "J"},
    # Group K
    {"date": date(2026, 6, 16), "home": "Indonesia", "away": "Thailand", "group": "K"},
    {"date": date(2026, 6, 16), "home": "New Zealand", "away": "Fiji", "group": "K"},
    {"date": date(2026, 6, 20), "home": "New Zealand", "away": "Indonesia", "group": "K"},
    {"date": date(2026, 6, 20), "home": "Fiji", "away": "Thailand", "group": "K"},
    {"date": date(2026, 6, 24), "home": "Thailand", "away": "New Zealand", "group": "K"},
    {"date": date(2026, 6, 24), "home": "Fiji", "away": "Indonesia", "group": "K"},
    # Group L
    {"date": date(2026, 6, 17), "home": "Nigeria", "away": "Ghana", "group": "L"},
    {"date": date(2026, 6, 17), "home": "Egypt", "away": "South Africa", "group": "L"},
    {"date": date(2026, 6, 21), "home": "Nigeria", "away": "Egypt", "group": "L"},
    {"date": date(2026, 6, 21), "home": "Ghana", "away": "South Africa", "group": "L"},
    {"date": date(2026, 6, 25), "home": "South Africa", "away": "Nigeria", "group": "L"},
    {"date": date(2026, 6, 25), "home": "Ghana", "away": "Egypt", "group": "L"},
]
