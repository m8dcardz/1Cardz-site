#!/usr/bin/env python3
"""Build board.html (Message Board page, coming soon: an arcade score board hall) from index.html's styles, binders, nav and Newsletter box.
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
head = re.sub(r'<title>.*?</title>', '<title>1 Cardz Message Board</title>', head)
head = re.sub(r'<link rel="preload"[^>]*>\n', '', head)
head = head.replace('href="https://1cardz.news/"', 'href="https://1cardz.news/board.html"')
head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="The 1 Cardz Message Board: an arcade hall of fame for trading card game fans. Coming soon.">', head)
style = src[src.index('<style>'):src.index('</style>')+len('</style>')]
hs = src.index('<header class="wrap cover-zone">'); header = src[hs:src.index('\n</header>', hs)+len('\n</header>')]
fs = src.index('<footer class="wrap">'); footer = src[fs:src.index('\n</footer>', fs)+len('\n</footer>')]
scrolltop = src[src.index('<script>'):src.index('</script>')+len('</script>')]
header = re.sub(r'<p>The trading card game news channel.*?</p>',
    '<p>The Message Board. An arcade hall of fame where card fans post their pulls, takes and high scores. Coming soon.</p>', header, flags=re.S)
header = header.replace('<a class="btn" href="#set" id="seeLatest">See the latest</a>', '<a class="btn" href="index.html">Back home</a>')
_k = arch.index('  /* binder videos: top first, bottom last */'); a_js = arch[arch.rindex('<script>', 0, _k):arch.index('</script>', _k)]
cover_js = a_js[a_js.index('  /* binder videos: top first, bottom last */'):a_js.rindex('})();')]



rows = [("1ST","ZIA","WELCOME TO THE HALL!","999,999"),
        ("2ND","LUNA","SHHH... POST LOUDLY.","888,888"),
        ("3RD","MIC","IS THIS THING ON?","777,777"),
        ("4TH","1CZ","MUDKIP OUTBID MY RENT","480,000"),
        ("5TH","???","YOUR MESSAGE HERE","000,000"),
        ("6TH","???","YOUR PULL HERE","000,000"),
        ("7TH","???","YOUR HOT TAKE HERE","000,000")]
rows_html = ''.join(f'<li class="r{i}"><span class="rk">{e(a)}</span><span class="nm2">{e(b)}</span><span class="msg">{e(c)}</span><span class="sc">{e(d)}</span></li>' for i,(a,b,c,d) in enumerate(rows,1))

extra_css = """<style>
/* message board: arcade score board hall */
.hall{position:relative;overflow:hidden;border-radius:18px;padding:clamp(22px,4vw,48px) clamp(12px,3vw,40px) clamp(30px,5vw,56px);
  background:radial-gradient(120% 70% at 50% 0%,#2a1650 0%,#120a2a 45%,#07060f 100%);box-shadow:0 0 0 3px #0d0b16,0 0 0 5px #2a2340,0 18px 40px rgba(0,0,0,.45);isolation:isolate}
.hall::before{content:"";position:absolute;left:-20%;right:-20%;bottom:-2px;height:42%;z-index:-1;
  background:linear-gradient(transparent 0 calc(100% - 1px),rgba(255,58,220,.55) 0) 0 0/100% 34px,linear-gradient(90deg,transparent 0 calc(100% - 1px),rgba(124,243,255,.45) 0) 0 0/60px 100%;
  transform:perspective(320px) rotateX(58deg);transform-origin:50% 100%;mask-image:linear-gradient(transparent,#000 40%);-webkit-mask-image:linear-gradient(transparent,#000 40%)}
.hall::after{content:"";position:absolute;inset:0;z-index:-1;pointer-events:none;background:radial-gradient(40% 30% at 15% 20%,rgba(124,243,255,.12),transparent 70%),radial-gradient(40% 30% at 85% 25%,rgba(255,138,216,.12),transparent 70%)}
.hall-marquee{font-family:"Press Start 2P",ui-monospace,monospace;text-align:center;margin:0 auto clamp(18px,3vw,30px);font-size:clamp(14px,2.6vw,30px);line-height:1.3;letter-spacing:.06em;color:#ffd23f;
  text-shadow:0 0 6px #ffd23f,0 0 16px #ff9d00,0 0 30px rgba(255,120,0,.6)}
.hall-marquee small{display:block;font-size:.42em;letter-spacing:.3em;color:#7cf3ff;text-shadow:0 0 8px #7cf3ff;margin-top:10px}
.hall-row{display:grid;grid-template-columns:1fr minmax(0,760px) 1fr;align-items:end;gap:clamp(10px,2vw,26px)}
.cab{justify-self:center;width:min(100%,130px);aspect-ratio:3/5;position:relative;border-radius:10px 10px 4px 4px;background:linear-gradient(180deg,#1b1240,#0c0820);box-shadow:inset 0 0 0 2px #2b3f80,0 0 18px rgba(124,243,255,.18)}
.cab::before{content:"";position:absolute;left:12%;right:12%;top:10%;height:34%;border-radius:6px;background:radial-gradient(circle at 50% 50%,#7cf3ff33,#05121a 70%);box-shadow:0 0 14px rgba(124,243,255,.5),inset 0 0 10px rgba(124,243,255,.4)}
.cab::after{content:"";position:absolute;left:20%;right:20%;top:56%;height:8%;border-radius:4px;background:radial-gradient(circle at 30% 50%,#ff3b5c 0 18%,transparent 20%),radial-gradient(circle at 70% 50%,#ffd23f 0 18%,transparent 20%),#120c26}
.cab.r::before{background:radial-gradient(circle at 50% 50%,#ff8ad833,#1a0516 70%);box-shadow:0 0 14px rgba(255,138,216,.5),inset 0 0 10px rgba(255,138,216,.4)}
.board{position:relative;border-radius:16px;padding:clamp(14px,2.4vw,26px);background:#05040b;
  box-shadow:0 0 0 4px #1a1530,0 0 0 7px #2b3f80,0 0 28px rgba(124,243,255,.35),inset 0 0 40px rgba(124,243,255,.08)}
.board::after{content:"";position:absolute;inset:0;border-radius:16px;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(255,255,255,.035) 0 1px,transparent 1px 3px)}
.board h3{font-family:"Press Start 2P",ui-monospace,monospace;font-size:clamp(11px,1.6vw,16px);text-align:center;color:#fff;margin:4px 0 16px;letter-spacing:.12em;text-shadow:0 0 8px rgba(255,255,255,.6)}
.board ol{list-style:none;margin:0;padding:0;display:grid;gap:clamp(8px,1.4vw,12px)}
.board li{display:grid;grid-template-columns:4.4em 4.4em minmax(0,1fr) 7.6em;gap:1.1em;align-items:baseline;font-family:"Press Start 2P",ui-monospace,monospace;font-size:clamp(9px,1.25vw,13px);line-height:1.5;letter-spacing:.04em}
.board .hd2{color:#8a90b8}
.board .sc{text-align:right}
.board .msg{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.board .r1{color:#ff3b5c;text-shadow:0 0 8px rgba(255,59,92,.7)}.board .r2{color:#ff9d2e;text-shadow:0 0 8px rgba(255,157,46,.6)}
.board .r3{color:#ffd23f;text-shadow:0 0 8px rgba(255,210,63,.6)}.board .r4{color:#58f08a;text-shadow:0 0 8px rgba(88,240,138,.6)}
.board .r5{color:#7cf3ff;text-shadow:0 0 8px rgba(124,243,255,.6)}.board .r6{color:#6d8cf0;text-shadow:0 0 8px rgba(109,140,240,.6)}
.board .r7{color:#c58cff;text-shadow:0 0 8px rgba(197,140,255,.6)}
.board-foot{margin-top:clamp(16px,2.6vw,24px);text-align:center;font-family:"Press Start 2P",ui-monospace,monospace;display:grid;gap:12px}
.board-foot .soon{font-size:clamp(16px,2.6vw,26px);color:#fff;letter-spacing:.08em;text-shadow:0 0 10px #7cf3ff,0 0 22px rgba(124,243,255,.7)}
.board-foot .ins{font-size:clamp(9px,1.2vw,12px);color:#ffd23f;letter-spacing:.1em}
.board-foot .ini{font-size:clamp(9px,1.2vw,12px);color:#cfd4e6;letter-spacing:.1em}
.board-foot .ini b{color:#7cf3ff;font-weight:400}
@media (prefers-reduced-motion:no-preference){.blink{animation:hblink 1.1s steps(1) infinite}.board .r1{animation:hblink 1.6s steps(1) infinite}}
@keyframes hblink{50%{opacity:.15}}
.hall-cta{position:relative;z-index:2;margin:clamp(20px,3vw,30px) auto 0;display:flex;flex-wrap:wrap;gap:12px 16px;align-items:center;justify-content:center;color:#e8ecf8;font-size:15px;text-align:center}
@media (max-width:760px){.hall-row{grid-template-columns:1fr}.cab{display:none}.board li{grid-template-columns:4.3em 4.3em minmax(0,1fr);gap:.6em;font-size:clamp(8px,2.3vw,10px)}.board .sc{display:none}}
</style>"""

header = header + '\n\n' + site_parts.navbar(src, 'board.html')
footer = site_parts.newsletter_section(src) + '\n' + footer + '\n\n' + site_parts.newsletter_script(src)
body = f"""{header}

<main>
  <section class="wrap mbp" aria-labelledby="mb-h">
    <div class="sheet-head">
      <h2 id="mb-h">Message Board</h2>
      <p>Coming soon: an arcade hall of fame where you can post your best pulls, hot takes and shout-outs to Zia and Luna.</p>
    </div>
    <div class="hall">
      <p class="hall-marquee">1CARDZ HALL OF FAME<small>MESSAGE BOARD</small></p>
      <div class="hall-row">
        <span class="cab" aria-hidden="true"></span>
        <div class="board" role="img" aria-label="Arcade high score board. The Message Board is coming soon.">
          <h3>HIGH SCORES</h3>
          <ol aria-hidden="true">
            <li class="hd2"><span>RANK</span><span>NAME</span><span>MESSAGE</span><span class="sc">SCORE</span></li>
            {rows_html}
          </ol>
          <div class="board-foot" aria-hidden="true">
            <span class="soon blink">COMING SOON</span>
            <span class="ins">INSERT COIN TO POST</span>
            <span class="ini">ENTER YOUR INITIALS: <b class="blink">A</b> _ _</span>
          </div>
        </div>
        <span class="cab r" aria-hidden="true"></span>
      </div>
      <div class="hall-cta"><span>Want to know when the hall opens?</span><a class="btn" href="#newsletter">Get the newsletter</a></div>
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
(root/'board.html').write_text(out)
print('board.html', len(out), 'bytes')
