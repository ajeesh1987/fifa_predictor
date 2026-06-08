# FIFA 2026 World Cup Predictor

Dixon-Coles Poisson model + Streamlit UI.

## Setup

```bash
cd "fifa predictor"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Train model (downloads ~47k historical international results, takes ~2 min)
python train.py

# Run app
streamlit run app.py
```

## Pages

- **Today's Matches** — scoreline predictions for any date in the tournament
- **Match Predictor** — any two teams, with score heatmap
- **Tournament Forecast** — Monte Carlo Top 4 / winner probabilities

## Retrain

```bash
python train.py --force   # re-download latest data
```
