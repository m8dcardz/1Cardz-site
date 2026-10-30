#!/usr/bin/env python3
"""Build news.html (News Headlines page, text only, card grid) from index.html's styles and binders + tools/news.json.
Run after build_archive.py (it reuses archive.html's binder script). Add new stories to tools/news.json."""
import json, sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import site_parts, re, html, datetime, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root/'index.html').read_text()
# index.html may be the standalone build (with its own doctype/head wrapper): strip it back to the fragment
if src.lstrip().lower().startswith('<!doctype'):
    vp = '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    src = src[src.index(vp)+len(vp):]
arch = (root/'archive.html').read_text()
news = sorted(json.loads((root/'tools'/'news.json').read_text()), key=lambda x: x['when'], reverse=True)
e = html.escape

head = src[:src.index('<style>')]
head = re.sub(r'<title>.*?</title>', '<title>1 Cardz Headlines</title>', head)
head = re.sub(r'<link rel="preload"[^>]*>\n', '', head)
head = head.replace('href="https://1cardz.news/"', 'href="https://1cardz.news/news.html"')
head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="News Headlines: the latest trading card game news from 1Cardz.news, newest first.">', head)
style = src[src.index('<style>'):src.index('</style>')+len('</style>')]
hs = src.index('<header class="wrap cover-zone">'); header = src[hs:src.index('\n</header>', hs)+len('\n</header>')]
fs = src.index('<footer class="wrap">'); footer = src[fs:src.index('\n</footer>', fs)+len('\n</footer>')]
scrolltop = src[src.index('<script>'):src.index('</script>')+len('</script>')]
header = re.sub(r'<p>The trading card game news channel.*?</p>',
    '<p>News Headlines. Every story from the 8 AM and 8 PM drops, newest first, in plain text.</p>', header, flags=re.S)
header = header.replace('<a class="btn" href="#set" id="seeLatest">See the latest</a>', '<a class="btn" href="index.html">Back to the binder</a>')
_k = arch.index('  /* binder videos: top first, bottom last */'); a_js = arch[arch.rindex('<script>', 0, _k):arch.index('</script>', _k)]
cover_js = a_js[a_js.index('  /* binder videos: top first, bottom last */'):a_js.rindex('})();')]

GC = {"Pokémon":"#ffd23f","Magic":"#ff8a5c","One Piece":"#ff5c7a","Lorcana":"#9d8cff","Flesh and Blood":"#ff6b4a",
      "Yu-Gi-Oh!":"#c58cff","Riftbound":"#5ce1ff","Gundam":"#9fe870","Dragon Ball":"#ffb347","Star Wars":"#cfd8ff"}
def when(s):
    d = datetime.datetime.fromisoformat(s); h = d.hour % 12 or 12
    m = f":{d.minute:02d}" if d.minute else ":00"
    return f"{d.strftime('%a')}, {d.strftime('%b')} {d.day} · {h}{m} {'AM' if d.hour < 12 else 'PM'} HKT"

tiles = []
for k, n in enumerate(news):
    tiles.append(f'''        <li class="news-tile{' lead' if k == 0 else ''}" data-game="{e(n['game'])}" style="--c:{GC.get(n['game'], '#7cf3ff')}">
          <div class="t-top"><span class="mw-game">{e(n['game'])}</span><time class="t-when" datetime="{e(n['when'])}:00+08:00">{when(n['when'])}</time></div>
          <h3 class="t-head">{e(n['title'])}</h3>
          <p class="t-sum">{e(n['summary'])}</p>
          <p class="t-src">Source: {e(n['source'])}</p>
        </li>''')
games = sorted({n['game'] for n in news})
chips = ['<button type="button" class="chip" data-g="all" aria-pressed="true">All games</button>']
chips += [f'<button type="button" class="chip" data-g="{e(g)}" aria-pressed="false">{e(g)}</button>' for g in games]
first = datetime.datetime.fromisoformat(news[-1]['when']); last = datetime.datetime.fromisoformat(news[0]['when'])

