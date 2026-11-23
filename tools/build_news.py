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
header = re.sub(r'<p class="home-intro">.*?</p>|<p>The trading card game news channel.*?</p>',
    '<p>News Headlines. Every story from the 8 AM and 8 PM drops, newest first, in plain text.</p>', header, flags=re.S)
header = header.replace('<a class="btn" href="#set" id="seeLatest">See the latest</a>', '<a class="btn" href="index.html">Back home</a>')
_k = arch.index('  /* binder videos: top first, bottom last */'); a_js = arch[arch.rindex('<script>', 0, _k):arch.index('</script>', _k)]
cover_js = a_js[a_js.index('  /* binder videos: top first, bottom last */'):a_js.rindex('})();')]

GC = {"Pokémon":"#ffd23f","Magic":"#ff8a5c","One Piece":"#ff5c7a","Lorcana":"#9d8cff","Flesh and Blood":"#ff6b4a",
      "Yu-Gi-Oh!":"#c58cff","Riftbound":"#5ce1ff","Gundam":"#9fe870","Dragon Ball":"#ffb347","Star Wars":"#cfd8ff"}
def when(s):
    d = datetime.datetime.fromisoformat(s); h = d.hour % 12 or 12
    m = f":{d.minute:02d}" if d.minute else ":00"
    return f"{d.strftime('%a')}, {d.strftime('%b')} {d.day} · {h}{m} {'AM' if d.hour < 12 else 'PM'}"

import unicodedata
def story_url(n):
    """news-YYYY-MM-DD-<slug>.html (the Home headline box builds the same name in JS)"""
    t = unicodedata.normalize('NFKD', n['title']).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:70].rstrip('-')
    return f"news-{n['when'][:10]}-{t}.html"

# Headlines page (Nov 16, 2026, user): only the newest 35 stories (25 on phones, hidden by CSS); each box shows the title only and
# expands down to the story when tapped. Every story still has its own page (built below from all of news.json).
shown = news[:35]
tiles = []
for k, n in enumerate(shown):
    tiles.append(f'''        <li class="news-tile{' lead' if k == 0 else ''}" data-game="{e(n['game'])}" style="--c:{GC.get(n['game'], '#7cf3ff')}">
          <div class="t-top"><span class="mw-game">{e(n['game'])}</span><time class="t-when" datetime="{e(n['when'])}:00+08:00">{when(n['when'])}</time></div>
          <h3 class="t-head"><button type="button" class="t-tog" aria-expanded="false" aria-controls="tb{k}"><span>{e(n['title'])}</span><i aria-hidden="true"></i></button></h3>
          <div class="t-body" id="tb{k}"><div>
            <p class="t-sum">{e(n['summary'])}</p>
            <p class="t-src">Source: {e(n['source'])}</p>
            <a class="t-more" href="{story_url(n)}">Read the full story ›</a>
          </div></div>
        </li>''')
games = sorted({n['game'] for n in shown})
chips = ['<button type="button" class="chip" data-g="all" aria-pressed="true">All games</button>']
chips += [f'<button type="button" class="chip" data-g="{e(g)}" aria-pressed="false">{e(g)}</button>' for g in games]
first = datetime.datetime.fromisoformat(shown[-1]['when']); last = datetime.datetime.fromisoformat(shown[0]['when'])

extra_css = '''<style>
/* news headlines page: card grid */
/* intro width comes from the page heading rules in index.html */
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
.news-tile .t-head a{color:inherit;text-decoration:none}.news-tile .t-head a:hover{text-decoration:underline;text-decoration-color:var(--c)}
.news-tile .t-head{font-family:var(--f-display);font-weight:700;font-stretch:88%;font-size:22px;line-height:1.1;color:#fff;margin:2px 0 0}
.news-tile .t-sum{margin:0;color:#cfd4e6;font-size:15px;line-height:1.5}
/* title only; tap to expand the story (Nov 16) */
.news-grid{align-items:start}
.news-tile{cursor:pointer}
.news-tile .t-tog{all:unset;box-sizing:border-box;display:flex;width:100%;align-items:flex-start;justify-content:space-between;gap:12px;cursor:pointer;color:inherit;font:inherit}
.news-tile .t-tog:focus-visible{outline:2px solid var(--c);outline-offset:4px;border-radius:4px}
.news-tile .t-tog i{flex:none;width:11px;height:11px;margin-top:.35em;border-right:2px solid var(--c);border-bottom:2px solid var(--c);transform:rotate(45deg);transition:transform .25s}
.news-tile.open .t-tog i{transform:rotate(-135deg) translate(-3px,-3px)}
.news-tile .t-body{display:grid;grid-template-rows:0fr;transition:grid-template-rows .3s ease}
.news-tile.open .t-body{grid-template-rows:1fr}
.news-tile .t-body>div{overflow:hidden;display:flex;flex-direction:column;gap:8px;min-height:0}
.news-tile .t-body>div>:first-child{margin-top:4px}
.news-tile .t-more{align-self:flex-start;margin-bottom:2px;font-family:var(--f-mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--c);text-decoration:none}
.news-tile .t-more:hover{text-decoration:underline}
@media (prefers-reduced-motion:reduce){.news-tile .t-body,.news-tile .t-tog i{transition:none}}
@media (max-width:759px){.news-tile:nth-child(n+26){display:none}}
.news-tile .t-src{margin:0;color:#8c93ad;font-size:12.5px}
@media (min-width:640px){.news-tile.lead{grid-column:span 2}.news-tile.lead .t-head{font-size:32px}.news-tile.lead .t-sum{font-size:17px}}
@media (max-width:560px){.news-grid{grid-template-columns:1fr;gap:10px;padding:12px}.news-tile .t-head{font-size:20px}}
</style>'''

