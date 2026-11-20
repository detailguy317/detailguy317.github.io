"""DG317 Garage Report - your to-do list, delivered by GitHub.

Weekly (Sunday morning): full report as a GitHub Issue -> GitHub emails it to you.
Daily (6pm Mountain):    only posts if a robot looks broken (stale data).
Run it any time: Actions tab -> garage-report -> Run workflow.

What's in it: site health, racing recap, market movers, your unchecked setup items
(from OWNER_TODO.md), reminders and a couple of ideas. Standard library only.
"""
import json, os, re, sys, urllib.request, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = dt.datetime.now(dt.timezone.utc)
MT = dt.timezone(dt.timedelta(hours=-7))
MODE = "daily" if "--daily" in sys.argv else "weekly"
HOME_TITLE = "📌 DG317 Garage Report (your to-do list)"

def load(path):
    try:
        txt = open(os.path.join(ROOT, path), encoding="utf-8").read()
    except Exception:
        return None
    try:
        return json.loads(txt[txt.index("= ") + 2:].strip().rstrip(";"))
    except Exception:   # hand-written JS (unquoted keys) - just grab the timestamp
        m = re.search(r'updated"?\s*:\s*"([^"]*)"', txt)
        return {"updated": m.group(1) if m else ""}

def age_h(iso):
    if not iso: return None
    try:
        d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if not d.tzinfo: d = d.replace(tzinfo=dt.timezone.utc)
        return (NOW - d).total_seconds() / 3600
    except Exception:
        return None

def nice(h):
    if h is None: return "never"
    return f"{h:.0f} hr ago" if h < 48 else f"{h/24:.0f} days ago"

# ---------------- site health ----------------
market_day = NOW.astimezone(MT).weekday() < 5
CHECKS = [  # (label, file, max hours before it's "stale", note)
    ("Headlines", "data/news.js", 6, "update-feeds robot"),
    ("Racing HQ standings + news", "data/series-live.js", 8, "update-series robot"),
    ("F1 standings", "data/series-auto.js", 8, "update-feeds robot"),
    ("Race videos", "data/racing-auto.js", 24 * 2, "update-videos robot - needs YOUTUBE_API_KEY secret"),
    ("Market-cap ranks", "data/marketcaps.js", 30 if market_day else 24 * 4, "update-marketcaps robot (weekdays only)"),
]
health, problems = [], []
for label, f, mx, note in CHECKS:
    d = load(f) or {}
    h = age_h(d.get("updated"))
    ok = h is not None and h <= mx
    if h is None and "YOUTUBE" in note:   # optional feature not switched on yet - not a problem
        health.append(f"| ⏸️ | {label} | not set up yet | {note} |"); continue
    health.append(f"| {'✅' if ok else '⚠️'} | {label} | {nice(h)} | {note} |")
    if not ok: problems.append(f"{label} ({nice(h)}) - check the **Actions** tab for a red ❌ run, open it, read the last lines")
live = load("data/series-live.js") or {}
fails = (live.get("stats") or {}).get("failed") or []
if fails:
    problems.append(f"Series robot couldn't read: {', '.join(fails[:12])}{' ...' if len(fails) > 12 else ''} (those cards keep their last good info - ask Claude to fix the Wikipedia title if it stays broken)")

# ---------------- racing recap ----------------
series = {}
try:
    st = open(os.path.join(ROOT, "data", "series.js"), encoding="utf-8").read()
    series = dict(re.findall(r'\{id:"([^"]+)",[^}]*?name:"((?:[^"\\]|\\.)*)"', st[: st.find("celebs:")]))
    manual_date = (re.search(r'updated:\s*"([\d-]+)"', st) or [None, None])[1]
except Exception:
    manual_date = None
