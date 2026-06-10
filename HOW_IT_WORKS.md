# How the FIFA 2026 Predictor Works

This is a plain English explanation of what this app does, how it thinks, and why it gets things right or wrong. No coding knowledge needed.

---

## The Big Idea

The app tries to answer one question: given two football teams, what is the most likely scoreline?

It does this not by guessing, but by studying history. It looks at tens of thousands of international football matches played over the last 18 months, learns how many goals each team typically scores and concedes, and uses that to calculate the probability of every possible score — 0-0, 1-0, 2-1, and so on.

---

## How Goals Are Modelled

Goals in football are rare, random events. A team might expect to score 1.4 goals in a game on average, but the actual number on the day could be 0, 1, 2, or occasionally 4. There is a branch of mathematics called the Poisson distribution that was specifically designed to model exactly this kind of thing — rare events happening randomly over a fixed time period. It turns out to be a very good fit for football.

So for every match, the app calculates two numbers: how many goals the home team is likely to score on average, and how many the away team is likely to score. From those two averages, it can calculate the exact probability of any scoreline. For example, it might find that Brazil vs Ecuador has a 14% chance of ending 1-0, an 11% chance of 2-0, a 9% chance of 1-1, and so on across every combination up to 10-10.

The most likely score is the one with the highest probability. The win/draw/loss percentages are just the sum of all the individual score probabilities that correspond to each outcome.

The model also includes a built-in correction for draws (the Dixon-Coles rho parameter). Pure Poisson models slightly underestimate draws because they assume the two teams' goals are independent of each other. In reality, close matches tend to stay close. This correction is learned from the data itself, so it self-calibrates to whatever patterns exist in modern international football.

---

## Where the Numbers Come From

The app downloaded a dataset of over 47,000 international football matches going back decades. From this it learned an attack strength and a defence strength for each of the 50 World Cup teams.

A team with a high attack strength scores more goals than average. A team with a high defence strength concedes fewer. When the two teams meet, the expected goals are calculated by combining the attacker's attack strength with the defender's defence strength — crucially, a strong defence reduces how many goals the opponent is expected to score. This is why a strong attack playing a weak defence produces a high expected scoreline, while two defensively solid teams tend to produce a low-scoring prediction.

Not all matches are treated equally. A World Cup final tells us far more about a team's true level than a friendly played in June with a rotated squad. So competitive matches like World Cup games, Copa América and European Championship fixtures are given three times the weight of friendlies when the model learns from history. Qualification matches sit somewhere in the middle. This way, the model's understanding of each team is shaped mostly by the matches that actually mattered.

---

## Recent Form Matters More

A match from three years ago is not as useful as a match from three months ago. Teams change. Players age. Managers get sacked. Tactics evolve.

To account for this, the app applies a time decay to every historical match. Recent matches carry their full weight. Matches from a year ago carry less. Anything older than about 18 months has almost no influence at all.

On top of this, matches from the last three months get an additional 1.5× boost. This means the team's form in the run-up to the World Cup carries extra weight compared to what they were doing a year ago. A team that peaked six months ago but has been in poor form recently will have that recent dip reflected.

---

## Elo Ratings

On top of the basic attack and defence numbers, the app also maintains a live Elo rating for every team. Elo was originally invented for chess rankings and works beautifully for football too.

The idea is simple. Every team starts with a score of 1500. When you beat a strong team, your rating goes up a lot. When you beat a weak team, it goes up a little. When you lose to a strong team, it barely drops. When you lose to a weak team, it drops significantly. Over time, the ratings converge on each team's true level.

These Elo ratings are used as an additional signal on top of the attack and defence parameters. A team with a notably higher Elo gets a small boost to their expected goals in that match.

Crucially, once the tournament starts, Elo ratings are updated with every completed World Cup match. So by the knockout stages, the Elo system reflects actual tournament performance — a team that surprised everyone in the group stage will see their rating climb, and that will be reflected in knockout predictions.

---

## Head-to-Head History

Some teams consistently perform above or below their general level against specific opponents — regardless of overall form. Argentina tend to be very good against European sides in knockout tournaments. Certain rivalries produce predictably low-scoring, tense affairs.

The app accounts for this by looking at the last ten meetings between any two teams and calculating an average goal-difference offset. This is applied as a small additional adjustment to the expected goals calculation. The effect is deliberately capped so it never overrides the core team strength signal — it is a nudge, not a rewrite.

---

## Squad Strength and Injuries

Knowing a team's historical goals is useful. Knowing who is actually on the pitch is better.