# ---------- Guides (evergreen articles, Nov 21, 2026): tools/guides.json + tools/<fragment> ----------
try:
    guides = sorted(json.loads((root/'tools'/'guides.json').read_text()), key=lambda g: g['published'], reverse=True)
except Exception:
    guides = []
guide_css = """<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@400;500;600&display=swap">
<style>
.guides{margin-top:clamp(22px,3vw,34px)}
.guides h2{font-family:var(--f-display);font-weight:800;font-stretch:80%;text-transform:uppercase;font-size:clamp(26px,3vw,36px);color:#fff;margin:0 0 18px}
.guides ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.guides li a{display:block;height:100%;border-radius:12px;padding:16px 18px;text-decoration:none;color:#fff;background:linear-gradient(160deg,rgba(233,196,106,.16),rgba(255,255,255,.03));box-shadow:inset 0 0 0 1px rgba(233,196,106,.45)}
.guides li a:hover{box-shadow:inset 0 0 0 1px rgba(233,196,106,.9)}
.guides li .g{display:block;font-family:var(--f-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--foil);margin-bottom:6px}
.guides li b{font-family:var(--f-display);font-weight:700;font-stretch:88%;font-size:20px;line-height:1.15}
.guide .body h2{font-family:var(--f-display);font-weight:800;font-stretch:88%;font-size:clamp(24px,2.6vw,32px);color:var(--foil);margin:34px 0 12px;line-height:1.1}
.guide .body h3{font-family:var(--f-display);font-weight:700;font-size:21px;color:#fff;margin:24px 0 8px}
.guide .body strong{color:#fff}
.guide-fig{margin:22px 0;max-width:100%}.guide-fig svg{display:block;width:100%;height:auto;border-radius:16px;box-shadow:0 0 0 1px rgba(124,243,255,.25),0 18px 40px rgba(0,0,0,.4)}
.guide-hero{margin:0 0 26px}
.guide-table{overflow-x:auto;margin:6px 0 18px;border-radius:12px;box-shadow:inset 0 0 0 1px rgba(124,243,255,.28);background:linear-gradient(160deg,rgba(255,255,255,.07),rgba(255,255,255,.02))}
.guide-table table{width:100%;border-collapse:collapse;font-size:15px}
.guide-table th{font-family:var(--f-mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#7cf3ff;text-align:left;padding:10px 14px}
.guide-table td{color:#fff;padding:9px 14px;border-top:1px solid rgba(255,255,255,.08)}
.guide .story-card{grid-template-columns:minmax(0,1fr)}.guide .body{max-width:72ch}
.story.guide .body{max-width:920px}
.story.guide .body>p,.story.guide .body>h2,.story.guide .body>h3{max-width:68ch}
.guide-products{list-style:none;margin:18px 0 22px;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px}
.guide-products.six{grid-template-columns:repeat(auto-fill,minmax(130px,1fr))}
.guide-products.two{grid-template-columns:repeat(auto-fill,minmax(220px,280px))}
.guide-products li{display:flex;flex-direction:column;gap:4px;border-radius:14px;padding:10px 10px 14px;background:linear-gradient(160deg,rgba(255,255,255,.08),rgba(255,255,255,.02));box-shadow:inset 0 0 0 1px rgba(124,243,255,.22)}
.guide-products figure{margin:0 0 6px;aspect-ratio:1/1;display:grid;place-items:center;border-radius:10px;background:radial-gradient(circle at 50% 45%,rgba(124,243,255,.12),transparent 70%)}
.guide-products img{width:100%;height:auto;display:block;filter:drop-shadow(0 10px 18px rgba(0,0,0,.5))}
.guide-products b{font-family:var(--f-display);font-weight:700;font-stretch:88%;font-size:17px;line-height:1.15;color:#fff}
.guide-products span{font-size:13px;line-height:1.4;color:#c9cfe4}
.guide-leaders{display:flex;flex-wrap:wrap;gap:18px;margin:16px 0 24px}
.guide-leaders figure{margin:0;flex:1 1 200px;max-width:260px}
.guide-leaders img{width:100%;height:auto;display:block;border-radius:12px;box-shadow:0 0 0 1px rgba(233,196,106,.6),0 18px 36px rgba(0,0,0,.5)}
.guide-leaders figcaption,.guide-photo figcaption{margin-top:8px;font-size:13px;color:#c9cfe4}
.guide-photo{margin:14px 0 18px;max-width:560px}.guide-photo img{width:100%;height:auto;display:block;border-radius:14px;background:radial-gradient(circle at 50% 40%,rgba(124,243,255,.14),rgba(255,255,255,.02) 70%)}
.guide-credit{font-size:12.5px;color:#8c93ad;margin-top:26px;max-width:68ch}
.story.guide .body>p.guide-credit{font-size:12.5px;line-height:1.5;color:#8c93ad}
/* Guides typography = Magazine Article sample B, with the newsletter's heading font DM Serif Display
   (user, Nov 22, 2026: "Use B for Guides, use the heading from the Newsletter ... just the fonts and writing
   style, don't change the backdrop designs"). Fonts and text only; backgrounds, cards and colours of the
   boxes are unchanged. */
.story.guide .story-kicker{font-family:Inter,system-ui,sans-serif;font-weight:600;font-size:11.5px;letter-spacing:.2em}
.story.guide h1{font-family:"DM Serif Display",Georgia,serif;font-weight:400;font-stretch:normal;font-size:clamp(34px,5vw,58px);line-height:1.06;letter-spacing:-.01em}
.story.guide .lead{font-family:"DM Serif Display",Georgia,serif;font-style:italic;font-size:clamp(19px,1.9vw,23px);line-height:1.45}
.story.guide .body{font-family:Inter,system-ui,sans-serif}
.story.guide .body>p{font-size:17px;line-height:1.8}
.story.guide .body>p:first-of-type::first-letter{font-family:"DM Serif Display",Georgia,serif;float:left;font-size:64px;line-height:.86;margin:6px 10px 0 0;color:#ffd23f}
.story.guide .body h2{font-family:"DM Serif Display",Georgia,serif;font-weight:400;font-stretch:normal;font-size:clamp(26px,2.8vw,32px);letter-spacing:-.005em;line-height:1.15}
.story.guide .body h3{font-family:"DM Serif Display",Georgia,serif;font-weight:400;font-size:23px;line-height:1.2}
.story.guide .body li{font-size:16.5px;line-height:1.7}
.story.guide .body blockquote{border-left:3px solid #ffd23f;margin:1.6em 0;padding:2px 0 2px 20px;font-family:"DM Serif Display",Georgia,serif;font-style:italic;font-size:21px;line-height:1.5}
.story.guide .guide-products b,.story.guide .more h2{font-family:"DM Serif Display",Georgia,serif;font-weight:400;font-stretch:normal}
.story.guide .guide-table table{font-family:Inter,system-ui,sans-serif}
.story.guide .src{font-family:Inter,system-ui,sans-serif;font-style:italic}
</style>"""
extra_css = extra_css + '\n' + guide_css
guides_strip = ''   # guides moved to their own page, guides.html (nav button "Guides", Nov 22, 2026)
header = header + '\n\n' + site_parts.navbar(src, 'news.html')
footer = site_parts.newsletter_section(src) + '\n' + footer + '\n\n' + site_parts.newsletter_script(src)
body = f'''{header}

<main>
  <section class="wrap news" aria-labelledby="news-h">
    <div class="sheet-head">
      <div class="sheet-title">
  <h2 id="news-h">News Headlines</h2>
  <p>All the latest trading card game news, newest first. Pick a game, tap a headline for the summary and source, then read the full story.</p>
      </div>
      <div class="chips" role="group" aria-label="Filter by game">{"".join(chips)}</div>
    </div>
    <div class="gd">
      <div class="mw-top">
        <span class="mono mw-label" style="color:#ffd23f"><i style="background:#ffd23f;box-shadow:0 0 10px #ffd23f"></i><span>Headlines</span></span>
        <span class="mono news-count" id="newsCount">{len(shown)} stories</span>
        <span class="mono mw-upd" id="newsRange">{first.strftime('%b')} {first.day} – {last.strftime('%b')} {last.day}, {last.year}</span>
      </div>
      <ol class="news-grid" id="newsGrid">
{chr(10).join(tiles)}
      </ol>
    </div>
  </section>
  {guides_strip}
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
  /* tap a box to open its story, tap again to close (Nov 16) */
  document.querySelectorAll('.news-tile').forEach(t=>{const b=t.querySelector('.t-tog');if(!b)return;
    const flip=()=>{const o=!t.classList.contains('open');t.classList.toggle('open',o);b.setAttribute('aria-expanded',String(o))};
    t.addEventListener('click',ev=>{if(ev.target.closest('a'))return;flip()})});
  /* game filter */
  const chips=[...document.querySelectorAll('.chip')],tiles=[...document.querySelectorAll('.news-tile')],cnt=document.getElementById('newsCount');
  chips.forEach(c=>c.addEventListener('click',()=>{chips.forEach(x=>x.setAttribute('aria-pressed',String(x===c)));const g=c.dataset.g;let n=0;
    tiles.forEach(t=>{const ok=g==='all'||t.dataset.game===g;t.hidden=!ok});count()}));
  /* count and date range of the boxes actually showing (35 on desktop, 25 on phones) */
  const rng=document.getElementById('newsRange'),M=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  function count(){if(!cnt)return;const v=tiles.filter(t=>t.offsetParent);cnt.textContent=v.length+(v.length===1?' story':' stories');
    const d=v.map(t=>t.querySelector('time').getAttribute('datetime').slice(0,10)).sort();if(rng&&d.length){const a=d[0].split('-'),b=d[d.length-1].split('-');
      rng.textContent=M[+a[1]-1]+' '+(+a[2])+' – '+M[+b[1]-1]+' '+(+b[2])+', '+b[0]}}
  count();addEventListener('resize',count);
__COVER__})();
</script>'''.replace('__COVER__', cover_js)

