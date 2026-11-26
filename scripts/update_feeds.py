"""DG317 daily robot - run by GitHub Actions (see .github/workflows/update-feeds.yml).
1) Pulls racing / auto headlines from RSS feeds + Google News, tags each one by maker/topic, ranks them
   -> data/news.js (Top Stories + CarStuff bubbles) and data/news-history.js (last 7 days)
2) If a YOUTUBE_API_KEY secret is set, finds live/upcoming/recent race videos -> data/racing-auto.js
Standard library only. Any feed that fails is skipped, the site keeps the last good copy."""
import json, os, re, sys, time, html, urllib.request, urllib.parse, datetime as dt
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDS = [  # (tag, source name, url) - add/remove freely. A feed that fails is skipped (see the robot log).
    ("RACING", "RACER", "https://racer.com/feed/"),
    ("RACING", "Motorsport.com", "https://www.motorsport.com/rss/all/news/"),
    ("RACING", "Autosport", "https://www.autosport.com/rss/feed/all"),
    ("FORD", "Ford Authority", "https://fordauthority.com/feed/"),
    ("AUTO", "Motor1", "https://www.motor1.com/rss/news/all/"),
    ("AUTO", "Carscoops", "https://www.carscoops.com/feed/"),
    ("AUTO", "Jalopnik", "https://jalopnik.com/rss"),
    ("AUTO", "Autoblog", "https://www.autoblog.com/rss.xml"),
    ("AUTO", "The Drive", "https://www.thedrive.com/feed"),
    ("AUTO", "Electrek", "https://electrek.co/feed/"),
    ("AUTO", "InsideEVs", "https://insideevs.com/rss/news/all/"),
    ("AUTO", "GM Authority", "https://gmauthority.com/blog/feed/"),
    ("AUTO", "Mopar Insiders", "https://moparinsiders.com/feed/"),
]
PER_FEED, MAX_ITEMS, MAX_AGE_DAYS = 8, 30, 4
HISTORY_DAYS, PER_DAY = 7, 45
UA = {"User-Agent": "Mozilla/5.0 (DG317 news robot)"}
now = dt.datetime.now(dt.timezone.utc)
try:
    from zoneinfo import ZoneInfo
    MT = ZoneInfo("America/Denver")
except Exception:
    MT = dt.timezone(dt.timedelta(hours=-7))

