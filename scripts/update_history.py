"""DG317 'This Day in Automotive History' robot.
Pulls Wikipedia's "On this day" list for today + the next 2 days (Mountain time), keeps only the
car / racing / industry items, and saves them in data/onthisday.js. Days pile up, so after a year
every date of the calendar is filled. The page also has a hand-picked list built in, so a day is never empty.
Runs inside the update-feeds robot. Standard library only."""
import json, os, re, urllib.request, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "onthisday.js")
UA = {"User-Agent": "DG317-Garage-robot/1.0 (fan site; github actions)"}
MT = dt.timezone(dt.timedelta(hours=-7))

STRONG = re.compile(r"\b(automobiles?|automotive|automakers?|carmakers?|car (?:manufacturer|company|maker|race|racing)|motor (?:company|corporation|car)|"
                    r"racing drivers?|race car|stock car|Formula (?:One|1)|Grand Prix|NASCAR|IndyCar|Indianapolis 500|Indy 500|Le Mans|Daytona 500|"
                    r"World Rally|rally driver|motorsports?|motor racing|drag racing|land speed record|speed record|hot rod|"
                    r"Model T|Henry Ford|Ford Motor|Edsel Ford|General Motors|Chrysler|Chevrolet|Toyota|Volkswagen|Porsche|Ferrari|Lamborghini|"
                    r"Mercedes-Benz|Karl Benz|Daimler|BMW|Cadillac|Pontiac|Oldsmobile|Buick|Jeep|Tesla, Inc|Tesla Motors|Harley-Davidson|"
                    r"motorcycles?|Honda Motor|Nissan|Mazda|Subaru|Hyundai|Kia Motors|Rolls-Royce Motor|Bentley|Aston Martin|Jaguar Cars|Land Rover|"
                    r"Interstate Highway|Federal-Aid Highway|highway system|seat belts?|airbags?|traffic lights?|driver'?s licen[cs]e|speed limit|"
                    r"gasoline|petrol|diesel engine|internal combustion|pickup truck|electric vehicles?|electric cars?|assembly line)\b", re.I)
# words that look automotive but usually aren't (Gerald Ford, Harrison Ford, political rallies, Dodge City...)
NOT = re.compile(r"\b(President of the United States|actor|actress|film director|singer|baseball|basketball|football|soccer|cricket|"
                 r"politician|Gerald Ford|Harrison Ford|Dodge City|aircraft|airline|spacecraft)\b", re.I)

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
        return json.loads(r.read())

def pick(day):
    mm, dd = f"{day.month:02d}", f"{day.day:02d}"
    data = None
    for url in (f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/{mm}/{dd}",
                f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{mm}/{dd}"):
        try:
            data = get(url); break
        except Exception as e:
            print("  try next:", url, e)
    if not data: return None
    out, seen = [], set()
    for kind in ("selected", "events", "births", "deaths"):
        for it in data.get(kind) or []:
            text, year = (it.get("text") or "").strip(), it.get("year")
            pages = it.get("pages") or []
            descs = " ".join((p.get("description") or "") for p in pages)
            blob = text + " " + descs
            if not STRONG.search(blob): continue
            # births/deaths: the PERSON must be automotive (their own description), not just mention a car
            if kind in ("births", "deaths"):
                d0 = (pages[0].get("description") or "") if pages else ""
                if not STRONG.search(d0 + " " + text) or NOT.search(d0): continue
            elif NOT.search(text) and not STRONG.search(text): continue
            key = (year, text[:40])
            if key in seen: continue
            seen.add(key)
            url = ""
            if pages:
                url = ((pages[0].get("content_urls") or {}).get("desktop") or {}).get("page") or ""
            label = {"births": "Born: ", "deaths": "Died: "}.get(kind, "")
            out.append({"y": year, "t": (label + text)[:220], "u": url, "k": kind})
    out.sort(key=lambda x: (x["k"] in ("births", "deaths"), -(x["y"] or 0)))
    return out[:8]

def main():
    try:
        txt = open(OUT, encoding="utf-8").read()
        old = json.loads(txt[txt.index("= ") + 2:].strip().rstrip(";"))
    except Exception:
        old = {"days": {}}
    days = old.get("days", {})
    today = dt.datetime.now(MT).date()
    for i in range(3):
        d = today + dt.timedelta(days=i)
        key = f"{d.month:02d}-{d.day:02d}"
        items = pick(d)
        if items is not None:
            days[key] = items
            print(key, len(items), "items")
    out = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), "days": days}
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* written by scripts/update_history.py - do not hand edit */\nwindow.DG_ONTHISDAY = " + json.dumps(out, ensure_ascii=False) + ";\n")

if __name__ == "__main__":
    main()