out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + head + style + '\n' + extra_css + '\n</head>\n<body>\n' + body + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
(root/'news.html').write_text(out)
print('news.html', len(out), 'bytes,', len(news), 'stories')
# ---------- one page per story (Nov 3, 2026): news-YYYY-MM-DD-<slug>.html ----------
SITE = 'https://1cardz.news/'
try:
    posts = {p['when']: p for p in json.loads((root/'tools'/'posts.json').read_text())}
except Exception:
    posts = {}
def iso(w):
    return w + ':00+08:00'
story_css = """<style>
/* story page */
.story .crumbs{font-family:var(--f-mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#8c93ad;margin:0 0 14px}
.story .crumbs a{color:#c9cfe4;text-decoration:none}.story .crumbs a:hover{color:#fff}
.story-card{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,300px);gap:clamp(18px,3vw,40px);align-items:start;padding:clamp(18px,3vw,36px);position:relative;z-index:4}
.story-card.noclip{grid-template-columns:minmax(0,1fr)}
.story-kicker{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;font-family:var(--f-mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#8c93ad;margin:0 0 12px}
.story-kicker .mw-game{background:var(--c);color:#12162b}
.story h1{font-family:var(--f-display);font-weight:800;font-stretch:80%;font-size:clamp(32px,4.6vw,58px);line-height:1;color:#fff;margin:0 0 30px;text-wrap:balance}
.story .lead{font-size:clamp(17px,1.7vw,21px);line-height:1.55;color:#dfe3f2;margin:0 0 14px;max-width:62ch}
.story .quip{font-style:italic;color:#c9cfe4;margin:0 0 14px}
.story .src{color:#8c93ad;font-size:14px;margin:0 0 18px}
.story .details{margin:4px 0 20px;max-width:62ch;padding:16px 18px;border-radius:12px;background:linear-gradient(160deg,rgba(255,255,255,.07),rgba(255,255,255,.02));box-shadow:inset 0 0 0 1px rgba(124,243,255,.28)}
.story .details h2{font-family:var(--f-mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#7cf3ff;margin:0 0 10px;font-weight:700}
.story .details ul{margin:0 0 12px;padding-left:20px;color:#dfe3f2;line-height:1.55;font-size:16px}
.story .details li{margin:0 0 6px}
.story .details .why{margin:0;color:#ffd23f;font-size:15px;line-height:1.5}
.story .details .why b{color:#fff}
.story .src a{color:#7cf3ff}
.story .actions{display:flex;flex-wrap:wrap;gap:10px}
.story .body{max-width:62ch;margin:0 0 18px}
.story .body p{font-size:17px;line-height:1.65;color:#dfe3f2;margin:0 0 14px}
.story .specs{width:100%;max-width:62ch;border-collapse:collapse;margin:4px 0 20px;font-size:15px;border-radius:12px;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(124,243,255,.28);background:linear-gradient(160deg,rgba(255,255,255,.07),rgba(255,255,255,.02))}
.story .specs caption{caption-side:top;text-align:left;font-family:var(--f-mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#7cf3ff;font-weight:700;padding:0 0 8px}
.story .specs th,.story .specs td{text-align:left;padding:10px 14px;border-top:1px solid rgba(255,255,255,.08);vertical-align:top}
.story .specs tr:first-child th,.story .specs tr:first-child td{border-top:0}
.story .specs th{width:38%;font-family:var(--f-mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#8c93ad;font-weight:500}
.story .specs td{color:#fff}
.story-media{align-self:start;position:sticky;top:20px}
.story-media-m{display:none;margin:0 0 22px}
.story-video{display:block;border:0;width:100%;aspect-ratio:9/16;border-radius:14px;background:#05040b;box-shadow:0 0 0 1px rgba(124,243,255,.5),0 0 22px rgba(124,243,255,.25),0 18px 40px rgba(0,0,0,.45);object-fit:cover}
.more{margin-top:clamp(22px,3vw,34px)}
.more h2{font-family:var(--f-display);font-weight:800;font-stretch:80%;text-transform:uppercase;font-size:clamp(26px,3vw,36px);color:#fff;margin:0 0 30px}
.more ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.more li a{display:block;height:100%;border-radius:12px;padding:14px 16px;text-decoration:none;color:#fff;background:linear-gradient(160deg,rgba(255,255,255,.09),rgba(255,255,255,.025));box-shadow:inset 0 0 0 1px rgba(255,255,255,.13)}
.more li a:hover{box-shadow:inset 0 0 0 1px rgba(255,255,255,.3)}
.more li .g{display:block;font-family:var(--f-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#8c93ad;margin-bottom:6px}
.more li b{font-family:var(--f-display);font-weight:700;font-stretch:88%;font-size:19px;line-height:1.15}
@media (max-width:760px){.story-card{grid-template-columns:minmax(0,1fr)}.story-media{display:none}.story-media-m{display:block}.story-video{max-width:300px;margin:0 auto}}
</style>"""
s_header = header.replace('<h1 class="foil">', '<div class="foil h1x">', 1)
s_header = re.sub(r'(<div class="foil h1x">.*?)</h1>', r'\1</div>', s_header, count=1, flags=re.S)
def seo_title(t):
    """<title>: keep the brand suffix only when the whole thing fits Google's ~65 characters (audit, Nov 22)."""
    return f'{t} | 1Cardz.news' if len(t) <= 50 else t

