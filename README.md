# DETAILGUY317 Garage (detailguy317.com)

Racing · Repairs · Automotive News · Information. A free car-help site that runs itself with robots on GitHub, with paid extras through Ko-fi.

**Your checklist is in `OWNER_TODO.md`.** The pinned **Garage Report** issue (emailed every Sunday) shows your next unchecked items, along with anything that broke.

---

## What's in here

| File | What it does |
|---|---|
| `index.html` | The whole site: homepage, Racing HQ, stocks, CarStuff, Jr Mechanics, Ask DG317, memberships. All settings live at the top in **`DG_CONFIG`**. |
| `privacy.html` | Privacy & disclaimer page (Cloudflare + Google Analytics, Ko-fi/Stripe, affiliates, car-advice disclaimer). |
| `admin.html` | Your private race-video picker. It isn't linked anywhere on the site. |
| `racing.html` | Racing pop-out window. |
| `dtc-data.js` | DG317's free brain: 149 trouble codes, first-check tips and 44 common symptoms. |
| `stocks-data.js` | The auto stocks in the scanner. |
| `data/live-content.js` | Race-video picks, "This Weekend" list, live channel buttons, joke headlines. Edit it through admin.html. |
| `data/series.js` | Racing HQ: 52 series, status lines, history links, celeb racers, car shows. Edit any time. |
| `data/sales.js` | Worldwide car-sales leaderboard (Sales Race tab). Refresh it monthly. |
| `data/*.js` (others) | Written by the robots. Don't edit by hand. |
| `guides/` | The 7 **free** PDF guides. **Never put the paid PDFs here**, because anyone could download them. The paid ones live only in the Ko-fi Shop. |
| `scripts/` + `.github/workflows/` | The robots (free on a public repo). |
| `worker/ask-dg317-worker.js` | Optional AI answers (Cloudflare Worker + Claude Haiku, about 30¢ per 1,000 questions, with a $5/month cap). |
| `sitemap.xml`, `robots.txt` | For Google and Bing. admin.html is hidden from search. |
| `CNAME`, `webback.jpg`, `moonimage.png` | **Keep these.** They hold your domain name and your background pictures. |

## The robots (all automatic)

| Robot | When | What it does |
|---|---|---|
| update-feeds | every 2 hrs | News headlines, F1 standings (adds each new champion by itself every January), This Day in Automotive History |
| update-series | every 2-3 hrs | Top-5 standings + headlines for all 52 Racing HQ series |
| update-videos | every 30 min | Finds live/recent racing on YouTube (needs the `YOUTUBE_API_KEY` secret). Skips videos whose owners block them from playing on other sites (like F1), and opens those on YouTube instead. |
| update-marketcaps | every 10 min, market hours | Market-cap ranks + pie chart |
| garage-report | Sunday ~8am MT + a 6pm heads-up only if something broke | Your to-do list, racing/market recap, dead-link check |

If a robot turns red ❌ in the Actions tab, open the run and read its last lines, or send a screenshot to Claude.

## Money (all through Ko-fi: ko-fi.com/dg317garage)

- **Tips:** "☕ Buy DG317 a Coffee" at $3 each
- **Garage Member:** $4.20/month. Members get every guide free automatically (100% member discount on all shop items).
- **Shop:** 3 guides at $1.99+ and the bundle at $2.99+ (pay what you want)
- Payouts go through Stripe to the business account. Buyers only see **DETAILGUY317** on their card statements.
- Every link lives in `DG_CONFIG` in index.html (`tiers[].link`, `premium[].link`, `support[]`). Blank ones stay hidden.

## Switches in `DG_CONFIG`

- `freeMode`: true = no prices anywhere
- `askMode`: `"bot"` (launch setting, nothing lands on you), `"stumper"` or `"personal"`
- `soon: true` on a tier shows it as "Coming soon"
- `aiEndpoint`: paste the Cloudflare Worker URL to turn on AI answers
- `cfAnalyticsToken`: Cloudflare Web Analytics (already set)
- `tickerSpeed`: news reader-board speed (60 is normal)
- `socials`: paste your DG317 social links. Blank ones stay hidden.

## Visitor stats & search

- **Cloudflare Web Analytics:** dash.cloudflare.com → Observability → Analytics → Web analytics
- **Google Analytics:** analytics.google.com. **Don't remove the gtag code**, because it's also what keeps Google Search Console verified.
- **Google Search Console + Bing Webmaster Tools:** both verified, sitemap submitted.

## Staying anonymous

- Nothing on the public site shows a real name, town or employer. Keep it that way, including in photos (no plates, shop signs or uniforms, and turn camera location off).
- Sign-ups use the Proton email. GitHub's email is private, and the robots commit as "dg317-robot".
- Stripe/Ko-fi have your real info privately for payouts only. The public name is DG317 Garage, and the support phone is a Google Voice number.
