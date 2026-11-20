"""DG317 series robot - keeps every Racing HQ card current. Run by GitHub Actions (update-series.yml).

For each series in data/series.js:
  * STANDINGS - reads the current season's Wikipedia page and pulls the top 5 from the
    drivers'/riders' championship table. Wikipedia is usually updated within hours of a race.
  * NEWS      - newest headlines for that series from Google News RSS (last 14 days).
Output: data/series-live.js  (window.DG_SERIES_LIVE)
If anything fails for a series, its last good copy is kept - the site never goes blank.
Standard library only.
"""
import json, os, re, sys, time, html, urllib.request, urllib.parse, datetime as dt
from html.parser import HTMLParser
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "series-live.js")
UA = {"User-Agent": "DG317-Garage-robot/1.0 (fan site; github actions)"}
NOW = dt.datetime.now(dt.timezone.utc)

# Wikipedia season-page titles. {Y}=this year, {PY}=last year, {NY}=next year, {YY}/{NYY}=2-digit.
# The robot tries each title in order and uses the first one that has a standings table.
# No entry = event or series without a reliable season page -> news only.
WIKI = {
  "nascar":   ["{Y} NASCAR Cup Series"],
  "nos":      ["{Y} NASCAR O'Reilly Auto Parts Series", "{Y} NASCAR Xfinity Series"],
  "trucks":   ["{Y} NASCAR Craftsman Truck Series"],
  "arca":     ["{Y} ARCA Menards Series"],
  "nmx":      ["{Y} NASCAR Mexico Series"],
  "ncan":     ["{Y} NASCAR Canada Series"],
  "neuro":    ["{Y} NASCAR Euro Series", "{Y} NASCAR Whelen Euro Series"],
  "indycar":  ["{Y} IndyCar Series"],
  "indynxt":  ["{Y} Indy NXT"],
  "imsa":     ["{Y} IMSA SportsCar Championship"],
  "wec":      ["{Y} FIA World Endurance Championship"],
  "f2":       ["{Y} FIA Formula 2 Championship"],
  "motogp":   ["{Y} MotoGP World Championship"],
  "wsbk":     ["{Y} Superbike World Championship"],
  "wrc":      ["{Y} World Rally Championship"],
  "fe":       ["{Y}–{NYY} Formula E World Championship", "{PY}–{YY} Formula E World Championship"],
  "sx":       ["{Y} AMA Supercross Championship"],
  "promx":    ["{Y} AMA Pro Motocross Championship"],
  "transam":  ["{Y} Trans-Am Series"],
  "btcc":     ["{Y} British Touring Car Championship"],
  "dtm":      ["{Y} Deutsche Tourenwagen Masters"],
  "supercars":["{Y} Supercars Championship"],
  "supergt":  ["{Y} Super GT Series"],
  "sformula": ["{Y} Super Formula Championship"],
  "ctcc":     ["{Y} TCR China Touring Car Championship"],
  "chinagt":  ["{Y} China GT Championship"],
  "rcrs":     ["{Y} Russian Circuit Racing Series"],
  "etrc":     ["{Y} European Truck Racing Championship"],
  "nhra":     ["{Y} NHRA Mission Foods Drag Racing Series", "{Y} NHRA Camping World Drag Racing Series"],
  "nrx":      ["{Y} Nitrocross Championship"],
  "macau":    [],
}
# Better Google News searches where the plain name is too vague
NEWSQ = {
  "nascar": '"NASCAR Cup Series"', "nos": '"NASCAR O\'Reilly" OR "Xfinity Series"', "trucks": '"Truck Series" NASCAR',
  "f1": '"Formula 1"', "fe": '"Formula E"', "f2": '"Formula 2" OR "F1 Academy"', "woo": '"World of Outlaws"',
  "imsa": "IMSA", "wec": '"World Endurance Championship" OR WEC Le Mans', "sx": "Supercross", "promx": '"Pro Motocross"',
  "nhra": "NHRA", "motogp": "MotoGP", "wrc": '"World Rally Championship" OR WRC rally', "barc": '"BARC" motorsport',
  "supercars": "Supercars Championship", "btcc": "BTCC", "dtm": "DTM racing", "superrace": "Superrace Korea",
  "ctcc": '"TCR China" OR CTCC', "chinagt": '"China GT"', "rcrs": '"SMP" racing Russia RCRS', "etrc": '"truck racing" ETRC',
  "koh": '"King of the Hammers"', "pikes": '"Pikes Peak" hill climb', "dakar": '"Dakar Rally"', "chili": '"Chili Bowl" midget',
  "hl": '"High Limit Racing"', "usac": "USAC sprint", "iomtt": '"Isle of Man TT"', "skusa": "SKUSA SuperNationals",
  "fiakart": '"karting world championship"', "ppl": '"Pro Pulling League" OR "tractor pull"', "ntpa": 'NTPA pulling OR "truck and tractor pull"', "abrr": '"American Big Rig Racing" OR "semi truck racing"', "macau": '"Macau Grand Prix"', "srx": '"Superstar Racing Experience" OR "SRX racing"', "score": '"Baja 1000" OR "SCORE off-road"',
}