def meta_desc(d, limit=160):
    """Meta description: at most ~160 characters, cut at a sentence end, else at a word, with an ellipsis."""
    d = ' '.join(d.split())
    if len(d) <= limit:
        return d
    cut = d[:limit]
    ends = [m.end() for m in re.finditer(r'[.!?](?=\s)', cut)]
    if ends and ends[-1] >= 70:
        return cut[:ends[-1]]
    return cut[:cut.rstrip().rfind(' ')].rstrip(',;:') + '…'

made = []
for k, (n, p) in enumerate(site_parts.story_items(news, list(posts.values()))):
    url = story_url(n)
    title = n['title']; desc = n['summary']; mdesc = meta_desc(desc)
    img = SITE + f"img/{p['clip']}.jpg" if p else SITE + 'img/og-1cardz.jpg'
    c = GC.get(n['game'], '#7cf3ff')
    more = [m for m in news if m is not n][:6]
    more_html = ''.join(f'<li><a href="{story_url(m)}"><span class="g">{e(m["game"])} · {when(m["when"])}</span><b>{e(m["title"])}</b></a></li>' for m in more)
    clip_html = ''
    yt = (p or {}).get('yt')
    if p and yt:      # Nov 16: the YouTube Short itself, so Google visitors add YouTube views
        clip_html = (f'<iframe class="story-video" src="https://www.youtube-nocookie.com/embed/{e(yt)}?rel=0&amp;playsinline=1" loading="lazy" '
                     f'title="YouTube Short: {e(title)}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
                     f'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>')
    elif p:
        clip_html = (f'<video class="story-video" controls playsinline preload="none" poster="img/{p["clip"]}.jpg" src="img/{p["clip"]}.mp4" '
                     f'aria-label="News clip with {e(p["host"])}: {e(title)}"></video>')
    host = f' · With {e(p["host"])}' if p else ''
    d = n.get('details') or {}
    details_html = ''
    if d.get('facts') or d.get('why'):
        lis = ''.join(f'<li>{e(f)}</li>' for f in d.get('facts', []))
        why = f'<p class="why"><b>Why it matters:</b> {e(d["why"])}</p>' if d.get('why') else ''
        details_html = f'<section class="details" aria-label="The details"><h2>The details</h2>{"<ul>"+lis+"</ul>" if lis else ""}{why}</section>'
    art = [t for t in (n.get('article') or []) if str(t).strip()]
    art_html = ''.join(f'<p>{e(t)}</p>' for t in art)
    if art:
        art_html = f'<div class="body">{art_html}</div>'
        # Nov 22, 2026 (user): every story page keeps the "The details" box (facts + why it matters), article or not
    specs = [r for r in (n.get('specs') or []) if isinstance(r, (list, tuple)) and len(r) == 2]
    specs_html = ''
    if specs:
        specs_html = ('<table class="specs"><caption>At a glance</caption><tbody>' +
                      ''.join(f'<tr><th scope="row">{e(a)}</th><td>{e(b)}</td></tr>' for a, b in specs) + '</tbody></table>')
    links = [u for u in (n.get('links') or []) if str(u).startswith('https://')]
    # No external links on the site (user rule, Nov 16, 2026): the source is named in plain text.
    # details.url and "links" are kept in news.json only as an internal record.
    src_html = e(n['source'])
    article = f"""
<main>
  <section class="wrap story">
    <p class="crumbs"><a href="index.html">Home</a> › <a href="news.html">Headlines</a> › {e(n['game'])}</p>
    <article class="gd" style="--c:{c}">
      <div class="story-card{'' if p else ' noclip'}">
        <div>
          <p class="story-kicker"><span class="mw-game">{e(n['game'])}</span><time datetime="{iso(n['when'])}">{when(n['when'])}</time>{host}</p>
          <h1>{e(title)}</h1>
          {f'<div class="story-media-m">{clip_html}</div>' if clip_html else ''}
          <p class="lead">{e(desc)}</p>
          {art_html}
          {specs_html}
          {f'<p class="quip">{e(p.get("quip",""))}</p>' if p and p.get('quip') else ''}
          {details_html}
          <p class="src">Source: {src_html}</p>
          <div class="actions"><a class="btn" href="news.html">All headlines</a>{'<a class="btn ghost" href="archive.html">Watch more clips</a>' if p else ''}</div>
        </div>
        {f'<div class="story-media">{clip_html}</div>' if clip_html else ''}
      </div>
    </article>
    <div class="more">
      <h2>More headlines</h2>
      <ul>{more_html}</ul>
    </div>
  </section>
</main>
"""
    ld = {'@context': 'https://schema.org', '@type': 'NewsArticle', 'headline': title[:110], 'description': desc,
          'datePublished': iso(n['when']), 'dateModified': iso(n['when']), 'image': [img], 'url': SITE + url,
          'mainEntityOfPage': SITE + url, 'articleSection': n['game'],
          'author': {'@type': 'Organization', 'name': '1Cardz.news', 'url': SITE},
          'publisher': {'@type': 'NewsMediaOrganization', 'name': '1Cardz.news', 'url': SITE,
                        'logo': {'@type': 'ImageObject', 'url': SITE + 'img/icon-512.png', 'width': 512, 'height': 512}}}
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE},
        {'@type': 'ListItem', 'position': 2, 'name': 'Headlines', 'item': SITE + 'news.html'},
        {'@type': 'ListItem', 'position': 3, 'name': title, 'item': SITE + url}]}
    if art:
        ld['articleBody'] = ' '.join(art); ld['wordCount'] = sum(len(t.split()) for t in art)
    if p:
        ld['video'] = {'@type': 'VideoObject', 'name': title, 'description': p.get('blurb') or desc, 'thumbnailUrl': img,
                       'uploadDate': iso(n['when']), 'contentUrl': SITE + f"img/{p['clip']}.mp4",
                       'embedUrl': f"https://www.youtube.com/embed/{p['yt']}" if p.get('yt') else SITE + url}
        if p.get('yt'):
            ld['video']['url'] = f"https://www.youtube.com/shorts/{p['yt']}"
    q = lambda t: html.escape(t, quote=True)
    seo = '\n'.join([
        '<!--seo-->',
        '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">',
        '<meta name="theme-color" content="#0b1030">',
        '<link rel="icon" type="image/png" sizes="32x32" href="img/favicon-32.png">',
        '<link rel="icon" type="image/png" sizes="192x192" href="img/icon-192.png">',
        '<link rel="apple-touch-icon" href="img/apple-touch-icon.png">',
        '<meta property="og:type" content="article">', '<meta property="og:site_name" content="1Cardz.news">',
        f'<meta property="og:title" content="{q(title)}">', f'<meta property="og:description" content="{q(mdesc)}">',
        f'<meta property="og:url" content="{SITE + url}">', f'<meta property="og:image" content="{img}">',
        f'<meta property="article:published_time" content="{iso(n["when"])}">', f'<meta property="article:section" content="{q(n["game"])}">',
        '<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:title" content="{q(title)}">',
        f'<meta name="twitter:description" content="{q(mdesc)}">', f'<meta name="twitter:image" content="{img}">',
        '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>',
        '<script type="application/ld+json">' + json.dumps(crumbs, ensure_ascii=False).replace('</', '<\\/') + '</script>',
        '<!--/seo-->'])
    shead = re.sub(r'<title>.*?</title>', lambda m: f'<title>{q(seo_title(title))}</title>', head)
    shead = shead.replace('href="https://1cardz.news/news.html"', f'href="{SITE + url}"')
    shead = re.sub(r'<meta name="description"[^>]*>', lambda m: f'<meta name="description" content="{q(mdesc)}">', shead)
    page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + shead + style + '\n' + extra_css + '\n' + story_css + '\n' + seo + '\n</head>\n<body>\n'
            + s_header + '\n' + article + '\n' + footer + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
    (root/url).write_text(page); made.append(url)
