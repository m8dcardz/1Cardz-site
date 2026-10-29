#!/usr/bin/env python3
"""Merge queued stories into tools/news.json.
Usage: python3 tools/add_news.py <queue.json>
The queue is a JSON array of {"when","game","title","summary","source","published"}.
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
    news.append(e); have.add(e['when']); added.append(e['title'])
news.sort(key=lambda x: x['when'], reverse=True)
nj.write_text('[\n' + ',\n'.join(' ' + json.dumps(n, ensure_ascii=False) for n in news) + '\n]\n')
print('\n'.join(added))
