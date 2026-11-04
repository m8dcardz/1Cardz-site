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
  <div class="ed">Magazine Edition</div>
  <div class="mast">1Cardz</div>
  <div class="tag">The Weekly · Issue {e(no)} · {e(short)}</div>
  <div class="side">{lines}</div>
  <div class="big"><b>{e(cv.get('main') or iss.get('title'))}</b><span>{e(cv.get('sub', ''))}</span></div>
  <div class="bar"><i></i>1CZ-{e(no)}</div>
</div>'''

    pages = []
    toc = [f'<li><div><b>{e(big[0].rstrip("."))}</b><span>The big one · p.3</span></div></li>']
    per = 4
    for k, t in enumerate(tops):
        g, ti = game_title(t[0])
        toc.append(f'<li><div><b>{e(ti)}</b><span>{e(g)} · p.{5 + k // per}</span></div></li>')
    last = 5 + max(0, (len(tops) - 1) // per) + 1
    if cal:
        toc.append(f'<li><div><b>The week ahead</b><span>p.{last}</span></div></li>')
    run = lambda a, b: f'<div class="run"><span>{e(a)}</span><span>{e(b)}</span></div>'
    pages.append(f'<div class="mz-page">{run("1Cardz Weekly", "No. " + no)}<p class="kick">In this issue</p><h3>Contents</h3><ol class="toc">{"".join(toc)}</ol><div class="folio">2</div></div>')
    pull = f'<div class="pull">"{e(iss["pull"])}"</div>' if iss.get('pull') else ''
    pages.append(f'''<div class="mz-page">{run("The big one", big[2])}<p class="kick">Cover story</p><h3>{e(big[0].rstrip("."))}</h3>