print(len(made), 'story pages')
# stage new story pages so the daily run's "git commit -am" includes them
if (root/'.git').exists() and made:
    try:
        import subprocess
        subprocess.run(['git', 'add', '--'] + made, cwd=root, timeout=60)
    except Exception as _e:
        print('git add skipped:', _e)

# ---------- one page per guide (Nov 21, 2026) + the Guides page, guides.html (Nov 22, 2026) ----------
g_made = []
_ni = '<p>News Headlines. Every story from the 8 AM and 8 PM drops, newest first, in plain text.</p>'
_gi = '<p>Your first deck, your next box, the card you dream about: plain-English guides, kept current as each new set lands.</p>'
g_header = s_header.replace(site_parts.navbar(src, 'news.html'), site_parts.navbar(src, 'guides.html')).replace(_ni, _gi)
for g in guides:
    frag_p = root/'tools'/g['fragment']
    if not frag_p.exists():
        continue
    url = g['slug']; title = g['title']; desc = g.get('description') or g['summary']; mdesc = meta_desc(desc)
    img = SITE + g['image'] if g.get('image') else SITE + 'img/og-1cardz.jpg'
    c = GC.get(g['game'], '#7cf3ff')
    upd = datetime.datetime.fromisoformat(g['updated'])
    more_html = ''.join(f'<li><a href="{story_url(m)}"><span class="g">{e(m["game"])} · {when(m["when"])}</span><b>{e(m["title"])}</b></a></li>'
                        for m in [m for m in news if m['game'] == g['game']][:6] or news[:6])
    article = f"""
<main>
  <section class="wrap story guide">
    <p class="crumbs"><a href="index.html">Home</a> › <a href="guides.html">Guides</a> › {e(g["game"])}</p>
    <article class="gd" style="--c:{c}">
      <div class="story-card noclip">
        <div>
          <p class="story-kicker"><span class="mw-game">{e(g['game'])}</span><span>Guide</span><time datetime="{iso(g['updated'])}">Updated {upd.strftime('%B')} {upd.day}, {upd.year}</time></p>
          <h1>{e(title)}</h1>
          <p class="lead">{e(g['summary'])}</p>
          <div class="body">{frag_p.read_text()}</div>
          <p class="src">Source: {e(g['source'])}</p>
          <div class="actions"><a class="btn" href="guides.html">All guides</a><a class="btn ghost" href="news.html">Latest headlines</a></div>
        </div>
      </div>
    </article>
    <div class="more">
      <h2>More {e(g['game'])} news</h2>
      <ul>{more_html}</ul>
    </div>
  </section>
</main>
"""
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': title[:110], 'description': desc,
          'datePublished': iso(g['published']), 'dateModified': iso(g['updated']), 'image': [img], 'url': SITE + url,
          'mainEntityOfPage': SITE + url, 'articleSection': g['game'],
          'author': {'@type': 'Organization', 'name': '1Cardz.news', 'url': SITE},
          'publisher': {'@type': 'NewsMediaOrganization', 'name': '1Cardz.news', 'url': SITE,
                        'logo': {'@type': 'ImageObject', 'url': SITE + 'img/icon-512.png', 'width': 512, 'height': 512}}}
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE},
        {'@type': 'ListItem', 'position': 2, 'name': 'Guides', 'item': SITE + 'guides.html'},
        {'@type': 'ListItem', 'position': 3, 'name': title, 'item': SITE + url}]}
    q = lambda t: html.escape(t, quote=True)
    seo = '\n'.join([
        '<!--seo-->',
        '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">',
        '<meta name="theme-color" content="#0b1030">',
        '<link rel="icon" type="image/png" sizes="32x32" href="img/favicon-32.png">',
        '<link rel="icon" type="image/png" sizes="192x192" href="img/icon-192.png">',
        '<link rel="apple-touch-icon" href="img/apple-touch-icon.png">',
        '<meta property="og:type" content="article">', '<meta property="og:site_name" content="1Cardz.news">',
        f'<meta property="og:title" content="{q(title)}">', f'<meta property="og:description" content="{q(mdesc)}">',
        f'<meta property="og:url" content="{SITE + url}">', f'<meta property="og:image" content="{img}">',
        f'<meta property="article:published_time" content="{iso(g["published"])}">', f'<meta property="article:modified_time" content="{iso(g["updated"])}">',
        f'<meta property="article:section" content="{q(g["game"])}">',
        '<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:title" content="{q(title)}">',
        f'<meta name="twitter:description" content="{q(mdesc)}">', f'<meta name="twitter:image" content="{img}">',
        '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>',
        '<script type="application/ld+json">' + json.dumps(crumbs, ensure_ascii=False).replace('</', '<\\/') + '</script>',
        '<!--/seo-->'])
    shead = re.sub(r'<title>.*?</title>', lambda m: f'<title>{q(seo_title(g.get("seo_title") or title))}</title>', head)
    shead = shead.replace('href="https://1cardz.news/news.html"', f'href="{SITE + url}"')
    shead = re.sub(r'<meta name="description"[^>]*>', lambda m: f'<meta name="description" content="{q(mdesc)}">', shead)
    page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + shead + style + '\n' + extra_css + '\n' + story_css + '\n' + seo + '\n</head>\n<body>\n'
            + g_header + '\n' + article + '\n' + footer + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
    (root/url).write_text(page); g_made.append(url)
