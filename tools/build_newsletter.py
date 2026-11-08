#!/usr/bin/env python3
"""Build newsletter.html (Newsletter page: coming soon) from index.html's styles, binders, nav and Newsletter box.
Run after build_archive.py (it reuses archive.html's binder script)."""
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
e = html.escape

head = src[:src.index('<style>')]
head = re.sub(r'<title>.*?</title>', '<title>1 Cardz Newsletter</title>', head)
head = re.sub(r'<link rel="preload"[^>]*>\n', '', head)
head = head.replace('href="https://1cardz.news/"', 'href="https://1cardz.news/newsletter.html"')
head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="The 1 Cardz newsletter: the week in trading card game news, in one email every Sunday. Free, sign up on 1cardz.news.">', head)
style = src[src.index('<style>'):src.index('</style>')+len('</style>')]
hs = src.index('<header class="wrap cover-zone">'); header = src[hs:src.index('\n</header>', hs)+len('\n</header>')]
fs = src.index('<footer class="wrap">'); footer = src[fs:src.index('\n</footer>', fs)+len('\n</footer>')]
scrolltop = src[src.index('<script>'):src.index('</script>')+len('</script>')]
header = re.sub(r'<p class="home-intro">.*?</p>|<p>The trading card game news channel.*?</p>',
    '<p>The Newsletter. The week in trading card game news, in one email every Sunday. Free, no spam.</p>', header, flags=re.S)
header = header.replace('<a class="btn" href="#set" id="seeLatest">See the latest</a>', '<a class="btn" href="index.html">Back home</a>')
_k = arch.index('  /* binder videos: top first, bottom last */'); a_js = arch[arch.rindex('<script>', 0, _k):arch.index('</script>', _k)]
cover_js = a_js[a_js.index('  /* binder videos: top first, bottom last */'):a_js.rindex('})();')]


# this week's issue (tools/newsletter_latest.json), shown at the top of the page
iss = json.loads((root/'tools'/'newsletter_latest.json').read_text())
def _item(t):
    b, txt, src_ = t
    return f'<strong>{e(b)}</strong> {e(txt)} <em>({e(src_)})</em>'
_secs = ''
for sec in iss['sections']:
    _secs += f'<h3>{e(sec["h"])}</h3>'
    for t in sec.get('p', []): _secs += f'<p>{_item(t)}</p>'
    if sec.get('li'): _secs += '<ul>' + ''.join(f'<li>{_item(t)}</li>' for t in sec['li']) + '</ul>'
import nl_magazine
mz_html, mz_css, mz_js = nl_magazine.render(iss, root)

# Past issues (Nov 8): every issue is kept in tools/newsletters/issue-NN.json. Each one is rendered to
# mag/issue-NN.html (just its page templates, loaded into the viewer when its cover is tapped).
# The side shelves hold up to 6 past covers each, newest first: left shelf first, then right.
issues = {}
for f in sorted((root/'tools'/'newsletters').glob('issue-*.json')):
    try:
        d = json.loads(f.read_text()); issues[str(d.get('no'))] = d
    except Exception as _x:
        print('skipped', f.name, _x)
issues[str(iss.get('no'))] = iss
(root/'mag').mkdir(exist_ok=True)
past = []
for no_, d in sorted(issues.items(), key=lambda kv: kv[0], reverse=True):
    h_ = mz_html if d is iss else nl_magazine.render(d, root)[0]
    tpls = ''.join(re.findall(r'<template[^>]*>.*?</template>', h_, flags=re.S))
    (root/'mag'/f'issue-{no_}.html').write_text(tpls + '\n')
    if d is not iss:
        cov = re.search(r'<template id="mzCover">(.*?)</template>', h_, flags=re.S)
        past.append((no_, d, cov.group(1) if cov else ''))
def _slot(item):
    if not item:
        return '<div class="mz-slot empty" aria-hidden="true"></div>'
    no_, d, cov = item
    return (f'<button type="button" class="mz-slot" data-src="mag/issue-{e(no_)}.html" data-date="{e(d.get("date", ""))}" '
            f'aria-label="Open Issue {e(no_)}, {e(d.get("date", ""))}">{cov}</button>')