MAJOR = ["nascar", "f1", "indycar", "imsa", "wec", "nhra", "motogp", "supercars", "wrc", "sx", "woo", "nmx", "btcc", "etrc"]
L = live.get("s") or {}
f1 = ((load("data/series-auto.js") or {}).get("f1")) or {}
racing = []
for sid in MAJOR:
    r = L.get(sid) or {}; name = series.get(sid, sid)
    lead = ""
    if sid == "f1" and f1.get("standings"):
        lead = f"🥇 {f1['standings'][0]['name']} ({f1['standings'][0]['pts']} pts, after rd {f1.get('round')})"
    elif r.get("top"):
        lead = f"🥇 {r['top'][0][1]} ({r['top'][0][2]} pts)"
    news = [n for n in (r.get("news") or []) if age_h(n.get("d") + "T12:00:00+00:00") is not None and age_h(n.get("d") + "T12:00:00+00:00") < 24 * 8]
    head = f"[{news[0]['t']}]({news[0]['u']})" if news else ""
    if lead or head:
        racing.append(f"- **{name}** {lead}{' - ' if lead and head else ''}{head}")

# ---------------- markets ----------------
caps = load("data/marketcaps.js") or {}
items = caps.get("items") or []
mk = []
if items:
    up = sorted(items, key=lambda x: -(x.get("chg") or 0))[:5]
    dn = sorted(items, key=lambda x: (x.get("chg") or 0))[:5]
    mk.append("Last session's biggest moves in your auto list:")
    mk.append("- 🟢 " + ", ".join(f"{x['t']} {x['chg']:+.1f}%" for x in up))
    mk.append("- 🔴 " + ", ".join(f"{x['t']} {x['chg']:+.1f}%" for x in dn))
    if items: mk.append(f"- 👑 Biggest by market cap: {items[0]['t']}")

# ---------------- owner to-do ----------------
todo_lines, open_count, done_count, section = [], 0, 0, ""
try:
    for line in open(os.path.join(ROOT, "OWNER_TODO.md"), encoding="utf-8"):
        if line.startswith("## "): section = line[3:].strip()
        m = re.match(r"\s*- \[( |x|X)\] (.*)", line)
        if not m: continue
        if m.group(1) == " ":
            open_count += 1
            if len(todo_lines) < 10: todo_lines.append(f"- [ ] {m.group(2).strip()}  _({section})_")
        else:
            done_count += 1
except FileNotFoundError:
    pass

# ---------------- dead links (from check_links.py, run just before this) ----------------
dead = []
try:
    lr = json.load(open(os.path.join(ROOT, "link-report.json")))
    for b in lr.get("bad", [])[:15]:
        dead.append(f"- `{b['code'] or 'no answer'}` {b['url']}  _(in {b['file']})_")
    if len(lr.get("bad", [])) > 15: dead.append(f"- ...and {len(lr['bad']) - 15} more")
    link_line = f"Checked {lr.get('checked', 0)} links: " + ("all good ✅" if not dead else f"**{len(lr['bad'])} look dead** - send this list to Claude to fix:")
except Exception:
    link_line = None

# ---------------- reminders + ideas ----------------
reminders = [
    "📨 Check the DG317 email for Formspree questions - answer the good ones (the best become newsletter/YouTube content).",
    "☕ Glance at Ko-fi / PayPal for sales, tips and messages.",
]
if manual_date and age_h(manual_date + "T00:00:00+00:00") and age_h(manual_date + "T00:00:00+00:00") > 24 * 30:
    reminders.append(f"✍️ Hand-written Racing HQ notes (celebs, car-show dates, series status lines) were last refreshed {manual_date}. Ask Claude: *\"refresh the DG317 celeb notes and car show dates\"*.")
_sales = load("data/sales.js") or {}
_sa = age_h((_sales.get("updated") or "") + "T00:00:00+00:00") if _sales.get("updated") else None
if _sa is None or _sa > 24 * 35:
    reminders.append(f"🚗 Sales Race board numbers were last checked {_sales.get('updated') or 'never'}. Automakers report early each month - ask Claude: *\"refresh the DG317 sales race board\"* (also great newsletter material).")
