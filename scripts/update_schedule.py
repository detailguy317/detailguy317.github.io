"""DG317 schedule robot - fills the Race Center's "This Weekend & Coming Up" list by itself.
Run by GitHub Actions (update-series.yml), every few hours.

Sources (all free, no keys):
  * Formula 1  - Jolpica (Ergast) API: exact session times
  * NASCAR     - nascar.com's public race-list feed: Cup, O'Reilly (Xfinity) and Trucks with start times
  * Everything else - the series' Wikipedia season page calendar (this year + next year, so the
    off-season already shows next season's openers). Wikipedia gives dates, not start times.
Output: data/schedule-auto.js (window.DG_SCHEDULE). Anything that fails is skipped and the
last good copy for that series is kept, so the list never goes blank. Standard library only.
"""
import json, os, re, sys, time, html, urllib.request, urllib.error, urllib.parse, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from update_series import Tables, grid          # same tiny Wikipedia table reader the standings robot uses

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "schedule-auto.js")
UA = {"User-Agent": "DG317-Garage-schedule-robot/1.1 (https://detailguy317.com; racing fan site)"}
WIKI_EVERY_HOURS = 20          # race calendars barely change - read Wikipedia about once a day, reuse the copy in between
NOW = dt.datetime.now(dt.timezone.utc)
try:
    from zoneinfo import ZoneInfo
    MT, ET_ = ZoneInfo("America/Denver"), ZoneInfo("America/New_York")
except Exception:
    MT, ET_ = dt.timezone(dt.timedelta(hours=-7)), dt.timezone(dt.timedelta(hours=-5))
TODAY = NOW.astimezone(MT).date()
KEEP_PAST_DAYS, AHEAD_DAYS = 1, 120

# series id (matches data/series.js) -> (display name, Wikipedia season page titles; {Y} = year)
WIKI = {
    "indycar":  ("IndyCar", ["{Y} IndyCar Series"]),
    "imsa":     ("IMSA", ["{Y} IMSA SportsCar Championship"]),
    "wec":      ("WEC", ["{Y} FIA World Endurance Championship"]),
    "motogp":   ("MotoGP", ["{Y} MotoGP World Championship"]),
    "wsbk":     ("World Superbike", ["{Y} Superbike World Championship"]),
    "wrc":      ("WRC Rally", ["{Y} World Rally Championship"]),
    "fe":       ("Formula E", ["{Y}–{NYY} Formula E World Championship", "{PY}–{YY} Formula E World Championship"]),
    "nhra":     ("NHRA", ["{Y} NHRA Mission Foods Drag Racing Series", "{Y} NHRA Camping World Drag Racing Series"]),
    "sx":       ("Supercross", ["{Y} AMA Supercross Championship"]),
    "promx":    ("Pro Motocross", ["{Y} AMA Pro Motocross Championship"]),
    "supercars":("Supercars", ["{Y} Supercars Championship"]),
    "btcc":     ("BTCC", ["{Y} British Touring Car Championship"]),
    "dtm":      ("DTM", ["{Y} Deutsche Tourenwagen Masters"]),
    "supergt":  ("Super GT", ["{Y} Super GT Series"]),
    "f2":       ("Formula 2", ["{Y} FIA Formula 2 Championship"]),
    "indynxt":  ("Indy NXT", ["{Y} Indy NXT"]),
    "gtwc":     ("GT World Challenge", ["{Y} GT World Challenge America"]),
    "dakar":    ("Dakar Rally", ["{Y} Dakar Rally"]),
}
NASCAR = {"1": ("nascar", "NASCAR Cup"), "2": ("nos", "NASCAR O'Reilly"), "3": ("trucks", "NASCAR Trucks")}

MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
MON = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
DASH = r"\s*[–—-]\s*"
DATE_RX = [  # (regex, how to read it) - order matters, ranges first
    (re.compile(rf"(\d{{1,2}})\s+{MON}{DASH}(\d{{1,2}})\s+{MON}", re.I), "dM-dM"),   # 28 November – 1 December
    (re.compile(rf"{MON}\s+(\d{{1,2}}){DASH}{MON}\s+(\d{{1,2}})", re.I), "Md-Md"),   # November 28 – December 1
    (re.compile(rf"(\d{{1,2}}){DASH}(\d{{1,2}})\s+{MON}", re.I), "d-dM"),             # 26–29 November
    (re.compile(rf"{MON}\s+(\d{{1,2}}){DASH}(\d{{1,2}})\b", re.I), "Md-d"),           # November 26–29
    (re.compile(rf"(\d{{1,2}})\s+{MON}", re.I), "dM"),                                  # 7 March
    (re.compile(rf"{MON}\s+(\d{{1,2}})\b", re.I), "Md"),                                # March 7
]

def get(url, timeout=25):
    for wait in (0, 20, 60):                     # Wikipedia says "slow down" (429)? wait and try again
        if wait: time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or wait == 60: raise
            try: time.sleep(min(60, int(e.headers.get("Retry-After") or 0)))
            except Exception: pass

def mo(s): return MONTHS[s.lower()[:3]]

def parse_dates(txt, year):
    """-> (first_day, last_day) as dates, or None"""
    t = html.unescape(re.sub(r"\[[^\]]*\]", "", txt or ""))
    for rx, kind in DATE_RX:
        m = rx.search(t)
        if not m: continue
        g = m.groups()
        try:
            if kind == "dM-dM": a, b = dt.date(year, mo(g[1]), int(g[0])), dt.date(year, mo(g[3]), int(g[2]))
            elif kind == "Md-Md": a, b = dt.date(year, mo(g[0]), int(g[1])), dt.date(year, mo(g[2]), int(g[3]))
            elif kind == "d-dM": a, b = dt.date(year, mo(g[2]), int(g[0])), dt.date(year, mo(g[2]), int(g[1]))
            elif kind == "Md-d": a, b = dt.date(year, mo(g[0]), int(g[1])), dt.date(year, mo(g[0]), int(g[2]))
            elif kind == "dM": a = b = dt.date(year, mo(g[1]), int(g[0]))
            else: a = b = dt.date(year, mo(g[0]), int(g[1]))
        except ValueError:
            continue
        if b < a: b = b.replace(year=b.year + 1)          # Dec 30 - Jan 2
        return a, b
    return None

DATE_COL = re.compile(r"^\W*(race |event )?dates?(\s*\(s\))?\W*$", re.I)
NAME_COLS = [re.compile(r"^(race name|grand prix|event|event name|race|rally|e-prix|name|round name)$", re.I),
             re.compile(r"^(circuit|track|venue|location|circuit name)$", re.I)]
STAND_HDR = re.compile(r"^(pos\.?|pts\.?|points|driver|drivers|rider|team|no\.)$", re.I)   # standings / entry tables, not calendars

def calendar_from_html(page_html, year, split=False):
    p = Tables(); p.feed(page_html)
    best, seen_hdrs = [], []
    for t in p.tables:
        if "wikitable" not in t["cls"]: continue
        g = grid(t["rows"])
        if len(g) < 3: continue
        hi = next((k for k, row in enumerate(g[:3]) if any(DATE_COL.match(v.strip()) for v in row)), None)   # header may be row 1-3
        if hi is None:
            if len(seen_hdrs) < 4: seen_hdrs.append(" | ".join(v.strip()[:18] for v in g[0][:7]))
            continue
        hdr = g[hi]; g = g[hi:]
        if sum(1 for v in hdr if STAND_HDR.match(v.strip())) >= 2: continue
        di = next((i for i, v in enumerate(hdr) if DATE_COL.match(v.strip())), None)
        ni = None
        for rx in NAME_COLS:                               # first name-ish column whose cells aren't just numbers
            for i, v in enumerate(hdr):
                if i != di and rx.match(v.strip()) and sum(1 for r in g[1:6] if len(r) > i and not re.fullmatch(r"[\d\s.]*", r[i])) >= 2:
                    ni = i; break
            if ni is not None: break
        if ni is None: continue
        rows, seen = [], set()
        for r in g[1:]:
            if len(r) <= max(di, ni): continue
            d = parse_dates(r[di], year)
            if not d: continue
            if split and d[0].month < 7: d = (d[0].replace(year=year + 1), d[1].replace(year=year + 1))   # "2026–27" season pages
            name = re.sub(r"\[[^\]]*\]", "", r[ni]).strip()
            name = re.sub(r"^[A-Z]{3}\s+(?=[A-Z])", "", name)    # drop leftover flag codes like "QAT "
            if not name or (name, d) in seen: continue
            seen.add((name, d)); rows.append((d[0], d[1], name[:80]))
        if len(rows) > len(best): best = rows
    calendar_from_html.debug = seen_hdrs
    return best