_sl = (past + [None] * 12)[:12]
shelf_l = '<div class="mz-shelf l" aria-label="Past issues">' + ''.join(_slot(x) for x in _sl[:6]) + '</div>'
shelf_r = '<div class="mz-shelf r" aria-label="More past issues">' + ''.join(_slot(x) for x in _sl[6:]) + '</div>'
mz_html = (f'<div class="mz-desk">{shelf_l}<div class="mz-mid"><button type="button" class="mz-home" id="mzHome" hidden>↩ This week\'s issue</button>'
           + mz_html + f'</div>{shelf_r}</div>')
issue_html = f"""  <section class="wrap nli" aria-labelledby="nli-h">
    <div class="sheet-head">
      <div class="sheet-title">
  <h2 id="nli-h">Newsletter</h2>
  <p>{e(iss['intro'])}</p>
      </div>
    </div>
    <div class="gd">
      <div class="mw-top">
        <span class="mono mw-label" style="color:#ffd23f"><i style="background:#ffd23f;box-shadow:0 0 10px #ffd23f"></i><span>Newsletter</span></span>
        <span class="mono mw-upd" id="mzDate">{e(iss['date'])}</span>
      </div>
{mz_html}
    </div>
  </section>
"""

extra_css = """<style>
/* newsletter page */
.nl-soon{position:relative;text-align:center;padding:clamp(34px,6vw,80px) clamp(18px,4vw,60px);display:grid;justify-items:center;gap:16px;z-index:4}
.nl-soon .nl-big{font-family:"Press Start 2P",ui-monospace,monospace;font-size:clamp(17px,3.4vw,37.4px);line-height:1.25;letter-spacing:.04em;margin:0;
  background:linear-gradient(100deg,#ff8ad8,#ffd23f,#7cf3ff,#c58cff,#ff8ad8);background-size:300% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:nlfoil 6s linear infinite;
  filter:drop-shadow(0 0 14px rgba(255,210,63,.35))}
@keyframes nlfoil{to{background-position:300% 0}}
.nl-soon p{margin:0;max-width:52ch;color:#cfd4e6;font-size:clamp(15px,1.5vw,18px);line-height:1.55}
.nl-soon ul{list-style:none;margin:6px 0 0;padding:0;display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.nl-soon li{font-family:var(--f-mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#e8ecf8;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:999px;padding:8px 14px}
@media (prefers-reduced-motion:reduce){.nl-soon .nl-big{animation:none}}
/* this week's issue */
.nli .gd{padding-bottom:clamp(18px,3vw,30px)}
.nli-mail{position:relative;z-index:4;max-width:680px;margin:clamp(14px,2.4vw,26px) auto 0;background:#fbf8f0;color:#1d2240;border-radius:14px;padding:clamp(20px,4vw,40px);
  box-shadow:0 0 0 1px rgba(124,243,255,.55),0 0 22px rgba(124,243,255,.25),0 18px 40px rgba(0,0,0,.45);font-size:16px;line-height:1.6;text-align:left}
.nli-mail p{margin:0 0 14px;color:#2a2f4d;max-width:none}
.nli-mail .nli-kick{font-family:var(--f-mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#6a6f8c;margin-bottom:6px}
.nli-mail .nli-title{font-family:var(--f-display);font-weight:800;font-stretch:80%;font-size:clamp(26px,3.6vw,38px);line-height:1.05;margin:0 0 6px;color:#12162b}
.nli-mail .nli-by{font-size:13px;color:#6a6f8c;margin-bottom:20px}
.nli-mail h3{font-family:var(--f-display);font-weight:800;font-stretch:85%;font-size:22px;margin:26px 0 10px;color:#12162b}
.nli-mail ul{margin:0 0 10px;padding-left:20px}.nli-mail li{margin:0 0 10px;color:#2a2f4d}
.nli-mail em{color:#6a6f8c}
.nli-mail a{color:#1a5fd0}
.nli-mail hr{border:0;border-top:1px solid #e2ddcf;margin:26px 0 0}
.nli-img{display:block;width:min(70%,240px);margin:18px auto 6px;text-decoration:none;text-align:center}
.nli-img img{display:block;width:100%;border-radius:12px;box-shadow:0 8px 22px rgba(0,0,0,.2)}
.nli-img span{display:block;font-size:13px;color:#6a6f8c;margin-top:8px}
.nli-sign{margin-top:20px !important;font-weight:700;color:#12162b !important}
.nli-cta{position:relative;z-index:4;display:flex;flex-wrap:wrap;gap:12px 16px;align-items:center;justify-content:center;margin-top:clamp(16px,2.4vw,24px);color:#e8ecf8;font-size:15px}

"""+mz_css+"""
@media (max-width:560px){.nli-mail{font-size:15px;border-radius:12px}.nli-mail h3{font-size:19px}}
</style>"""

