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
head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="The 1 Cardz newsletter: the week in trading card game news, in one email. Free, sign up on 1cardz.news.">', head)
style = src[src.index('<style>'):src.index('</style>')+len('</style>')]
hs = src.index('<header class="wrap cover-zone">'); header = src[hs:src.index('\n</header>', hs)+len('\n</header>')]
fs = src.index('<footer class="wrap">'); footer = src[fs:src.index('\n</footer>', fs)+len('\n</footer>')]
scrolltop = src[src.index('<script>'):src.index('</script>')+len('</script>')]
header = re.sub(r'<p>The trading card game news channel.*?</p>',
    '<p>The Newsletter. The week in trading card game news, in one email. Free, no spam.</p>', header, flags=re.S)
header = header.replace('<a class="btn" href="#set" id="seeLatest">See the latest</a>', '<a class="btn" href="index.html">Back home</a>')
_k = arch.index('  /* binder videos: top first, bottom last */'); a_js = arch[arch.rindex('<script>', 0, _k):arch.index('</script>', _k)]
cover_js = a_js[a_js.index('  /* binder videos: top first, bottom last */'):a_js.rindex('})();')]


extra_css = """<style>
/* newsletter page */
.nl-soon{position:relative;text-align:center;padding:clamp(34px,6vw,80px) clamp(18px,4vw,60px);display:grid;justify-items:center;gap:16px;z-index:4}
.nl-soon .nl-big{font-family:"Press Start 2P",ui-monospace,monospace;font-size:clamp(20px,4vw,44px);line-height:1.25;letter-spacing:.04em;margin:0;
  background:linear-gradient(100deg,#ff8ad8,#ffd23f,#7cf3ff,#c58cff,#ff8ad8);background-size:300% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:nlfoil 6s linear infinite;
  filter:drop-shadow(0 0 14px rgba(255,210,63,.35))}
@keyframes nlfoil{to{background-position:300% 0}}
.nl-soon p{margin:0;max-width:52ch;color:#cfd4e6;font-size:clamp(15px,1.5vw,18px);line-height:1.55}
.nl-soon ul{list-style:none;margin:6px 0 0;padding:0;display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.nl-soon li{font-family:var(--f-mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#e8ecf8;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:999px;padding:8px 14px}
@media (prefers-reduced-motion:reduce){.nl-soon .nl-big{animation:none}}
</style>"""

header = header + '\n\n' + site_parts.navbar(src, 'newsletter.html')
footer = site_parts.newsletter_section(src) + '\n' + footer + '\n\n' + site_parts.newsletter_script(src)
body = f"""{header}

<main>
  <section class="wrap nlp" aria-labelledby="nl-h">
    <div class="sheet-head">
      <h2 id="nl-h">Newsletter</h2>
      <p>One email a week with everything worth knowing in cards. Free, no spam, unsubscribe any time.</p>
    </div>
    <div class="gd">
      <div class="mw-top">
        <span class="mono mw-label" style="color:#ffd23f"><i style="background:#ffd23f;box-shadow:0 0 10px #ffd23f"></i><span>Newsletter</span></span>
        <span class="mono mw-upd">Free · weekly</span>
      </div>
      <div class="nl-soon">
        <p class="nl-big">Sign up free</p>
        <p>The week in trading card game news: the biggest stories from Zia and Luna, release dates to watch and the Market Watch picks. Pop your email in the box below.</p>
        <a class="btn" href="#newsletter">Sign me up</a>
        <ul aria-label="What's in it"><li>Top stories</li><li>Release dates</li><li>Market Watch</li><li>Free</li></ul>
      </div>
    </div>
  </section>
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
       + head + style + '\n' + extra_css + '\n</head>\n<body>\n' + body + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
(root/'newsletter.html').write_text(out)
print('newsletter.html', len(out), 'bytes')
