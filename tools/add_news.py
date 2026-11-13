#!/usr/bin/env python3
"""Merge queued stories into tools/news.json.
Usage: python3 tools/add_news.py <queue.json>
The queue is a JSON array of {"when","game","title","summary","source","published"},
plus an optional "details": {"facts": [3-5 short lines], "why": "one line", "url": "source article"}.
Entries with published:true are ignored; entries whose "when" already exists in news.json are skipped.
Prints the titles it added (one per line) and nothing else."""
import json, sys, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
nj = root/'tools'/'news.json'
news = json.loads(nj.read_text())
have = {n['when'] for n in news}
queue = json.loads(pathlib.Path(sys.argv[1]).read_text())
added = []
for q in queue:
    if q.get('published') or q.get('when') in have:
        continue
    e = {k: str(q[k]).strip() for k in ('when', 'game', 'title', 'summary', 'source')}
    d = q.get('details')
    if isinstance(d, dict) and (d.get('facts') or d.get('why')):
        e['details'] = {'facts': [str(f).strip() for f in d.get('facts', []) if str(f).strip()][:6],
                        'why': str(d.get('why', '')).strip(), 'url': str(d.get('url', '')).strip()}
    news.append(e); have.add(e['when']); added.append(e['title'])
news.sort(key=lambda x: x['when'], reverse=True)
nj.write_text('[\n' + ',\n'.join(' ' + json.dumps(n, ensure_ascii=False) for n in news) + '\n]\n')
print('\n'.join(added))
