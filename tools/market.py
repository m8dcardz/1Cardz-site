#!/usr/bin/env python3
"""Builds data/market.json for the Market Watch chart from TCGCSV (daily TCGplayer price mirror).
Run daily. Keeps the last 30 days of market prices per item for the trend line."""
import json, os, urllib.request, datetime

ITEMS = [
  # kind, game, label, set, categoryId, groupId, productId, subType
  ("sealed","Pokémon","30th Celebration Elite Trainer Box","30th Celebration",3,24722,704143,"Normal"),
  ("sealed","Magic","Reality Fracture Collector Booster Display","Reality Fracture",1,24684,692983,"Normal"),
  ("sealed","One Piece","The World's Strongest Warriors Booster Box","World's Strongest Warriors",68,24736,704752,"Normal"),
  ("sealed","Yu-Gi-Oh!","Magnificent Monsters Display","Magnificent Monsters",2,24707,694826,"Normal"),
  ("sealed","Riftbound","Origins Booster Display","Origins",89,24344,635368,"Normal"),
  ("sealed","Pokémon","Pitch Black Booster Box","Pitch Black",3,24688,692939,"Normal"),
  ("single","Pokémon","Mega Darkrai ex 116/084","Pitch Black",3,24688,704873,"Holofoil"),
  ("single","Yu-Gi-Oh!","Magician of Dark Chaos – Black Chaos (Starlight)","Chaos Origins",2,24675,702385,"1st Edition"),
  ("single","One Piece","Rocks.D.Xebec (Super Alt Art)","World's Strongest Warriors",68,24736,712117,"Foil"),
  ("single","Magic","The Theorist, Jace Beleren (Fracture Foil)","Reality Fracture",1,24684,706993,"Foil"),
  ("single","Riftbound","Ahri, Nine-Tailed Fox (Signature)","Origins",89,24344,653102,"Foil"),
  ("single","Pokémon","Mega Zygarde ex 124/088","Perfect Order",3,24587,684339,"Holofoil"),
]

def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": "1cardz-market-watch/1.0", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=60))

def main(path="data/market.json"):
    old = {}
    if os.path.exists(path):
        try: old = {i["id"]: i for i in json.load(open(path)).get("items", [])}
        except Exception: old = {}
    try: stamp = urllib.request.urlopen(urllib.request.Request("https://tcgcsv.com/last-updated.txt", headers={"User-Agent":"1cardz-market-watch/1.0"}), timeout=30).read().decode().strip()
    except Exception: stamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0000")
    day = stamp[:10]
    cache = {}
    out = []
    for kind, game, label, setname, cat, grp, pid, sub in ITEMS:
        key = (cat, grp)
        if key not in cache:
            cache[key] = get(f"https://tcgcsv.com/tcgplayer/{cat}/{grp}/prices")["results"]
        row = next((p for p in cache[key] if p["productId"] == pid and p["subTypeName"] == sub), None)
        iid = f"{pid}-{sub}"
        hist = old.get(iid, {}).get("history", [])
        price = row and row.get("marketPrice")
        if price is not None:
            hist = [h for h in hist if h[0] != day] + [[day, round(price, 2)]]
        hist = sorted(hist)[-30:]
        out.append({"id": iid, "kind": kind, "game": game, "name": label, "set": setname,
                    "price": hist[-1][1] if hist else None,
                    "low": row and row.get("lowPrice"),
                    "url": f"https://www.tcgplayer.com/product/{pid}",
                    "history": hist})
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump({"updated": stamp, "source": "TCGplayer market price via TCGCSV", "items": out}, open(path, "w"), ensure_ascii=False, indent=1)
    print("wrote", path, len(out), "items", stamp)

if __name__ == "__main__":
    main()