extra_css = '''<style>
/* news headlines page: card grid */
.news .sheet-head p{max-width:60ch}
.news .chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;align-items:center;flex-basis:100%}
.chip{font-family:var(--f-mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#c9cfe4;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:999px;padding:8px 14px;cursor:pointer}
.chip:hover{border-color:rgba(233,196,106,.6)}
.chip[aria-pressed="true"]{background:var(--foil);border-color:var(--foil);color:var(--cover)}
.btn.ghost{background:transparent;color:var(--foil);box-shadow:inset 0 0 0 1px rgba(233,196,106,.6)}
.news .gd{margin-top:8px}
.news-count{color:#8c93ad}
.news-grid{list-style:none;margin:0;padding:clamp(14px,2vw,22px);display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;position:relative;z-index:4}
.news-tile{position:relative;border-radius:14px;padding:16px 16px 14px;display:flex;flex-direction:column;gap:8px;min-width:0;overflow:hidden;
  background:linear-gradient(160deg,rgba(255,255,255,.09),rgba(255,255,255,.025));box-shadow:inset 0 0 0 1px rgba(255,255,255,.13),0 14px 30px rgba(0,0,0,.3);
  transition:transform .2s,box-shadow .2s}
.news-tile[hidden]{display:none}
.news-tile::before{content:"";position:absolute;left:0;top:0;right:0;height:3px;background:var(--c,#7cf3ff);opacity:.9}
.news-tile:hover{transform:translateY(-3px);box-shadow:inset 0 0 0 1px rgba(255,255,255,.22),0 20px 38px rgba(0,0,0,.42)}
.news-tile .t-top{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.news-tile .mw-game{background:var(--c);color:#12162b}
.news-tile .t-when{font-family:var(--f-mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:#8c93ad}
.news-tile .t-head{font-family:var(--f-display);font-weight:700;font-stretch:88%;font-size:22px;line-height:1.1;color:#fff;margin:2px 0 0}
.news-tile .t-sum{margin:0;color:#cfd4e6;font-size:15px;line-height:1.5}
.news-tile .t-src{margin:auto 0 0;padding-top:6px;color:#8c93ad;font-size:12.5px}
@media (min-width:640px){.news-tile.lead{grid-column:span 2}.news-tile.lead .t-head{font-size:32px}.news-tile.lead .t-sum{font-size:17px}}
@media (max-width:560px){.news-grid{grid-template-columns:1fr;gap:10px;padding:12px}.news-tile .t-head{font-size:20px}}
</style>'''

header = header + '\n\n' + site_parts.navbar(src, 'news.html')
footer = site_parts.newsletter_section(src) + '\n' + footer + '\n\n' + site_parts.newsletter_script(src)
body = f'''{header}

<main>
  <section class="wrap news" aria-labelledby="news-h">
    <div class="sheet-head">
      <h2 id="news-h">News Headlines</h2>
      <p>Every story from the 8 AM and 8 PM drops, newest first. Text only, with the source for each one.</p>
      <div class="chips" role="group" aria-label="Filter by game">{"".join(chips)}</div>
    </div>
    <div class="gd">
      <div class="mw-top">
        <span class="mono mw-label" style="color:#ffd23f"><i style="background:#ffd23f;box-shadow:0 0 10px #ffd23f"></i><span>Headlines</span></span>
        <span class="mono news-count" id="newsCount">{len(news)} stories</span>
        <span class="mono mw-upd">{first.strftime('%b')} {first.day} – {last.strftime('%b')} {last.day}, {last.year}</span>
      </div>
      <ol class="news-grid" id="newsGrid">
{chr(10).join(tiles)}
      </ol>
    </div>
  </section>
</main>

{footer}
'''

js = r'''<script>
(function(){
  const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.cover').forEach(cov=>{const ch=cov.querySelector('.cover-holo');if(reduce||!ch)return;
    cov.addEventListener('pointermove',e=>{const r=cov.getBoundingClientRect();cov.classList.add('hover');
      ch.style.setProperty('--hx',((e.clientX-r.left)/r.width*100).toFixed(1)+'%');ch.style.setProperty('--hy',((e.clientY-r.top)/r.height*100).toFixed(1)+'%')});
    cov.addEventListener('pointerleave',()=>{cov.classList.remove('hover');ch.style.removeProperty('--hx');ch.style.removeProperty('--hy')})});
  /* game filter */
  const chips=[...document.querySelectorAll('.chip')],tiles=[...document.querySelectorAll('.news-tile')],cnt=document.getElementById('newsCount');
  chips.forEach(c=>c.addEventListener('click',()=>{chips.forEach(x=>x.setAttribute('aria-pressed',String(x===c)));const g=c.dataset.g;let n=0;
    tiles.forEach(t=>{const ok=g==='all'||t.dataset.game===g;t.hidden=!ok;if(ok)n++});cnt.textContent=n+(n===1?' story':' stories')}));
__COVER__})();
</script>'''.replace('__COVER__', cover_js)

out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + head + style + '\n' + extra_css + '\n</head>\n<body>\n' + body + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
(root/'news.html').write_text(out)
print('news.html', len(out), 'bytes,', len(news), 'stories')
