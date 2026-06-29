"""FIFA 2026 World Cup Predictor — Streamlit app."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pytz
from datetime import datetime

CEST = pytz.timezone("Europe/Paris")

def _today_cest():
    return datetime.now(CEST).date()

from data.fixtures_2026 import GROUP_FIXTURES, GROUPS, ALL_FIXTURES
from data.fetch_data import FIFA_RANKINGS
from model.dixon_coles import load_model, predict_match, MODEL_PATH
from model.tournament_sim import run_simulation
from data.predictions_store import save_prediction, save_actual, load_with_actuals, accuracy_summary
from data.fetch_scores import fetch_and_update_actuals
from data.elo import load_elo, ELO_CSV
from data.injuries import auto_detect_injuries, get_all as get_injuries, set_injury, set_suspension, clear_player
from data.squad_strength import get_key_players, get_all_teams

st.set_page_config(page_title="FIFA 2026 Predictor", page_icon="⚽", layout="wide")

# Auto-fetch scores + injury news once per 24h
if "scores_fetched" not in st.session_state:
    updated, msgs = fetch_and_update_actuals()
    injury_msgs = auto_detect_injuries()
    st.session_state["scores_fetched"] = True
    if updated:
        st.session_state["fetch_msgs"] = msgs
        st.cache_resource.clear()
    if injury_msgs:
        st.session_state["injury_msgs"] = injury_msgs

# ── Model + Elo loading ────────────────────────────────────────────────────────
@st.cache_resource
def get_model():
    if not os.path.exists(MODEL_PATH):
        st.error("Model not trained yet. Run `python train.py` first.")
        st.stop()
    return load_model()

@st.cache_resource
def get_elo():
    return load_elo() if os.path.exists(ELO_CSV) else {}


model = get_model()
elo_ratings = get_elo()
injuries = get_injuries()

# ── Sidebar navigation ─────────────────────────────────────────────────────────
st.sidebar.title("⚽ FIFA 2026 Predictor")
page = st.sidebar.radio("Navigation", ["Today's Matches", "Match Predictor", "Tournament Forecast", "Results & Accuracy", "Squad & Injuries"], label_visibility="collapsed")

ALL_TEAMS = sorted(FIFA_RANKINGS.keys())

# ── Page 1: Today's Matches ────────────────────────────────────────────────────
if page == "Today's Matches":
    st.title("Today's Matches")
    from datetime import date as _date
    _min, _max = _date(2026, 6, 11), _date(2026, 7, 19)
    _default = max(_min, min(_today_cest(), _max))
    selected_date = st.date_input("Select date", value=_default, min_value=_min, max_value=_max)

    from data.fetch_data import FIFA_RANKINGS as _FR
    day_fixtures = [f for f in ALL_FIXTURES if f["date"] == selected_date]

    if not day_fixtures:
        st.info(f"No fixtures on {selected_date}.")
    else:
        for fx in day_fixtures:
            is_group = "group" in fx
            stage_label = f"Group {fx['group']}" if is_group else fx.get("round", "Knockout")
            home, away = fx["home"], fx["away"]
            is_tbd = home not in _FR or away not in _FR

            with st.container():
                st.markdown(f"### {stage_label}: {home} vs {away}")
                if is_tbd:
                    st.info("Teams not yet determined — check back after qualifying rounds complete.")
                else:
                    neutral = not is_group
                    pred = predict_match(model, home, away, neutral=neutral,
                                        elo_ratings=elo_ratings, injuries=injuries)
                    save_prediction(fx, pred)
                    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 2])
                    c1.metric(home, f"xG {pred['home_xg']}")
                    c2.metric("Home Win", f"{pred['home_win_prob']*100:.1f}%")
                    c3.metric("Draw", f"{pred['draw_prob']*100:.1f}%")
                    c4.metric("Away Win", f"{pred['away_win_prob']*100:.1f}%")
                    c5.metric(away, f"xG {pred['away_xg']}")

                    ms = pred["most_likely_score"]
                    st.markdown(f"**Most likely score:** {home} **{ms[0]} – {ms[1]}** {away}")

                    labels = [f"{h}-{a}" for _, h, a in pred["top_scores"]]
                    values = [p for p, _, _ in pred["top_scores"]]
                    fig = go.Figure(go.Bar(x=labels, y=values, marker_color="#1f77b4"))
                    fig.update_layout(
                        height=200, margin=dict(t=10, b=10, l=10, r=10),
                        yaxis_title="Probability (%)", xaxis_title="Score",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                st.divider()


# ── Page 2: Match Predictor ────────────────────────────────────────────────────
elif page == "Match Predictor":
    st.title("Match Predictor")
    st.caption("Predict any matchup — group stage or hypothetical knockout.")

    col1, col2, col3 = st.columns([2, 1, 2])
    home = col1.selectbox("Home Team", ALL_TEAMS, index=ALL_TEAMS.index("Brazil"))
    col2.markdown("<br><br><center>vs</center>", unsafe_allow_html=True)
    away = col3.selectbox("Away Team", ALL_TEAMS, index=ALL_TEAMS.index("Argentina"))
    neutral = st.checkbox("Neutral venue (knockout stage)", value=False)

    if st.button("Predict", type="primary"):
        if home == away:
            st.error("Select two different teams.")
        else:
            pred = predict_match(model, home, away, neutral=neutral,
                                  elo_ratings=elo_ratings, injuries=injuries)

            c1, c2, c3 = st.columns(3)
            c1.metric(f"{home} Win", f"{pred['home_win_prob']*100:.1f}%")
            c2.metric("Draw", f"{pred['draw_prob']*100:.1f}%")
            c3.metric(f"{away} Win", f"{pred['away_win_prob']*100:.1f}%")

            ms = pred["most_likely_score"]
            st.success(f"Most likely: **{home} {ms[0]}–{ms[1]} {away}**  |  xG: {pred['home_xg']} – {pred['away_xg']}")

            # Score heatmap
            matrix = pred["score_matrix"][:8, :8]
            fig = px.imshow(
                matrix * 100,
                labels=dict(x=f"{away} Goals", y=f"{home} Goals", color="Prob %"),
                x=list(range(8)), y=list(range(8)),
                color_continuous_scale="Blues",
                title="Score probability heatmap (%)",
                text_auto=".1f",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Top 5 scores
            st.markdown("**Top 5 most likely scores:**")
            rows = [{"Score": f"{home} {h}–{a} {away}", "Probability": f"{p}%"}
                    for p, h, a in pred["top_scores"]]
            st.table(pd.DataFrame(rows))


# ── Page 3: Tournament Forecast ────────────────────────────────────────────────
elif page == "Tournament Forecast":
    st.title("Tournament Forecast")
    st.caption("Monte Carlo simulation of the full tournament.")

    n_sims = st.slider("Simulations", 1000, 20000, 5000, 1000)

    col_run, col_clear = st.columns([2, 1])
    if col_run.button("Run Simulation", type="primary"):
        with st.spinner("Simulating tournament... (~30s for 5000 sims)"):
            df = run_simulation(model, n_sims=n_sims, elo_ratings=elo_ratings, injuries=injuries)
        st.session_state["sim_results"] = df
    if col_clear.button("Clear results"):
        st.session_state.pop("sim_results", None)
        st.rerun()

    if "sim_results" in st.session_state:
        df = st.session_state["sim_results"]

        st.subheader("🏆 Top 4 Probabilities")
        top20 = df.head(20)
        fig = go.Figure()
        fig.add_bar(name="Win Tournament", x=top20["team"], y=top20["win_%"], marker_color="#FFD700")
        fig.add_bar(name="Reach Final", x=top20["team"], y=top20["final_%"], marker_color="#C0C0C0")
        fig.add_bar(name="Top 4", x=top20["team"], y=top20["top4_%"], marker_color="#CD7F32")
        fig.update_layout(barmode="group", height=400, xaxis_tickangle=-45,
                          yaxis_title="Probability (%)")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Full Rankings Table")
        st.dataframe(
            df,
            use_container_width=True,
            height=600,
            column_config={
                "win_%":      st.column_config.ProgressColumn("Win %",    min_value=0, max_value=100, format="%.1f%%"),
                "final_%":    st.column_config.ProgressColumn("Final %",  min_value=0, max_value=100, format="%.1f%%"),
                "top4_%":     st.column_config.ProgressColumn("Top 4 %",  min_value=0, max_value=100, format="%.1f%%"),
                "semifinal_%":st.column_config.ProgressColumn("Semi %",   min_value=0, max_value=100, format="%.1f%%"),
            },
        )


# ── Page 4: Results & Accuracy ─────────────────────────────────────────────────
elif page == "Results & Accuracy":
    st.title("Results & Accuracy")

    now_cest = datetime.now(CEST)
    st.caption(f"All times CEST. Last checked: {now_cest.strftime('%Y-%m-%d %H:%M CEST')}")

    # Show what was fetched this session
    if st.session_state.get("fetch_msgs"):
        with st.expander("Scores fetched on load", expanded=True):
            for msg in st.session_state["fetch_msgs"]:
                st.write(f"• {msg}")

    # Manual re-fetch button
    col_fetch, col_retrain, col_force = st.columns([1, 1, 1])
    if col_fetch.button("Re-fetch scores now"):
        updated, msgs = fetch_and_update_actuals(force=True)
        st.session_state["fetch_msgs"] = msgs
        if updated:
            st.success(f"Updated {updated} result(s). Model retrained.")
            st.cache_resource.clear()
            st.rerun()
        else:
            st.info(msgs[0] if msgs else "No new results found.")

    if col_retrain.button("Retrain model on WC results"):
        from data.fetch_scores import retrain_with_wc_results
        with st.spinner("Retraining…"):
            msg = retrain_with_wc_results()
        st.success(msg)
        st.cache_resource.clear()

    if col_force.button("Force full retrain", help="Re-fetches all historical data from ESPN then retrains. Use after a matchday."):
        from data.fetch_data import fetch_results, FIFA_RANKINGS
        from data.elo import build_elo, save_elo
        from data.fetch_scores import retrain_with_wc_results
        from model.dixon_coles import train
        with st.spinner("Fetching fresh data from ESPN and retraining…"):
            df = fetch_results(force=True)
            ratings = build_elo(df)
            save_elo(ratings)
            train(df, list(FIFA_RANKINGS.keys()))
            wc_msg = retrain_with_wc_results()
        st.success(f"Full retrain complete on {len(df)} matches. {wc_msg}")
        st.cache_resource.clear()
        st.rerun()

    st.divider()

    log = load_with_actuals()

    # Backfill predictions for rows that have actuals but no stored prediction
    missing_pred = log[log["actual_home"].notna() & log["pred_most_likely_home"].isna()]
    if not missing_pred.empty:
        from data.fixtures_2026 import ALL_FIXTURES
        fixture_map = {(str(f["date"]), f["home"], f["away"]): f for f in ALL_FIXTURES}
        for _, row in missing_pred.iterrows():
            home, away = row["home_team"], row["away_team"]
            if home not in FIFA_RANKINGS or away not in FIFA_RANKINGS:
                continue
            fx_key = (str(row["date"])[:10], home, away)
            fx = fixture_map.get(fx_key, {"date": row["date"], "home": home, "away": away})
            is_group = "group" in fx
            pred = predict_match(model, home, away, neutral=not is_group,
                                 elo_ratings=elo_ratings, injuries=injuries)
            save_prediction(fx, pred)
        log = load_with_actuals()

    summary = accuracy_summary(log)

    if not summary:
        st.info("No completed results yet — scores are fetched automatically once per day (CEST).")
    else:
        st.subheader(f"Accuracy over {summary['total']} matches")
        m1, m2, m3 = st.columns(3)
        m1.metric("Outcome correct (most likely score)", f"{summary['outcome_accuracy']}%")
        m2.metric("Favourite correct (highest prob)", f"{summary['favourite_accuracy']}%")
        m3.metric("Exact score correct", f"{summary['exact_score_accuracy']}%")

        st.subheader("Match-by-match breakdown")
        # All rows with actuals (incl. knockout results with no prediction yet)
        all_with_actuals = log.dropna(subset=["actual_home", "actual_away"]).copy()
        all_with_actuals["date"] = pd.to_datetime(all_with_actuals["date"])
        all_with_actuals.sort_values("date", ascending=False, inplace=True)
        all_with_actuals["date"] = all_with_actuals["date"].dt.strftime("%Y-%m-%d")
        all_with_actuals["actual_home"] = all_with_actuals["actual_home"].astype(int)
        all_with_actuals["actual_away"] = all_with_actuals["actual_away"].astype(int)

        if "penalty_winner" not in all_with_actuals.columns:
            all_with_actuals["penalty_winner"] = None
        has_pred = all_with_actuals["pred_most_likely_home"].notna()

        def _outcome(h, a):
            return "H" if h > a else ("D" if h == a else "A")

        def _actual_outcome(r):
            pw = r.get("penalty_winner")
            if pw == "home":
                return "H"
            if pw == "away":
                return "A"
            return _outcome(r["actual_home"], r["actual_away"])

        all_with_actuals["predicted"] = np.where(
            has_pred,
            all_with_actuals["pred_most_likely_home"].fillna(0).astype(int).astype(str) + "–" +
            all_with_actuals["pred_most_likely_away"].fillna(0).astype(int).astype(str),
            "—"
        )
        # Show "(pens)" suffix for penalty matches
        pens_suffix = all_with_actuals["penalty_winner"].notna().map({True: " (pens)", False: ""}).fillna("")
        all_with_actuals["actual"] = (
            all_with_actuals["actual_home"].astype(str) + "–" + all_with_actuals["actual_away"].astype(str) + pens_suffix
        )
        all_with_actuals["Outcome"] = all_with_actuals.apply(
            lambda r: ("✓" if _outcome(r["pred_most_likely_home"], r["pred_most_likely_away"]) == _actual_outcome(r) else "✗")
            if pd.notna(r["pred_most_likely_home"]) else "—", axis=1
        )
        all_with_actuals["Exact"] = all_with_actuals.apply(
            lambda r: "—" if r.get("penalty_winner") else
            (("✓" if int(r["pred_most_likely_home"]) == r["actual_home"] and int(r["pred_most_likely_away"]) == r["actual_away"] else "✗")
             if pd.notna(r["pred_most_likely_home"]) else "—"),
            axis=1
        )

        display = all_with_actuals.rename(columns={
            "date": "Date", "home_team": "Home", "away_team": "Away",
            "predicted": "Predicted", "actual": "Actual",
            "pred_home_win_pct": "H%", "pred_draw_pct": "D%", "pred_away_win_pct": "A%",
        })[["Date", "Home", "Away", "Predicted", "Actual", "H%", "D%", "A%", "Outcome", "Exact"]]

        st.dataframe(display, use_container_width=True, hide_index=True)


# ── Page 5: Squad & Injuries ───────────────────────────────────────────────────
elif page == "Squad & Injuries":
    st.title("Squad & Injuries")

    # Show auto-detected injury news
    if st.session_state.get("injury_msgs"):
        with st.expander("Auto-detected injury news (from ESPN)", expanded=True):
            for msg in st.session_state["injury_msgs"]:
                st.warning(msg)

    if st.button("Re-scan ESPN injury news"):
        msgs = auto_detect_injuries(force=True)
        injuries = get_injuries()  # reload
        if msgs:
            st.session_state["injury_msgs"] = msgs
            st.rerun()
        else:
            st.info("No new injury mentions detected.")

    st.divider()

    team = st.selectbox("Select team", get_all_teams())
    players = get_key_players(team)
    current_injuries = injuries.get(team, {"injured": [], "suspended": [], "notes": {}})

    st.subheader(f"{team} — Key Players")

    for p in players:
        is_injured = p["name"] in current_injuries.get("injured", [])
        is_suspended = p["name"] in current_injuries.get("suspended", [])
        note = current_injuries.get("notes", {}).get(p["name"], "")

        status = "🔴 Injured" if is_injured else ("🟡 Suspended" if is_suspended else "🟢 Available")
        c1, c2, c3, c4 = st.columns([3, 1, 1, 3])
        c1.markdown(f"**{p['name']}** ({p['role']})")
        c2.markdown(f"Rating: **{p['rating']}**")
        c3.markdown(status)
        if note:
            c4.caption(note)

        bc1, bc2, bc3 = st.columns([1, 1, 1])
        key_base = p["name"].replace(" ", "_").replace(".", "")
        if not is_injured and bc1.button("Mark Injured", key=f"inj_{key_base}"):
            set_injury(team, p["name"])
            st.rerun()
        if not is_suspended and bc2.button("Mark Suspended", key=f"sus_{key_base}"):
            set_suspension(team, p["name"])
            st.rerun()
        if (is_injured or is_suspended) and bc3.button("Clear", key=f"clr_{key_base}"):
            clear_player(team, p["name"])
            st.rerun()

    st.divider()
    st.subheader("Impact on xG")
    st.caption("Shows how current injuries shift expected goals vs a fully-fit squad.")

    from data.squad_strength import strength_offset
    full_atk, full_def = strength_offset(team, {})
    inj_atk, inj_def = strength_offset(team, injuries)
    delta_atk = inj_atk - full_atk
    delta_def = inj_def - full_def

    col1, col2 = st.columns(2)
    col1.metric("Attack offset (log-scale)", f"{inj_atk:+.4f}", delta=f"{delta_atk:+.4f}")
    col2.metric("Defence offset (log-scale)", f"{inj_def:+.4f}", delta=f"{delta_def:+.4f}")
    if delta_atk < -0.01 or delta_def < -0.01:
        xg_impact = (1 - np.exp(delta_atk)) * 100
        st.warning(f"Injuries reducing {team}'s expected goals by ~{abs(xg_impact):.1f}%")