<p class="first">{e(iss.get("opening", ""))}</p><p>{e(big[1])}</p>{pull}<div class="folio">3</div></div>''')
    f = iss.get('feature') or {}
    fimg = _img(root, f.get('clip'))
    if fimg:
        pages.append(f'<div class="mz-page mz-full"><img src="{e(fimg)}" alt="" loading="lazy"><div class="cap"><b>{e(f.get("title", ""))}</b>{e(f.get("text", ""))}</div><div class="folio light">4</div></div>')
    else:
        pages.append(f'<div class="mz-page mz-full"><img src="{e(cover_img)}" alt="" loading="lazy"><div class="folio light">4</div></div>')
    for k in range(0, len(tops), per):
        cards = ''
        for j, t in enumerate(tops[k:k + per]):
            g, ti = game_title(t[0])
            im = _img(root, tclips[k + j]) if k + j < len(tclips) else ''
            cards += (f'<div class="st">{f"<img src={chr(34)}{e(im)}{chr(34)} alt={chr(34)}{chr(34)} loading={chr(34)}lazy{chr(34)}>" if im else ""}'
                      f'<span class="g">{e(g)}</span><b>{e(ti)}</b><p>{e(t[1])}</p><small>{e(t[2])}</small></div>')
        n = k // per
        pages.append(f'<div class="mz-page">{run("Top stories", f"{n + 1} of {(len(tops) + per - 1) // per}")}<div class="stories">{cards}</div><div class="folio">{5 + n}</div></div>')
    if cal:
        rows = ''.join(f'<div><b>{e(c[0].rstrip(":"))}</b><span>{e(c[1])}<i>{e(c[2])}</i></span></div>' for c in cal)
        sign = '<br>'.join(e(x) for x in iss.get('signoff', [])[:2])
        pages.append(f'<div class="mz-page">{run("The week ahead", short)}<p class="kick">Mark your calendar</p><h3>The week ahead</h3><div class="cal">{rows}</div>'
                     f'<div class="sign">{sign}</div><a class="cta" href="#newsletter">Get it every Sunday · free</a><div class="folio">{last}</div></div>')

    html_ = f'''<div class="mz" id="mz" data-pages="{len(pages) + 1}">
  <div class="mz-book" id="mzBook" aria-live="polite"></div>
  <div class="mz-ctl"><button type="button" class="mz-prev" aria-label="Previous page">‹</button><span class="mz-no"></span><button type="button" class="mz-next" aria-label="Next page">›</button></div>
  <template id="mzCover">{cover}</template>
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
.mz-page{position:relative;aspect-ratio:3/4;overflow:hidden;container-type:inline-size;background:#fbf8f1;color:#1b1a22;padding:6cqw;font-family:var(--f-body)}
.mz-page+.mz-page{box-shadow:inset 1.4cqw 0 2cqw -1cqw rgba(0,0,0,.35)}
.mz-page .run{display:flex;justify-content:space-between;font-family:var(--f-mono);font-size:2.3cqw;letter-spacing:.14em;text-transform:uppercase;color:#6a6878;border-bottom:.3cqw solid #d8d1c3;padding-bottom:2cqw;margin-bottom:5cqw}
.mz-page .kick{font-family:var(--f-mono);font-size:2.6cqw;letter-spacing:.2em;text-transform:uppercase;color:#c8102e;margin:0 0 2cqw}
.mz-page h3{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:8.6cqw;line-height:.98;margin:0 0 4cqw;color:#1b1a22;text-transform:none;letter-spacing:0}
.mz-page p{font-size:3.3cqw;line-height:1.6;margin:0 0 3cqw;color:#2a2833;max-width:none}
.mz-page p.first::first-letter{float:left;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:12cqw;line-height:.8;padding:1cqw 1.6cqw 0 0;color:#c8102e}
.mz-page .pull{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:6cqw;line-height:1.08;border-top:.6cqw solid #1b1a22;border-bottom:.6cqw solid #1b1a22;padding:3cqw 0;margin:5cqw 0}
.mz-page .toc{list-style:none;margin:0;padding:0;counter-reset:t}
.mz-page .toc li{display:grid;grid-template-columns:9cqw 1fr;gap:3cqw;padding:2.4cqw 0;border-bottom:.25cqw solid #d8d1c3;counter-increment:t}
.mz-page .toc li::before{content:counter(t,decimal-leading-zero);font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:6cqw;color:#c8102e;line-height:1}
.mz-page .toc b{display:block;font-size:3.3cqw;line-height:1.25}.mz-page .toc span{font-size:2.6cqw;color:#6a6878}
.mz-page .stories{display:grid;grid-template-columns:1fr 1fr;gap:4cqw}
.mz-page .st img{display:block;width:100%;aspect-ratio:4/3;object-fit:cover;object-position:50% 15%;border-radius:1.2cqw;margin-bottom:2cqw}
.mz-page .st .g{font-family:var(--f-mono);font-size:2.2cqw;letter-spacing:.14em;text-transform:uppercase;color:#c8102e}
.mz-page .st b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:4cqw;line-height:1.08;margin:1cqw 0 1.4cqw}
.mz-page .st p{font-size:2.7cqw;line-height:1.45;margin:0}
.mz-page .st small{display:block;font-size:2.2cqw;color:#8a8796;font-style:italic;margin-top:1cqw}
.mz-page .cal div{display:grid;grid-template-columns:24cqw 1fr;gap:3cqw;padding:3cqw 0;border-top:.25cqw solid #d8d1c3;font-size:3.2cqw;line-height:1.4}
.mz-page .cal b{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:4.2cqw;color:#c8102e;line-height:1.05}
.mz-page .cal i{display:block;font-size:2.5cqw;color:#6a6878;margin-top:.6cqw}
.mz-page .sign{margin-top:6cqw;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:6cqw;line-height:1.05}
.mz-page .cta{display:inline-block;margin-top:4cqw;font-family:var(--f-mono);font-size:2.8cqw;letter-spacing:.12em;text-transform:uppercase;background:#c8102e;color:#fff;padding:2.4cqw 4cqw;border-radius:1.2cqw;text-decoration:none}
.mz-page .folio{position:absolute;bottom:3cqw;left:0;right:0;text-align:center;font-family:var(--f-mono);font-size:2.2cqw;color:#6a6878}
.mz-page .folio.light{color:#fff}
.mz-full{padding:0}.mz-full img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 10%}
.mz-full::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 55%,rgba(10,8,20,.8))}
.mz-full .cap{position:absolute;left:5cqw;right:5cqw;bottom:8cqw;z-index:2;color:#fff;font-size:3cqw;line-height:1.45;text-shadow:0 .3cqw 1cqw rgba(0,0,0,.8)}
.mz-full .cap b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:8cqw;line-height:.95;margin-bottom:2cqw}
.mz-full .folio{z-index:2}
/* cover */
.mz-cover{padding:0;background:#f4efe4;cursor:pointer;isolation:isolate}
.mz-cover .ph{position:absolute;inset:0;z-index:0}.mz-cover .ph img{width:100%;height:100%;object-fit:cover;object-position:50% 0}
.mz-cover .ph::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,16,30,.35) 0%,transparent 22%,transparent 58%,rgba(20,16,30,.75) 100%)}
.mz-cover .ed{position:absolute;left:0;right:0;top:3cqw;z-index:2;text-align:center;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-weight:700;font-size:5.4cqw;letter-spacing:.04em;color:#fff;text-shadow:0 .3cqw 1cqw rgba(0,0,0,.6)}
.mz-cover .mast{position:absolute;left:4cqw;right:4cqw;top:10cqw;z-index:2;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:21cqw;line-height:.9;color:#c8102e;letter-spacing:-.02em;text-align:center;text-shadow:0 .4cqw 1.2cqw rgba(0,0,0,.25)}
.mz-cover .tag{position:absolute;left:0;right:0;top:30.5cqw;z-index:2;text-align:center;font-family:var(--f-mono);font-size:2.3cqw;letter-spacing:.25em;text-transform:uppercase;color:#fff;text-shadow:0 .3cqw .8cqw rgba(0,0,0,.6)}
.mz-cover .side{position:absolute;left:4cqw;top:46cqw;z-index:2;width:30cqw;display:flex;flex-direction:column;gap:4cqw}
.mz-cover .side b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:5.6cqw;line-height:1;color:#fff;text-shadow:0 .4cqw 1.2cqw rgba(0,0,0,.75)}
.mz-cover .side span{display:block;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-size:3cqw;color:#fde8c2;text-shadow:0 .3cqw .8cqw rgba(0,0,0,.8)}
.mz-cover .big{position:absolute;left:4cqw;right:30cqw;bottom:4cqw;z-index:2;color:#fff}
.mz-cover .big b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:9cqw;line-height:.92;text-shadow:0 .4cqw 1.2cqw rgba(0,0,0,.6)}
.mz-cover .big span{display:block;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-size:3.6cqw;margin-top:1.5cqw;color:#fde8c2}
.mz-cover .bar{position:absolute;right:3.5cqw;bottom:3.5cqw;z-index:2;background:#fff;color:#000;padding:1.4cqw 2cqw 1cqw;font-family:var(--f-mono);font-size:2.2cqw;text-align:center;line-height:1.2}
.mz-cover .bar i{display:block;width:22cqw;height:7cqw;background:repeating-linear-gradient(90deg,#000 0 .5cqw,#fff .5cqw .8cqw,#000 .8cqw 1.1cqw,#fff 1.1cqw 1.9cqw,#000 1.9cqw 2.6cqw,#fff 2.6cqw 3cqw);margin-bottom:.6cqw}
'''

JS = r'''<script id="mz-js">
(function(){const mz=document.getElementById('mz');if(!mz)return;
  const book=document.getElementById('mzBook'),prev=mz.querySelector('.mz-prev'),next=mz.querySelector('.mz-next'),no=mz.querySelector('.mz-no');
  const cover=document.getElementById('mzCover').innerHTML,pgs=[...mz.querySelectorAll('template.mzPg')].map(t=>t.innerHTML),total=pgs.length+1;
  const two=()=>matchMedia('(min-width:760px)').matches;
  let pos=0; /* 0 = cover; then page index (0-based) into pgs */
  function view(){if(pos===0){book.classList.remove('two');book.innerHTML=cover;no.textContent='Cover · tap to open';prev.disabled=true;next.disabled=false;
      const c=book.querySelector('.mz-cover');if(c)c.addEventListener('click',()=>go(1));return}
    const step=two()?2:1;let i=pos-1;if(step===2)i-=i%2;pos=i+1;
    book.classList.toggle('two',step===2);book.innerHTML=pgs.slice(i,i+step).join('');
    no.textContent=step===2&&i+1<pgs.length?`Pages ${i+2}–${i+3} of ${total}`:`Page ${i+2} of ${total}`;
    prev.disabled=false;next.disabled=i+step>=pgs.length}
  function go(d){const step=two()?2:1;if(d>0)pos=pos===0?1:Math.min(pgs.length,pos+step);else pos=pos<=1?0:pos-step;view()}
  prev.addEventListener('click',()=>go(-1));next.addEventListener('click',()=>go(1));
  addEventListener('keydown',e=>{const r=book.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight)return;if(e.key==='ArrowRight')go(1);if(e.key==='ArrowLeft')go(-1)});
  let sx=null;book.addEventListener('touchstart',e=>{sx=e.touches[0].clientX},{passive:true});
  book.addEventListener('touchend',e=>{if(sx===null)return;const dx=e.changedTouches[0].clientX-sx;sx=null;if(Math.abs(dx)>50)go(dx<0?1:-1)},{passive:true});
  addEventListener('resize',()=>{if(pos)view()});view()})();
</script>'''