# the Guides page (guides.html): every guide, newest first
def _gd(g):
    d = datetime.datetime.fromisoformat(g['updated'])
    return f"{d.strftime('%b')} {d.day}, {d.year}"
cards = '\n'.join(
    f'<li><a href="{e(g["slug"])}">'
    + (f'<img src="{e(g["image"])}" alt="" loading="lazy" width="1200" height="520">' if g.get('image') else '')
    + f'<span class="g">{e(g["game"])} · Guide · Updated {_gd(g)}</span><b>{e(g["title"])}</b>'
    + f'<span class="s">{e(g["summary"])}</span><span class="r">Read the guide ›</span></a></li>'
    for g in guides)
gi_css = """<style>
.guides-grid{list-style:none;margin:0;padding:clamp(14px,2vw,22px);display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;position:relative;z-index:4}
.guides-grid a{display:flex;flex-direction:column;gap:8px;height:100%;border-radius:14px;padding:0 0 16px;overflow:hidden;text-decoration:none;color:#fff;background:linear-gradient(160deg,rgba(233,196,106,.14),rgba(255,255,255,.03));box-shadow:inset 0 0 0 1px rgba(233,196,106,.45),0 14px 30px rgba(0,0,0,.3);transition:transform .2s,box-shadow .2s}
.guides-grid a:hover{transform:translateY(-3px);box-shadow:inset 0 0 0 1px rgba(233,196,106,.9),0 20px 38px rgba(0,0,0,.42)}
.guides-grid img{display:block;width:100%;height:auto;aspect-ratio:1200/520;object-fit:cover}
.guides-grid .g,.guides-grid b,.guides-grid .s,.guides-grid .r{padding:0 16px}
.guides-grid .g{font-family:var(--f-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--foil);margin-top:6px}
.guides-grid b{font-family:var(--f-display);font-weight:700;font-stretch:88%;font-size:24px;line-height:1.1}
.guides-grid .s{color:#cfd4e6;font-size:15px;line-height:1.5}
.guides-grid .r{margin-top:auto;font-family:var(--f-mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--foil)}
/* Guides typography (Nov 22, 2026): DM Serif Display titles, Inter text */
@media (max-width:560px){.sheet-title .gx{display:none}}
.guides-grid b{font-family:"DM Serif Display",Georgia,serif;font-weight:400;font-stretch:normal;font-size:25px;line-height:1.12}
.guides-grid .s{font-family:Inter,system-ui,sans-serif}
</style>"""
gi_head = re.sub(r'<title>.*?</title>', '<title>TCG Guides | 1Cardz.news</title>', head)
gi_head = gi_head.replace('href="https://1cardz.news/news.html"', 'href="https://1cardz.news/guides.html"')
gi_head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="Starter decks, record sales and the cards everyone asks about, explained in plain English and updated as new sets land.">', gi_head)
gi_header = header.replace(site_parts.navbar(src, 'news.html'), site_parts.navbar(src, 'guides.html')).replace(_ni, _gi)
gi_body = f"""{gi_header}

<main>
  <section class="wrap news" aria-labelledby="guides-h">
    <div class="sheet-head">
      <div class="sheet-title">
  <h2 id="guides-h">Guides</h2>
  <p>Where to start, what to buy and which cards matter in every game<span class="gx">: starter decks, record sales and the cards everyone asks about</span>. Checked against official sources, kept up to date.</p>
      </div>
    </div>
    <div class="gd">
      <div class="mw-top">
        <span class="mono mw-label" style="color:#e9c46a"><i style="background:#e9c46a;box-shadow:0 0 10px #e9c46a"></i><span>Guides</span></span>
        <span class="mono news-count">{len(guides)} guide{'' if len(guides) == 1 else 's'}</span>
      </div>
      <ol class="guides-grid">
{cards}
      </ol>
    </div>
  </section>
</main>

{footer}
"""
gi_page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
           + gi_head + style + '\n' + extra_css + '\n' + gi_css + '\n</head>\n<body>\n' + gi_body + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
