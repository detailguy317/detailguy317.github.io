# DETAILGUY317 Garage - v2 upgrade (built 2026-11-14)

Same look. New guts. Everything you edit week-to-week lives in `data/` - no more digging in index.html.

## What's in here
| File | What it does |
|---|---|
| `index.html` | The site. Same layout/colors; now scales evenly on any screen. |
| `racing.html` | Racing pop-out window (now resizes properly). |
| `admin.html` | **Your racing picker.** Find this weekend's YouTube race videos, pick 3, copy one file to GitHub. Not linked anywhere on the site. |
| `data/live-content.js` | The 3 race videos, race buttons, "This weekend" list, live channels, **your joke headlines**. |
| `data/news.js` | Real headlines - rewritten every morning by the robot. |
| `data/racing-auto.js` | Race videos the robot picked (used when live-content says `"mode": "auto"`). |
| `stocks-data.js` | 173 verified auto stocks for the scanner. |
| `data/marketcaps.js` | Market-cap rankings - rewritten ~every 10 min in market hours by `update-marketcaps` robot. |
| `data/series.js` | Racing HQ: series status lines, history links, celeb racers, car shows & auctions - edit anytime. |
| `data/series-auto.js` | F1 standings + every F1 champion since 1950 - robot updates every 2 hours. |
| `data/series-live.js` | Top-5 standings (from each season's Wikipedia page) + latest headlines (Google News) for every Racing HQ series - `update-series` robot, every 2-3 hours. |
| `OWNER_TODO.md` | **Your setup checklist.** The Sunday Garage Report shows the next unchecked items. |
| `scripts/garage_report.py` + `garage-report.yml` | Sunday Garage Report (GitHub Issue → emailed to you) + a 6pm heads-up only if a robot breaks. |
| `scripts/check_links.py` | Finds dead links every Sunday; they're listed in the Garage Report. |
| `sitemap.xml`, `robots.txt` | For Google / Bing. admin.html is hidden from search engines. |
| `guides/` | Free PDF guides (used car checklist, dash lights, quote red flags, winter kit, kids coloring page). |
| `dtc-data.js` | Trouble codes, first-check tips, common symptom answers for Ask A Mechanic. |
| `scripts/update_feeds.py` + `.github/workflows/update-feeds.yml` | The robot (GitHub Actions, free). |
| `worker/ask-dg317-worker.js` | DG317 AI answers (Cloudflare Worker + Claude Haiku, ~30 cents per 1,000 questions). Recommended. |

## Install (once)
1. Back up your current repo (Code -> Download ZIP).
2. Upload everything in this folder to the repo root. **Keep your `webback.jpg` and `moonimage.png`** - the new page uses them exactly like before.
3. Repo **Settings -> Actions -> General -> Workflow permissions -> Read and write** -> Save.
4. (For auto race videos) get a free YouTube Data API key, then **Settings -> Secrets and variables -> Actions -> New secret**: `YOUTUBE_API_KEY`.
5. **Actions tab -> Run workflow** on **update-feeds**, **update-videos**, **update-series**, **update-marketcaps** and **garage-report** to fill everything right away.
6. Repo main page -> **Watch -> All Activity** so the Garage Report reaches your (DG317) email.

## Robot schedule (all automatic, all free on a public repo)
| Robot | When | What |
|---|---|---|
| update-feeds | every 2 hrs | headlines, F1, This Day in Automotive History |
| update-videos | every 30 min, every day | catches LIVE racing on YouTube (channel RSS + one wide search, ~5,000 of 10,000 free units/day). Trusted channels fill the boxes; others show in admin.html for you to approve |
| update-series | every 3 hrs Mon-Thu, every 2 hrs Fri-Sun | standings + news for all 48 Racing HQ series |
| update-marketcaps | every 10 min, market hours Mon-Fri | market-cap ranks + pie chart |
| garage-report | Sunday ~8am MT (full) + 6pm daily (only if broken) | your to-do list, racing/market recap, dead links |

The full step-by-step setup list is in **OWNER_TODO.md**.

## Turn on the money / contact stuff (top of the script in index.html, `DG_CONFIG`)
- `formspreeId` - free at formspree.io. Questions land in your inbox; your email is never on the site.
- `tiers[].link` - Stripe Payment Links (or Ko-fi / Buy Me a Coffee memberships). Prices are suggestions - change them.
- `support[]` - tip/donate links. `socials{}` - only filled-in accounts show on the home box.
- `affiliates[]` - swap in your Summit / ALLDATA affiliate links when approved.
- `aiEndpoint` - optional, after deploying `worker/ask-dg317-worker.js`.

## Weekly racing routine (2 minutes, or zero if you let the robot do it)
Open `yoursite/admin.html` -> Find racing -> click "-> Big / Box 2 / Box 3" -> fix the buttons/weekend list -> **Copy** ->
GitHub -> `data/live-content.js` -> pencil -> paste -> Commit. Uncheck "Use MY picks" to hand it back to the robot.

## Staying anonymous
- Nothing personal is in these files. Make every social/payment account under DG317 / DetailGuy317.
- Use a separate email for Formspree, Stripe, YouTube, etc. Stripe/PayPal need your ID privately for payouts but don't show it to customers - set the public "business name" to DG317.
- Your GitHub username is public on the repo - make sure it isn't your real name.
- Robot commits are signed "dg317-robot", not you.
