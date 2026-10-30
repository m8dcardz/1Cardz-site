#!/usr/bin/env python3
"""Copy every posted 1 Cardz clip into the user's "All Clips" folder.
Reads tools/posts.json (the Stories list) from GitHub; downloads each entry that has a "media" URL and isn't in the folder yet.
Usage: python3 collect_clips.py "<path to All Clips>"   (never deletes or overwrites anything)"""
import json, re, sys, os, urllib.request
dest = sys.argv[1]; os.makedirs(dest, exist_ok=True)
posts = json.load(urllib.request.urlopen('https://raw.githubusercontent.com/m8dcardz/1Cardz-site/main/tools/posts.json'))
def name(p):
    t = re.sub(r'[^A-Za-z0-9]+', '-', p['title'].replace('$', '').replace("'", '').replace('’', '')).strip('-')
    w = p['when']; return f"{w[:10]}_{w[11:13]}{w[14:16]}_{p['host'].replace(' & ', '-')}_{t}.mp4"
added = []
for p in sorted(posts, key=lambda p: p['when']):
    if not p.get('media'): continue
    f = os.path.join(dest, name(p))
    if os.path.exists(f): continue
    tmp = f + '.part'
    with urllib.request.urlopen(p['media']) as r, open(tmp, 'wb') as o: o.write(r.read())
    os.rename(tmp, f); added.append(os.path.basename(f))
print(f"{len(added)} new clip(s)" + (': ' + ', '.join(added) if added else ''))
