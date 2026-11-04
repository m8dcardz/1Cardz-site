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

tiles = []
for k, n in enumerate(news):
    tiles.append(f'''        <li class="news-tile{' lead' if k == 0 else ''}" data-game="{e(n['game'])}" style="--c:{GC.get(n['game'], '#7cf3ff')}">
          <div class="t-top"><span class="mw-game">{e(n['game'])}</span><time class="t-when" datetime="{e(n['when'])}:00+08:00">{when(n['when'])}</time></div>
          <h3 class="t-head"><a href="{story_url(n)}">{e(n['title'])}</a></h3>
          <p class="t-sum">{e(n['summary'])}</p>
          <p class="t-src">Source: {e(n['source'])}</p>
        </li>''')
games = sorted({n['game'] for n in news})
chips = ['<button type="button" class="chip" data-g="all" aria-pressed="true">All games</button>']
chips += [f'<button type="button" class="chip" data-g="{e(g)}" aria-pressed="false">{e(g)}</button>' for g in games]
first = datetime.datetime.fromisoformat(news[-1]['when']); last = datetime.datetime.fromisoformat(news[0]['when'])

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
      <div class="sheet-title">
  <h2 id="news-h">News Headlines</h2>
  <p>Every story from the 8 AM and 8 PM drops, newest first. Text only, with the source for each one.</p>
      </div>
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
.story-card{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,300px);gap:clamp(18px,3vw,40px);align-items:center;padding:clamp(18px,3vw,36px);position:relative;z-index:4}
.story-card.noclip{grid-template-columns:minmax(0,1fr)}
.story-kicker{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;font-family:var(--f-mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#8c93ad;margin:0 0 12px}
.story-kicker .mw-game{background:var(--c);color:#12162b}
.story h1{font-family:var(--f-display);font-weight:800;font-stretch:80%;font-size:clamp(32px,4.6vw,58px);line-height:1;color:#fff;margin:0 0 30px;text-wrap:balance}
.story .lead{font-size:clamp(17px,1.7vw,21px);line-height:1.55;color:#dfe3f2;margin:0 0 14px;max-width:62ch}
.story .quip{font-style:italic;color:#c9cfe4;margin:0 0 14px}
.story .src{color:#8c93ad;font-size:14px;margin:0 0 18px}
.story .actions{display:flex;flex-wrap:wrap;gap:10px}
.story-video{width:100%;aspect-ratio:9/16;border-radius:14px;background:#05040b;box-shadow:0 0 0 1px rgba(124,243,255,.5),0 0 22px rgba(124,243,255,.25),0 18px 40px rgba(0,0,0,.45);object-fit:cover}
.more{margin-top:clamp(22px,3vw,34px)}
.more h2{font-family:var(--f-display);font-weight:800;font-stretch:80%;text-transform:uppercase;font-size:clamp(26px,3vw,36px);color:#fff;margin:0 0 30px}
.more ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.more li a{display:block;height:100%;border-radius:12px;padding:14px 16px;text-decoration:none;color:#fff;background:linear-gradient(160deg,rgba(255,255,255,.09),rgba(255,255,255,.025));box-shadow:inset 0 0 0 1px rgba(255,255,255,.13)}
.more li a:hover{box-shadow:inset 0 0 0 1px rgba(255,255,255,.3)}
.more li .g{display:block;font-family:var(--f-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#8c93ad;margin-bottom:6px}
.more li b{font-family:var(--f-display);font-weight:700;font-stretch:88%;font-size:19px;line-height:1.15}
@media (max-width:760px){.story-card{grid-template-columns:minmax(0,1fr)}.story-video{max-width:300px;justify-self:center}}
</style>"""
s_header = header.replace('<h1 class="foil">', '<div class="foil h1x">', 1)
s_header = re.sub(r'(<div class="foil h1x">.*?)</h1>', r'\1</div>', s_header, count=1, flags=re.S)
made = []
for k, n in enumerate(news):
    url = story_url(n); p = posts.get(n['when'])
    title = n['title']; desc = n['summary']
    img = SITE + f"img/{p['clip']}.jpg" if p else SITE + 'img/og-1cardz.jpg'
    c = GC.get(n['game'], '#7cf3ff')
    more = [m for m in news if m is not n][:6]
    more_html = ''.join(f'<li><a href="{story_url(m)}"><span class="g">{e(m["game"])} · {when(m["when"])}</span><b>{e(m["title"])}</b></a></li>' for m in more)
    clip_html = ''
    if p:
        clip_html = (f'<video class="story-video" controls playsinline preload="none" poster="img/{p["clip"]}.jpg" src="img/{p["clip"]}.mp4" '
                     f'aria-label="News clip with {e(p["host"])}: {e(title)}"></video>')
    host = f' · With {e(p["host"])}' if p else ''
    article = f"""
<main>
  <section class="wrap story">
    <p class="crumbs"><a href="index.html">Home</a> › <a href="news.html">Headlines</a> › {e(n['game'])}</p>
    <article class="gd" style="--c:{c}">
      <div class="story-card{'' if p else ' noclip'}">
        <div>
          <p class="story-kicker"><span class="mw-game">{e(n['game'])}</span><time datetime="{iso(n['when'])}">{when(n['when'])}</time>{host}</p>
          <h1>{e(title)}</h1>
          <p class="lead">{e(desc)}</p>
          {f'<p class="quip">{e(p.get("quip",""))}</p>' if p and p.get('quip') else ''}
          <p class="src">Source: {e(n['source'])}</p>
          <div class="actions"><a class="btn" href="news.html">All headlines</a>{'<a class="btn ghost" href="archive.html">Watch more clips</a>' if p else ''}</div>
        </div>
        {clip_html}
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
    if p:
        ld['video'] = {'@type': 'VideoObject', 'name': title, 'description': p.get('blurb') or desc, 'thumbnailUrl': img,
                       'uploadDate': iso(n['when']), 'contentUrl': SITE + f"img/{p['clip']}.mp4", 'embedUrl': SITE + url}
    q = lambda t: html.escape(t, quote=True)
    seo = '\n'.join([
        '<!--seo-->',
        '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">',
        '<meta name="theme-color" content="#0b1030">',
        '<link rel="icon" type="image/png" sizes="32x32" href="img/favicon-32.png">',
        '<link rel="icon" type="image/png" sizes="192x192" href="img/icon-192.png">',
        '<link rel="apple-touch-icon" href="img/apple-touch-icon.png">',
        '<meta property="og:type" content="article">', '<meta property="og:site_name" content="1Cardz.news">',
        f'<meta property="og:title" content="{q(title)}">', f'<meta property="og:description" content="{q(desc)}">',
        f'<meta property="og:url" content="{SITE + url}">', f'<meta property="og:image" content="{img}">',
        f'<meta property="article:published_time" content="{iso(n["when"])}">', f'<meta property="article:section" content="{q(n["game"])}">',
        '<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:title" content="{q(title)}">',
        f'<meta name="twitter:description" content="{q(desc)}">', f'<meta name="twitter:image" content="{img}">',
        '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>',
        '<!--/seo-->'])
    shead = re.sub(r'<title>.*?</title>', lambda m: f'<title>{q(title)} | 1Cardz.news</title>', head)
    shead = shead.replace('href="https://1cardz.news/news.html"', f'href="{SITE + url}"')
    shead = re.sub(r'<meta name="description"[^>]*>', lambda m: f'<meta name="description" content="{q(desc)}">', shead)
    page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + shead + style + '\n' + extra_css + '\n' + story_css + '\n' + seo + '\n</head>\n<body>\n'
            + s_header + '\n\n' + site_parts.navbar(src, 'news.html') + '\n' + article + '\n' + footer + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
    (root/url).write_text(page); made.append(url)
print(len(made), 'story pages')
# stage new story pages so the daily run's "git commit -am" includes them
if (root/'.git').exists() and made:
    try:
        import subprocess
        subprocess.run(['git', 'add', '--'] + made, cwd=root, timeout=60)
    except Exception as _e:
        print('git add skipped:', _e)

# SEO pass (titles, share previews, structured data, sitemap.xml, robots.txt); safe to repeat
try:
    import subprocess
    subprocess.run([sys.executable, str(root/'tools'/'seo.py')], timeout=120)
except Exception as _e:
    print('seo skipped:', _e)