def get(url, timeout=25):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()

# ---------- tiny table parser that understands rowspan/colspan ----------
class Tables(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True)
        s.tables, s.stack, s.heading, s.in_h, s.skip = [], [], "", False, 0
    VOID = {"br","img","hr","meta","link","input","wbr","col","source"}
    def handle_starttag(s, tag, a):
        a = dict(a)
        if s.skip:
            if tag not in s.VOID: s.skip += 1
            return
        if tag in ("sup", "style", "script") or "display:none" in (a.get("style") or "").replace(" ", ""):
            if tag not in s.VOID: s.skip = 1
            return
        if tag in ("h2", "h3", "h4"): s.in_h, s.heading = True, ""
        if tag == "table":
            s.stack.append({"cls": a.get("class") or "", "rows": [], "row": None, "cell": None, "heading": s.heading})
        if not s.stack: return
        t = s.stack[-1]
        if tag == "tr": t["row"] = []
        if tag in ("td", "th") and t["row"] is not None:
            t["cell"] = {"txt": "", "rs": int(re.sub(r"\D", "", a.get("rowspan") or "1") or 1), "cs": int(re.sub(r"\D", "", a.get("colspan") or "1") or 1)}
        if tag == "br" and t.get("cell") is not None: t["cell"]["txt"] += " / "
    def handle_endtag(s, tag):
        if s.skip:
            s.skip -= 1
            return
        if tag in ("h2", "h3", "h4"): s.in_h = False
        if not s.stack: return
        t = s.stack[-1]
        if tag in ("td", "th") and t["cell"] is not None and t["row"] is not None:
            t["row"].append(t["cell"]); t["cell"] = None
        if tag == "tr" and t["row"] is not None:
            if t["cell"] is not None: t["row"].append(t["cell"]); t["cell"] = None
            t["rows"].append(t["row"]); t["row"] = None
        if tag == "table":
            s.tables.append(s.stack.pop())
    def handle_data(s, d):
        if s.in_h: s.heading += d
        if s.skip or not s.stack: return
        c = s.stack[-1]["cell"]
        if c is not None: c["txt"] += d

def grid(rows):
    """expand rowspan/colspan into a plain 2-D list of strings"""
    out, carry = [], {}
    for r in rows:
        line, ci, cells = [], 0, list(r)
        while cells or ci in carry:
            if ci in carry:
                txt, left = carry[ci]; line.append(txt)
                if left > 1: carry[ci] = (txt, left - 1)
                else: del carry[ci]
                ci += 1; continue
            c = cells.pop(0); txt = re.sub(r"\s+", " ", c["txt"]).strip(" /")
            for _ in range(c["cs"]):
                line.append(txt)
                if c["rs"] > 1: carry[ci] = (txt, c["rs"] - 1)
                ci += 1
        out.append(line)
    return out

POS = re.compile(r"^(pos\.?|position|rank)$", re.I)
WHO = re.compile(r"^(driver|drivers|rider|riders|driver\(s\)|competitor|crew)$", re.I)
TEAM = re.compile(r"^(team|teams|entrant|manufacturer)$", re.I)
PTS = re.compile(r"^(pts\.?|points|total)$", re.I)

def standings_from_html(page_html):
    p = Tables(); p.feed(page_html)
    best = None
    for t in p.tables:
        if "wikitable" not in t["cls"]: continue
        g = grid(t["rows"])
        if len(g) < 3: continue
        # header = first 1-3 rows; find column indexes
        hdr_rows = g[:3]
        def col(rx):
            for hr in hdr_rows:
                for i, v in enumerate(hr):
                    if rx.match(v.strip()): return i
            return None
        def lastcol(rx):
            found = None
            for hr in hdr_rows:
                for i, v in enumerate(hr):
                    if rx.match(v.strip()): found = i if found is None else max(found, i)
            return found
        pi, wi, ti, xi = col(POS), col(WHO), col(TEAM), lastcol(PTS)
        if pi is None or xi is None or (wi is None and ti is None): continue
        who = wi if wi is not None else ti
        top = []
        for r in g:
            if len(r) <= max(pi, who, xi): continue
            pos = re.sub(r"[^\d]", "", r[pi])
            if not pos or not (1 <= int(pos) <= 5) or any(int(pos) == x[0] for x in top): continue
            name = re.sub(r"\[[^\]]*\]", "", r[who]).strip()
            pts = re.sub(r"\[[^\]]*\]", "", r[xi]).strip()
            if not name or name.lower() in ("driver", "rider", "team"): continue
            top.append([int(pos), name[:60], pts[:12]])
        if len(top) < 3: continue
        top.sort()
        score = (2 if wi is not None else 1) + (1 if re.search(r"standing|championship", t["heading"], re.I) else 0)
        if best is None or score > best[0]:
            best = (score, top[:5], t["heading"].strip())
        if score >= 3: break   # first driver table under a standings heading wins
    return (best[1], best[2]) if best else (None, None)

