"""DG317 race-video robot - catches LIVE racing on YouTube within ~30 minutes, any day, any time zone.

How it stays inside YouTube's free quota (10,000 units/day):
  * Channel uploads come from each channel's public RSS feed            -> 0 units
  * One videos.list call checks up to 50 of those videos for LIVE/UPCOMING -> 1 unit
  * One wide "who's streaming racing right now" search per run             -> 100 units
  Run every 30 min = ~48 x ~105 = ~5,000 units/day.
  * Replay Theater list (most-watched highlights per trusted channel), once a day -> ~100 units per channel (~2,000)
  Total ~7,000 of the free 10,000.

Trusted channels (data/live-content.js "channels") can fill the 3 video slots automatically.
Anything the wide search finds from OTHER channels goes on the admin.html list for you to pick -
the public page never auto-plays an unknown channel (fake "F1 LIVE" streams are common).
Output: data/racing-auto.js. Standard library only. Needs repo secret YOUTUBE_API_KEY.
"""
import json, os, re, sys, urllib.request, urllib.parse, datetime as dt
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "racing-auto.js")
IDS = os.path.join(ROOT, "data", "yt-channel-ids.json")
KEY = os.environ.get("YOUTUBE_API_KEY", "")
NOW = dt.datetime.now(dt.timezone.utc)
UA = {"User-Agent": "Mozilla/5.0 DG317-robot"}

RACE = re.compile(r"race|racing|grand prix|\bgp\b|qualif|practice|\bfp[123]\b|sprint|rally|nascar|indy|formula|\bf[1234]\b|supercars|"
                  r"le mans|imsa|wec|motogp|superbike|nhra|drag|dirt|sprint car|late model|karting|supercross|motocross|"
                  r"endurance|\bgt\b|tcr|touring car|truck|pull|baja|off-?road|world cup|macau|highlights|final", re.I)
JUNK = re.compile(r"iracing|sim ?racing|assetto|gran turismo|forza|\bf1 ?2[0-9]\b game|roblox|gameplay|reaction|watchalong|"
                  r"watch party|live commentary only|radio only|no video|fan stream|free stream|\bhd stream\b", re.I)

def get(url, timeout=25):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()

def yt(path, **p):
    p["key"] = KEY
    return json.loads(get("https://www.googleapis.com/youtube/v3/" + path + "?" + urllib.parse.urlencode(p)))

def load_js(path, var):
    try:
        t = open(path, encoding="utf-8").read()
        return json.loads(t[t.index(var + " = ") + len(var) + 3:].strip().rstrip(";"))
    except Exception:
        return {}

def channel_ids(handles):
    try: cache = json.load(open(IDS))
    except Exception: cache = {}
    changed = False
    for h in handles:
        if h in cache: continue
        try:
            items = yt("channels", part="id", forHandle=h).get("items") or []   # 1 unit, only the first time
            cache[h] = items[0]["id"] if items else ""
            changed = True
            print(("ok   " if cache[h] else "MISS ") + h)
        except Exception as e:
            print("skip", h, e)
    if changed: json.dump(cache, open(IDS, "w"), indent=1)
    return {h: cache.get(h) for h in handles if cache.get(h)}

def rss_ids(cid):
    try:
        root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
        ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
        return [e.findtext("yt:videoId", namespaces=ns) for e in root.findall("a:entry", ns)][:12]
    except Exception as e:
        print("rss fail", cid, e); return []

def describe(ids):
    out = {}
    for i in range(0, len(ids), 50):
        chunk = [x for x in ids[i:i + 50] if x]
        if not chunk: continue
        for v in yt("videos", part="snippet,liveStreamingDetails,status,statistics,contentDetails", id=",".join(chunk), maxResults=50).get("items", []):
            out[v["id"]] = v
    return out

def ts(s):
    try: return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception: return None

LOOP = re.compile(r"24/7|24-7|24 ?hours? a day|nonstop|non-stop|around the clock|replay channel|marathon|retro review", re.I)

def classify(v):
    s, L = v["snippet"], v.get("liveStreamingDetails") or {}
    state = s.get("liveBroadcastContent")
    if state == "live": return ("loop", 2) if LOOP.search(s.get("title", "")) else ("live", 0)
    if state == "upcoming":
        st = ts(L.get("scheduledStartTime", "")) or NOW
        hrs = (st - NOW).total_seconds() / 3600
        return ("upcoming", 1) if -2 < hrs < 36 else (None, 9)
    pub = ts(s.get("publishedAt", "")) or NOW
    if (NOW - pub).days <= 4 and RACE.search(s.get("title", "")): return "recent", 3
    return None, 9

# Channels whose owners block their videos from playing on other websites (YouTube shows "Video unavailable").
# Their live streams still show in LIVE NOW, but open on YouTube instead of in the site's player.
NO_EMBED = re.compile(r"^(formula ?1|f1)$", re.I)

def can_embed(v):
    return bool((v.get("status") or {}).get("embeddable", True)) and not NO_EMBED.match(v["snippet"].get("channelTitle", "").strip())

def row(v, kind, trusted):
    s, L = v["snippet"], v.get("liveStreamingDetails") or {}
    th = (s.get("thumbnails") or {}).get("medium") or (s.get("thumbnails") or {}).get("default") or {}
    return {"type": "video", "id": v["id"], "title": s.get("title", "")[:140], "channel": s.get("channelTitle", ""),
            "kind": kind, "date": L.get("actualStartTime") or L.get("scheduledStartTime") or s.get("publishedAt"),
            "viewers": L.get("concurrentViewers"), "thumb": th.get("url", ""), "trusted": trusted, "embed": can_embed(v)}