# ---- CarStuff bubbles: (id, label, group, words that tag a headline, Google News search that fills the bubble) ----
BUBBLES = [
 ("ford", "Ford", "make", r"\bford\b|lincoln|mustang|f-?150|f-?250|super duty|bronco|ranger|maverick|explorer|expedition|mach-e|blue oval|\bfomoco\b", '"Ford" (Mustang OR "F-150" OR Bronco OR Ranger OR Explorer OR Lincoln OR recall OR truck)'),
 ("gm", "GM / Chevy", "make", r"\bgm\b|general motors|chevrolet|chevy|\bgmc\b|buick|cadillac|corvette|silverado|sierra|tahoe|suburban|escalade|camaro|colorado|equinox", '("General Motors" OR Chevrolet OR GMC OR Cadillac OR Buick OR Corvette OR Silverado)'),
 ("stellantis", "Jeep / Ram / Dodge", "make", r"stellantis|\bjeep\b|\bram\b|dodge|chrysler|mopar|wrangler|gladiator|hemi|hellcat|charger|durango|\bfiat\b|alfa romeo|maserati|peugeot|opel|citro", '(Stellantis OR Jeep OR "Ram truck" OR Dodge OR Chrysler OR Mopar)'),
 ("toyota", "Toyota / Lexus", "make", r"toyota|lexus|tacoma|tundra|4runner|rav4|camry|supra|gr86|land cruiser|hilux|\bgr\b corolla|sequoia", '(Toyota OR Lexus) (car OR truck OR SUV OR recall OR EV OR hybrid)'),
 ("honda", "Honda / Acura", "make", r"honda|acura|civic|accord|cr-v|pilot|ridgeline|integra|\bnsx\b|prelude", '(Honda OR Acura) (car OR SUV OR recall OR EV OR hybrid OR Civic)'),
 ("hyundai", "Hyundai / Kia", "make", r"hyundai|\bkia\b|genesis|ioniq|telluride|tucson|palisade|santa fe|\bev9\b|\bev6\b|sportage|elantra", '(Hyundai OR Kia OR Genesis) (car OR SUV OR recall OR EV)'),
 ("nissan", "Nissan", "make", r"nissan|infiniti|frontier|\bgt-?r\b|\bleaf\b|titan|pathfinder|rogue|\bnismo\b", 'Nissan (car OR truck OR SUV OR recall OR EV)'),
 ("subaru", "Subaru / Mazda", "make", r"subaru|\bwrx\b|outback|forester|crosstrek|mazda|miata|mx-5|\bcx-\d", '(Subaru OR Mazda) (car OR SUV OR recall OR WRX OR Miata)'),
 ("vw", "VW / Audi / Porsche", "make", r"volkswagen|\bvw\b|audi|porsche|lamborghini|bentley|bugatti|skoda|\bgti\b|\bid\.\s?\w+|scout motors|\bscout\b", '(Volkswagen OR Audi OR Porsche OR Lamborghini OR "Scout Motors")'),
 ("bmw", "BMW / Mercedes", "make", r"\bbmw\b|\bmini\b|rolls-royce|mercedes|\bamg\b|maybach|g-class", '(BMW OR Mercedes-Benz OR AMG OR "Rolls-Royce" OR MINI) car'),
 ("tesla", "Tesla", "make", r"tesla|cybertruck|model [3sxy]\b|robotaxi|\bfsd\b", 'Tesla (Cybertruck OR "Model Y" OR "Model 3" OR robotaxi OR FSD OR deliveries)'),
 ("evnew", "Rivian / Lucid / EV startups", "make", r"rivian|lucid|polestar|slate auto|\bslate\b|fisker|vinfast|canoo|lordstown", '(Rivian OR Lucid OR Polestar OR "Slate Auto" OR VinFast)'),
 ("china", "BYD / China", "make", r"\bbyd\b|geely|xiaomi|\bnio\b|xpeng|zeekr|chery|great wall|\bsaic\b|li auto|changan|chinese automaker|chinese ev", '(BYD OR Geely OR Xiaomi OR Chery OR "Chinese automaker" OR "Chinese EV")'),
 ("ev", "EVs & Hybrids", "topic", r"\bevs?\b|electric|battery|batteries|charging|charger|hybrid|plug-in|\berev\b|range|supercharger|nacs", '("electric vehicle" OR EV OR hybrid) (automaker OR charging OR battery) -bike'),
 ("trucks", "Trucks & Off-Road", "topic", r"\btrucks?\b|pickup|off-?road|4x4|raptor|\btrx\b|zr2|trailhawk|overland|towing|tow\b|rock crawl|baja|lifted", '(pickup OR "off-road" OR 4x4) (truck OR Raptor OR Wrangler OR Tacoma OR Silverado)'),
 ("racing", "Racing", "topic", r"nascar|\bf1\b|formula (1|one|e)|indycar|imsa|\bwec\b|le mans|motogp|\bnhra\b|rally|supercars|dakar|grand prix|\bgp\b|podium|pole position|championship|qualifying", None),
 ("industry", "Industry & Sales", "topic", r"\bsales\b|tariff|plant|factory|layoff|jobs|union|\buaw\b|earnings|profit|loss|\bceo\b|prices?\b|market|production|deliveries|settlement|lawsuit|invest|billion|million|dealers?|inventory|exports?|imports?", '(automaker OR "auto industry" OR "car sales" OR tariffs OR UAW OR "auto plant")'),
 ("recalls", "Recalls", "topic", r"recall|nhtsa|investigation|probe|defect|stop-sale|do not drive|safety issue|airbag|fire risk", '(recall OR NHTSA) (vehicles OR cars OR trucks OR SUVs) -food'),
 ("deals", "Deals & Incentives", "topic", r"\bdeals?\b|lease|incentive|rebate|discount|0%|\bapr\b|employee pricing|x-plan|cash back|financing|price cut|cheaper|affordable", '("car deals" OR "lease deals" OR "auto incentives" OR "employee pricing" OR "0% APR" OR "cash back") car'),
 ("classics", "Classics & Auctions", "topic", r"classic|auction|barrett-jackson|mecum|\bbat\b|bring a trailer|restomod|vintage|barn find|concours|collector|for sale|up for auction|restored|\b19[2-9]\d\b", '("classic car" OR "car auction" OR Mecum OR "Barrett-Jackson" OR restomod OR "barn find")'),
]
BRX = {b[0]: re.compile(b[3], re.I) for b in BUBBLES}
SOURCE_W = {"Ford Authority": 1.8, "RACER": 2.0, "Motorsport.com": 1.8, "Autosport": 1.8, "The Drive": 1.6, "Motor1": 1.5,
            "Carscoops": 1.4, "Electrek": 1.3, "InsideEVs": 1.3, "GM Authority": 1.6, "Mopar Insiders": 1.5, "Jalopnik": 1.3, "Autoblog": 1.3,
            "Reuters": 2.2, "Associated Press": 2.0, "AP News": 2.0, "Automotive News": 2.2, "CNBC": 1.6, "Car and Driver": 1.7,
            "MotorTrend": 1.7, "Road & Track": 1.6, "Hagerty": 1.5, "The Detroit News": 1.6, "Detroit Free Press": 1.6}