def wiki_page(title):
    q = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "text", "format": "json", "formatversion": "2", "redirects": "1"})
    data = json.loads(get("https://en.wikipedia.org/w/api.php?" + q))
    if "error" in data: return None
    return data["parse"]["text"]

def titles(pats, year):
    sub = {"{Y}": str(year), "{PY}": str(year - 1), "{NY}": str(year + 1), "{YY}": str(year)[-2:], "{NYY}": str(year + 1)[-2:]}
    out = []
    for t in pats:
        s = t
        for k, v in sub.items(): s = s.replace(k, v)
        out.append(s)
    return out

WHY = {}
BLOCKED = {"on": False}        # Wikipedia still says "too many requests" after waiting -> stop asking this run, keep old copies
def wiki_series(sid, name, pats):
    rows = []
    if BLOCKED["on"]:
        WHY[sid] = ["skipped this run - Wikipedia asked us to slow down; using the last good copy"]; return rows
    for year in (TODAY.year, TODAY.year + 1):              # next year too: in the off-season that's what's coming up
        for title in titles(pats, year):
            try:
                page = wiki_page(title)
                if not page: WHY.setdefault(sid, []).append(f"{title}: no page"); continue
                cal = calendar_from_html(page, year, split="–" in title)
                if not cal: WHY.setdefault(sid, []).append(f"{title}: no calendar table; first table headers: {getattr(calendar_from_html, 'debug', [])}")
                if cal:
                    src = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
                    rows += [{"sid": sid, "series": name, "event": n, "start": a.isoformat(), "end": b.isoformat(),
                              "exact": False, "src": src} for a, b, n in cal]
                    break
            except Exception as e:
                print(f"   wiki {title}: {e}"); WHY.setdefault(sid, []).append(f"{title}: {e}")
                if "429" in str(e): BLOCKED["on"] = True; return rows
            time.sleep(1.5)
    return rows

def f1():
    rows = []
    for season in ("current", str(TODAY.year + 1)):
        try:
            races = json.loads(get(f"https://api.jolpi.ca/ergast/f1/{season}.json"))["MRData"]["RaceTable"]["Races"]
        except Exception as e:
            print(f"   F1 {season}: {e}"); continue
        for r in races:
            def at(x):
                if not x or not x.get("date"): return None
                return dt.datetime.fromisoformat(x["date"] + "T" + (x.get("time") or "12:00:00Z").replace("Z", "+00:00"))
            race = at(r)
            sess = [at(r.get(k)) for k in ("FirstPractice", "SecondPractice", "ThirdPractice", "SprintQualifying", "Sprint", "Qualifying")]
            sess = [s for s in sess if s] + ([race] if race else [])
            if not race: continue
            first = min(sess).astimezone(MT).date(); last = race.astimezone(MT).date()
            q = r.get("Qualifying"); sp = r.get("Sprint")
            extra = []
            if q and at(q): extra.append("Qualifying " + at(q).astimezone(MT).strftime("%a %-I:%M%p").replace(":00", "").replace("AM", "am").replace("PM", "pm"))
            if sp and at(sp): extra.append("Sprint " + at(sp).astimezone(MT).strftime("%a %-I:%M%p").replace(":00", "").replace("AM", "am").replace("PM", "pm"))
            rows.append({"sid": "f1", "series": "Formula 1", "event": r.get("raceName", "Grand Prix"), "start": first.isoformat(),
                         "end": last.isoformat(), "exact": True, "race_utc": race.isoformat(), "extra": " · ".join(extra),
                         "src": r.get("url") or "https://www.formula1.com"})
    return rows

