"""
Dixon-Coles Poisson model — enhanced:
  - 18-month training window (xi=0.003) + 3-month recency boost (1.5×)
  - Competition weights (WC/majors 3×, qualifiers 1.5×, friendlies 0.5×)
  - Elo delta as feature (attack offset)
  - Squad strength + injury offset (attack and defence separately)
  - Learned rho parameter handles draw calibration (no hard-coded heuristic)
  - Head-to-head history offset
  - Warm-start from previous model
  - Separate home_adv for group stage vs neutral (knockout)
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson
from datetime import date, timedelta
import os, pickle

MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model.pkl")

XI = 0.003          # decay rate: ~18-month effective window
MIN_WEIGHT = 0.05

COMPETITION_WEIGHTS = {
    "FIFA World Cup": 3.0,
    "Copa América": 2.5,
    "UEFA Euro": 2.5,
    "Africa Cup of Nations": 2.0,
    "AFC Asian Cup": 2.0,
    "CONCACAF Gold Cup": 1.8,
    "UEFA Nations League": 1.5,
    "CONCACAF Nations League": 1.3,
    "FIFA World Cup qualification": 1.5,
    "UEFA Euro qualification": 1.5,
    "Copa América qualification": 1.4,
    "Friendly": 0.5,
}
DEFAULT_COMP_WEIGHT = 1.0


def _comp_weight(tournament: str) -> float:
    for key, w in COMPETITION_WEIGHTS.items():
        if key.lower() in str(tournament).lower():
            return w
    return DEFAULT_COMP_WEIGHT


def _time_weight(match_date, ref_date=None):
    if ref_date is None:
        ref_date = date.today()
    days = max((ref_date - match_date).days, 0)
    return np.exp(-XI * days)


def _tau(hg, ag, lam, mu, rho):
    if hg == 0 and ag == 0:
        return max(1 - lam * mu * rho, 1e-6)
    if hg == 0 and ag == 1:
        return max(1 + lam * rho, 1e-6)
    if hg == 1 and ag == 0:
        return max(1 + mu * rho, 1e-6)
    if hg == 1 and ag == 1:
        return max(1 - rho, 1e-6)
    return 1.0


def _neg_log_likelihood(params, teams, home_idx, away_idx, home_goals, away_goals, weights):
    n = len(teams)
    attack = params[:n]
    defence = params[n:2*n]
    home_adv = params[2*n]
    rho = params[2*n + 1]

    lam = np.exp(attack[home_idx] + defence[away_idx] + home_adv)
    mu = np.exp(attack[away_idx] + defence[home_idx])

    ll = 0
    for i in range(len(home_goals)):
        t = _tau(home_goals[i], away_goals[i], lam[i], mu[i], rho)
        ll += weights[i] * (
            np.log(t)
            + np.log(poisson.pmf(home_goals[i], lam[i]) + 1e-10)
            + np.log(poisson.pmf(away_goals[i], mu[i]) + 1e-10)
        )
    return -ll


def train(df: pd.DataFrame, known_teams: list, wc_matches=None):
    """
    Train on historical results + optional WC actuals (surprise-weighted).
    Applies 18-month window + competition weights.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    today = date.today()
    cutoff = today - timedelta(days=548)  # 18 months

    df = df[df["home_team"].isin(known_teams) & df["away_team"].isin(known_teams)]
    df = df[df["date"] >= cutoff]
    df["time_w"] = df["date"].apply(lambda d: _time_weight(d, today))
    df["comp_w"] = df.get("tournament", pd.Series("", index=df.index)).apply(_comp_weight)
    # Extra recency boost for matches in the last 90 days (form going into tournament)
    recent_cutoff = today - timedelta(days=90)
    df["recency_boost"] = df["date"].apply(lambda d: 1.5 if d >= recent_cutoff else 1.0)
    df["weight"] = df["time_w"] * df["comp_w"] * df["recency_boost"]
    df = df[df["weight"] > MIN_WEIGHT]

    if wc_matches is not None and not wc_matches.empty:
        wc = wc_matches.copy()
        wc = wc[wc["home_team"].isin(known_teams) & wc["away_team"].isin(known_teams)]
        wc["date"] = pd.to_datetime(wc["date"]).dt.date
        # WC matches: full time weight (today) × 3.0 comp weight × surprise multiplier
        wc["weight"] = wc.get("surprise_weight", pd.Series(1.0, index=wc.index)).clip(1.0, 4.0) * 3.0
        df = pd.concat(
            [df[["date","home_team","away_team","home_score","away_score","weight"]],
             wc[["date","home_team","away_team","home_score","away_score","weight"]]],
            ignore_index=True,
        )
        print(f"Injected {len(wc)} WC match(es).")

    teams = sorted(known_teams)
    t_idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)

    home_idx = df["home_team"].map(t_idx).values
    away_idx = df["away_team"].map(t_idx).values
    home_goals = df["home_score"].values.astype(int)
    away_goals = df["away_score"].values.astype(int)
    weights = df["weight"].values

    # Warm-start
    x0 = np.zeros(2 * n + 2)
    x0[2*n] = 0.3
    x0[2*n + 1] = -0.1
    if os.path.exists(MODEL_PATH):
        try:
            prev = load_model()
            for i, t in enumerate(teams):
                x0[i] = prev["attack"].get(t, 0.0)
                x0[n + i] = prev["defence"].get(t, 0.0)
            x0[2*n] = prev.get("home_adv", 0.3)
            x0[2*n + 1] = prev.get("rho", -0.1)
        except Exception:
            pass

    print(f"Training on {len(df)} matches for {n} teams...")

    result = minimize(
        _neg_log_likelihood, x0,
        args=(teams, home_idx, away_idx, home_goals, away_goals, weights),
        method="L-BFGS-B",
        options={"maxiter": 300, "ftol": 1e-7},
    )

    params = result.x
    # Normalise: enforce sum(attack) = 0 manually
    params[:n] -= params[:n].mean()
    model = {
        "teams": teams,
        "attack": dict(zip(teams, params[:n])),
        "defence": dict(zip(teams, params[n:2*n])),
        "home_adv": params[2*n],
        "rho": params[2*n + 1],
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print("Model saved.")
    return model


def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def _get_team_params(model, team):
    from data.fetch_data import FIFA_RANKINGS
    if team in model["attack"]:
        return model["attack"][team], model["defence"][team]
    rank_pts = FIFA_RANKINGS.get(team, 1300)
    scale = (rank_pts - 1550) / 1000
    return scale * 0.3, -scale * 0.3


def predict_score_matrix(model, home_team, away_team, neutral=False, max_goals=10,
                          elo_ratings=None, injuries=None):
    from data.squad_strength import strength_offset
    from data.elo import get_elo_delta, BASE_ELO
    from data.h2h import get_h2h_offset

    att_h, def_h = _get_team_params(model, home_team)
    att_a, def_a = _get_team_params(model, away_team)

    # Elo delta offset on attack (log-scale, ~0.05 per 20-Elo-point gap)
    elo_offset = 0.0
    if elo_ratings:
        delta = get_elo_delta(home_team, away_team, elo_ratings)
        elo_offset = delta * 0.05

    # Squad / injury offset (atk offset raises/lowers expected goals; def offset raises/lowers goals conceded)
    sq_atk_h, sq_def_h = strength_offset(home_team, injuries)
    sq_atk_a, sq_def_a = strength_offset(away_team, injuries)

    # H2H offset: +ve means home team historically outperforms vs this opponent
    h2h_offset = get_h2h_offset(home_team, away_team)

    home_adv = 0.0 if neutral else model["home_adv"]
    rho = model["rho"]

    # def offset: better defence = lower goals conceded by opponent, so subtract from opponent's lambda
    lam = np.exp(att_h + sq_atk_h - sq_def_a + home_adv + elo_offset + h2h_offset)
    mu  = np.exp(att_a + sq_atk_a - sq_def_h - elo_offset - h2h_offset)

    matrix = np.zeros((max_goals + 1, max_goals + 1))
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            t = _tau(i, j, lam, mu, rho)
            matrix[i][j] = t * poisson.pmf(i, lam) * poisson.pmf(j, mu)

    matrix /= matrix.sum()
    return lam, mu, matrix


def predict_match(model, home_team, away_team, neutral=False, elo_ratings=None, injuries=None):
    lam, mu, matrix = predict_score_matrix(
        model, home_team, away_team, neutral, elo_ratings=elo_ratings, injuries=injuries
    )

    home_win = float(np.sum(np.tril(matrix, -1)))
    draw     = float(np.sum(np.diag(matrix)))
    away_win = float(np.sum(np.triu(matrix, 1)))

    idx = np.unravel_index(np.argmax(matrix), matrix.shape)
    flat = [(matrix[i][j], i, j) for i in range(11) for j in range(11)]
    top_scores = sorted(flat, reverse=True)[:5]

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_xg": round(lam, 2),
        "away_xg": round(mu, 2),
        "home_win_prob": round(home_win, 3),
        "draw_prob": round(draw, 3),
        "away_win_prob": round(away_win, 3),
        "most_likely_score": (idx[0], idx[1]),
        "top_scores": [(round(p * 100, 1), h, a) for p, h, a in top_scores],
        "score_matrix": matrix,
    }
