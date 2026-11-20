"""DG317 market-cap robot - run by .github/workflows/update-marketcaps.yml every ~10 min in market hours.
Reads every ticker in stocks-data.js, pulls price + market cap (Yahoo Finance quote feed, ~15 min delayed for some exchanges),
ranks them, and writes data/marketcaps.js. If Yahoo fails, the old file is kept so the site never goes blank."""
import json, os, re, sys, time, http.cookiejar, urllib.request, urllib.parse, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "marketcaps.js")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"

txt = open(os.path.join(ROOT, "stocks-data.js"), encoding="utf-8").read()
stocks = json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
tickers = [s["t"] for s in stocks]

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = [("User-Agent", UA)]
def get(url):
    with op.open(url, timeout=25) as r: return r.read()

try: get("https://fc.yahoo.com")           # sets the consent cookie (a 404 here is normal)
except Exception: pass
crumb = get("https://query1.finance.yahoo.com/v1/test/getcrumb").decode().strip()

rows = []
for i in range(0, len(tickers), 50):
    batch = tickers[i:i + 50]
    url = "https://query1.finance.yahoo.com/v7/finance/quote?" + urllib.parse.urlencode(
        {"symbols": ",".join(batch), "crumb": crumb,
         "fields": "marketCap,regularMarketPrice,regularMarketChangePercent,currency"})
    for q in json.loads(get(url))["quoteResponse"]["result"]:
        cap = q.get("marketCap")
        if not cap or q.get("currency", "USD") != "USD": continue
        rows.append({"t": q["symbol"], "cap": int(cap),
                     "price": round(q.get("regularMarketPrice") or 0, 2),
                     "chg": round(q.get("regularMarketChangePercent") or 0, 2)})
    time.sleep(1)

if len(rows) < 50:
    sys.exit(f"only {len(rows)} quotes came back - keeping the old file")

# previous ranks -> lets the page show who moved up/down since the last update
prev = {}
if os.path.exists(OUT):
    try:
        old = open(OUT, encoding="utf-8").read()
        prev = {x["t"]: x["rank"] for x in json.loads(old[old.index("{"):old.rindex("}") + 1]).get("items", [])}
    except Exception: pass

rows.sort(key=lambda x: -x["cap"])
for n, r in enumerate(rows, 1):
    r["rank"] = n
    r["prev"] = prev.get(r["t"], n)
total = sum(r["cap"] for r in rows)
data = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(), "source": "Yahoo Finance (may be delayed)", "total": total, "items": rows}
open(OUT, "w", encoding="utf-8").write(
    "/* Written automatically by scripts/update_marketcaps.py - don't edit by hand. */\nwindow.DG_CAPS = "
    + json.dumps(data, separators=(",", ":")) + ";\n")
print(f"ranked {len(rows)} stocks, total ${total/1e12:.2f}T")
