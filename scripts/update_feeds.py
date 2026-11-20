"""DG317 daily robot - run by GitHub Actions (see .github/workflows/update-feeds.yml).
1) Pulls racing / auto / Ford headlines from RSS feeds  -> data/news.js
2) If a YOUTUBE_API_KEY secret is set, finds live/upcoming/recent race videos -> data/racing-auto.js
Standard library only. Any feed that fails is skipped, the site keeps the last good copy."""
import json, os, re, sys, urllib.request, urllib.parse, datetime as dt
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDS = [  # (tag, source name, url) - add/remove freely
    ("RACING", "RACER", "https://racer.com/feed/"),
    ("RACING", "Motorsport.com", "https://www.motorsport.com/rss/all/news/"),
    ("RACING", "Autosport", "https://www.autosport.com/rss/feed/all"),
    ("FORD", "Ford Authority", "https://fordauthority.com/feed/"),
    ("AUTO", "Motor1", "https://www.motor1.com/rss/news/all/"),
    ("AUTO", "Carscoops", "https://www.carscoops.com/feed/"),
    ("AUTO", "Jalopnik", "https://jalopnik.com/rss"),
    ("AUTO", "Autoblog", "https://www.autoblog.com/rss.xml"),
]
PER_FEED, MAX_ITEMS, MAX_AGE_DAYS = 5, 30, 4
UA = {"User-Agent": "Mozilla/5.0 (DG317 news robot)"}
now = dt.datetime.now(dt.timezone.utc)

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

def news():
    items = []
    for tag, name, url in FEEDS:
        try:
            root = ET.fromstring(get(url))
            got = 0
            for it in root.iter():
                t = it.tag.split('}')[-1]
                if t not in ("item", "entry"): continue
                kid = {c.tag.split('}')[-1]: c for c in it}
                title = (kid.get("title").text or "").strip() if kid.get("title") is not None else ""
                link = ""
                if kid.get("link") is not None:
                    link = (kid["link"].text or kid["link"].get("href") or "").strip()
                d = when((kid.get("pubDate") or kid.get("published") or kid.get("updated") or ET.Element("x")).text)
                if not title or not link or (d and (now - d).days > MAX_AGE_DAYS): continue
                items.append({"tag": tag, "title": re.sub(r"\s+", " ", title)[:160], "source": name, "url": link,
                              "date": (d or now).date().isoformat(), "_ts": (d or now).timestamp()})
                got += 1
                if got >= PER_FEED: break
            print(f"ok   {name}: {got}")
        except Exception as e:
            print(f"skip {name}: {e}")
    seen, out = set(), []
    for x in sorted(items, key=lambda x: -x["_ts"]):
        k = x["title"].lower()[:60]
        if k in seen: continue
        seen.add(k); x.pop("_ts"); out.append(x)
    if not out:
        print("no headlines fetched - keeping old news.js"); return
    js = ("/* Written automatically by scripts/update_feeds.py - don't edit by hand. */\n"
          "window.DG_NEWS = " + json.dumps({"updated": now.isoformat(), "items": out[:MAX_ITEMS]}, indent=1, ensure_ascii=False) + ";\n")
    open(os.path.join(ROOT, "data", "news.js"), "w", encoding="utf-8").write(js)

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
