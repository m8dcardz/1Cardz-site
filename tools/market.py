#!/usr/bin/env python3
"""Market Watch builder (runs daily on GitHub Actions).
- Finds the 2 newest main sets per game on TCGplayer (via the TCGCSV daily mirror).
- Pool = their booster boxes / displays / ETBs + the 3 priciest singles per set.
- Each day features 6 sealed + 6 singles, rotating through the pool and mixing games.
- Keeps up to 30 days of market-price history for every pooled item."""
import json, os, re, urllib.request, datetime

GAMES = [(3,"Pokémon"),(1,"Magic"),(68,"One Piece"),(2,"Yu-Gi-Oh!"),(71,"Lorcana"),(89,"Riftbound"),(86,"Gundam")]
SETS_PER_GAME = 2
SINGLES_PER_SET = 3
FEATURE = 6
SEALED_RE = re.compile(r"(Booster Box|Booster Display|Collector Booster Display|Play Booster Display|Elite Trainer Box|Booster Box \[1st Edition\]|Display)$", re.I)
BOX_RE = re.compile(r"Booster (Box|Display)", re.I)
SEALED_SKIP = re.compile(r"Case|Code Card|Pokemon Center|Pokémon Center|Build & Battle|Mini Tin|Blister|Prerelease|Art Series|Deck|Starter|Double Pack|Champion|Gift|Collection", re.I)

def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": "1cardz-market-watch/2.0", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=60))

def best_price(rows):
    rows = [r for r in rows if r.get("marketPrice")]
    return max(rows, key=lambda r: r["marketPrice"]) if rows else None

def build_pool(today):
    pool = []
    for cat, game in GAMES:
        try: groups = get(f"https://tcgcsv.com/tcgplayer/{cat}/groups")["results"]
        except Exception as e: print("skip", game, e); continue
        groups = [g for g in groups if g.get("publishedOn","")[:10] <= today]
        groups.sort(key=lambda g: g.get("publishedOn",""), reverse=True)
        taken = 0
        for g in groups[:40]:
            if taken >= SETS_PER_GAME: break
            gid = g["groupId"]
            try:
                prods = get(f"https://tcgcsv.com/tcgplayer/{cat}/{gid}/products")["results"]
                prices = get(f"https://tcgcsv.com/tcgplayer/{cat}/{gid}/prices")["results"]
            except Exception as e: print("skip group", gid, e); continue
            pm = {}
            for p in prices: pm.setdefault(p["productId"], []).append(p)
            isnum = lambda p: any(e.get("name") == "Number" for e in p.get("extendedData", []))
            sealed = [p for p in prods if not isnum(p) and SEALED_RE.search(p["name"]) and not SEALED_SKIP.search(p["name"])]
            sealed = [(p, best_price(pm.get(p["productId"], []))) for p in sealed]
            sealed = [(p, r) for p, r in sealed if r and r["marketPrice"] >= 20]
            if not any(BOX_RE.search(p["name"]) for p, r in sealed): continue
            taken += 1
            setname = re.sub(r"^[A-Z]{1,4}\d{0,3}[a-z]?:\s*", "", g["name"])
            sealed.sort(key=lambda x: -x[1]["marketPrice"])
            for p, r in sealed[:2]:
                pool.append(dict(kind="sealed", game=game, name=p["name"].replace(" - ", " "), set=setname, pid=p["productId"], sub=r["subTypeName"], price=r["marketPrice"], low=r.get("lowPrice")))
            singles = [(p, best_price(pm.get(p["productId"], []))) for p in prods if isnum(p)]
            singles = [(p, r) for p, r in singles if r and r["marketPrice"] >= 20]
            singles.sort(key=lambda x: -x[1]["marketPrice"])
            for p, r in singles[:SINGLES_PER_SET]:
                pool.append(dict(kind="single", game=game, name=p["name"], set=setname, pid=p["productId"], sub=r["subTypeName"], price=r["marketPrice"], low=r.get("lowPrice")))
    return pool

def rotate(items, n, day_index):
    """Round-robin across games, starting at a different offset each day."""
    by_game = {}
    for it in items: by_game.setdefault(it["game"], []).append(it)
    games = sorted(by_game)
    if not games: return []
    for g in games: by_game[g].sort(key=lambda i: i["id"])
    pick, k = [], 0
    off = day_index % len(games)
    while len(pick) < min(n, len(items)):
        g = games[(off + k) % len(games)]
        lst = by_game[g]
        cand = lst[(day_index // len(games) + k // len(games)) % len(lst)]
        if cand not in pick: pick.append(cand)
        k += 1
        if k > 10 * n: break
    return pick

def main(path="data/market.json"):
    old = {}
    if os.path.exists(path):
        try: old = {i["id"]: i for i in json.load(open(path)).get("pool", json.load(open(path)).get("items", []))}
        except Exception: old = {}
    try: stamp = urllib.request.urlopen(urllib.request.Request("https://tcgcsv.com/last-updated.txt", headers={"User-Agent":"1cardz-market-watch/2.0"}), timeout=30).read().decode().strip()
    except Exception: stamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0000")
    day = stamp[:10]
    pool = []
    for it in build_pool(day):
        iid = f"{it['pid']}-{it['sub']}"
        hist = [h for h in old.get(iid, {}).get("history", []) if h[0] != day] + [[day, round(it["price"], 2)]]
        pool.append({"id": iid, "kind": it["kind"], "game": it["game"], "name": it["name"], "set": it["set"],
                     "price": round(it["price"], 2), "low": it["low"],
                     "url": f"https://www.tcgplayer.com/product/{it['pid']}", "history": sorted(hist)[-30:]})
    di = datetime.date.fromisoformat(day).toordinal()
    feat = rotate([p for p in pool if p["kind"] == "sealed"], FEATURE, di) + rotate([p for p in pool if p["kind"] == "single"], FEATURE, di)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump({"updated": stamp, "source": "TCGplayer market price via TCGCSV",
               "items": feat, "pool": pool}, open(path, "w"), ensure_ascii=False, indent=1)
    print("wrote", path, "featured", len(feat), "pool", len(pool), stamp)

if __name__ == "__main__":
    main()
