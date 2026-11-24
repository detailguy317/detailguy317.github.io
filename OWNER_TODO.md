# DG317 Garage - Owner To-Do List

Check things off on GitHub: open this file → pencil ✏️ → change `[ ]` to `[x]` → **Commit changes**.
The Sunday **Garage Report** (emailed to you) always shows the next unchecked items.

**Everything here is free.** The only thing that costs money is the optional DG317 AI (about 30 cents per 1,000 questions, capped at $5/month).

---

## 🚀 TONIGHT - go live (about 1-1.5 hours)

### A. Stay anonymous (15 min) - do these first
- [x] Make one new email used ONLY for DG317 (Proton Mail or Gmail). Every signup below uses it.
- [x] GitHub → Settings → Emails → turn ON "Keep my email addresses private" and "Block command line pushes that expose my email".
- [x] GitHub → your Profile → no real name, town or employer in Name / Bio / Location.

### B. Put the new site up (30 min)
- [x] Back up the current site: repo page → green **Code** button → **Download ZIP**. Save it.
- [x] Unzip DG317-site-v2.zip. On the repo page: **Add file → Upload files** → drag in EVERYTHING (folders too) → **Commit changes**. Keep your `webback.jpg`, `moonimage.png` and `CNAME` (if you have one) - don't delete anything that isn't being replaced.
  - Tip: the `.github` folder is hidden on Mac/Windows. Turn on "show hidden files" before dragging, or the robots won't come along.
- [x] Settings → Actions → General → **Workflow permissions → Read and write** → Save.
- [x] Actions tab → if it asks, click **"I understand my workflows, go ahead and enable them."**
- [x] Actions → run each one: **update-feeds**, **update-series**, **update-marketcaps**, **garage-report** (select it → **Run workflow**). Wait for green ✅. (update-videos waits for the YouTube key below.)
- [x] Open detailguy317.com on your phone AND computer. Check the footer's **Privacy & disclaimer** link opens. Hard-refresh (Ctrl+Shift+R / pull down on phone). Tap every bubble once.

### C. See who's visiting - free analytics (10 min)
- [x] dash.cloudflare.com → sign up with the DG317 email (free plan).
- [x] Left menu: **Analytics & Logs → Web Analytics → Add a site** → type detailguy317.com → choose the **JavaScript snippet** option (no DNS change needed).
- [x] Copy just the **token** from the snippet (the long code after `"token": "`) → paste it into `cfAnalyticsToken: ""` in index.html (edit on GitHub with the pencil) → Commit.
- [x] Visitors, top pages, countries and phone vs computer show up in Cloudflare within a few minutes. No cookie banner needed.

### D. Get the Garage Report email (5 min)
- [ ] Repo page → **Watch → All Activity**.
- [x] GitHub → Settings → Notifications → default email = your DG317 (Proton) email. (Done - custom routing not needed.)
- [x] After garage-report runs: **Issues** tab → open "📌 DG317 Garage Report" → right side **Pin issue**. Bookmark it on your phone.

**🎉 That's live.** Everything below makes it better, but the site works without it.

---

## 📅 THIS WEEK

### E. Turn on the money - Ko-fi does all of it on the free plan (30 min)
- [x] Ko-fi account made (DG317 Garage, Proton email, tips + memberships + shop turned on).
- [x] **Finish Stripe (started Nov 21 - saved, just pick up where you left off).** Gather first (packed-up desktop PC): **LLC EIN**, **registered agent / SOS business address** (check the agent allows it as a business address - if not, get a PO Box or virtual mailbox), and a business phone (used a free **Google Voice** number - Telnyx was never fully set up).
  - Business details: M.O.D.S. LLC (single-member LLC) · EIN · DBA DetailGuy317 · business address
  - Public details: statement descriptor `DETAILGUY317` · shortened `DG317` · support phone = **Google Voice number** (NOT personal cell) · support address = business address (NOT home)
  - Add bank (LLC business account if you have one) → Review and submit
  - If ID check fails because of the recent move: upload a driver's license photo / recent bill
  - Back in Ko-fi → Settings → Payment → Stripe should say **Connected**