def wiki_titles(sid):
    y = NOW.year
    sub = {"{Y}": str(y), "{PY}": str(y - 1), "{NY}": str(y + 1), "{YY}": str(y)[-2:], "{NYY}": str(y + 1)[-2:]}
    out = []
    for t in WIKI.get(sid, []):
        for yr in (0, -1):      # this year first, then last year (off-season / page not made yet)
            s = t
            for k, v in sub.items():
                v2 = str(int(v) + yr) if k in ("{Y}", "{PY}", "{NY}") else str(int(v) + yr).zfill(2)[-2:]
                s = s.replace(k, v2)
            if s not in out: out.append(s)
    return out

def standings(sid):
    for title in wiki_titles(sid):
        q = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "text", "format": "json",
                                    "formatversion": "2", "redirects": "1"})
        try:
            data = json.loads(get("https://en.wikipedia.org/w/api.php?" + q))
            if "error" in data: continue
            top, head = standings_from_html(data["parse"]["text"])
            if top:
                return {"top": top, "title": data["parse"]["title"], "table": head,
                        "src": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(data["parse"]["title"].replace(" ", "_"))}
        except Exception as e:
            print(f"   wiki {title}: {e}")
        time.sleep(0.4)
    return None

def news(sid, name):
    q = NEWSQ.get(sid) or '"' + re.sub(r"\s*\(.*?\)|\s+-\s+.*$", "", name).strip() + '"'
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q + " when:14d", "hl": "en-US", "gl": "US", "ceid": "US:en"})
    items = []
    try:
        root = ET.fromstring(get(url))
        for it in root.iter("item"):
            t = (it.findtext("title") or "").strip(); l = (it.findtext("link") or "").strip()
            src = (it.findtext("source") or "").strip()
            try: d = parsedate_to_datetime(it.findtext("pubDate"))
            except Exception: d = NOW
            if src and t.endswith(" - " + src): t = t[: -len(src) - 3]
            if t and l: items.append({"t": html.unescape(t)[:150], "u": l, "s": src[:40], "d": d.date().isoformat(), "_ts": d.timestamp()})
        items.sort(key=lambda x: -x["_ts"])
        for x in items: x.pop("_ts")
        return items[:4]
    except Exception as e:
        print(f"   news {sid}: {e}")
        return None

def load_js(path, var):
    try:
        txt = open(path, encoding="utf-8").read()
        return json.loads(txt[txt.index("=") + 1:].strip().rstrip(";"))
    except Exception:
        return {}

def series_list():
    """read ids + names out of data/series.js without needing node"""
    txt = open(os.path.join(ROOT, "data", "series.js"), encoding="utf-8").read()
    txt = txt[: txt.find("celebs:")] if "celebs:" in txt else txt
    return re.findall(r'\{id:"([^"]+)",[^}]*?name:"((?:[^"\\]|\\.)*)"', txt)

def main():
    only = sys.argv[1:]  # optional: python update_series.py nascar imsa
    old = load_js(OUT, "DG_SERIES_LIVE")
    live = old.get("s", {})
    stats = {"standings_ok": 0, "news_ok": 0, "failed": []}
    for sid, name in series_list():
        if only and sid not in only: continue
        rec = live.get(sid, {})
        if sid in WIKI:
            st = standings(sid)
            if st: rec.update(st); rec["st_at"] = NOW.isoformat(timespec="minutes"); stats["standings_ok"] += 1
            else: stats["failed"].append(sid + ":standings")
        n = news(sid, name.replace('\\"', '"'))
        if n is not None: rec["news"] = n; rec["news_at"] = NOW.isoformat(timespec="minutes"); stats["news_ok"] += 1
        else: stats["failed"].append(sid + ":news")
        live[sid] = rec
        print(f"ok   {sid}: top={'yes' if rec.get('top') else '-'} news={len(rec.get('news') or [])}")
        time.sleep(0.8)
    if not only:   # extra feed for the Sales Race board in the stock window
        q = '"auto sales" OR "car sales" automaker monthly OR quarterly'
        try:
            NEWSQ["_sales"] = q; n = news("_sales", "sales")
        except Exception: n = None
        if n: live["_sales"] = {"news": n, "news_at": NOW.isoformat(timespec="minutes")}
    out = {"updated": NOW.isoformat(timespec="minutes"), "stats": stats, "s": live}
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* written by scripts/update_series.py - do not hand edit */\nwindow.DG_SERIES_LIVE = " + json.dumps(out, ensure_ascii=False) + ";\n")
    print("done", stats)

if __name__ == "__main__":
    main()