IDEAS = [
    "🧒 Kids: new monthly coloring page (a famous race car or a tow truck) - quick PDF, big hit with parents.",
    "🏁 Racers: 'First Autocross Day' checklist PDF - $1.99 or free newsletter bonus.",
    "📄 PDF idea: 'What that noise means' - squeals, clunks, grinds by symptom.",
    "📄 PDF idea: 'Buying tires without getting ripped off' - sizes, dates, load ratings.",
    "🎥 Short video: 'Code of the week' - pick the most-asked code from your inbox.",
    "🧒 Kids: 'Name that car sound' quiz round for the Kids Garage.",
    "🛡️ Newsletter: one insurance-saving tip a week (links to the CarStuff insurance box).",
    "📈 Newsletter: the weekly auto-stock movers above, in two sentences, with your mechanic's take.",
    "🔧 Ask A Mechanic: add your 10 most common answers to dtc-data.js so the bot handles them.",
    "🏆 Racing HQ: a 'Race of the week' pick on Fridays via admin.html.",
]
wk = int(NOW.strftime("%V"))
ideas = [IDEAS[wk % len(IDEAS)], IDEAS[(wk + 3) % len(IDEAS)]]

# ---------------- build ----------------
date = NOW.astimezone(MT).strftime("%a %b %d, %Y")
if MODE == "daily":
    if not problems:
        print("daily: all good, nothing to post"); sys.exit(0)
    title = f"⚠️ DG317 heads-up {date}: a robot needs a look"
    body = "Something on the site hasn't updated on schedule:\n\n" + "\n".join("- " + p for p in problems) + \
           "\n\nUsually it fixes itself on the next run. If this shows up 2 days in a row, paste the red ❌ run's last lines to Claude."
else:
    title = f"🔧 DG317 Garage Report - {date}"
    parts = [f"**{'✅ Site is running well.' if not problems else '⚠️ ' + str(len(problems)) + ' thing(s) need a look.'}**", ""]
    if problems: parts += ["### Fix first"] + ["- " + p for p in problems] + [""]
    parts += ["### Your to-do list", f"{done_count} done · **{open_count} left**. Next up:"] + (todo_lines or ["- 🎉 Setup list is all done!"]) + \
             ["", "_Check items off by editing `OWNER_TODO.md` on GitHub (pencil icon → change `[ ]` to `[x]` → Commit)._", ""]
    parts += ["### This week in racing"] + (racing or ["- (no racing data yet - the series robot fills this in)"]) + [""]
    if mk: parts += ["### Markets"] + mk + [""]
    if link_line: parts += ["### Link check", link_line] + dead + [""]
    parts += ["### Reminders"] + ["- " + r for r in reminders] + [""]
    parts += ["### Ideas to make the site better"] + ["- " + i for i in ideas] + [""]
    parts += ["### Robot health", "| | Data | Last update | Robot |", "|---|---|---|---|"] + health
    parts += ["", "_Auto-written every Sunday by `scripts/garage_report.py`. Don't close this one - it updates itself._"]
    body = "\n".join(parts)

repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
if not (repo and token):
    print(title); print(body); sys.exit(0)

def api(method, path, data=None):
    req = urllib.request.Request("https://api.github.com/repos/" + repo + path, method=method,
                                 data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                                          "User-Agent": "dg317-garage-report"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null")

# WEEKLY: one permanent issue you pin once. Each week its text is replaced with the newest
# report AND the report is added as a comment - the comment is what triggers the email.
# DAILY heads-up: its own issue (older heads-ups get closed).
issues = api("GET", "/issues?state=open&per_page=50") or []
if MODE == "weekly":
    home = next((i for i in issues if i.get("title") == HOME_TITLE and "pull_request" not in i), None)
    page = f"_Latest report: {date}. Older ones are in the comments below._\n\n" + body
    if home:
        api("PATCH", f"/issues/{home['number']}", {"body": page})
    else:
        home = api("POST", "/issues", {"title": HOME_TITLE, "body": page})
    api("POST", f"/issues/{home['number']}/comments", {"body": f"## {title}\n\n" + body})
    print("updated", home.get("html_url"))
else:
    for i in issues:
        if i.get("title", "").startswith("⚠️ DG317 heads-up") and "pull_request" not in i:
            api("PATCH", f"/issues/{i['number']}", {"state": "closed"})
    new = api("POST", "/issues", {"title": title, "body": body})
    print("posted", new.get("html_url"))