def nascar():
    rows = []
    for year in (TODAY.year, TODAY.year + 1):
        try:
            data = json.loads(get(f"https://cf.nascar.com/cacher/{year}/race_list_basic.json"))
        except Exception as e:
            print(f"   NASCAR {year}: {e}"); continue
        for key, races in data.items():
            num = key.split("_")[-1]
            if num not in NASCAR or not isinstance(races, list): continue
            sid, name = NASCAR[num]
            for r in races:
                ds = r.get("date_scheduled") or r.get("race_date")
                if not ds: continue
                try:
                    t = dt.datetime.fromisoformat(ds.replace("Z", "+00:00"))
                    if not t.tzinfo: t = t.replace(tzinfo=ET_)   # nascar.com times are Eastern
                except Exception:
                    continue
                rows.append({"sid": sid, "series": name, "event": (r.get("race_name") or "Race").strip()[:80] + (f" · {r['track_name']}" if r.get("track_name") else ""),
                             "start": t.astimezone(MT).date().isoformat(), "end": t.astimezone(MT).date().isoformat(),
                             "exact": True, "race_utc": t.astimezone(dt.timezone.utc).isoformat(), "src": "https://www.nascar.com/nascar-cup-series/schedule/"})
    return rows

def load_old():
    try:
        t = open(OUT, encoding="utf-8").read()
        return json.loads(t[t.index("=") + 1:].strip().rstrip(";"))
    except Exception:
        return {}

def main():
    old = load_old(); old_by = {}
    for r in old.get("all", old.get("rows", [])): old_by.setdefault(r["sid"], []).append(r)
    groups, stats = {}, {"ok": [], "kept_old": []}
    for sid, fn in (("f1", f1), ("nascar_all", nascar)):
        rows = fn()
        if rows:
            for r in rows: groups.setdefault(r["sid"], []).append(r)
            stats["ok"].append(sid)
    wiki_at = dict(old.get("wiki_at", {}))
    for sid, (name, pats) in WIKI.items():
        last = wiki_at.get(sid)
        fresh = last and (NOW - dt.datetime.fromisoformat(last)).total_seconds() < WIKI_EVERY_HOURS * 3600
        if fresh and old_by.get(sid):                    # read it recently - reuse, be nice to Wikipedia
            groups[sid] = old_by[sid]; continue
        rows = wiki_series(sid, name, pats)
        if rows:
            groups[sid] = rows; stats["ok"].append(sid); wiki_at[sid] = NOW.isoformat(timespec="minutes"); print(f"ok   {sid}: {len(rows)} dates")
        else: print(f"miss {sid}: {WHY.get(sid)}")
    for sid, rows in old_by.items():                        # a source failed this run -> keep its last good copy
        if sid not in groups: groups[sid] = rows; stats["kept_old"].append(sid)
    keep_all = [r for rows in groups.values() for r in rows if dt.date.fromisoformat(r["end"]) >= TODAY - dt.timedelta(days=KEEP_PAST_DAYS)]
    lo, hi = TODAY - dt.timedelta(days=KEEP_PAST_DAYS), TODAY + dt.timedelta(days=AHEAD_DAYS)
    allrows = [r for rows in groups.values() for r in rows
               if dt.date.fromisoformat(r["end"]) >= lo and dt.date.fromisoformat(r["start"]) <= hi]
    seen, out = set(), []
    for r in sorted(allrows, key=lambda r: (r["start"], r.get("race_utc", ""), r["series"])):
        k = (r["sid"], r["event"].lower(), r["start"])
        if k in seen: continue
        seen.add(k); out.append(r)
    if not out and old.get("rows"):
        print("nothing new - keeping the old schedule"); return
    open(OUT, "w", encoding="utf-8").write(
        "/* Written automatically by scripts/update_schedule.py - don't edit by hand. Add your own rows in admin.html instead. */\n"
        "window.DG_SCHEDULE = " + json.dumps({"updated": NOW.isoformat(timespec="minutes"), "rows": out, "stats": stats, "why_missed": WHY, "wiki_at": wiki_at, "all": keep_all}, ensure_ascii=False) + ";\n")
    print(f"schedule: {len(out)} upcoming dates from {len(groups)} series")

if __name__ == "__main__":
    main()
