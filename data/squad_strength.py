"""
Squad strength per team: key players with FIFA ratings.
Injury adjustments are applied on top at prediction time.

strength_offset() returns (attack_offset, defence_offset) as log-scale values.

Roles and weights:
  ATK = 0.35  → attack offset
  MID = 0.20  → 50% attack / 50% defence
  DEF = 0.15  → defence offset
  GK  = 0.30  → defence offset

+0.10 attack offset ≈ 10% more goals expected
-0.10 defence offset ≈ 10% more goals conceded
"""

import os
import json

DATA_DIR = os.path.dirname(__file__)
INJURIES_FILE = os.path.join(DATA_DIR, "injuries.json")

KEY_PLAYERS: dict[str, list[dict]] = {
    "Argentina": [
        {"name": "L. Messi",        "rating": 93, "role": "ATK"},
        {"name": "J. Álvarez",      "rating": 83, "role": "ATK"},
        {"name": "R. De Paul",      "rating": 85, "role": "MID"},
        {"name": "A. Mac Allister", "rating": 84, "role": "MID"},
        {"name": "N. Otamendi",     "rating": 82, "role": "DEF"},
        {"name": "L. Martínez",     "rating": 82, "role": "DEF"},
        {"name": "E. Martínez",     "rating": 88, "role": "GK"},
        {"name": "Enzo Fernández",  "rating": 83, "role": "MID"},
    ],
    "France": [
        {"name": "K. Mbappé",       "rating": 91, "role": "ATK"},
        {"name": "A. Griezmann",    "rating": 86, "role": "ATK"},
        {"name": "A. Tchouaméni",   "rating": 84, "role": "MID"},
        {"name": "A. Rabiot",       "rating": 82, "role": "MID"},
        {"name": "W. Saliba",       "rating": 85, "role": "DEF"},
        {"name": "T. Hernandez",    "rating": 84, "role": "DEF"},
        {"name": "M. Maignan",      "rating": 87, "role": "GK"},
        {"name": "M. Camavinga",    "rating": 83, "role": "MID"},
    ],
    "Brazil": [
        {"name": "Vinicius Jr.",    "rating": 91, "role": "ATK"},
        {"name": "Rodrygo",         "rating": 85, "role": "ATK"},
        {"name": "Casemiro",        "rating": 85, "role": "MID"},
        {"name": "Lucas Paquetá",   "rating": 85, "role": "MID"},
        {"name": "Marquinhos",      "rating": 86, "role": "DEF"},
        {"name": "Éder Militão",    "rating": 84, "role": "DEF"},
        {"name": "Alisson",         "rating": 89, "role": "GK"},
        {"name": "Raphinha",        "rating": 84, "role": "ATK"},
    ],
    "England": [
        {"name": "J. Bellingham",   "rating": 89, "role": "MID"},
        {"name": "H. Kane",         "rating": 90, "role": "ATK"},
        {"name": "B. Saka",         "rating": 87, "role": "ATK"},
        {"name": "P. Foden",        "rating": 88, "role": "MID"},
        {"name": "J. Stones",       "rating": 84, "role": "DEF"},
        {"name": "K. Walker",       "rating": 82, "role": "DEF"},
        {"name": "J. Pickford",     "rating": 83, "role": "GK"},
        {"name": "D. Rice",         "rating": 85, "role": "MID"},
    ],
    "Spain": [
        {"name": "Y. Yamal",        "rating": 87, "role": "ATK"},
        {"name": "P. Pedri",        "rating": 87, "role": "MID"},
        {"name": "A. Morata",       "rating": 83, "role": "ATK"},
        {"name": "F. Ruiz",         "rating": 83, "role": "MID"},
        {"name": "A. Laporte",      "rating": 84, "role": "DEF"},
        {"name": "D. Carvajal",     "rating": 83, "role": "DEF"},
        {"name": "U. Simón",        "rating": 83, "role": "GK"},
        {"name": "G. Rodri",        "rating": 91, "role": "MID"},
    ],
    "Portugal": [
        {"name": "C. Ronaldo",      "rating": 88, "role": "ATK"},
        {"name": "B. Fernandes",    "rating": 87, "role": "MID"},
        {"name": "R. Leão",         "rating": 86, "role": "ATK"},
        {"name": "J. Cancelo",      "rating": 84, "role": "DEF"},
        {"name": "R. Dias",         "rating": 88, "role": "DEF"},
        {"name": "D. Costa",        "rating": 84, "role": "GK"},
        {"name": "V. Horta",        "rating": 80, "role": "ATK"},
        {"name": "Otávio",          "rating": 81, "role": "MID"},
    ],
    "Germany": [
        {"name": "J. Musiala",      "rating": 87, "role": "MID"},
        {"name": "K. Havertz",      "rating": 85, "role": "ATK"},
        {"name": "F. Wirtz",        "rating": 87, "role": "MID"},
        {"name": "I. Gündogan",     "rating": 85, "role": "MID"},
        {"name": "A. Rüdiger",      "rating": 85, "role": "DEF"},
        {"name": "J. Kimmich",      "rating": 87, "role": "DEF"},
        {"name": "M. ter Stegen",   "rating": 88, "role": "GK"},
        {"name": "L. Goretzka",     "rating": 84, "role": "MID"},
    ],
    "Netherlands": [
        {"name": "V. van Dijk",     "rating": 88, "role": "DEF"},
        {"name": "C. Gakpo",        "rating": 84, "role": "ATK"},
        {"name": "X. Simons",       "rating": 84, "role": "MID"},
        {"name": "F. de Jong",      "rating": 87, "role": "MID"},
        {"name": "D. Blind",        "rating": 80, "role": "DEF"},
        {"name": "B. Timber",       "rating": 82, "role": "DEF"},
        {"name": "B. Flekken",      "rating": 82, "role": "GK"},
        {"name": "S. Bergwijn",     "rating": 82, "role": "ATK"},
    ],
    "Belgium": [
        {"name": "K. De Bruyne",    "rating": 90, "role": "MID"},
        {"name": "R. Lukaku",       "rating": 84, "role": "ATK"},
        {"name": "J. Doku",         "rating": 82, "role": "ATK"},
        {"name": "A. Onana",        "rating": 83, "role": "MID"},
        {"name": "J. Vertonghen",   "rating": 81, "role": "DEF"},
        {"name": "T. Alderweireld", "rating": 80, "role": "DEF"},
        {"name": "K. Casteels",     "rating": 84, "role": "GK"},
        {"name": "Y. Tielemans",    "rating": 83, "role": "MID"},
    ],
    "Morocco": [
        {"name": "H. Ziyech",       "rating": 82, "role": "MID"},
        {"name": "Y. En-Nesyri",    "rating": 82, "role": "ATK"},
        {"name": "A. Hakimi",       "rating": 85, "role": "DEF"},
        {"name": "S. Amrabat",      "rating": 82, "role": "MID"},
        {"name": "N. Aguerd",       "rating": 81, "role": "DEF"},
        {"name": "R. Saïss",        "rating": 79, "role": "DEF"},
        {"name": "Y. Bounou",       "rating": 84, "role": "GK"},
        {"name": "I. Ounahi",       "rating": 78, "role": "MID"},
    ],
    "Croatia": [
        {"name": "L. Modrić",       "rating": 85, "role": "MID"},
        {"name": "M. Kovačić",      "rating": 84, "role": "MID"},
        {"name": "A. Kramarić",     "rating": 82, "role": "ATK"},
        {"name": "I. Perišić",      "rating": 82, "role": "ATK"},
        {"name": "J. Šutalo",       "rating": 78, "role": "DEF"},
        {"name": "D. Lovren",       "rating": 79, "role": "DEF"},
        {"name": "D. Livaković",    "rating": 83, "role": "GK"},
        {"name": "L. Gvardiol",     "rating": 84, "role": "DEF"},
    ],
    "Uruguay": [
        {"name": "F. Valverde",     "rating": 87, "role": "MID"},
        {"name": "D. Núñez",        "rating": 85, "role": "ATK"},
        {"name": "R. Bentancur",    "rating": 83, "role": "MID"},
        {"name": "M. Ugarte",       "rating": 81, "role": "MID"},
        {"name": "R. Araujo",       "rating": 84, "role": "DEF"},
        {"name": "J. Giménez",      "rating": 83, "role": "DEF"},
        {"name": "S. Rochet",       "rating": 80, "role": "GK"},
        {"name": "L. Suárez",       "rating": 80, "role": "ATK"},
    ],
    "Colombia": [
        {"name": "L. Díaz",         "rating": 85, "role": "ATK"},
        {"name": "J. Cuadrado",     "rating": 80, "role": "MID"},
        {"name": "R. Falcao",       "rating": 79, "role": "ATK"},
        {"name": "M. Caicedo",      "rating": 83, "role": "MID"},
        {"name": "D. Sánchez",      "rating": 78, "role": "DEF"},
        {"name": "Y. Mina",         "rating": 79, "role": "DEF"},
        {"name": "D. Ospina",       "rating": 82, "role": "GK"},
        {"name": "J. Lerma",        "rating": 79, "role": "MID"},
    ],
    "USA": [
        {"name": "C. Pulisic",      "rating": 83, "role": "ATK"},
        {"name": "W. McKennie",     "rating": 79, "role": "MID"},
        {"name": "G. Reyna",        "rating": 78, "role": "ATK"},
        {"name": "Y. Musah",        "rating": 79, "role": "MID"},
        {"name": "S. Richards",     "rating": 76, "role": "DEF"},
        {"name": "T. Ream",         "rating": 77, "role": "DEF"},
        {"name": "M. Turner",       "rating": 78, "role": "GK"},
        {"name": "B. Aaronson",     "rating": 76, "role": "ATK"},
    ],
    "Mexico": [
        {"name": "H. Lozano",       "rating": 80, "role": "ATK"},
        {"name": "A. Guardado",     "rating": 77, "role": "MID"},
        {"name": "R. Jiménez",      "rating": 78, "role": "ATK"},
        {"name": "E. Herrera",      "rating": 78, "role": "MID"},
        {"name": "H. Moreno",       "rating": 79, "role": "DEF"},
        {"name": "J. Sánchez",      "rating": 77, "role": "DEF"},
        {"name": "G. Ochoa",        "rating": 83, "role": "GK"},
        {"name": "C. Antuna",       "rating": 76, "role": "ATK"},
    ],
    "Japan": [
        {"name": "T. Minamino",     "rating": 80, "role": "ATK"},
        {"name": "W. Endo",         "rating": 81, "role": "MID"},
        {"name": "K. Mitoma",       "rating": 81, "role": "ATK"},
        {"name": "D. Kamada",       "rating": 79, "role": "MID"},
        {"name": "M. Yoshida",      "rating": 78, "role": "DEF"},
        {"name": "H. Sakai",        "rating": 77, "role": "DEF"},
        {"name": "S. Gonda",        "rating": 78, "role": "GK"},
        {"name": "R. Doan",         "rating": 79, "role": "ATK"},
    ],
    "South Korea": [
        {"name": "Son Heung-min",   "rating": 87, "role": "ATK"},
        {"name": "H. Hwang",        "rating": 79, "role": "ATK"},
        {"name": "J. Hwang",        "rating": 78, "role": "MID"},
        {"name": "W. In-Beom",      "rating": 77, "role": "MID"},
        {"name": "K. Min-Jae",      "rating": 85, "role": "DEF"},
        {"name": "Y. Hyun-Jun",     "rating": 76, "role": "DEF"},
        {"name": "J. Seung-Gyu",    "rating": 79, "role": "GK"},
        {"name": "L. Jae-Sung",     "rating": 78, "role": "ATK"},
    ],
    "Senegal": [
        {"name": "S. Mané",         "rating": 84, "role": "ATK"},
        {"name": "I. Gueye",        "rating": 80, "role": "MID"},
        {"name": "K. Kouyaté",      "rating": 78, "role": "MID"},
        {"name": "I. Sarr",         "rating": 79, "role": "ATK"},
        {"name": "K. Koulibaly",    "rating": 83, "role": "DEF"},
        {"name": "S. Sabaly",       "rating": 77, "role": "DEF"},
        {"name": "E. Mendy",        "rating": 84, "role": "GK"},
        {"name": "P. Gueye",        "rating": 76, "role": "MID"},
    ],
    "Italy": [
        {"name": "F. Chiesa",       "rating": 83, "role": "ATK"},
        {"name": "N. Barella",      "rating": 87, "role": "MID"},
        {"name": "L. Pellegrini",   "rating": 82, "role": "MID"},
        {"name": "C. Immobile",     "rating": 84, "role": "ATK"},
        {"name": "G. Chiellini",    "rating": 82, "role": "DEF"},
        {"name": "A. Bastoni",      "rating": 85, "role": "DEF"},
        {"name": "G. Donnarumma",   "rating": 90, "role": "GK"},
        {"name": "M. Verratti",     "rating": 84, "role": "MID"},
    ],
    "Poland": [
        {"name": "R. Lewandowski",  "rating": 87, "role": "ATK"},
        {"name": "P. Zieliński",    "rating": 82, "role": "MID"},
        {"name": "K. Piątek",       "rating": 78, "role": "ATK"},
        {"name": "G. Krychowiak",   "rating": 79, "role": "MID"},
        {"name": "J. Bednarek",     "rating": 80, "role": "DEF"},
        {"name": "M. Cash",         "rating": 79, "role": "DEF"},
        {"name": "W. Szczesny",     "rating": 84, "role": "GK"},
        {"name": "T. Milik",        "rating": 80, "role": "ATK"},
    ],
    "Australia": [
        {"name": "M. Leckie",       "rating": 76, "role": "ATK"},
        {"name": "A. Hrustic",      "rating": 75, "role": "MID"},
        {"name": "M. Sainsbury",    "rating": 72, "role": "DEF"},
        {"name": "A. Mabil",        "rating": 74, "role": "ATK"},
        {"name": "H. Souttar",      "rating": 73, "role": "DEF"},
        {"name": "M. Rowles",       "rating": 72, "role": "DEF"},
        {"name": "M. Ryan",         "rating": 76, "role": "GK"},
        {"name": "R. McGree",       "rating": 73, "role": "MID"},
    ],
    "Ecuador": [
        {"name": "E. Valencia",     "rating": 77, "role": "ATK"},
        {"name": "M. Caicedo",      "rating": 83, "role": "MID"},
        {"name": "A. Preciado",     "rating": 76, "role": "DEF"},
        {"name": "G. Plata",        "rating": 77, "role": "ATK"},
        {"name": "P. Hincapié",     "rating": 78, "role": "DEF"},
        {"name": "R. Arboleda",     "rating": 76, "role": "DEF"},
        {"name": "H. Galíndez",     "rating": 77, "role": "GK"},
        {"name": "J. Sarmiento",    "rating": 75, "role": "MID"},
    ],
    "Serbia": [
        {"name": "D. Vlahović",     "rating": 84, "role": "ATK"},
        {"name": "N. Milinković-Savić", "rating": 83, "role": "MID"},
        {"name": "A. Mitrović",     "rating": 82, "role": "ATK"},
        {"name": "D. Tadić",        "rating": 82, "role": "ATK"},
        {"name": "N. Pavlović",     "rating": 77, "role": "DEF"},
        {"name": "S. Mitrović",     "rating": 78, "role": "DEF"},
        {"name": "V. Milinković-Savić", "rating": 83, "role": "GK"},
        {"name": "F. Kostić",       "rating": 81, "role": "MID"},
    ],
    "Canada": [
        {"name": "A. Davies",       "rating": 84, "role": "DEF"},
        {"name": "J. David",        "rating": 83, "role": "ATK"},
        {"name": "T. Buchanan",     "rating": 78, "role": "ATK"},
        {"name": "S. Larin",        "rating": 77, "role": "ATK"},
        {"name": "K. Miller",       "rating": 77, "role": "DEF"},
        {"name": "A. Johnston",     "rating": 76, "role": "MID"},
        {"name": "M. Crepeau",      "rating": 79, "role": "GK"},
        {"name": "M. Eustaquio",    "rating": 79, "role": "MID"},
    ],
    "Iran": [
        {"name": "M. Taremi",       "rating": 81, "role": "ATK"},
        {"name": "A. Jahanbakhsh",  "rating": 78, "role": "ATK"},
        {"name": "S. Azmoun",       "rating": 80, "role": "ATK"},
        {"name": "S. Gholizadeh",   "rating": 77, "role": "MID"},
        {"name": "E. Hajsafi",      "rating": 76, "role": "DEF"},
        {"name": "R. Rezaeian",     "rating": 74, "role": "DEF"},
        {"name": "A. Beiranvand",   "rating": 78, "role": "GK"},
        {"name": "O. Pouraliganji", "rating": 75, "role": "DEF"},
    ],
    "Saudi Arabia": [
        {"name": "S. Al-Dawsari",   "rating": 76, "role": "ATK"},
        {"name": "M. Al-Buraikan",  "rating": 74, "role": "ATK"},
        {"name": "F. Al-Bulayhi",   "rating": 73, "role": "DEF"},
        {"name": "A. Al-Amri",      "rating": 72, "role": "DEF"},
        {"name": "Y. Al-Shahrani",  "rating": 72, "role": "DEF"},
        {"name": "S. Al-Owais",     "rating": 76, "role": "GK"},
        {"name": "S. Al-Malki",     "rating": 71, "role": "MID"},
        {"name": "H. Al-Tambakti",  "rating": 72, "role": "DEF"},
    ],
    "Nigeria": [
        {"name": "V. Osimhen",      "rating": 86, "role": "ATK"},
        {"name": "A. Iwobi",        "rating": 79, "role": "MID"},
        {"name": "K. Lookman",      "rating": 82, "role": "ATK"},
        {"name": "W. Troost-Ekong", "rating": 78, "role": "DEF"},
        {"name": "C. Bassey",       "rating": 77, "role": "DEF"},
        {"name": "F. Onyekachi",    "rating": 74, "role": "MID"},
        {"name": "F. Uzoho",        "rating": 76, "role": "GK"},
        {"name": "S. Ighalo",       "rating": 76, "role": "ATK"},
    ],
    "Ghana": [
        {"name": "J. Ayew",         "rating": 76, "role": "ATK"},
        {"name": "M. Kudus",        "rating": 81, "role": "MID"},
        {"name": "I. Sulemana",     "rating": 77, "role": "ATK"},
        {"name": "T. Partey",       "rating": 84, "role": "MID"},
        {"name": "D. Amartey",      "rating": 77, "role": "DEF"},
        {"name": "A. Djiku",        "rating": 76, "role": "DEF"},
        {"name": "L. Ati-Zigi",     "rating": 76, "role": "GK"},
        {"name": "J. Paintsil",     "rating": 76, "role": "ATK"},
    ],
    "Egypt": [
        {"name": "M. Salah",        "rating": 89, "role": "ATK"},
        {"name": "T. Mohamed",      "rating": 75, "role": "MID"},
        {"name": "O. Kamal",        "rating": 73, "role": "ATK"},
        {"name": "A. Elneny",       "rating": 78, "role": "MID"},
        {"name": "M. Abdelmonem",   "rating": 74, "role": "DEF"},
        {"name": "A. Hegazi",       "rating": 78, "role": "DEF"},
        {"name": "G. El-Shenawy",   "rating": 78, "role": "GK"},
        {"name": "R. Sobhi",        "rating": 76, "role": "MID"},
    ],
    "Chile": [
        {"name": "A. Vidal",        "rating": 78, "role": "MID"},
        {"name": "E. Vargas",       "rating": 77, "role": "ATK"},
        {"name": "B. Brereton",     "rating": 75, "role": "ATK"},
        {"name": "C. Aránguiz",     "rating": 79, "role": "MID"},
        {"name": "G. Medel",        "rating": 78, "role": "DEF"},
        {"name": "M. Isla",         "rating": 76, "role": "DEF"},
        {"name": "C. Bravo",        "rating": 80, "role": "GK"},
        {"name": "A. Sánchez",      "rating": 78, "role": "ATK"},
    ],
    "Peru": [
        {"name": "G. Lapadula",     "rating": 74, "role": "ATK"},
        {"name": "C. Cueva",        "rating": 76, "role": "MID"},
        {"name": "Y. Pineau",       "rating": 72, "role": "MID"},
        {"name": "E. Flores",       "rating": 74, "role": "ATK"},
        {"name": "L. Abram",        "rating": 74, "role": "DEF"},
        {"name": "A. Callens",      "rating": 73, "role": "DEF"},
        {"name": "P. Gallese",      "rating": 76, "role": "GK"},
        {"name": "A. Carrillo",     "rating": 75, "role": "ATK"},
    ],
    "Venezuela": [
        {"name": "S. Rondón",       "rating": 74, "role": "ATK"},
        {"name": "T. Brekalo",      "rating": 75, "role": "ATK"},
        {"name": "Y. Herrera",      "rating": 73, "role": "MID"},
        {"name": "J. Murillo",      "rating": 74, "role": "DEF"},
        {"name": "O. González",     "rating": 72, "role": "DEF"},
        {"name": "W. Faríñez",      "rating": 76, "role": "GK"},
        {"name": "F. Casseres",     "rating": 72, "role": "MID"},
        {"name": "E. Cásseres",     "rating": 72, "role": "MID"},
    ],
    "Paraguay": [
        {"name": "M. Almirón",      "rating": 80, "role": "MID"},
        {"name": "Ángel Romero",    "rating": 75, "role": "ATK"},
        {"name": "R. Sánchez",      "rating": 73, "role": "ATK"},
        {"name": "G. Enciso",       "rating": 75, "role": "MID"},
        {"name": "F. Balbuena",     "rating": 76, "role": "DEF"},
        {"name": "O. Romero",       "rating": 73, "role": "DEF"},
        {"name": "A. Silva",        "rating": 74, "role": "GK"},
        {"name": "C. Báez",         "rating": 72, "role": "MID"},
    ],
    "Bolivia": [
        {"name": "M. Martins",      "rating": 70, "role": "ATK"},
        {"name": "R. Justiniano",   "rating": 68, "role": "MID"},
        {"name": "G. Antelo",       "rating": 67, "role": "ATK"},
        {"name": "C. Bejarano",     "rating": 67, "role": "MID"},
        {"name": "L. Haquín",       "rating": 66, "role": "DEF"},
        {"name": "J. Sagredo",      "rating": 65, "role": "DEF"},
        {"name": "C. Lampe",        "rating": 70, "role": "GK"},
        {"name": "J. Arce",         "rating": 65, "role": "MID"},
    ],
    "Cameroon": [
        {"name": "V. Aboubakar",    "rating": 79, "role": "ATK"},
        {"name": "A. Onana",        "rating": 86, "role": "GK"},
        {"name": "N. Nkoulou",      "rating": 77, "role": "DEF"},
        {"name": "M. Ngadeu",       "rating": 75, "role": "DEF"},
        {"name": "J. Kunde",        "rating": 73, "role": "DEF"},
        {"name": "S. Moukouri",     "rating": 72, "role": "MID"},
        {"name": "E. Choupo-Moting","rating": 78, "role": "ATK"},
        {"name": "G. Tolo",         "rating": 74, "role": "MID"},
    ],
    "Mali": [
        {"name": "A. Traoré",       "rating": 77, "role": "ATK"},
        {"name": "D. Samaké",       "rating": 72, "role": "MID"},
        {"name": "M. Haïdara",      "rating": 74, "role": "MID"},
        {"name": "Y. Kouyaté",      "rating": 72, "role": "DEF"},
        {"name": "H. Traoré",       "rating": 74, "role": "DEF"},
        {"name": "S. Diarra",       "rating": 70, "role": "GK"},
        {"name": "K. Coulibaly",    "rating": 71, "role": "ATK"},
        {"name": "M. Coulibaly",    "rating": 70, "role": "MID"},
    ],
    "Algeria": [
        {"name": "R. Mahrez",       "rating": 83, "role": "ATK"},
        {"name": "I. Bennacer",     "rating": 82, "role": "MID"},
        {"name": "Y. Brahimi",      "rating": 77, "role": "ATK"},
        {"name": "R. Ounas",        "rating": 77, "role": "ATK"},
        {"name": "D. Benlamri",     "rating": 76, "role": "DEF"},
        {"name": "R. Mandi",        "rating": 77, "role": "DEF"},
        {"name": "R. M'Bolhi",      "rating": 77, "role": "GK"},
        {"name": "N. Bentaleb",     "rating": 78, "role": "MID"},
    ],
    "Iraq": [
        {"name": "A. Mohanad",      "rating": 70, "role": "ATK"},
        {"name": "A. Karrar",       "rating": 68, "role": "MID"},
        {"name": "B. Nassir",       "rating": 67, "role": "ATK"},
        {"name": "A. Al-Hamdani",   "rating": 68, "role": "MID"},
        {"name": "A. Hashed",       "rating": 66, "role": "DEF"},
        {"name": "S. Kadhim",       "rating": 65, "role": "DEF"},
        {"name": "M. Hamid",        "rating": 68, "role": "GK"},
        {"name": "H. Kadeem",       "rating": 66, "role": "MID"},
    ],
    "Qatar": [
        {"name": "A. Afif",         "rating": 76, "role": "ATK"},
        {"name": "A. Al-Haydos",    "rating": 74, "role": "MID"},
        {"name": "A. Ali",          "rating": 72, "role": "ATK"},
        {"name": "K. Boudiaf",      "rating": 73, "role": "MID"},
        {"name": "P. Miguel",       "rating": 72, "role": "DEF"},
        {"name": "B. Khoukhi",      "rating": 72, "role": "DEF"},
        {"name": "S. Al-Sheeb",     "rating": 74, "role": "GK"},
        {"name": "H. Al-Haydos",    "rating": 71, "role": "ATK"},
    ],
    "Costa Rica": [
        {"name": "K. Navas",        "rating": 82, "role": "GK"},
        {"name": "J. Campbell",     "rating": 75, "role": "ATK"},
        {"name": "B. Ruiz",         "rating": 73, "role": "ATK"},
        {"name": "Y. Tejeda",       "rating": 74, "role": "MID"},
        {"name": "C. Gamboa",       "rating": 73, "role": "DEF"},
        {"name": "Ó. Duarte",       "rating": 74, "role": "DEF"},
        {"name": "J. Oviedo",       "rating": 73, "role": "DEF"},
        {"name": "A. Contreras",    "rating": 72, "role": "ATK"},
    ],
    "Panama": [
        {"name": "R. Torres",       "rating": 73, "role": "MID"},
        {"name": "G. Torres",       "rating": 74, "role": "ATK"},
        {"name": "M. Murillo",      "rating": 74, "role": "DEF"},
        {"name": "J. Davis",        "rating": 72, "role": "DEF"},
        {"name": "A. Murillo",      "rating": 71, "role": "DEF"},
        {"name": "L. Mejía",        "rating": 72, "role": "GK"},
        {"name": "A. Figuera",      "rating": 71, "role": "MID"},
        {"name": "J. Córdoba",      "rating": 71, "role": "ATK"},
    ],
    "Honduras": [
        {"name": "R. Aceituno",     "rating": 68, "role": "MID"},
        {"name": "J. Benguché",     "rating": 69, "role": "ATK"},
        {"name": "M. Elis",         "rating": 71, "role": "ATK"},
        {"name": "D. Acosta",       "rating": 68, "role": "MID"},
        {"name": "M. Beckeles",     "rating": 67, "role": "DEF"},
        {"name": "O. García",       "rating": 66, "role": "DEF"},
        {"name": "L. López",        "rating": 67, "role": "GK"},
        {"name": "A. Lozano",       "rating": 67, "role": "ATK"},
    ],
    "Jamaica": [
        {"name": "L. Bailey",       "rating": 78, "role": "ATK"},
        {"name": "M. Antonio",      "rating": 76, "role": "ATK"},
        {"name": "R. Lowe",         "rating": 72, "role": "MID"},
        {"name": "B. Reid",         "rating": 73, "role": "DEF"},
        {"name": "A. Pinnock",      "rating": 72, "role": "DEF"},
        {"name": "A. Blake",        "rating": 73, "role": "GK"},
        {"name": "D. Powell",       "rating": 71, "role": "MID"},
        {"name": "S. Nicholson",    "rating": 71, "role": "ATK"},
    ],
    "New Zealand": [
        {"name": "C. Wood",         "rating": 75, "role": "ATK"},
        {"name": "R. De Vries",     "rating": 70, "role": "MID"},
        {"name": "J. Garuccio",     "rating": 67, "role": "DEF"},
        {"name": "T. Payne",        "rating": 68, "role": "ATK"},
        {"name": "T. Smith",        "rating": 67, "role": "DEF"},
        {"name": "M. Woud",         "rating": 69, "role": "GK"},
        {"name": "B. Old",          "rating": 67, "role": "MID"},
        {"name": "N. Cacace",       "rating": 68, "role": "DEF"},
    ],
    "South Africa": [
        {"name": "P. Grobler",      "rating": 70, "role": "ATK"},
        {"name": "K. Dolly",        "rating": 72, "role": "ATK"},
        {"name": "T. Zungu",        "rating": 71, "role": "MID"},
        {"name": "S. Hlanti",       "rating": 70, "role": "DEF"},
        {"name": "L. Baloyi",       "rating": 69, "role": "DEF"},
        {"name": "R. Williams",     "rating": 71, "role": "GK"},
        {"name": "E. Zwane",        "rating": 70, "role": "ATK"},
        {"name": "G. Modise",       "rating": 69, "role": "MID"},
    ],
    "Indonesia": [
        {"name": "E. Haaland",      "rating": 65, "role": "ATK"},
        {"name": "T. Arhan",        "rating": 63, "role": "DEF"},
        {"name": "M. Ferarri",      "rating": 64, "role": "DEF"},
        {"name": "S. Pratama",      "rating": 62, "role": "MID"},
        {"name": "I. Arhan",        "rating": 62, "role": "DEF"},
        {"name": "E. Ndicka",       "rating": 63, "role": "DEF"},
        {"name": "E. Pahabol",      "rating": 61, "role": "ATK"},
        {"name": "M. Rashid",       "rating": 60, "role": "GK"},
    ],
    "Fiji": [
        {"name": "R. Kumar",        "rating": 58, "role": "ATK"},
        {"name": "J. Singh",        "rating": 56, "role": "MID"},
        {"name": "P. Brown",        "rating": 55, "role": "ATK"},
        {"name": "A. Waqaniburotu", "rating": 55, "role": "DEF"},
        {"name": "S. Dunn",         "rating": 54, "role": "DEF"},
        {"name": "P. Delai",        "rating": 55, "role": "GK"},
        {"name": "V. Sahib",        "rating": 54, "role": "MID"},
        {"name": "N. McGarry",      "rating": 54, "role": "ATK"},
    ],
    "Thailand": [
        {"name": "T. Dangda",       "rating": 65, "role": "ATK"},
        {"name": "C. Supachai",     "rating": 63, "role": "MID"},
        {"name": "P. Atirat",       "rating": 60, "role": "ATK"},
        {"name": "C. Chanathip",    "rating": 66, "role": "MID"},
        {"name": "T. Campiranon",   "rating": 60, "role": "DEF"},
        {"name": "P. Baihakki",     "rating": 59, "role": "DEF"},
        {"name": "K. Kawin",        "rating": 64, "role": "GK"},
        {"name": "T. Bunmathan",    "rating": 59, "role": "DEF"},
    ],
    "Czech Republic": [
        {"name": "P. Schick",       "rating": 83, "role": "ATK"},
        {"name": "T. Souček",       "rating": 84, "role": "MID"},
        {"name": "V. Coufal",       "rating": 78, "role": "DEF"},
        {"name": "A. Barák",        "rating": 79, "role": "MID"},
        {"name": "T. Čvančara",     "rating": 78, "role": "ATK"},
        {"name": "L. Krejčí",       "rating": 77, "role": "DEF"},
        {"name": "J. Staněk",       "rating": 79, "role": "GK"},
        {"name": "M. Havel",        "rating": 76, "role": "DEF"},
    ],
    "Switzerland": [
        {"name": "G. Xhaka",        "rating": 83, "role": "MID"},
        {"name": "B. Embolo",       "rating": 80, "role": "ATK"},
        {"name": "X. Shaqiri",      "rating": 80, "role": "ATK"},
        {"name": "R. Vargas",       "rating": 78, "role": "ATK"},
        {"name": "N. Elvedi",       "rating": 81, "role": "DEF"},
        {"name": "M. Akanji",       "rating": 83, "role": "DEF"},
        {"name": "Y. Sommer",       "rating": 84, "role": "GK"},
        {"name": "D. Ndoye",        "rating": 77, "role": "ATK"},
    ],
    "Turkey": [
        {"name": "H. Çalhanoğlu",   "rating": 84, "role": "MID"},
        {"name": "K. Akturkoglu",   "rating": 79, "role": "ATK"},
        {"name": "B. Yilmaz",       "rating": 78, "role": "ATK"},
        {"name": "S. Özcan",        "rating": 78, "role": "MID"},
        {"name": "M. Demiral",      "rating": 80, "role": "DEF"},
        {"name": "Z. Çelik",        "rating": 77, "role": "DEF"},
        {"name": "A. Günok",        "rating": 78, "role": "GK"},
        {"name": "E. Can",          "rating": 76, "role": "DEF"},
    ],
    "Norway": [
        {"name": "E. Haaland",      "rating": 94, "role": "ATK"},
        {"name": "M. Ødegaard",     "rating": 88, "role": "MID"},
        {"name": "A. Sørloth",      "rating": 81, "role": "ATK"},
        {"name": "S. Berge",        "rating": 79, "role": "MID"},
        {"name": "L. Ryerson",      "rating": 76, "role": "DEF"},
        {"name": "A. Strand Larsen","rating": 79, "role": "ATK"},
        {"name": "R. Nyland",       "rating": 78, "role": "GK"},
        {"name": "O. Ajer",         "rating": 77, "role": "DEF"},
    ],
    "Sweden": [
        {"name": "V. Gyökeres",     "rating": 86, "role": "ATK"},
        {"name": "A. Isak",         "rating": 84, "role": "ATK"},
        {"name": "D. Kulusevski",   "rating": 83, "role": "ATK"},
        {"name": "E. Forsberg",     "rating": 82, "role": "MID"},
        {"name": "A. Danielson",    "rating": 78, "role": "DEF"},
        {"name": "V. Lindelöf",     "rating": 81, "role": "DEF"},
        {"name": "R. Olsen",        "rating": 79, "role": "GK"},
        {"name": "M. Svanberg",     "rating": 77, "role": "MID"},
    ],
    "Tunisia": [
        {"name": "Y. Msakni",       "rating": 78, "role": "ATK"},
        {"name": "N. Sliti",        "rating": 76, "role": "MID"},
        {"name": "F. Ben Youssef",  "rating": 75, "role": "ATK"},
        {"name": "E. Skhiri",       "rating": 78, "role": "MID"},
        {"name": "D. Bronn",        "rating": 76, "role": "DEF"},
        {"name": "Y. Meriah",       "rating": 74, "role": "DEF"},
        {"name": "A. Dahmen",       "rating": 76, "role": "GK"},
        {"name": "H. Laïdouni",     "rating": 74, "role": "MID"},
    ],
    "Austria": [
        {"name": "D. Alaba",        "rating": 84, "role": "DEF"},
        {"name": "M. Arnautovic",   "rating": 81, "role": "ATK"},
        {"name": "K. Laimer",       "rating": 82, "role": "MID"},
        {"name": "C. Baumgartner",  "rating": 79, "role": "MID"},
        {"name": "P. Lienhart",     "rating": 78, "role": "DEF"},
        {"name": "R. Dragovic",     "rating": 78, "role": "DEF"},
        {"name": "P. Pentz",        "rating": 78, "role": "GK"},
        {"name": "F. Grillitsch",   "rating": 78, "role": "MID"},
    ],
    "Jordan": [
        {"name": "M. Al-Tamari",    "rating": 72, "role": "ATK"},
        {"name": "Y. Al-Naimat",    "rating": 70, "role": "MID"},
        {"name": "O. Al-Rashdan",   "rating": 68, "role": "ATK"},
        {"name": "B. Al-Omari",     "rating": 68, "role": "MID"},
        {"name": "B. Al-Dardour",   "rating": 67, "role": "DEF"},
        {"name": "A. Al-Hamarsheh", "rating": 66, "role": "DEF"},
        {"name": "A. Al-Rashdan",   "rating": 69, "role": "GK"},
        {"name": "W. Amarin",       "rating": 66, "role": "DEF"},
    ],
    "DR Congo": [
        {"name": "C. Mbemba",       "rating": 79, "role": "DEF"},
        {"name": "S. Kakesa",       "rating": 74, "role": "ATK"},
        {"name": "D. Bolasie",      "rating": 75, "role": "ATK"},
        {"name": "M. Luyindama",    "rating": 76, "role": "DEF"},
        {"name": "T. Tisserand",    "rating": 75, "role": "DEF"},
        {"name": "J. Mpoku",        "rating": 73, "role": "MID"},
        {"name": "A. Matampi",      "rating": 73, "role": "GK"},
        {"name": "P. Bongonda",     "rating": 73, "role": "ATK"},
    ],
    "Uzbekistan": [
        {"name": "E. Shomurodov",   "rating": 76, "role": "ATK"},
        {"name": "J. Khamdamov",    "rating": 72, "role": "ATK"},
        {"name": "O. Alijonov",     "rating": 70, "role": "MID"},
        {"name": "A. Ashurmatov",   "rating": 70, "role": "DEF"},
        {"name": "J. Teshaev",      "rating": 69, "role": "DEF"},
        {"name": "U. Nishonboev",   "rating": 70, "role": "GK"},
        {"name": "F. Holmatov",     "rating": 69, "role": "MID"},
        {"name": "I. Alikhonov",    "rating": 68, "role": "MID"},
    ],
    "Cape Verde": [
        {"name": "D. Andrade",      "rating": 74, "role": "ATK"},
        {"name": "J. Lopes",        "rating": 73, "role": "MID"},
        {"name": "R. Tavares",      "rating": 71, "role": "DEF"},
        {"name": "H. Djaniny",      "rating": 73, "role": "ATK"},
        {"name": "A. Borges",       "rating": 70, "role": "DEF"},
        {"name": "C. Fortes",       "rating": 70, "role": "DEF"},
        {"name": "M. Fona",         "rating": 69, "role": "GK"},
        {"name": "P. Varela",       "rating": 69, "role": "MID"},
    ],
    "Bosnia and Herzegovina": [
        {"name": "E. Džeko",        "rating": 82, "role": "ATK"},
        {"name": "M. Pjanić",       "rating": 83, "role": "MID"},
        {"name": "S. Kolasinac",    "rating": 79, "role": "DEF"},
        {"name": "H. Hajradinović", "rating": 76, "role": "MID"},
        {"name": "A. Civic",        "rating": 75, "role": "DEF"},
        {"name": "V. Kovacevic",    "rating": 74, "role": "DEF"},
        {"name": "I. Petrak",       "rating": 74, "role": "GK"},
        {"name": "M. Stajic",       "rating": 73, "role": "ATK"},
    ],
    "Haiti": [
        {"name": "K. Luckens",      "rating": 68, "role": "ATK"},
        {"name": "R. Borgella",     "rating": 66, "role": "MID"},
        {"name": "J. Pierre",       "rating": 65, "role": "ATK"},
        {"name": "S. Ceus",         "rating": 65, "role": "MID"},
        {"name": "G. Guerrier",     "rating": 64, "role": "DEF"},
        {"name": "P. Pétion",       "rating": 63, "role": "DEF"},
        {"name": "C. Léon",         "rating": 64, "role": "GK"},
        {"name": "B. Vilfort",      "rating": 63, "role": "MID"},
    ],
    "Scotland": [
        {"name": "A. Robertson",    "rating": 83, "role": "DEF"},
        {"name": "K. Tierney",      "rating": 81, "role": "DEF"},
        {"name": "J. McGinn",       "rating": 80, "role": "MID"},
        {"name": "S. McTominay",    "rating": 79, "role": "MID"},
        {"name": "L. Ferguson",     "rating": 77, "role": "ATK"},
        {"name": "C. Adams",        "rating": 76, "role": "ATK"},
        {"name": "A. Gunn",         "rating": 77, "role": "GK"},
        {"name": "G. Hendry",       "rating": 78, "role": "DEF"},
    ],
    "Ivory Coast": [
        {"name": "S. Haller",       "rating": 80, "role": "ATK"},
        {"name": "F. Koné",         "rating": 79, "role": "ATK"},
        {"name": "F. Kessié",       "rating": 83, "role": "MID"},
        {"name": "T. Doumbia",      "rating": 76, "role": "MID"},
        {"name": "W. Bailly",       "rating": 80, "role": "DEF"},
        {"name": "S. Aurier",       "rating": 79, "role": "DEF"},
        {"name": "A. Sangaré",      "rating": 80, "role": "MID"},
        {"name": "Y. Fofana",       "rating": 81, "role": "DEF"},
    ],
    "Curaçao": [
        {"name": "C. Bacuna",       "rating": 73, "role": "MID"},
        {"name": "G. Martina",      "rating": 71, "role": "DEF"},
        {"name": "L. Fer",          "rating": 72, "role": "MID"},
        {"name": "J. Clasie",       "rating": 71, "role": "MID"},
        {"name": "E. Botteghin",    "rating": 70, "role": "DEF"},
        {"name": "T. Trindade",     "rating": 69, "role": "DEF"},
        {"name": "E. Sanchez",      "rating": 70, "role": "GK"},
        {"name": "S. dos Santos",   "rating": 69, "role": "ATK"},
    ],
}

