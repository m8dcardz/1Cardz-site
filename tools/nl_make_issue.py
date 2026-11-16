"""Make the week's magazine issue file (Nov 16, 2026): tools/newsletters/issue-NN.json + tools/newsletter_latest.json.

The week = stories posted after last Sunday 7:47 AM up to this Sunday 7:47 AM (the newsletter run's time).
Stories come from tools/news.json (title, summary, source, details) and tools/posts.json (clip, host, quip).

  python3 tools/nl_make_issue.py --date 2026-11-15 --big clip50 [--clips clip49,clip47,...]
      [--cover-clip clip50 | --cover-image img/<file>.jpg (3:4)] [--cover-main "..."] [--cover-sub "..."] [--line "Title|sub" (up to 3)]
      [--title "..."] [--opening "..."] [--pull "..."] [--calendar release-calendar.md] [--no 03]

--big     the cover story's clip. --clips  the top stories' clips in order (default: the rest of the week, newest first, max 12: 4 in the photo sets, 8 on the top-stories pages; clips used in an earlier issue are skipped).
--calendar  the project's release calendar (markdown table) for "The week ahead" and "Further ahead".
Anything not given gets a plain default from the stories. Then run tools/build_newsletter.py."""
import argparse, datetime, json, pathlib, re

root = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--date', required=True); ap.add_argument('--big', required=True); ap.add_argument('--clips', default='')
ap.add_argument('--cover-clip'); ap.add_argument('--cover-image'); ap.add_argument('--cover-main'); ap.add_argument('--cover-sub', default='')
ap.add_argument('--line', action='append', default=[]); ap.add_argument('--title'); ap.add_argument('--opening', default='')
ap.add_argument('--pull'); ap.add_argument('--calendar'); ap.add_argument('--no')
a = ap.parse_args()

d = datetime.date.fromisoformat(a.date)
t1 = f'{d.isoformat()}T07:47'; t0 = f'{(d - datetime.timedelta(days=7)).isoformat()}T07:47'
news = json.loads((root / 'tools' / 'news.json').read_text())
posts = json.loads((root / 'tools' / 'posts.json').read_text())
by_when = {n['when']: n for n in news}
week = sorted([p for p in posts if t0 < p.get('when', '') <= t1 and p.get('clip')], key=lambda p: p['when'], reverse=True)
by_clip = {p['clip']: p for p in posts}

def story(clip):
    p = by_clip[clip]; n = by_when.get(p['when'], {})
    s = {'clip': clip, 'when': p['when'], 'game': n.get('game') or p.get('game', ''), 'title': n.get('title') or p.get('title', ''),
         'summary': n.get('summary') or p.get('blurb', ''), 'source': n.get('source') or p.get('source', ''),
         'host': p.get('host', ''), 'quip': p.get('quip', '')}
    if n.get('details'): s['details'] = n['details']
    return s

# skip clips already used in last week's issue
_prev = set()
for f in (root / 'tools' / 'newsletters').glob('issue-*.json'):
    _d = json.loads(f.read_text())
    if _d.get('date') and datetime.datetime.strptime(_d['date'], '%A, %B %d, %Y').date() < d:
        _prev |= {s.get('clip') for s in _d.get('stories', [])} | set((_d.get('sections') or [{}, {}])[1].get('clips', []) if len(_d.get('sections') or []) > 1 else []) | {_d.get('big_clip'), _d.get('cover_clip')}
clips = [c for c in a.clips.split(',') if c] or [p['clip'] for p in week if p['clip'] != a.big and p['clip'] not in _prev][:12]
sts = [story(a.big)] + [story(c) for c in clips]

if a.no:
    no = a.no
else:
    nos = [int(json.loads(f.read_text()).get('no', 0)) for f in (root / 'tools' / 'newsletters').glob('issue-*.json')]
    no = f'{max(nos + [0]) + 1:02d}'
    old = root / 'tools' / 'newsletters' / f'issue-{int(no) - 1:02d}.json'
    if old.exists() and json.loads(old.read_text()).get('date', '').endswith(f'{d.day}, {d.year}') and d.strftime('%B') in json.loads(old.read_text()).get('date', ''):
        no = f'{int(no) - 1:02d}'                     # re-running the same Sunday: replace that issue
day = lambda x: x.strftime('%a, %b ') + str(x.day)

# calendar: next 7 days (incl. events still running) and further ahead
cal, radar = [], []
if a.calendar:
    for row in pathlib.Path(a.calendar).read_text().splitlines():
        c = [x.strip() for x in row.strip().strip('|').split('|')]
        if len(c) < 6 or not re.match(r'\d{4}-\d\d-\d\d$', c[0]): continue
        start = datetime.date.fromisoformat(c[0]); what = c[2].replace('\\|', '|'); game = c[1]; status = c[4]
        m = re.search(r'\(to ([A-Z][a-z]{2}) (\d+)(?:, (\d{4}))?[^)]*\)', what)
        end = start
        if m:
            end = datetime.datetime.strptime(f'{m.group(1)} {m.group(2)} {m.group(3) or start.year}', '%b %d %Y').date()
            if end < start: end = end.replace(year=end.year + 1)
        if start < d <= end:
            cal.append([f'Now to {end.strftime("%b")} {end.day}', f'{game}: {re.sub(r" ?\(to [^)]*\)", "", what)}', status])
        elif d <= start <= d + datetime.timedelta(days=6):
            cal.append([day(start), f'{game}: {what}', status])
        elif start > d + datetime.timedelta(days=6) and len(radar) < 8:
            radar.append([f'{start.strftime("%b")} {start.day}, {start.year}', f'{game}: {what}' + (' (reported)' if status.lower() == 'reported' else '')])

b0 = sts[0]
issue = {
    'no': no, 'vol': int(no), 'date': d.strftime('%A, %B ') + f'{d.day}, {d.year}',
    'title': a.title or f'{b0["title"]}: the week in cards',
    'intro': "One free email every Sunday with the week in cards. Here's the latest issue as a magazine: tap the cover to open it, and sign up free at the bottom of the page.",
    'greeting': 'Hey there,', 'opening': a.opening,
    'image': f'img/{b0["clip"]}.jpg', 'image_alt': f'{b0["host"]} reports: {b0["title"]}',
    'cover_clip': a.cover_clip or b0['clip'], 'big_clip': b0['clip'],
    'cover': {'main': a.cover_main or b0['title'], 'sub': a.cover_sub,
              'lines': [l.split('|', 1) if '|' in l else [l, ''] for l in a.line][:3] or [[s['title'], s['game']] for s in sts[1:4]]},
    'pull': a.pull or b0.get('quip', ''),
    **({'cover_image': a.cover_image} if a.cover_image else {}),
    'stories': sts,
    'radar': radar,
    'sections': [
        {'h': 'The big one', 'p': [[b0['title'] + '.', b0['summary'], b0['source']]]},
        {'h': 'Top stories this week', 'li': [[f'{s["game"]}: {s["title"]}.', s['summary'], s['source']] for s in sts[1:]], 'clips': [s['clip'] for s in sts[1:]]},
        {'h': 'Coming up this week', 'li': cal},
    ],
    'signoff': ['Shuffle up,', 'Zia & Luna'],
}
txt = json.dumps(issue, ensure_ascii=False, indent=1) + '\n'
(root / 'tools' / 'newsletters' / f'issue-{no}.json').write_text(txt)
(root / 'tools' / 'newsletter_latest.json').write_text(txt)
print(f'issue-{no}.json: {len(sts)} stories ({sum(1 for s in sts if s.get("details"))} with details), {len(cal)} this week, {len(radar)} further ahead')