BOOST = [(re.compile(r"recall|do not drive|stop-sale|fire risk", re.I), 1.4, "Safety / recall"),
         (re.compile(r"\bford\b|mustang|bronco|f-?150|super duty|raptor|lincoln", re.I), 0.6, "Ford news"),
         (re.compile(r"nascar|indycar|nhra|imsa|daytona|indianapolis|le mans", re.I), 0.6, "Big U.S. racing"),
         (re.compile(r"price|tariff|\$\d|billion|settlement|lawsuit", re.I), 0.5, "Money / prices"),
         (re.compile(r"revealed|unveil|debut|first look|all-new|new \w+ (is|gets)", re.I), 0.4, "New model")]
STOP = set("the a an to of in on for and or with is are at by from as its it this that new will be after how why what you your".split())

def get(url, timeout=20):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()

def when(s):
    if not s: return None
    try: d = parsedate_to_datetime(s)
    except Exception:
        try: d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception: return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)

def load_js(path, var):
    try:
        t = open(path, encoding="utf-8").read()
        return json.loads(t[t.index("=", t.index(var)) + 1:].strip().rstrip(";"))
    except Exception:
        return {}

def parse_feed(raw, tag, name, limit):
    out, got = [], 0
    root = ET.fromstring(raw)
    for it in root.iter():
        t = it.tag.split('}')[-1]
        if t not in ("item", "entry"): continue
        kid = {c.tag.split('}')[-1]: c for c in it}
        title = (kid.get("title").text or "").strip() if kid.get("title") is not None else ""
        link = ""
        if kid.get("link") is not None:
            link = (kid["link"].text or kid["link"].get("href") or "").strip()
        src = name
        if kid.get("source") is not None and (kid["source"].text or "").strip():
            src = kid["source"].text.strip()[:40]                      # Google News: the real outlet
            if title.endswith(" - " + src): title = title[: -len(src) - 3]
        d = when((kid.get("pubDate") or kid.get("published") or kid.get("updated") or ET.Element("x")).text)
        if not title or not link or (d and (now - d).days > MAX_AGE_DAYS): continue
        out.append({"tag": tag, "title": html.unescape(re.sub(r"\s+", " ", title))[:160], "source": src, "url": link,
                    "_dt": d or now})
        got += 1
        if got >= limit: break
    return out