(root/'guides.html').write_text(gi_page); g_made.append('guides.html')
print(len(g_made), 'guide pages (incl. guides.html)')
if (root/'.git').exists() and g_made:
    try:
        import subprocess
        subprocess.run(['git', 'add', '--'] + g_made, cwd=root, timeout=60)
    except Exception as _e:
        print('git add skipped:', _e)

# 404 page: GitHub Pages serves 404.html for any missing URL (audit, Nov 22)
nf_head = re.sub(r'<title>.*?</title>', '<title>Page not found | 1Cardz.news</title>', head)
nf_head = re.sub(r'<link rel="canonical"[^>]*>\n?', '', nf_head)
nf_head = re.sub(r'<meta name="robots"[^>]*>', '', nf_head)
nf_head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="This page could not be found on 1Cardz.news.">', nf_head)
nf_head = '<base href="/">\n<meta name="robots" content="noindex">\n' + nf_head
nf_header = header.replace(site_parts.navbar(src, 'news.html'), site_parts.navbar(src, ''))
nf_body = f"""{nf_header}

<main>
  <section class="wrap news" aria-labelledby="nf-h">
    <div class="sheet-head">
      <div class="sheet-title">
  <h2 id="nf-h">Card not found</h2>
  <p>This page isn't in the binder. It may have moved, or the link has a typo.</p>
      </div>
    </div>
    <div class="actions" style="display:flex;flex-wrap:wrap;gap:12px;margin:8px 0 40px">
      <a class="btn" href="index.html">Go to the homepage</a>
      <a class="btn ghost" href="news.html">Latest headlines</a>
      <a class="btn ghost" href="guides.html">Guides</a>
    </div>
  </section>
</main>

{footer}
"""
(root/'404.html').write_text('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    + nf_head + style + '\n' + extra_css + '\n' + story_css + '\n</head>\n<body>\n' + nf_body + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')

# SEO pass (titles, share previews, structured data, sitemap.xml, robots.txt); safe to repeat
try:
    import subprocess
    subprocess.run([sys.executable, str(root/'tools'/'seo.py')], timeout=120)
except Exception as _e:
    print('seo skipped:', _e)