REEL_WORDS = re.compile(r"highlights|full race|full broadcast|full replay|replay|extended|race recap|best moments|top \d+|onboard|last lap|finish", re.I)
ISO_DUR = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")

def minutes(v):
    m = ISO_DUR.match((v.get("contentDetails") or {}).get("duration", "") or "")
    return (int(m.group(1) or 0) * 60 + int(m.group(2) or 0) + int(m.group(3) or 0) / 60) if m else 0

def reel(cids, old):
    """Replay Theater list: the most-watched recent highlights + full races from trusted channels.
    Refreshed about once a day (~100 units per channel). Dec-Feb it reaches back ~5 months (off-season)."""
    if old.get("reel") and (NOW - (ts(old.get("reel_at", "")) or dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc))).total_seconds() < 20 * 3600:
        return old["reel"], old["reel_at"]
    back = 150 if NOW.month in (12, 1, 2) else 30
    since = (NOW - dt.timedelta(days=back)).isoformat(timespec="seconds").replace("+00:00", "Z")
    picks = {}
    for h, cid in cids.items():
        try:
            r = yt("search", part="snippet", channelId=cid, type="video", order="viewCount", publishedAfter=since,
                   q="highlights|full race|replay|extended|recap", maxResults=8)
            picks[cid] = [it["id"]["videoId"] for it in r.get("items", []) if it.get("id", {}).get("videoId")]
        except Exception as e:
            print("reel skip", h, e)
    info = describe([v for ids in picks.values() for v in ids])
    per = {}
    for cid, ids in picks.items():
        rows = []
        for vid in ids:
            v = info.get(vid)
            if not v or not can_embed(v): continue
            t = v["snippet"].get("title", "")
            if JUNK.search(t) or not REEL_WORDS.search(t) or minutes(v) < 3: continue   # no Shorts, no junk
            row_ = row(v, "reel", True); row_["views"] = int((v.get("statistics") or {}).get("viewCount") or 0)
            rows.append(row_)
        per[cid] = sorted(rows, key=lambda x: -x["views"])[:3]
    out, seen = [], set()                              # take turns between channels so it isn't 10 F1 clips in a row
    for k in range(3):
        for cid in sorted(per, key=lambda c: -(per[c][0]["views"] if per[c] else 0)):
            if k < len(per[cid]) and per[cid][k]["id"] not in seen:
                seen.add(per[cid][k]["id"]); out.append(per[cid][k])
    print(f"reel: {len(out)} replays (looked back {back} days)")
    return out[:30], NOW.isoformat(timespec="minutes")

def main():
    if not KEY:
        print("no YOUTUBE_API_KEY secret - skipping"); return
    live_cfg = load_js(os.path.join(ROOT, "data", "live-content.js"), "window.DG_LIVE")
    handles = list(dict.fromkeys((live_cfg.get("channels") or []) + ["@FIA"]))
    cids = channel_ids(handles)
    trusted_ids = set(cids.values())

    vids = []
    for h, cid in cids.items(): vids += rss_ids(cid)
    # wide net: anything streaming racing live right now (100 units)
    wide = []
    try:
        r = yt("search", part="snippet", eventType="live", type="video", maxResults=25, order="viewCount",
               q='racing|"grand prix"|motorsport|NASCAR|"Formula 1"|IndyCar|rally|Supercars|"drag racing"|MotoGP|qualifying')
        for it in r.get("items", []):
            t = it["snippet"]["title"]
            if RACE.search(t) and not JUNK.search(t): wide.append(it["id"]["videoId"])
    except Exception as e:
        print("wide search failed:", e)
    info = describe(list(dict.fromkeys(vids + wide)))

    rows = []
    for vid, v in info.items():
        kind, rank = classify(v)
        if not kind: continue
        trusted = v["snippet"].get("channelId") in trusted_ids
        if not trusted and kind != "live": continue          # only show strangers' streams if live right now (never their 24/7 loops)
        if JUNK.search(v["snippet"].get("title", "")): continue
        rows.append((rank, 0 if trusted else 1, -(int((v.get("liveStreamingDetails") or {}).get("concurrentViewers") or 0)), row(v, kind, trusted)))
    rows.sort(key=lambda x: (x[0], x[1], x[2], -(ts(x[3]["date"] or "") or NOW).timestamp()))
    allrows = [r[3] for r in rows]
    slots = [r for r in allrows if r["trusted"] and r.get("embed", True)][:3]   # only videos that actually play on the site
    live_now = [r for r in allrows if r["kind"] == "live"]

    old = load_js(OUT, "window.DG_RACING_AUTO")
    try: reel_list, reel_at = reel(cids, old)
    except Exception as e: print("reel failed:", e); reel_list, reel_at = old.get("reel", []), old.get("reel_at", "")
    new = {"updated": NOW.isoformat(timespec="minutes"), "slots": slots, "live": live_now[:12], "found": allrows[:40],
           "reel": reel_list, "reel_at": reel_at}
    same = {k: old.get(k) for k in ("slots", "live", "reel")} == {k: new[k] for k in ("slots", "live", "reel")}
    if same and old.get("updated") and (NOW - (ts(old["updated"]) or NOW)).total_seconds() < 6 * 3600:
        print("no change - not rewriting"); return      # keeps the git history quiet
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* Written automatically by scripts/update_videos.py - don't edit by hand. */\nwindow.DG_RACING_AUTO = "
                + json.dumps(new, indent=1, ensure_ascii=False) + ";\n")
    print(f"live={len(live_now)} slots={[s['title'][:40] for s in slots]}")

if __name__ == "__main__":
    main()