- [ ] Ko-fi Settings → Payment: confirm location (US) · tip mode Coffee ($3) or Simple (min $2) · wording **Tip** · thank-you message
- [ ] ko-fi.com → sign up with the DG317 email → page name **DG317 Garage** → connect **Stripe** and/or **PayPal** (Settings → Payments). Payment apps need your real name for taxes, which is normal and private. Set every PUBLIC name to "DG317 Garage".
- [x] **PICK UP HERE (Nov 22):** Shop setup page is filled out. Finish adding the 4 products - each needs: name, description, **price** (watch it - it defaults to $0), Pay what you want ON, the PDF, the **cover image** (Claude made 4: DG317-cover-*.png - download to your computer first, then click the Preview images box and pick the file), the rights checkbox → Save and publish. Descriptions are in the chat (matched to what's in each PDF).
- [ ] Members get guides free: Shop → **Discounts** → make a **100% off** code for all 4 products → put the code in the Garage Member **welcome message** (Memberships → Edit tier).
- [x] **Shop → Add product** (Digital) for each paid guide. The PDFs are in your separate `premium` folder, NOT the website:
  - Voice Start Guide - **$1.99** minimum, turn ON **Pay what you want**
  - DIY Diagnostics Toolkit - **$1.99**, Pay what you want
  - AGM Battery & Sensor Guide - **$1.99**, Pay what you want
  - Bundle (all 3 in one zip) - **$2.99**, Pay what you want
- [x] **Memberships → Garage Member, $4.20/month.** Benefit: ALL guides included - post the 3 guides as members-only posts, and add each new guide there too. (Single guides stay $1.99 each in the Shop.)
- [ ] Later: edit the Garage Member **benefits** from the generic labels to custom text (remove each with ×, then + Add benefit → type in the top box):
  - All DG317 guides included: Voice Start, DIY Diagnostics, AGM Battery & Sensor
  - Every new guide free for members as it's released
  - Members-only how-tos & Market Mechanics extras
- [ ] Later (optional): add a 2:1 tier image / banner for Garage Member (ask Claude to make one).
- [x] Copy each Ko-fi link into index.html (DG_CONFIG): the guides' `link:""`, the Garage Member `link:""`, and your Ko-fi page URL in `support` (the ☕ button). Commit. The "Coming soon" buttons switch on by themselves.
- [ ] **Special codes for people you like:** Ko-fi → Shop → ••• on a product → **Create a discount**. 100% off = a free download. You can make one per person.
- [ ] Optional: PayPal business account → ask PayPal for **micropayments pricing** (cheaper on $1-3 sales).

### F. YouTube key - turns on the live race-video robot (15 min)
- [ ] console.cloud.google.com (DG317 Google account) → New project "DG317" → APIs & Services → Library → **YouTube Data API v3** → Enable → Credentials → **Create API key** → Restrict key → YouTube Data API v3.
- [ ] GitHub repo → Settings → Secrets and variables → Actions → **New repository secret** → name `YOUTUBE_API_KEY` → paste.
- [ ] Actions → **update-videos** → Run workflow → green ✅. From now on it checks for live racing every 30 minutes.
- [ ] Also paste the key once into yoursite/admin.html (it stays only in that browser) so you can hand-pick videos.

### G. Make DG317 answer almost anything - AI (20 min, about 30¢ per 1,000 questions)
The free DG317 already decodes any trouble code, knows 149 codes and 44 common symptoms, spots year/make/model, and links to free help for that exact vehicle. This step adds real AI answers on top.
- [ ] console.anthropic.com (DG317 email) → API Keys → Create key. **Billing → set a monthly limit of $5** so a flood can never run up a bill.
- [ ] dash.cloudflare.com (same account as step C) → **Workers & Pages → Create → Worker** → name it `dg317-ask` → Deploy → **Edit code** → paste ALL of `worker/ask-dg317-worker.js` → Deploy.
- [ ] Worker → **Settings → Variables and Secrets → Add** → type Secret, name `ANTHROPIC_API_KEY`, paste the key → Deploy.
- [ ] Copy the worker's URL (like `https://dg317-ask.yourname.workers.dev`) into `aiEndpoint: ""` in index.html → Commit.
- [ ] Ask it something on the site. You should see "🤖 DG317: ..." under the instant answer.

### H. Form for later (5 min - only needed when you switch `askMode`)
- [ ] formspree.io (DG317 email) → New form → copy the ID → paste into `formspreeId` in index.html. Not used while `askMode: "bot"`.

### I. Get found (spread over the week)
- [ ] **Google Search Console** (search.google.com/search-console) → Add property → URL prefix `https://detailguy317.com` → verify with **HTML file** (download it, upload it to the repo) → Sitemaps → submit `sitemap.xml`.
- [ ] **Bing Webmaster Tools** → "Import from Google Search Console".
- [ ] Claim **DG317 / DetailGuy317** everywhere, even if you don't post yet: YouTube, TikTok, Instagram, Facebook Page, X, Threads, Bluesky, Reddit, Pinterest, Rumble, Twitch. Paste each link into `socials` in index.html - blank ones stay hidden.
- [ ] Put the site link in the bio of every one of those, plus your beehiiv newsletter footer.
- [ ] Before posting any photo: no plates, shop signs, uniforms or street signs; phone camera location OFF.

---

### J. Keep a copy of NHTSA recall data (5 min, whenever you can - nightly is great, weekly is fine)
NHTSA updates its recall file every day. Keeping copies builds the data for the future DG317 Recall Center.
- [ ] Download the recalls file (2010 and newer, about 14 MB): https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip
- [ ] Save it in one folder (like `DG317 Recalls`) and rename it with the date, e.g. `recalls-2026-11-19.zip`. Keep the newest 4-5 and delete older ones - each new file already contains everything.
- [ ] Also bookmark the free lookups the Recall Center will use:
  - By year/make/model: `https://api.nhtsa.gov/recalls/recallsByVehicle?make=ford&model=f-150&modelYear=2016`
  - By recall (campaign) number: `https://api.nhtsa.gov/recalls/campaignNumber?campaignNumber=12V176000`
- [ ] Tip: when we build the Recall Center, a robot can download this file for you every night automatically - then this step goes away.

### N. Race videos - hand-pick one, or add a channel for the robot to watch
- [ ] **One race right now:** open `detailguy317.com/admin.html` (paste the YouTube key once) → paste the race's YouTube link into **Big / Box 1** (or click one in the robot-finds list) → check **"Use MY picks"** → **Copy** → GitHub → `data/live-content.js` → pencil → Ctrl+A, paste → Commit. When the race is over: uncheck "Use MY picks" → Copy → paste → Commit (hands it back to the robot).
- [ ] **A channel you always want covered:** in admin.html add its handle (like `@SRXracing`) to **Live Now Channels** → Copy → paste into `data/live-content.js` → Commit. The robot checks it every 30 minutes from then on.
- Heads-up: a video only plays on the site if its channel allows sharing (F1's doesn't - those open on YouTube instead). Only use official/licensed channels - no "free stream" sites (copyright takedowns, malware ads, and affiliates/Ko-fi ban them).

---

## 🔜 LATER - when it's earning or getting traffic

### K. Affiliates (apply after the site's been live 1-2 weeks - they look at it first)
- [ ] FlexOffers → **ALLDATAdiy** (8%)
- [ ] TradingView → Partner Program
- [ ] impact.com (one account) → **Summit Racing**, **JEGS**, **Allstate**
- [ ] CJ Affiliate (one account) → **Insurify**, **Liberty Mutual**, **Auto Barn**
- [ ] Lemonade → lemonade.com/partners
- [ ] Amazon Associates LAST (AGM chargers, maintainers, scan tools tie right into the guides). Heads-up: 3 sales in the first 180 days or they close the account.
- [ ] As each one approves: paste the link into `affiliates` (parts/tools) or `insurance` (quotes). Keep the "may earn a commission" lines.

### L. Switches you can flip any time (all in index.html → DG_CONFIG)
| Setting | What it does |
|---|---|
| `freeMode: true / false` | true = no prices anywhere. If you flip it on, ALSO put the 3 paid PDFs back in `guides/` so the free download buttons work. |
| `askMode: "bot"` | DG317 answers, nothing lands on you (launch setting) |
| `askMode: "stumper"` | Adds the optional "Stump the Master Tech" box - you pick a few for the newsletter when YOU want |
| `askMode: "personal"` | People expect a reply from you |
| `soon: true` on a tier | Shows it as "Coming soon". Delete `soon:true` and add price + link to turn one on (Stump, Quote 2nd Opinion, Remote Diag) |

### M. Bigger upgrades when money allows
- [ ] **DG317 Recall Center** (ask Claude to build it): a button for each U.S. builder (Ford/Lincoln, GM brands, Stellantis brands, Tesla, plus imports) → look up open recalls by year/make/model, by VIN, or by recall number - NHTSA's numbers AND the carmaker's own recall numbers - with links to each maker's official recall lookup. A nightly robot keeps the data fresh.
- [ ] ALLDATA / repair-data API for DG317 (ask Claude to wire it into the worker).
- [ ] beehiiv paid plan + Ad Network once the newsletter list is in the thousands.
- [ ] Stump the Master Tech → Quote 2nd Opinion → Remote Diag, one at a time, when you have the hours.

---

## 🔁 YOUR NORMAL WEEK (30-60 min - the Garage Report reminds you)
- When you can: grab the NHTSA recall file (section J).
- Sunday: read the Garage Report. Fix anything ⚠️, do the next 1-2 unchecked items.
- Glance at Cloudflare analytics (visitors) and Ko-fi (sales, members, messages).
- Race weekends: leave videos on auto, or hand-pick in admin.html (2 minutes).
- Once a month: ask Claude to "refresh the DG317 sales race board, celeb notes, car show dates and series status lines". Dead links are checked automatically every Sunday.