ROLE_WEIGHTS = {"ATK": 0.35, "MID": 0.20, "DEF": 0.15, "GK": 0.30}
AVG_RATING = 78


def _load_injuries() -> dict:
    if not os.path.exists(INJURIES_FILE):
        return {}
    with open(INJURIES_FILE) as f:
        return json.load(f)


def strength_offset(team: str, injuries=None):
    """
    Returns (attack_offset, defence_offset) as log-scale values.
    attack_offset: add to team's lambda (goals expected to score)
    defence_offset: subtract from opponent's lambda (goals expected to concede)
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
        contribution = (r - AVG_RATING) / 100  # e.g. rating 88 → +0.10, rating 68 → -0.10

        if role == "ATK":
            atk_offset += contribution * ROLE_WEIGHTS["ATK"]
        elif role == "MID":
            atk_offset += contribution * ROLE_WEIGHTS["MID"] * 0.5
            def_offset += contribution * ROLE_WEIGHTS["MID"] * 0.5
        elif role == "DEF":
            def_offset += contribution * ROLE_WEIGHTS["DEF"]
        elif role == "GK":
            def_offset += contribution * ROLE_WEIGHTS["GK"]

    # Subtract contribution of unavailable players
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
            elif role == "DEF":
                def_offset -= contribution * ROLE_WEIGHTS["DEF"]
            elif role == "GK":
                def_offset -= contribution * ROLE_WEIGHTS["GK"]

    return round(atk_offset, 4), round(def_offset, 4)


def get_all_teams() -> list[str]:
    return sorted(KEY_PLAYERS.keys())


def get_key_players(team: str) -> list[dict]:
    return KEY_PLAYERS.get(team, [])