def words(t):
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if len(w) > 2 and w not in STOP}

def tag_and_score(items):
    """bubbles, a display category, a score and a one-line reason for every story"""
    toks = [words(x["title"]) for x in items]
    for i, x in enumerate(items):
        t = x["title"]
        b = [bid for bid, rx in BRX.items() if rx.search(t)]
        if x["tag"] == "RACING" and "racing" not in b: b.append("racing")
        if x["tag"] == "FORD" and "ford" not in b: b.insert(0, "ford")
        x["b"] = b
        make = next((bb for bb in b if bb in MAKES), None)
        x["cat"] = "RACING" if "racing" in b and x["tag"] == "RACING" else (CAT.get(make, LABEL.get(make, "").upper()) if make else
                   ("RECALL" if "recalls" in b else ("EV" if "ev" in b else ("INDUSTRY" if "industry" in b else "AUTO"))))
        # how many OTHER outlets have the same story
        same = {items[j]["source"] for j in range(len(items)) if j != i and items[j]["source"] != x["source"]
                and toks[i] and toks[j] and len(toks[i] & toks[j]) / max(1, min(len(toks[i]), len(toks[j]))) >= 0.6}
        hrs = max(0.0, (now - x["_dt"]).total_seconds() / 3600)
        score = SOURCE_W.get(x["source"], 1.0) + 1.6 * min(len(same), 4) + max(0.0, 3.0 - hrs / 8)
        why = []
        if same: why.append(f"{len(same) + 1} outlets covering it")
        for rx, pts, label in BOOST:
            if rx.search(t): score += pts; why.append(label) if len(why) < 2 else None
        if not why: why.append("Fresh" if hrs < 6 else x["source"])
        x["score"] = round(score, 2); x["why"] = " · ".join(why[:2])
    return items

def clean(x):
    return {"tag": x["tag"], "cat": x["cat"], "title": x["title"], "source": x["source"], "url": x["url"],
            "date": x["_dt"].astimezone(MT).date().isoformat(), "ts": x["_dt"].isoformat(timespec="minutes"),
            "score": x["score"], "why": x["why"], "b": x["b"]}

def key(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())[:55]

def dedupe(items):
    seen, out = set(), []
    for x in items:
        k = key(x["title"])
        if k in seen: continue
        seen.add(k); out.append(x)
    return out

MAKES = {b[0] for b in BUBBLES if b[2] == "make"}
CAT = {"ford": "FORD", "gm": "GM", "stellantis": "STELLANTIS", "toyota": "TOYOTA", "honda": "HONDA", "hyundai": "HYUNDAI·KIA",
       "nissan": "NISSAN", "subaru": "SUBARU·MAZDA", "vw": "VW GROUP", "bmw": "BMW·MERCEDES", "tesla": "TESLA",
       "evnew": "EV STARTUPS", "china": "CHINA"}
LABEL = {b[0]: b[1] for b in BUBBLES}

