"""DG317 Dashboard robot - runs inside the update-feeds robot (every 2 hours).
Writes data/dashboard.js with:
  fuel        U.S. average regular gas + diesel (EIA weekly) and WTI / Brent crude (Yahoo, ~live)
  newsletter  the newest Market Mechanics issue (title, link, cover picture, date) from the beehiiv site
Anything that fails keeps its old value, so the Dashboard never goes blank. Standard library only.

Optional: a free EIA key (https://www.eia.gov/opendata/register.php) saved as the repo secret EIA_API_KEY
gives the exact weekly numbers + last week's for the up/down arrows. Without it the robot reads EIA's public RSS feed."""
import json, os, re, html, http.cookiejar, urllib.request, urllib.parse, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "dashboard.js")
NEWSLETTER = "https://themarketmechanics.beehiiv.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = [("User-Agent", UA)]
def get(url, timeout=25):
    with op.open(url, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def load_old():
    try:
        s = open(OUT, encoding="utf-8").read()
        return json.loads(s[s.index("{"):s.rindex("}") + 1])
    except Exception:
        return {}

old = load_old()
data = {"fuel": old.get("fuel", {}), "newsletter": old.get("newsletter", {})}
log = []

# ---------------- gas + diesel (weekly) ----------------
def eia_series(sid, key):
    j = json.loads(get(f"https://api.eia.gov/v2/seriesid/{sid}?api_key={key}&length=2"))
    rows = j["response"]["data"]
    rows.sort(key=lambda r: r["period"], reverse=True)
    return [(r["period"], float(r["value"])) for r in rows[:2]]

def set_weekly(name, week, val, prev=None):
    o = data["fuel"].get(name, {})
    if prev is None:                       # RSS only gives this week: remember last week's ourselves
        prev = o.get("prev") if o.get("week") == week else o.get("v")
    data["fuel"][name] = {"v": round(val, 3), "prev": prev, "week": week}

key = os.environ.get("EIA_API_KEY", "").strip()
done = False
if key:
    try:
        for name, sid in (("gas", "PET.EMM_EPMR_PTE_NUS_DPG.W"), ("diesel", "PET.EMD_EPD2D_PTE_NUS_DPG.W")):
            r = eia_series(sid, key)
            set_weekly(name, r[0][0], r[0][1], r[1][1] if len(r) > 1 else None)
        done = True; log.append("fuel: EIA API")
    except Exception as e:
        log.append(f"fuel: EIA API failed ({e})")
if not done:
    try:
        x = get("https://www.eia.gov/petroleum/gasdiesel/includes/gas_diesel_rss.xml")
        m = re.search(r"Data For (\d+)/(\d+)/(\d+)", x)
        week = f"20{m.group(3)[-2:]}-{int(m.group(1)):02d}-{int(m.group(2)):02d}" if m else ""
        body = html.unescape(x)
        g = re.search(r"Regular Gasoline.*?U\.S\.[ .\t]*([0-9]\.[0-9]{2,3})", body, re.S)
        d = re.search(r"Diesel.*?U\.S\.[ .\t]*([0-9]\.[0-9]{2,3})", body, re.S)
        if g: set_weekly("gas", week, float(g.group(1)))
        if d: set_weekly("diesel", week, float(d.group(1)))
        log.append(f"fuel: EIA RSS week {week} gas={g and g.group(1)} diesel={d and d.group(1)}")
    except Exception as e:
        log.append(f"fuel: EIA RSS failed ({e})")

# ---------------- crude (Yahoo, same way the market-cap robot does it) ----------------
try:
    try: get("https://fc.yahoo.com")       # consent cookie (a 404 here is normal)
    except Exception: pass
    crumb = get("https://query1.finance.yahoo.com/v1/test/getcrumb").strip()
    url = "https://query1.finance.yahoo.com/v7/finance/quote?" + urllib.parse.urlencode(
        {"symbols": "CL=F,BZ=F", "crumb": crumb, "fields": "regularMarketPrice,regularMarketChangePercent"})
    for q in json.loads(get(url))["quoteResponse"]["result"]:
        name = {"CL=F": "wti", "BZ=F": "brent"}.get(q["symbol"])
        if name and q.get("regularMarketPrice"):
            data["fuel"][name] = {"v": round(q["regularMarketPrice"], 2), "chg": round(q.get("regularMarketChangePercent") or 0, 2)}
    data["fuel"]["crude_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    log.append("crude: Yahoo ok")
except Exception as e:
    log.append(f"crude: Yahoo failed ({e})")
    if key:
        try:
            for name, sid in (("wti", "PET.RWTC.D"), ("brent", "PET.RBRTE.D")):
                r = eia_series(sid, key)
                chg = round((r[0][1] / r[1][1] - 1) * 100, 2) if len(r) > 1 and r[1][1] else 0
                data["fuel"][name] = {"v": round(r[0][1], 2), "chg": chg, "day": r[0][0]}
            log.append("crude: EIA daily spot")
        except Exception as e2:
            log.append(f"crude: EIA failed too ({e2})")

# ---------------- newest Market Mechanics issue ----------------
def meta(page, prop):
    m = re.search(r'<meta[^>]+(?:property|name)=["\']' + re.escape(prop) + r'["\'][^>]+content=["\']([^"\']*)', page, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']' + re.escape(prop) + r'["\']', page, re.I)
    return html.unescape(m.group(1)).strip() if m else ""

try:
    sm = get(NEWSLETTER + "/sitemap.xml")
    posts = re.findall(r"<loc>\s*(https?://[^<]+/p/[^<\s]+)\s*</loc>\s*(?:<lastmod>\s*([^<\s]+)\s*</lastmod>)?", sm)
    posts.sort(key=lambda p: p[1] or "", reverse=True)
    best = None
    for url, lastmod in posts[:4]:              # lastmod moves when an old issue is edited, so check the top few
        page = get(url)
        pub = meta(page, "article:published_time") or meta(page, "og:updated_time") or lastmod
        item = {"url": url, "title": meta(page, "og:title") or meta(page, "twitter:title"),
                "image": meta(page, "og:image") or meta(page, "twitter:image"),
                "desc": meta(page, "og:description")[:160], "date": (pub or "")[:10]}
        if item["title"] and (best is None or item["date"] > best["date"]):
            best = item
    if best:
        best["issue"] = len(set(u for u, _ in posts))   # every /p/ page is one issue
        data["newsletter"] = best; log.append(f"newsletter: {best['date']} {best['title'][:60]}")
    else:
        log.append("newsletter: no posts found - kept the old one")
except Exception as e:
    log.append(f"newsletter: failed ({e})")

data["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")
with open(OUT, "w", encoding="utf-8") as f:
    f.write("/* Written automatically by scripts/update_dashboard.py - don't edit by hand. */\n")
    f.write("window.DG_DASH = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
print("\n".join(log))
