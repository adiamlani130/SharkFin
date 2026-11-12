# Phone alerts and the threat level

## Portfolio threat level

The Portfolio page shows a **LOW / MEDIUM / HIGH** banner with a 0-100 score built from seven warning signs
(`sharkfin/threat.py`). Open "How the threat level is scored" under the banner to see each sign's points.

| Sign | Max points |
| --- | --- |
| Drop from the portfolio's 1-year peak (0 at 5% down, full at 20%) | 20 |
| Last day's loss worse than the normal daily range (95% VaR) | 15 |
| One stock too big (0 at 25% of the portfolio, full at 50%) | 15 |
| One sector too big (0 at 40%, full at 70%) | 10 |
| A holding reports earnings within 3 days (scaled by its weight) | 10 |
| SPY below its 200-day average | 10 |
| VIX above 25 | 10 |
| Holdings closed below their own 200-day average (scaled by weight) | 10 |

0-24 is LOW, 25-49 MEDIUM, and 50+ HIGH. It's a rule-of-thumb checklist, not a tested forecast: HIGH means
"look closer", not "sell".

## Phone alerts (free, through ntfy)

A GitHub Action (`.github/workflows/daily-alerts.yml`) runs on weekdays at 21:30 UTC, after the US close. It sends:

- **to you** (optional `NTFY_TOPIC`): that day's Dive Zone and Tech Breakout Rider buy signals.
- **to each signed-in user who turned alerts on**: the same signals if they want them, exit signals on stocks they
  hold, and their threat level when it rises a level or sits at HIGH. Quiet days send nothing.

Each run also reads Supabase, which stops a free project from pausing.

### One-time setup (about 3 minutes)

1. On GitHub, open the repo's **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `SUPABASE_URL`: the same URL as the app's `[supabase] url`
   - `SUPABASE_KEY`: the same `sb_secret_...` key
   - `NTFY_TOPIC` (optional): a long random name for your own signal feed, e.g. `sharkfin-k3j9x...`
2. Open the **Actions** tab, pick **Daily alerts**, and click **Run workflow** with "dry run" ticked. The log shows
   the day's buy signals and how many users have something to send. Because the repo is public, its Actions logs
   are too, so users' holdings and threat details are never printed there. Run it again without the dry run to send for real.

### Each user (in the app)

Portfolio → **Phone alerts after the close**: install the ntfy app, subscribe to the topic shown, choose what to
receive, and click **Save alerts**. **Send a test** sends a ping right away.

An ntfy topic works like a password: anyone who knows the name can read it. That's why the app makes long random
ones, and why messages never include share counts or dollar amounts.

### Keeping it running

- GitHub turns off scheduled workflows in a repo with **no commits for 60 days**. It emails you first, and one
  click (or any commit) turns the workflow back on.
- Actions minutes are free for public repos. The job takes a few minutes, because it downloads the S&P 500.
- ntfy.sh's free tier allows far more messages than this sends.
