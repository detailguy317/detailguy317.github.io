"""DG317 link checker - finds dead links on the site so you don't have to click 300 buttons.
Runs every Sunday inside the garage-report robot; results show up in the Garage Report.
Run by hand:  python scripts/check_links.py   (writes link-report.json next to the scripts folder)
Standard library only."""
import json, os, re, sys, time, urllib.request, concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["index.html", "racing.html", "data/series.js", "data/live-content.js", "stocks-data.js"]
SKIP = re.compile(r"googletagmanager|\{Y\}|\$\{|youtube\.com/results|news\.google\.com|localhost|example\.com|wikipedia\.org/w/index\.php|"
                  r"googleapis|cdn\.|fonts\.|tradingview\.com/(embed|widget)|s3\.tradingview|\.js$|\.css$")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DG317-linkcheck"}

def urls():
    found = {}
    for f in FILES:
        try: txt = open(os.path.join(ROOT, f), encoding="utf-8").read()
        except FileNotFoundError: continue
        for u in re.findall(r"https?://[^\s\"'`<>)\\]+", txt):
            u = u.rstrip(".,;")
            if not SKIP.search(u): found.setdefault(u, f)
    return found

def check(u):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(u, method=method, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                return u, r.status, r.geturl()
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 400, 429, 501): continue
            return u, e.code, ""
        except Exception as e:
            if method == "HEAD": continue
            return u, 0, str(e)[:80]
    return u, 0, ""

def main():
    found = urls(); bad = []
    with cf.ThreadPoolExecutor(8) as ex:
        for u, code, info in ex.map(check, found):
            # 401/403/429 = site blocks robots but works in a browser -> not "dead"
            if code in (404, 410) or code >= 500 or code == 0:
                bad.append({"url": u, "code": code, "file": found[u], "info": info})
    out = {"checked": len(found), "bad": sorted(bad, key=lambda x: x["file"]), "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(out, open(os.path.join(ROOT, "link-report.json"), "w"), indent=1)
    print(f"checked {len(found)} links, {len(bad)} look dead")
    for b in bad: print(f"  {b['code']}  {b['url']}  ({b['file']})")

if __name__ == "__main__":
    main()
