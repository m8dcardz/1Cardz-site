"""Newsletter page: this week's issue as a magazine (Nov 4, 2026, style C "Classic glossy").
render(iss, root) -> (html, css, js). Reads tools/newsletter_latest.json fields:
  no, date, title, opening, image, cover_clip, cover{main, sub, lines[[title, sub]..]}, pull,
  feature{clip, title, text}, sections[ {h:'The big one', p:[[lead,text,src]]},
  {h:'Top stories this week', li:[[lead,text,src]..], clips:[clipN..]}, {h:'Coming up this week', li:[[date,text,status]..]} ],
  signoff. Missing fields fall back gracefully.
Images: img/nl-cover-<clip>.jpg (cover, crop of the clip above the captions) and img/nl-<clip>.jpg (story photos)
are made with ffmpeg from img/<clip>.mp4 the first time; without ffmpeg the clip posters are used."""
import html, json, shutil, subprocess, pathlib

e = lambda t: html.escape(str(t if t is not None else ''), quote=True)

def _img(root, clip, cover=False):
    if not clip:
        return ''
    out = root / 'img' / (f'nl-cover-{clip}.jpg' if cover else f'nl-{clip}.jpg')
    src = root / 'img' / f'{clip}.mp4'
    if not out.exists() and src.exists() and shutil.which('ffmpeg'):
        vf = 'crop=iw:ih*0.69:0:0' if cover else 'crop=iw:ih*0.64:0:ih*0.05,scale=480:-2'
        try:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '5' if cover else '2.5', '-i', str(src), '-frames:v', '1',
                            '-vf', vf, '-q:v', '4', str(out)], timeout=60)
        except Exception:
            pass
    if out.exists():
        return 'img/' + out.name
    return f'img/{clip}.jpg' if (root / 'img' / f'{clip}.jpg').exists() else ''