header = header + '\n\n' + site_parts.navbar(src, 'newsletter.html')
footer = site_parts.newsletter_section(src) + '\n' + footer + '\n\n' + site_parts.newsletter_script(src)
body = f"""{header}

<main>
{issue_html}
</main>

{footer}
"""

js = r"""<script>
(function(){
  const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.cover').forEach(cov=>{const ch=cov.querySelector('.cover-holo');if(reduce||!ch)return;
    cov.addEventListener('pointermove',e=>{const r=cov.getBoundingClientRect();cov.classList.add('hover');
      ch.style.setProperty('--hx',((e.clientX-r.left)/r.width*100).toFixed(1)+'%');ch.style.setProperty('--hy',((e.clientY-r.top)/r.height*100).toFixed(1)+'%')});
    cov.addEventListener('pointerleave',()=>{cov.classList.remove('hover');ch.style.removeProperty('--hx');ch.style.removeProperty('--hy')})});
__COVER__})();
</script>""".replace('__COVER__', cover_js)

out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + head + '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&display=swap">\n' + style + '\n' + extra_css + '\n</head>\n<body>\n' + body + '\n' + scrolltop + '\n' + js + '\n' + mz_js + '\n</body>\n</html>\n')
(root/'newsletter.html').write_text(out)

# Magazine cover picture for emails (img/magazine-cover.jpg, used by the beehiiv welcome email, Nov 6, 2026).
# Re-rendered from the live cover whenever this page is rebuilt; skipped quietly if Playwright isn't there.
try:
    import subprocess, os
    js = """const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1200,height:1400},deviceScaleFactor:1.5});
await p.goto('file://'+process.argv[1]);await p.waitForTimeout(1500);
await p.evaluate(()=>document.querySelectorAll('.mz-cover .ho').forEach(e=>{e.style.animation='none';e.style.opacity='0'}));
const el=await p.$('.mz-cover');await el.screenshot({path:process.argv[2]});await b.close()})().catch(e=>{console.error(e.message);process.exit(1)})"""
    png = root/'img'/'magazine-cover.png'
    r = subprocess.run(['node', '-e', js, str(root/'newsletter.html'), str(png)], timeout=90, capture_output=True, text=True)
    if r.returncode == 0 and png.exists():
        from PIL import Image
        Image.open(png).convert('RGB').save(root/'img'/'magazine-cover.jpg', quality=84, optimize=True, progressive=True)
        png.unlink()
        print('magazine-cover.jpg updated')
    else:
        print('magazine cover skipped:', (r.stderr or '').strip()[:120])
except Exception as _e:
    print('magazine cover skipped:', _e)
print('newsletter.html', len(out), 'bytes')
# SEO pass (titles, share previews, structured data, sitemap.xml, robots.txt); safe to repeat
try:
    import subprocess
    subprocess.run([sys.executable, str(root/'tools'/'seo.py')], timeout=120)
except Exception as _e:
    print('seo skipped:', _e)
