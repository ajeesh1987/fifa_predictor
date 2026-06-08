"""Monte Carlo tournament simulator for 2026 WC."""

import numpy as np
import pandas as pd
from collections import defaultdict
from data.fixtures_2026 import GROUPS, GROUP_FIXTURES


def simulate_match(model, home, away, neutral=True, elo_ratings=None, injuries=None):
    from model.dixon_coles import predict_score_matrix
    lam, mu, matrix = predict_score_matrix(model, home, away, neutral=neutral,
                                            elo_ratings=elo_ratings, injuries=injuries)
    probs = matrix.flatten()
    probs /= probs.sum()
    idx = np.random.choice(len(probs), p=probs)
    h, a = divmod(idx, matrix.shape[1])
    return int(h), int(a)


def simulate_group_stage(model, n_sims=10000, elo_ratings=None, injuries=None):
    """Return dict: team -> array of group points over n_sims."""
    teams_all = [t for grp in GROUPS.values() for t in grp]
    points_accum = defaultdict(lambda: np.zeros(n_sims))
    gd_accum = defaultdict(lambda: np.zeros(n_sims))
    gf_accum = defaultdict(lambda: np.zeros(n_sims))

    for sim in range(n_sims):
        pts = defaultdict(int)
        gd = defaultdict(int)
        gf = defaultdict(int)
        for fx in GROUP_FIXTURES:
            hg, ag = simulate_match(model, fx["home"], fx["away"], neutral=False,
                                     elo_ratings=elo_ratings, injuries=injuries)
            if hg > ag:
                pts[fx["home"]] += 3
            elif hg == ag:
                pts[fx["home"]] += 1
                pts[fx["away"]] += 1
            else:
                pts[fx["away"]] += 3
            gd[fx["home"]] += hg - ag
            gd[fx["away"]] += ag - hg
            gf[fx["home"]] += hg
            gf[fx["away"]] += ag

        for t in teams_all:
            points_accum[t][sim] = pts[t]
            gd_accum[t][sim] = gd[t]
            gf_accum[t][sim] = gf[t]

    return points_accum, gd_accum, gf_accum


def qualify_from_groups(pts_sim, gd_sim, gf_sim, sim_idx):
    """For one simulation, return list of 32 qualified teams (top 2 per group + 8 best 3rd place)."""
    qualified = []
    third_place = []

    for grp, teams in GROUPS.items():
        standings = sorted(
            teams,
            key=lambda t: (pts_sim[t][sim_idx], gd_sim[t][sim_idx], gf_sim[t][sim_idx]),
            reverse=True,
        )
        qualified.extend(standings[:2])
        third_place.append((standings[2], pts_sim[standings[2]][sim_idx],
                            gd_sim[standings[2]][sim_idx], gf_sim[standings[2]][sim_idx]))

    # Best 8 third-place teams
    third_place.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
    qualified.extend([t[0] for t in third_place[:8]])
    return qualified  # 32 teams


def simulate_knockout(model, teams_32, elo_ratings=None, injuries=None):
    bracket = list(teams_32)
    np.random.shuffle(bracket)
    top4 = []

    while len(bracket) > 1:
        next_round = []
        semifinalists = len(bracket) == 4

        for i in range(0, len(bracket), 2):
            h, a = bracket[i], bracket[i+1]
            hg, ag = simulate_match(model, h, a, neutral=True,
                                     elo_ratings=elo_ratings, injuries=injuries)
            # Extra time / pens if draw
            if hg == ag:
                winner = h if np.random.random() < 0.5 else a
            else:
                winner = h if hg > ag else a
            next_round.append(winner)
            if semifinalists:
                loser = a if winner == h else h
                top4.append(loser)  # semi-final losers = 3rd/4th

        bracket = next_round

    top4.extend(bracket)  # winner
    return bracket[0], top4


def run_simulation(model, n_sims=5000, elo_ratings=None, injuries=None):
    print(f"Running {n_sims} simulations...")
    pts_sim, gd_sim, gf_sim = simulate_group_stage(model, n_sims,
                                                    elo_ratings=elo_ratings, injuries=injuries)

    top4_count = defaultdict(int)
    winner_count = defaultdict(int)
    finalist_count = defaultdict(int)
    semifinal_count = defaultdict(int)

    for sim in range(n_sims):
        qualified = qualify_from_groups(pts_sim, gd_sim, gf_sim, sim)
        winner, top4 = simulate_knockout(model, qualified, elo_ratings=elo_ratings, injuries=injuries)
        winner_count[winner] += 1
        for t in top4:
            top4_count[t] += 1
        if len(top4) >= 2:
            finalist_count[top4[-1]] += 1
            finalist_count[winner] += 1
        for t in top4:
            semifinal_count[t] += 1
        semifinal_count[winner] += 1

    teams = [t for grp in GROUPS.values() for t in grp]
    rows = []
    for t in teams:
        rows.append({
            "team": t,
            "win_%": round(winner_count[t] / n_sims * 100, 1),
            "final_%": round(finalist_count[t] / n_sims * 100, 1),
            "top4_%": round(top4_count[t] / n_sims * 100, 1),
            "semifinal_%": round(semifinal_count[t] / n_sims * 100, 1),
            "avg_group_pts": round(np.mean(pts_sim[t]), 2),
        })

    df = pd.DataFrame(rows).sort_values("win_%", ascending=False).reset_index(drop=True)
    return df