def render(iss, root):
    root = pathlib.Path(root)
    secs = {s.get('h', ''): s for s in iss.get('sections', [])}
    big = (secs.get('The big one', {}).get('p') or [['', '', '']])[0]
    top = secs.get('Top stories this week', {})
    tops = top.get('li', []); tclips = top.get('clips', [])
    cal = secs.get('Coming up this week', {}).get('li', [])
    no = iss.get('no', '')
    cv = iss.get('cover', {})
    cover_img = _img(root, iss.get('cover_clip'), cover=True) or iss.get('image', '')
    short = iss.get('date', '').split(', ', 1)[-1] if iss.get('date') else ''

    def game_title(lead):
        g, _, t = lead.partition(': ')
        return (g, t.rstrip('.')) if t else ('', lead.rstrip('.'))

    lines = ''.join(f'<div><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in cv.get('lines', [])[:2])
    cover = f'''<div class="mz-page mz-cover" role="img" aria-label="Magazine cover: {e(cv.get('main') or iss.get('title'))}">
  <div class="ph"><img src="{e(cover_img)}" alt="" loading="lazy"></div>
  <div class="mhd"><div class="mast" aria-label="1Cardz"><span class="sh">1Cardz</span><span class="sv">1Cardz</span><span class="ho" aria-hidden="true">1Cardz</span></div>
  <div class="wm">Weekly Magazine</div></div>
  <div class="vol">Vol.{e(str(iss.get('vol', 1)))}</div>
  <div class="tag">Issue {e(no)} · {e(short)}</div>
  <div class="side">{lines}</div>
  <div class="big"><b>{e(cv.get('main') or iss.get('title'))}</b><span>{e(cv.get('sub', ''))}</span></div>
  <div class="bar"><i></i>1CZ-{e(no)}</div>
</div>'''

    import datetime, re as _re
    try:
        idate = datetime.datetime.strptime(iss.get('date', ''), '%A, %B %d, %Y').date()
    except Exception:
        idate = datetime.date.today()
    wk0 = (idate - datetime.timedelta(days=6)).isoformat(); wk1 = idate.isoformat()
    try:
        posts = [x for x in json.loads((root / 'tools' / 'posts.json').read_text()) if wk0 <= x.get('when', '')[:10] <= wk1]
    except Exception:
        posts = []
    try:
        market = json.loads((root / 'data' / 'market.json').read_text()).get('items', [])
    except Exception:
        market = []

    run = lambda a, b: f'<div class="run"><span>{e(a)}</span><span>{e(b)}</span></div>'
    body = []          # (key, toc title, toc sub, html-without-folio)
    big_t = big[0].rstrip('.')
    strip = (f'<div class="strip"><div><b>{len(posts)}</b><span>clips this week</span></div><div><b>{len({x["game"] for x in posts})}</b><span>games covered</span></div><div><b>2</b><span>drops a day</span></div></div>' if posts else '')
    about = ''.join(f'<div><a href="{h}"><b>{t}</b></a><span>{d}</span></div>' for h, t, d in [
        ('index.html', 'Home', 'The binder: the Shuffle Machine game, the headline box and every host card.'),
        ('news.html', 'Headlines', 'Every story from the daily drops, newest first, each with its own page.'),
        ('market.html', 'Market', 'Daily prices for sealed boxes and chase singles across seven games.'),
        ('archive.html', 'Library', 'Every clip from Zia and Luna, playable right on the page.'),
        ('board.html', 'Message Board', 'The arcade hall of fame: post your pulls and hot takes.'),
        ('newsletter.html', 'Newsletter', 'This magazine, free in your inbox every Sunday.')])
    body.append(('about', 'Inside 1Cardz.news', 'About the site', f"""{run('About the site', 'Issue ' + no)}<p class="kick">Welcome to</p><h3>Inside 1Cardz.news</h3>
<div class="hosts"><img src="img/zia.webp" alt="Zia" loading="lazy"><img src="img/luna.webp" alt="Luna" loading="lazy"><p>Trading card game news in two short clips a day: <b>Zia at 8 AM</b> and <b>Luna at 8 PM</b>, on Instagram, YouTube and TikTok.</p></div>
<div class="about">{about}</div>"""))
    pull = f'<div class="pull">"{e(iss["pull"])}"</div>' if iss.get('pull') else ''
    body.append(('big', big_t, 'Cover story', f"""{run('Cover story', big[2])}<p class="kick">The big one</p><h3>{e(big_t)}</h3>
<p class="first">{e(iss.get('opening', ''))}</p><p>{e(big[1])}</p>{pull}<p class="src">Source: {e(big[2])}</p>""" + (f'<a class="watch" href="archive.html"><img src="{e(_img(root, iss.get("cover_clip")))}" alt="" loading="lazy"><span><b>Watch the report</b>The 1Cardz clip on this story is in the Library. ▶</span></a>' if _img(root, iss.get('cover_clip')) else '')))
    f = iss.get('feature') or {}
    fimg = _img(root, f.get('clip')) or cover_img
    body.append(('feat', f.get('title') or 'Photo feature', 'Feature', f'<img class="bg" src="{e(fimg)}" alt="" loading="lazy"><div class="cap"><span class="kick">Feature</span><b>{e(f.get("title", ""))}</b>{e(f.get("text", ""))}</div>'))
    sp_stories = set()
    for sp in iss.get('spreads', []):
        sp_stories.add(sp.get('story'))
        im = _img(root, sp.get('clip'))
        paras = ''.join(f'<p{" class=first" if k == 0 else ""}>{e(t)}</p>' for k, t in enumerate(sp.get('text', [])))
        pq = f'<div class="pull">"{e(sp["pull"])}"</div>' if sp.get('pull') else ''
        watch = f'<a class="watch" href="archive.html"><img src="{e(im)}" alt="" loading="lazy"><span><b>Watch the report</b>The 1Cardz clip on this story is in the Library. ▶</span></a>' if im else ''
        body.append(('story', sp.get('title', ''), sp.get('kick', 'Feature'), f"""{run(sp.get('kick', 'Feature'), sp.get('src', ''))}<p class="kick">{e(sp.get('kick', ''))}</p><h3>{e(sp.get('title', ''))}</h3>
{paras}{pq}<p class="src">Source: {e(sp.get('src', ''))}</p>{watch}"""))
        if im:
            body.append(('feat', sp.get('photo_title', ''), 'Feature', f'<img class="bg" src="{e(im)}" alt="" loading="lazy"><div class="cap"><span class="kick">{e(sp.get("kick", ""))}</span><b>{e(sp.get("photo_title", ""))}</b>{e(sp.get("photo_text", ""))}</div>'))
    keep = [n for n, t in enumerate(tops) if t[0] not in sp_stories]
    tops = [tops[n] for n in keep]; tclips = [tclips[n] for n in keep if n < len(tclips)]
    per = 2
    npages = (len(tops) + per - 1) // per
    for k in range(0, len(tops), per):
        cards = ''
        for jx, t in enumerate(tops[k:k + per]):
            g, ti = game_title(t[0])
            im = _img(root, tclips[k + jx]) if k + jx < len(tclips) else ''
            cards += (f'<div class="st">' + (f'<img src="{e(im)}" alt="" loading="lazy">' if im else '') +
                      f'<span class="g">{e(g)}</span><b>{e(ti)}</b><p>{e(t[1])}</p><small>Source: {e(t[2])}</small></div>')
        firsts = ' & '.join(game_title(t[0])[1] for t in tops[k:k + per])
        if len(firsts) > 46: firsts = ' · '.join(dict.fromkeys(game_title(t[0])[0] or game_title(t[0])[1] for t in tops[k:k + per]))
        body.append(('top', firsts, 'Top stories', f'{run("Top stories", f"{k // per + 1} of {npages}")}<div class="stories">{cards}</div>'))
    nums = iss.get('numbers') or []
    if posts:
        games = sorted({x['game'] for x in posts})
        nums = nums + [[str(len(posts)), 'news clips from Zia & Luna this week'], [str(len(games)), 'games covered on the channel']]
    if nums:
        body.append(('nums', 'By the numbers', 'The week in stats', f"""{run('By the numbers', short)}<p class="kick">The week in stats</p><h3>By the numbers</h3>
<div class="nums">{''.join(f'<div><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in nums[:8])}</div>"""))
    def chg(it):
        h = [x for x in it.get('history', []) if x[0] <= wk1]
        if len(h) < 2 or not h[0][1]:
            return None
        return h[-1][1], (h[-1][1] - h[0][1]) / h[0][1] * 100
    mv = [(it, chg(it)) for it in market if it.get('price') is not None]
    mv = sorted([x for x in mv if x[1]], key=lambda x: -abs(x[1][1]))[:5]
    if mv:
        rows = ''.join(f'<div><span class="g">{e(it["game"])}</span><b>{e(it["name"])}</b><em>${c[0]:,.2f}</em><i class="{"up" if c[1] > 0 else "down"}">{"▲" if c[1] > 0 else "▼"} {abs(c[1]):.1f}%</i></div>' for it, c in mv)
        body.append(('mkt', 'Market Watch: the movers', 'Prices', f"""{run('Market Watch', 'Week to ' + short)}<p class="kick">Prices</p><h3>The week's movers</h3>
<div class="mv">{rows}</div><p class="note">Recent sold averages in USD, change over the week. Daily prices on the <a href="market.html">Market</a> page.</p>"""))
    q = [x for x in posts if x.get('quip')]
    if q:
        quips = ''.join(f'<blockquote><p>"{e(x["quip"])}"</p><cite>{e(x["host"])} on {e(x["title"])}</cite></blockquote>' for x in q[-6:])
        body.append(('quips', 'Overheard in the studio', 'The best lines', f"""{run('Overheard in the studio', 'The best lines')}<p class="kick">Said on air</p><h3>Overheard in the studio</h3><div class="quips">{quips}</div>"""))
    radar = iss.get('radar') or []
    if radar:
        rr = ''.join(f'<div><b>{e(d_)}</b><span>{e(t_)}</span></div>' for d_, t_ in radar)
        body.append(('radar', 'Release radar', 'Further ahead', f"""{run('Release radar', 'Further ahead')}<p class="kick">Save the dates</p><h3>Release radar</h3><div class="radar">{rr}</div><p class="note">Dates as announced in this issue's stories. Every story is on the <a href="news.html">Headlines</a> page.</p>"""))
    if cal:
        rows = ''.join(f'<div><b>{e(c[0].rstrip(":"))}</b><span>{e(c[1])}<i>{e(c[2])}</i></span></div>' for c in cal)
        body.append(('cal', 'The week ahead', 'Calendar', f"""{run('The week ahead', 'Next 7 days')}<p class="kick">Mark your calendar</p><h3>The week ahead</h3><div class="cal">{rows}</div>"""))
    sign = '<br>'.join(e(x) for x in iss.get('signoff', [])[:2])
    body.append(('back', 'Never miss an issue', 'Back page', f"""<p class="kick">See you next Sunday</p><h3>Never miss an issue</h3>
<p>One free email every Sunday with the week in cards, the market movers and what's coming up. New clips every day at 8 AM (Zia) and 8 PM (Luna).</p>
<div class="links"><a href="archive.html">Watch the clips</a><a href="news.html">All headlines</a></div>
<div class="sign">{sign}</div><p class="small">1Cardz.news · Instagram @1cardz_news · YouTube @1Cardzcom · TikTok @1cardz.com</p>"""))

    # contents (page 2), then the body pages from page 3
    toc = ''; seen_top = False
    tpages = [3 + n for n, b in enumerate(body) if b[0] == 'top']
    games_l = ', '.join(dict.fromkeys(game_title(t[0])[0] for t in tops if game_title(t[0])[0]))
    for n, (key, t, sub, _) in enumerate(body):
        if key in ('feat', 'back'): continue
        if key == 'top':
            if seen_top: continue
            seen_top = True
            t, sub, pg = 'Top stories of the week', f"{len(tops)} stories · {len(games_l.split(', ')) if games_l else 0} games", f'{tpages[0]}–{tpages[-1]}' if len(tpages) > 1 else str(tpages[0])
        else:
            pg = str(3 + n)
        toc += f'<li><div><span>{e(sub)}</span><b>{e(t)}</b></div><em>{pg}</em></li>'
    pages = [f'<div class="mz-page">{run("1Cardz Weekly", "No. " + no)}<p class="kick">In this issue</p><h3>Contents</h3><ol class="toc">{toc}</ol><div class="folio">2</div></div>']
    back_html = ''
    if body and body[-1][0] == 'back':
        back_html = f'<div class="mz-page mz-back">{body[-1][3]}</div>'
        body = body[:-1]
    for n, (key, _, _, h) in enumerate(body):
        cls = ' mz-full' if key == 'feat' else (' mz-back' if key == 'back' else '')
        pages.append(f'<div class="mz-page mz-{key}{cls}">{h}<div class="folio">{3 + n}</div></div>')

    html_ = f'''<div class="mz" id="mz" data-pages="{len(pages) + 2}">
  <div class="mz-book" id="mzBook" aria-live="polite"></div>
  <div class="mz-ctl"><button type="button" class="mz-prev" aria-label="Previous page">‹</button><span class="mz-no"></span><button type="button" class="mz-next" aria-label="Next page">›</button></div>
  <template id="mzCover">{cover}</template>
  <template id="mzBack">{back_html}</template>
  {''.join(f'<template class="mzPg">{p}</template>' for p in pages)}
</div>'''
    return html_, CSS, JS

CSS = r'''
/* newsletter magazine (style C, Nov 4) */
.mz{position:relative;z-index:4;padding:clamp(16px,3vw,32px) 0 0}
.mz-book{display:grid;grid-template-columns:minmax(0,1fr);max-width:440px;margin:0 auto;border-radius:6px;overflow:hidden;box-shadow:0 26px 54px rgba(0,0,0,.55)}
.mz-book.two{grid-template-columns:minmax(0,1fr) minmax(0,1fr);max-width:880px}
.mz-ctl{display:flex;justify-content:center;align-items:center;gap:14px;margin-top:16px}
.mz-ctl button{font:inherit;font-size:22px;width:44px;height:44px;border-radius:50%;border:0;background:var(--foil,#e9c46a);color:#12162b;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,.35)}
.mz-ctl button:disabled{opacity:.3;cursor:default}
.mz-no{font-family:var(--f-mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#aab1c9;min-width:130px;text-align:center}
.mz-page{position:relative;aspect-ratio:3/4;overflow:hidden;container-type:inline-size;background:#fbf8f1;color:#9ea3ad;padding:5.5% 6.5% 4.5%;font-family:var(--f-body);display:flex;flex-direction:column}
.mz-page h3,.mz-page .pull,.mz-page blockquote p,.mz-page .toc em{padding-bottom:.12em;background:linear-gradient(180deg,#d4d8de 0%,#a7adb7 45%,#c9cdd4 55%,#8f959f 100%);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.mz-page .folio{margin-top:auto;padding-top:2cqw}
.mz-page+.mz-page{box-shadow:inset 1.4cqw 0 2cqw -1cqw rgba(0,0,0,.35)}
.mz-page .run{display:flex;justify-content:space-between;font-family:var(--f-mono);font-size:2.3cqw;letter-spacing:.14em;text-transform:uppercase;color:#6a6878;border-bottom:.3cqw solid #d8d1c3;padding-bottom:2cqw;margin-bottom:4cqw;flex:none}
.mz-page .kick{font-family:var(--f-mono);font-size:2.6cqw;letter-spacing:.2em;text-transform:uppercase;color:#c8102e;margin:0 0 2cqw}
.mz-page h3{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:8.6cqw;line-height:.98;margin:0 0 3cqw;color:#9ea3ad;text-transform:none;letter-spacing:0}
.mz-page p{font-size:3.3cqw;line-height:1.6;margin:0 0 3cqw;color:#9ea3ad;max-width:none}
.mz-page p.first::first-letter{float:left;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:12cqw;line-height:.8;padding:1cqw 1.6cqw 0 0;color:#c8102e}
.mz-page .pull{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:6cqw;line-height:1.08;border-top:.6cqw solid #1b1a22;border-bottom:.6cqw solid #1b1a22;padding:2.6cqw 0;margin:3.5cqw 0}
.mz-page .toc{list-style:none;margin:0;padding:0;counter-reset:t}
.mz-page .toc li{display:grid;grid-template-columns:8cqw 1fr auto;align-items:baseline;gap:3cqw;padding:.45cqw 0;border-bottom:.25cqw solid #d8d1c3;counter-increment:t}
.mz-page .toc li::before{content:counter(t,decimal-leading-zero);font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:5cqw;color:#c8102e;line-height:1}
.mz-page .toc b{display:block;font-size:3.1cqw;line-height:1.25}.mz-page .toc span{display:block;font-family:var(--f-mono);font-size:2cqw;letter-spacing:.12em;text-transform:uppercase;color:#6a6878}.mz-page .toc em{font-style:normal;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:3.6cqw;color:#9ea3ad}
.mz-page .stories{display:grid;grid-template-rows:1fr 1fr;gap:4cqw;flex:1;min-height:0}
.mz-page .st{display:grid;grid-template-columns:44% 1fr;grid-template-rows:auto auto auto 1fr;column-gap:4cqw;align-content:start;align-items:start;border-bottom:.25cqw solid #d8d1c3;padding-bottom:4cqw}.mz-page .st:last-child{border-bottom:0}
.mz-page .st img{display:block;width:100%;aspect-ratio:3/4;object-fit:cover;object-position:50% 12%;border-radius:1.2cqw;grid-row:span 4}
.mz-page .st .g{font-family:var(--f-mono);font-size:2.5cqw;letter-spacing:.14em;text-transform:uppercase;color:#c8102e}
.mz-page .st b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:5.6cqw;line-height:1.05;margin:1cqw 0 2cqw}
.mz-page .st p{font-size:3.3cqw;line-height:1.5;margin:0}
.mz-page .st small{display:block;font-size:2.5cqw;color:#8a8796;font-style:italic;margin-top:1cqw}
.mz-page .cal div{display:grid;grid-template-columns:24cqw 1fr;gap:3cqw;padding:3cqw 0;border-top:.25cqw solid #d8d1c3;font-size:3.2cqw;line-height:1.4}
.mz-page .cal b{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:4.2cqw;color:#c8102e;line-height:1.05}
.mz-page .cal i{display:block;font-size:2.5cqw;color:#6a6878;margin-top:.6cqw}
.mz-page .sign{margin-top:6cqw;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:6cqw;line-height:1.05}
.mz-page .cta{display:inline-block;margin-top:4cqw;font-family:var(--f-mono);font-size:2.8cqw;letter-spacing:.12em;text-transform:uppercase;background:#c8102e;color:#fff;padding:2.4cqw 4cqw;border-radius:1.2cqw;text-decoration:none}
.mz-page .folio{text-align:center;font-family:var(--f-mono);font-size:2.2cqw;color:#6a6878;flex:none}
.mz-page .folio.light{color:#fff}
.mz-full{padding:0;color:#fff}.mz-full .bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 10%}
.mz-full::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 50%,rgba(10,8,20,.85))}
.mz-full .cap{position:absolute;left:6.5cqw;right:6.5cqw;bottom:10cqw;z-index:2;font-size:3.3cqw;line-height:1.45;text-shadow:0 .3cqw 1cqw rgba(0,0,0,.8)}
.mz-full .cap .kick{color:#fde8c2}
.mz-full .cap b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:9cqw;line-height:.95;margin-bottom:2cqw}
.mz-full .folio{position:absolute;left:0;right:0;bottom:4cqw;z-index:2;color:#fff}
.mz-page .src{font-size:2.6cqw;color:#6a6878;font-style:italic}
.mz-page .hosts{display:flex;gap:3cqw;margin:0 0 4cqw;align-items:center}.mz-page .hosts img{flex:none;width:20cqw;height:20cqw;border-radius:50%;object-fit:cover;object-position:50% 15%;box-shadow:0 0 0 .5cqw #fff,0 1cqw 2cqw rgba(0,0,0,.2)}
.mz-page .strip{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:3cqw;border-top:.6cqw solid #1b1a22;padding-top:3cqw}.mz-page .strip b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:8cqw;line-height:1;color:#c8102e}.mz-page .strip span{font-family:var(--f-mono);font-size:2.2cqw;letter-spacing:.12em;text-transform:uppercase;color:#6a6878}
.mz-page .hosts p{margin:0;font-size:3.3cqw;line-height:1.5}
.mz-page .about{display:grid;grid-template-columns:1fr 1fr;gap:3cqw 4cqw;margin-top:1cqw}
.mz-page .about a{text-decoration:none}.mz-page .about b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:4.6cqw;color:#c8102e;line-height:1.1}
.mz-page .about span{display:block;font-size:2.8cqw;line-height:1.4;margin-top:.6cqw;color:#9ea3ad}
.mz-page .sig{font-family:"Playfair Display",Georgia,serif;font-style:italic;font-weight:700;font-size:5cqw;color:#c8102e}
.mz-page .nums{display:grid;grid-template-columns:1fr 1fr;gap:6cqw 5cqw;flex:1;align-content:space-evenly}
.mz-page .nums b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:11cqw;line-height:1;color:#c8102e}
.mz-page .nums span{display:block;font-size:3cqw;line-height:1.35;margin-top:1cqw}
.mz-page .mv div{display:grid;grid-template-columns:1fr auto;gap:.4cqw 3cqw;padding:2cqw 0;border-top:.25cqw solid #d8d1c3}
.mz-page .mv .g{grid-column:1/-1;font-family:var(--f-mono);font-size:2.3cqw;letter-spacing:.14em;text-transform:uppercase;color:#c8102e}
.mz-page .mv b{font-size:3cqw;line-height:1.3}.mz-page .mv em{font-style:normal;font-family:var(--f-mono);font-size:3.2cqw;text-align:right}
.mz-page .mv i{grid-column:2;font-style:normal;font-family:var(--f-mono);font-size:3cqw;text-align:right}.mz-page .mv i.up{color:#1a8f4a}.mz-page .mv i.down{color:#c8102e}
.mz-page .mv em{grid-row:2;grid-column:2}.mz-page .mv i{grid-row:3}
.mz-page .note{font-size:2.6cqw;color:#6a6878;margin-top:3cqw}.mz-page .note a{color:#c8102e}
.mz-page .quips{display:grid;grid-template-columns:1fr 1fr;gap:4cqw;flex:1;align-content:start}
.mz-page blockquote{margin:0;padding:3cqw;border-left:1cqw solid #c8102e;background:#f2ecdf}
.mz-page blockquote p{font-family:"Playfair Display",Georgia,serif;font-style:italic;font-weight:700;font-size:3.8cqw;line-height:1.25;margin:0 0 1.5cqw;color:#9ea3ad}
.mz-page blockquote cite{font-style:normal;font-family:var(--f-mono);font-size:2.2cqw;letter-spacing:.1em;text-transform:uppercase;color:#6a6878}
.mz-back{background:linear-gradient(160deg,#1b2a6b 0%,#0e1640 55%,#060a22 100%);color:#fff;justify-content:center}.mz-back .folio{position:absolute;left:0;right:0;bottom:4%}
.mz-page .radar div{display:grid;grid-template-columns:30cqw 1fr;gap:3cqw;padding:3.4cqw 0;border-top:.25cqw solid #d8d1c3;font-size:3.3cqw;line-height:1.4}.mz-page .radar b{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:4.4cqw;color:#c8102e;line-height:1.1}
.mz-page .watch{margin-top:auto;display:grid;grid-template-columns:26% 1fr;gap:4cqw;align-items:center;text-decoration:none;color:#9ea3ad;background:#f2ecdf;border-radius:1.4cqw;padding:2.4cqw}.mz-page .watch img{width:100%;aspect-ratio:4/3;object-fit:cover;object-position:50% 15%;border-radius:1cqw}.mz-page .watch span{font-size:2.9cqw;line-height:1.4}.mz-page .watch b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:5cqw;color:#c8102e}.mz-back .kick{color:#7cf3ff}.mz-back h3{color:#fff;font-size:11cqw}.mz-back p{color:#fff}
.mz-back .links{display:flex;flex-direction:column;gap:3cqw;margin:4cqw 0}
.mz-back .links a{font-family:var(--f-mono);font-size:3.2cqw;letter-spacing:.12em;text-transform:uppercase;color:#0e1640;background:#fff;padding:3cqw 4cqw;border-radius:1.2cqw;text-decoration:none;text-align:center}
.mz-back .sign{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:6cqw;line-height:1.05;margin:2cqw 0}
.mz-back .small{font-size:2.5cqw;opacity:.85}.mz-back .folio{color:#9fb3ff}
/* cover */
.mz-cover{display:block;padding:0;background:#f4efe4;cursor:pointer;isolation:isolate}
.mz-cover .ph{position:absolute;inset:0;z-index:0}.mz-cover .ph img{width:100%;height:100%;object-fit:cover;object-position:50% 0}
.mz-cover .ph::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,16,30,.35) 0%,transparent 22%,transparent 58%,rgba(20,16,30,.75) 100%)}
.mz-cover .mhd{position:absolute;left:0;right:0;top:4cqw;z-index:2;display:grid;justify-content:center}
.mz-cover .vol{position:absolute;right:4cqw;top:44cqw;z-index:2;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-weight:900;font-size:7cqw;line-height:1;color:#ffd23f;text-shadow:0 .4cqw 1.2cqw rgba(0,0,0,.7)}
.mz-cover .wm{text-align:center;margin-top:.7cqw;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-weight:700;font-size:5.6cqw;letter-spacing:.06em;color:#ffd23f;text-shadow:0 .3cqw 1cqw rgba(0,0,0,.65)}
.mz-cover .mast{position:relative;display:grid;justify-items:center;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:22cqw;line-height:.9;letter-spacing:-.02em;text-align:center}
.mz-cover .mast>span{grid-area:1/1}
.mz-cover .mast .sh{color:transparent;text-shadow:0 .5cqw 1.4cqw rgba(0,0,0,.55)}
.mz-cover .mast .sv{background:linear-gradient(180deg,#ffffff 0%,#f1f3f6 22%,#c9ced8 46%,#ffffff 54%,#dde1e8 72%,#aeb5c1 100%);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:#d9dde4}
.mz-cover .mast .ho{background:linear-gradient(105deg,transparent 0 30%,rgba(255,92,200,.85) 36%,rgba(255,226,92,.85) 41%,rgba(92,255,170,.85) 46%,rgba(92,200,255,.85) 51%,rgba(170,120,255,.85) 56%,transparent 62% 100%);
  background-size:300% 100%;background-repeat:no-repeat;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;
  will-change:background-position;transform:translateZ(0);animation:mzholo 3.2s linear infinite}
@keyframes mzholo{from{background-position:100% 0}to{background-position:0% 0}}
@media (prefers-reduced-motion:reduce){.mz-cover .mast .ho{animation:none;opacity:0}}
.mz-cover .tag{position:absolute;left:0;right:0;top:34.5cqw;z-index:2;text-align:center;font-family:var(--f-mono);font-size:2.3cqw;letter-spacing:.25em;text-transform:uppercase;color:#fff;text-shadow:0 .3cqw .8cqw rgba(0,0,0,.6)}
.mz-cover .side{position:absolute;left:4cqw;top:46cqw;z-index:2;width:30cqw;display:flex;flex-direction:column;gap:4cqw}
.mz-cover .side b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:5.6cqw;line-height:1;color:#fff;text-shadow:0 .4cqw 1.2cqw rgba(0,0,0,.75)}
.mz-cover .side span{display:block;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-size:3cqw;color:#fde8c2;text-shadow:0 .3cqw .8cqw rgba(0,0,0,.8)}
.mz-cover .big{position:absolute;left:4cqw;right:30cqw;bottom:4cqw;z-index:2;color:#fff}
.mz-cover .big b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:9cqw;line-height:.92;text-shadow:0 .4cqw 1.2cqw rgba(0,0,0,.6)}
.mz-cover .big span{display:block;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-size:3.6cqw;margin-top:1.5cqw;color:#fde8c2}
.mz-cover .bar{position:absolute;right:3.5cqw;bottom:3.5cqw;z-index:2;background:#fff;color:#8a8f99;padding:1.4cqw 2cqw 1cqw;font-family:var(--f-mono);font-size:2.2cqw;text-align:center;line-height:1.2}
.mz-cover .bar i{display:block;width:22cqw;height:7cqw;background:repeating-linear-gradient(90deg,#000 0 .5cqw,#fff .5cqw .8cqw,#000 .8cqw 1.1cqw,#fff 1.1cqw 1.9cqw,#000 1.9cqw 2.6cqw,#fff 2.6cqw 3cqw);margin-bottom:.6cqw}
'''

JS = r'''<script id="mz-js">
(function(){const mz=document.getElementById('mz');if(!mz)return;
  const book=document.getElementById('mzBook'),prev=mz.querySelector('.mz-prev'),next=mz.querySelector('.mz-next'),no=mz.querySelector('.mz-no');
  const cover=document.getElementById('mzCover').innerHTML,back=(document.getElementById('mzBack')||{}).innerHTML||'',pgs=[...mz.querySelectorAll('template.mzPg')].map(t=>t.innerHTML);
  const total=pgs.length+1+(back?1:0);
  const two=()=>matchMedia('(min-width:760px)').matches;
  /* views: cover alone, inside pages in spreads (or singles on phones), back page alone */
  function views(){const v=[{h:cover,first:1,n:1,cov:1}],st=two()?2:1;for(let i=0;i<pgs.length;i+=st)v.push({h:pgs.slice(i,i+st).join(''),first:i+2,n:Math.min(st,pgs.length-i)});
    if(back)v.push({h:back,first:pgs.length+2,n:1});return v}
  let idx=0,firstShown=1;
  function view(){const v=views();idx=Math.max(0,Math.min(idx,v.length-1));const c=v[idx];firstShown=c.first;
    book.classList.toggle('two',c.n===2);book.innerHTML=c.h;
    no.textContent=c.cov?'Cover · tap to open':(c.n===2?`Pages ${c.first}–${c.first+1} of ${total}`:(idx===v.length-1&&back?'Back cover':`Page ${c.first} of ${total}`));
    prev.disabled=idx===0;next.disabled=idx===v.length-1;
    if(c.cov){const el=book.querySelector('.mz-cover');if(el)el.addEventListener('click',()=>go(1))}}
  function go(d){idx+=d>0?1:-1;view()}
  addEventListener('resize',()=>{const v=views();idx=v.findIndex(x=>x.first<=firstShown&&firstShown<x.first+x.n);if(idx<0)idx=0;view()});
  prev.addEventListener('click',()=>go(-1));next.addEventListener('click',()=>go(1));
  addEventListener('keydown',e=>{const r=book.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight)return;if(e.key==='ArrowRight')go(1);if(e.key==='ArrowLeft')go(-1)});
  let sx=null;book.addEventListener('touchstart',e=>{sx=e.touches[0].clientX},{passive:true});
  book.addEventListener('touchend',e=>{if(sx===null)return;const dx=e.changedTouches[0].clientX-sx;sx=null;if(Math.abs(dx)>50)go(dx<0?1:-1)},{passive:true});
  view()})();
</script>'''
