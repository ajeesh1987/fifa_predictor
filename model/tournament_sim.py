"""Monte Carlo tournament simulator for 2026 WC."""

import numpy as np
import pandas as pd
from collections import defaultdict
from data.fixtures_2026 import GROUPS, GROUP_FIXTURES


def _build_matrix_cache(model, elo_ratings, injuries):
    """Precompute score matrices for group fixtures only; KO pairs computed lazily."""
    from model.dixon_coles import predict_score_matrix
    cache = {}
    for fx in GROUP_FIXTURES:
        key = (fx["home"], fx["away"], False)
        if key not in cache:
            _, _, matrix = predict_score_matrix(model, fx["home"], fx["away"],
                                                neutral=False, elo_ratings=elo_ratings,
                                                injuries=injuries)
            cache[key] = matrix.flatten() / matrix.sum()
    return cache


def _sim_from_cache(cache, home, away, neutral):
    probs = cache[(home, away, neutral)]
    idx = np.random.choice(len(probs), p=probs)
    n = int(len(probs) ** 0.5)
    return divmod(idx, n)


def simulate_match(model, home, away, neutral=True, elo_ratings=None, injuries=None):
    from model.dixon_coles import predict_score_matrix
    lam, mu, matrix = predict_score_matrix(model, home, away, neutral=neutral,
                                            elo_ratings=elo_ratings, injuries=injuries)
    probs = matrix.flatten()
    probs /= probs.sum()
    idx = np.random.choice(len(probs), p=probs)
    h, a = divmod(idx, matrix.shape[1])
    return int(h), int(a)


def simulate_group_stage(model, n_sims=10000, elo_ratings=None, injuries=None, cache=None):
    """Return dict: team -> array of group points over n_sims."""
    teams_all = [t for grp in GROUPS.values() for t in grp]
    points_accum = defaultdict(lambda: np.zeros(n_sims))
    gd_accum = defaultdict(lambda: np.zeros(n_sims))
    gf_accum = defaultdict(lambda: np.zeros(n_sims))

    # Vectorise: for each fixture draw all n_sims outcomes at once
    # Draw all fixture outcomes at once: shape (n_fixtures, n_sims)
    n_fx = len(GROUP_FIXTURES)
    all_hg = np.zeros((n_fx, n_sims), dtype=np.int8)
    all_ag = np.zeros((n_fx, n_sims), dtype=np.int8)
    side = 11  # score matrix side length

    for fi, fx in enumerate(GROUP_FIXTURES):
        key = (fx["home"], fx["away"], False)
        if cache and key in cache:
            probs = cache[key]
        else:
            from model.dixon_coles import predict_score_matrix
            _, _, mat = predict_score_matrix(model, fx["home"], fx["away"], neutral=False,
                                             elo_ratings=elo_ratings, injuries=injuries)
            probs = mat.flatten(); probs /= probs.sum()
        idxs = np.random.choice(len(probs), size=n_sims, p=probs)
        all_hg[fi] = idxs // side
        all_ag[fi] = idxs % side

    # Score points/gd/gf using numpy ops — no per-sim Python loop
    team_idx = {t: i for i, t in enumerate(teams_all)}
    n_teams = len(teams_all)
    pts_arr = np.zeros((n_teams, n_sims), dtype=np.int16)
    gd_arr  = np.zeros((n_teams, n_sims), dtype=np.int16)
    gf_arr  = np.zeros((n_teams, n_sims), dtype=np.int16)

    for fi, fx in enumerate(GROUP_FIXTURES):
        hi = team_idx[fx["home"]]
        ai = team_idx[fx["away"]]
        hg = all_hg[fi]  # shape (n_sims,)
        ag = all_ag[fi]

        home_win = hg > ag
        draw     = hg == ag
        away_win = ag > hg

        pts_arr[hi] += np.where(home_win, 3, np.where(draw, 1, 0))
        pts_arr[ai] += np.where(away_win, 3, np.where(draw, 1, 0))
        gd_arr[hi]  += hg - ag
        gd_arr[ai]  += ag - hg
        gf_arr[hi]  += hg
        gf_arr[ai]  += ag

    for t in teams_all:
        i = team_idx[t]
        points_accum[t] = pts_arr[i].astype(float)
        gd_accum[t]     = gd_arr[i].astype(float)
        gf_accum[t]     = gf_arr[i].astype(float)

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


def simulate_knockout(model, teams_32, elo_ratings=None, injuries=None, cache=None):
    bracket = list(teams_32)
    np.random.shuffle(bracket)
    top4 = []

    while len(bracket) > 1:
        next_round = []
        semifinalists = len(bracket) == 4

        for i in range(0, len(bracket), 2):
            h, a = bracket[i], bracket[i+1]
            key = (h, a, True)
            if cache is not None and key not in cache:
                from model.dixon_coles import predict_score_matrix
                _, _, mat = predict_score_matrix(model, h, a, neutral=True,
                                                 elo_ratings=elo_ratings, injuries=injuries)
                cache[key] = mat.flatten() / mat.sum()
            if cache and key in cache:
                hg, ag = _sim_from_cache(cache, h, a, True)
            else:
                hg, ag = simulate_match(model, h, a, neutral=True,
                                        elo_ratings=elo_ratings, injuries=injuries)
            if hg == ag:
                winner = h if np.random.random() < 0.5 else a
            else:
                winner = h if hg > ag else a
            next_round.append(winner)
            if semifinalists:
                loser = a if winner == h else h
                top4.append(loser)

        bracket = next_round

    top4.extend(bracket)
    return bracket[0], top4


def run_simulation(model, n_sims=5000, elo_ratings=None, injuries=None):
    print(f"Running {n_sims} simulations...")
    print("Precomputing match matrices...")
    cache = _build_matrix_cache(model, elo_ratings, injuries)
    pts_sim, gd_sim, gf_sim = simulate_group_stage(model, n_sims,
                                                    elo_ratings=elo_ratings, injuries=injuries,
                                                    cache=cache)

    top4_count = defaultdict(int)
    winner_count = defaultdict(int)
    finalist_count = defaultdict(int)
    semifinal_count = defaultdict(int)

    for sim in range(n_sims):
        qualified = qualify_from_groups(pts_sim, gd_sim, gf_sim, sim)
        winner, top4 = simulate_knockout(model, qualified, elo_ratings=elo_ratings, injuries=injuries, cache=cache)
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