For each of the 50 World Cup teams, the app now tracks eight key players rather than three — covering the main attackers, midfielders, defenders, and goalkeeper. Each player has a FIFA rating. Their overall contribution is split between attack (goalscoring threat) and defence (goals conceded) depending on their role.

The roles and their influence work as follows:
- **Attackers** (35% weight) shift how many goals the team is expected to score
- **Midfielders** (20% weight) split evenly between attack and defence
- **Defenders** (15% weight) shift how many goals the opponent is expected to score
- **Goalkeepers** (30% weight) significantly influence how many goals are conceded

A world-class goalkeeper like Alisson or Donnarumma meaningfully reduces the team's expected goals against. A top striker adds to their expected goals scored. If either is injured, both sides of that equation shift.

Every day the app automatically scans ESPN's World Cup news feed for injury and suspension mentions. If it finds a headline that says a key player is injured, it flags it automatically. You can review these on the Squad and Injuries page, confirm or dismiss them, and manually mark players as injured or suspended yourself. The moment you do that, every future prediction adjusts.

---

## Learning From Mistakes During the Tournament

Every time the app shows you a prediction for today's matches, it saves that prediction to a log. The next day, once the real scores come in, it compares what it predicted to what actually happened.

If the result was expected — say, Brazil winning comfortably as the 75% favourite — the model updates only slightly. It already knew this.

If the result was a surprise — say, a heavy underdog wins — the model takes that much more seriously. The upset is given a higher weight, up to four times the normal influence, when the model retrains. This is how it adapts during the tournament.

Three things happen after each matchday:

1. **The Dixon-Coles model retrains** incorporating the new WC results, with surprise results weighted heavily
2. **Elo ratings update** using the actual WC scores — tournament performance now feeds directly into the team quality signal
3. **H2H history refreshes** — if teams have now played each other at this tournament, that meeting enters future H2H calculations

This retraining happens automatically every night. You can also trigger it manually using the **Retrain model on WC results** button on the Results page. By the knockout stages, the model has absorbed everything from the group stage and adjusted accordingly.

---

## The Tournament Simulator

The Top 4 prediction works differently from a single match prediction. Rather than just calculating one most-likely outcome, the app simulates the entire tournament thousands of times from start to finish.

In each simulation, every group match is played out using the score probabilities, knockout games are resolved including extra time and penalties, and a winner is crowned. After running this process five thousand times, the app counts how often each team won, reached the final, or finished in the top four. Those counts become percentages — so if France wins the simulated tournament 1,400 times out of 5,000, they have a 28% chance of winning.

This approach captures something important: the randomness of football. Even the best team in the world does not win every tournament. Upsets happen. A single red card or missed penalty can change everything. The simulation reflects that uncertainty honestly rather than pretending any one outcome is inevitable.

---

## What the Model Does Not Know

It is worth being honest about the limits.

The model does not know about tactical setups. It does not know if a team is playing a high press or sitting deep. It does not know about the mental state of a squad, the quality of a manager's preparation, or the effect of altitude and heat at the venue. It does not have access to training ground news or pre-match press conferences.

It also does not know about players outside the tracked eight per team. A fringe squad member with excellent club form who earns an unexpected starting role will not be in the database.

These gaps are real. They are why even the best models in the world — including those used by professional betting firms — are wrong about specific matches more than half the time. Football is wonderfully unpredictable, and a model that claimed otherwise would be lying to you.

What a good model does is get the direction right more often than chance, identify which teams are genuinely strong versus overrated, and price the probability of upsets honestly. That is what this app aims to do.

---

## How to Get the Best Out of It

**Check the Squad and Injuries page before big matches.** The auto-detection from ESPN catches most things but sometimes misses or misidentifies. A two-minute manual check before matchday will meaningfully improve accuracy.

**Keep the model up to date.** After each matchday, either let the app auto-retrain overnight or hit the Retrain button on the Results page. The knockout predictions will be noticeably sharper once the model has absorbed the group stage results.

**Run the Tournament Forecast with at least 5,000 simulations** for reliable percentages. Lower numbers are faster but noisier.

**Look at the score heatmap on the Match Predictor page** rather than just the single most likely score. The most likely score might only have a 12% chance of happening. The heatmap shows you the full picture — whether a game is likely to be high-scoring or tight, and where the probability is spread.

**Check back on the Results and Accuracy page** as the tournament progresses. Watching how the model performs in real time, where it is confident and correct versus where it is surprised, tells you a lot about which teams are playing above or below their historical level.