def news():
    main = []
    for tag, name, url in FEEDS:
        try:
            got = parse_feed(get(url), tag, name, PER_FEED)
            for g in got: g["_main"] = True
            main += got
            print(f"ok   {name}: {len(got)}")
        except Exception as e:
            print(f"skip {name}: {e}")
    extra = []                                   # Google News fills each bubble so no maker is left empty
    for bid, label, grp, rx, q in BUBBLES:
        if not q: continue
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q + " when:2d", "hl": "en-US", "gl": "US", "ceid": "US:en"})
        try:
            got = parse_feed(get(url), "AUTO", "Google News", 10)
            for g in got: g["_want"] = bid; g["_main"] = False
            extra += got; print(f"ok   bubble {bid}: {len(got)}")
        except Exception as e:
            print(f"skip bubble {bid}: {e}")
        time.sleep(0.3)
    if not main and not extra:
        print("no headlines fetched - keeping old news.js"); return
    wants = {}                                    # which bubble searches found each story
    for x in extra: wants.setdefault(key(x["title"]), set()).add(x["_want"])
    allx = dedupe(sorted(main + extra, key=lambda x: -x["_dt"].timestamp()))
    tag_and_score(allx)
    for x in allx:                                # a Google News find lands in the bubble that searched for it,
        x.pop("_want", None)                      # unless the headline is clearly about a different maker
        for w in wants.get(key(x["title"]), ()):
            if w not in x["b"] and (BRX[w].search(x["title"]) or not any(bb in MAKES for bb in x["b"]) or w not in MAKES):
                x["b"].append(w)
    ranked = sorted(allx, key=lambda x: -x["score"])
    pool = [x for x in ranked if x["_main"]] or ranked
    top, cats = [], set()                         # top 3 cards: best story from 3 different categories
    for x in pool:
        if x["cat"] not in cats: top.append(x); cats.add(x["cat"])
        if len(top) == 3: break
    rest = [x for x in pool if x not in top]
    items = [clean(x) for x in (top + rest)[:MAX_ITEMS]]
    bubbles = {}
    for bid, label, grp, rx, q in BUBBLES:
        bubbles[bid] = {"label": label, "group": grp, "items": [clean(x) for x in ranked if bid in x["b"]][:12]}
    out = {"updated": now.isoformat(), "items": items, "bubbles": bubbles,
           "order": [b[0] for b in BUBBLES]}
    js = ("/* Written automatically by scripts/update_feeds.py - don't edit by hand. */\n"
          "window.DG_NEWS = " + json.dumps(out, indent=1, ensure_ascii=False) + ";\n")
    open(os.path.join(ROOT, "data", "news.js"), "w", encoding="utf-8").write(js)
    history([clean(x) for x in ranked])
    print(f"news: {len(items)} top stories, {sum(len(v['items']) for v in bubbles.values())} bubble slots")

def history(ranked):
    """keeps the last 7 days of ranked stories (Mountain time days) -> data/news-history.js"""
    path = os.path.join(ROOT, "data", "news-history.js")
    old = load_js(path, "window.DG_NEWS_HISTORY").get("days", {})
    today = now.astimezone(MT).date().isoformat()
    for x in ranked:                              # each story is filed under the day it was published
        old.setdefault(x["date"], []).append(x)
    keep = sorted(old.keys(), reverse=True)[:HISTORY_DAYS]
    days = {}
    for d in keep:
        if d > today: continue
        best = {}
        for x in old[d]:                          # same story seen in several runs -> keep the best copy
            k = re.sub(r"[^a-z0-9]", "", x["title"].lower())[:55]
            if k not in best or x.get("score", 0) > best[k].get("score", 0): best[k] = x
        days[d] = sorted(best.values(), key=lambda x: -x.get("score", 0))[:PER_DAY]
    js = ("/* Written automatically by scripts/update_feeds.py - the last 7 days of CarStuff stories. Don't edit by hand. */\n"
          "window.DG_NEWS_HISTORY = " + json.dumps({"updated": now.isoformat(), "days": days}, ensure_ascii=False) + ";\n")
    open(path, "w", encoding="utf-8").write(js)

def read_live():
    txt = open(os.path.join(ROOT, "data", "live-content.js"), encoding="utf-8").read()
    return json.loads(txt[txt.index("{"): txt.rindex("}") + 1])

