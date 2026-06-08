"""Fetch data, build Elo ratings, train Dixon-Coles model."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from data.fetch_data import fetch_results, FIFA_RANKINGS
from data.elo import build_elo, save_elo
from model.dixon_coles import train

if __name__ == "__main__":
    force = "--force" in sys.argv
    df = fetch_results(force=force)
    known_teams = list(FIFA_RANKINGS.keys())

    print("Building Elo ratings...")
    ratings = build_elo(df)
    save_elo(ratings)
    print(f"Elo built for {len(ratings)} teams.")

    train(df, known_teams)
    print("Done. Run: streamlit run app.py")