def yt(path, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    return json.loads(get("https://www.googleapis.com/youtube/v3/" + path + "?" + urllib.parse.urlencode(params)))

RACE_WORDS = re.compile(r"race|highlights|live|final|qualif|grand prix|\bgp\b|rally|500|24|eliminat", re.I)
def racing():
    if not os.environ.get("YOUTUBE_API_KEY"):
        print("no YOUTUBE_API_KEY secret - skipping video picks"); return
    live = read_live(); found = []
    week = (now - dt.timedelta(days=4)).isoformat().replace("+00:00", "Z")
    for h in live.get("channels", []):
        try:
            cid = (yt("channels", part="id", forHandle=h).get("items") or [{}])[0].get("id")
            if not cid: continue
            for ev, rank in (("live", 0), ("upcoming", 1)):
                for it in yt("search", part="snippet", channelId=cid, eventType=ev, type="video", maxResults=2).get("items", []):
                    found.append((rank, it))
            for it in yt("search", part="snippet", channelId=cid, type="video", order="date", publishedAfter=week, maxResults=4).get("items", []):
                if RACE_WORDS.search(it["snippet"]["title"]): found.append((2, it))
            print(f"ok   {h}")
        except Exception as e:
            print(f"skip {h}: {e}")
    seen, rows = set(), []
    for rank, it in sorted(found, key=lambda x: (x[0], -dt.datetime.fromisoformat(x[1]["snippet"]["publishedAt"].replace("Z", "+00:00")).timestamp())):
        vid = it["id"].get("videoId")
        if not vid or vid in seen: continue
        seen.add(vid); s = it["snippet"]
        rows.append({"type": "video", "id": vid, "title": s["title"], "channel": s["channelTitle"], "kind": ["live", "upcoming", "recent"][rank], "date": s["publishedAt"]})
    js = ("/* Written automatically by scripts/update_feeds.py - don't edit by hand. */\n"
          "window.DG_RACING_AUTO = " + json.dumps({"updated": now.isoformat(), "slots": rows[:3], "found": rows[:30]}, indent=1, ensure_ascii=False) + ";\n")
    open(os.path.join(ROOT, "data", "racing-auto.js"), "w", encoding="utf-8").write(js)

# Past World Champions never change, so they live here (the free F1 API can't list all seasons at once).
# Nothing to do each year: f1() below looks up any finished season after the last one listed and adds it itself.
CHAMPS = [(1950,"Giuseppe Farina","Alfa Romeo"),(1951,"Juan Manuel Fangio","Alfa Romeo"),(1952,"Alberto Ascari","Ferrari"),
 (1953,"Alberto Ascari","Ferrari"),(1954,"Juan Manuel Fangio","Mercedes"),(1955,"Juan Manuel Fangio","Mercedes"),
 (1956,"Juan Manuel Fangio","Ferrari"),(1957,"Juan Manuel Fangio","Maserati"),(1958,"Mike Hawthorn","Ferrari"),
 (1959,"Jack Brabham","Cooper"),(1960,"Jack Brabham","Cooper"),(1961,"Phil Hill","Ferrari"),(1962,"Graham Hill","BRM"),
 (1963,"Jim Clark","Lotus"),(1964,"John Surtees","Ferrari"),(1965,"Jim Clark","Lotus"),(1966,"Jack Brabham","Brabham"),
 (1967,"Denny Hulme","Brabham"),(1968,"Graham Hill","Lotus"),(1969,"Jackie Stewart","Matra"),(1970,"Jochen Rindt","Lotus"),
 (1971,"Jackie Stewart","Tyrrell"),(1972,"Emerson Fittipaldi","Lotus"),(1973,"Jackie Stewart","Tyrrell"),
 (1974,"Emerson Fittipaldi","McLaren"),(1975,"Niki Lauda","Ferrari"),(1976,"James Hunt","McLaren"),(1977,"Niki Lauda","Ferrari"),
 (1978,"Mario Andretti","Lotus"),(1979,"Jody Scheckter","Ferrari"),(1980,"Alan Jones","Williams"),(1981,"Nelson Piquet","Brabham"),
 (1982,"Keke Rosberg","Williams"),(1983,"Nelson Piquet","Brabham"),(1984,"Niki Lauda","McLaren"),(1985,"Alain Prost","McLaren"),
 (1986,"Alain Prost","McLaren"),(1987,"Nelson Piquet","Williams"),(1988,"Ayrton Senna","McLaren"),(1989,"Alain Prost","McLaren"),
 (1990,"Ayrton Senna","McLaren"),(1991,"Ayrton Senna","McLaren"),(1992,"Nigel Mansell","Williams"),(1993,"Alain Prost","Williams"),
 (1994,"Michael Schumacher","Benetton"),(1995,"Michael Schumacher","Benetton"),(1996,"Damon Hill","Williams"),
 (1997,"Jacques Villeneuve","Williams"),(1998,"Mika Häkkinen","McLaren"),(1999,"Mika Häkkinen","McLaren"),
 (2000,"Michael Schumacher","Ferrari"),(2001,"Michael Schumacher","Ferrari"),(2002,"Michael Schumacher","Ferrari"),
 (2003,"Michael Schumacher","Ferrari"),(2004,"Michael Schumacher","Ferrari"),(2005,"Fernando Alonso","Renault"),
 (2006,"Fernando Alonso","Renault"),(2007,"Kimi Räikkönen","Ferrari"),(2008,"Lewis Hamilton","McLaren"),(2009,"Jenson Button","Brawn"),
 (2010,"Sebastian Vettel","Red Bull"),(2011,"Sebastian Vettel","Red Bull"),(2012,"Sebastian Vettel","Red Bull"),
 (2013,"Sebastian Vettel","Red Bull"),(2014,"Lewis Hamilton","Mercedes"),(2015,"Lewis Hamilton","Mercedes"),
 (2016,"Nico Rosberg","Mercedes"),(2017,"Lewis Hamilton","Mercedes"),(2018,"Lewis Hamilton","Mercedes"),
 (2019,"Lewis Hamilton","Mercedes"),(2020,"Lewis Hamilton","Mercedes"),(2021,"Max Verstappen","Red Bull"),
 (2022,"Max Verstappen","Red Bull"),(2023,"Max Verstappen","Red Bull"),(2024,"Max Verstappen","Red Bull"),
 (2025,"Lando Norris","McLaren")]

def f1():
    """Live F1 standings from the free Jolpica (Ergast) API + the champions list above -> data/series-auto.js"""
    base = "https://api.jolpi.ca/ergast/f1/"
    try:
        cur = json.loads(get(base + "current/driverStandings.json"))["MRData"]["StandingsTable"]["StandingsLists"][0]
        rows = [{"pos": int(d["position"]), "name": d["Driver"]["givenName"] + " " + d["Driver"]["familyName"],
                 "team": (d.get("Constructors") or [{}])[0].get("name", ""), "pts": d["points"], "wins": d["wins"]}
                for d in cur["DriverStandings"][:12]]
    except Exception as e:
        print(f"skip F1: {e}"); return
    champs = [{"y": y, "name": n, "team": t} for y, n, t in CHAMPS]
    for y in range(CHAMPS[-1][0] + 1, now.year):          # finished seasons not in the list yet (e.g. 2026, starting Jan 2027)
        try:
            d = json.loads(get(base + f"{y}/driverStandings.json"))["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]
            champs.append({"y": y, "name": d["Driver"]["givenName"] + " " + d["Driver"]["familyName"],
                           "team": (d.get("Constructors") or [{}])[0].get("name", "")})
        except Exception as e:
            print(f"note: couldn't add {y} champion yet: {e}")
    out = {"updated": now.isoformat(), "f1": {"season": cur["season"], "round": cur["round"], "standings": rows, "champions": champs}}
    open(os.path.join(ROOT, "data", "series-auto.js"), "w", encoding="utf-8").write(
        "/* Written automatically by scripts/update_feeds.py - don't edit by hand. */\nwindow.DG_SERIES_AUTO = " + json.dumps(out, ensure_ascii=False) + ";\n")
    print(f"ok   F1: {len(rows)} drivers, {len(champs)} champions")

if __name__ == "__main__":
    news()
    f1()
    # YouTube search costs ~300 quota units per channel (free quota = 10,000/day),
    # so videos only refresh when the workflow asks for them (a few times a day on race days).
    # race videos moved to scripts/update_videos.py (runs every 30 min, catches live streams)
