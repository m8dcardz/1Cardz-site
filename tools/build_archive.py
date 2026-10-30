#!/usr/bin/env python3
"""Build archive.html (all past posts) from index.html's styles/binders + tools/posts.json."""
import json, re, html, datetime, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root/'index.html').read_text()
# index.html may be the standalone build (with its own doctype/head wrapper): strip it back to the fragment
if src.lstrip().lower().startswith('<!doctype'):
    vp = '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    src = src[src.index(vp)+len(vp):]
posts = json.loads((root/'tools'/'posts.json').read_text())

head_end = src.index('<style>')
head = src[:head_end]
head = re.sub(r'<title>.*?</title>', '<title>1 Cardz Stories</title>', head)
head = re.sub(r'<link rel="preload"[^>]*>\n', '', head)
head = head.replace('href="https://1cardz.news/"', 'href="https://1cardz.news/archive.html"')
head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="Every 1Cardz.news clip from Zia and Luna, newest first.">', head)
style = src[head_end:src.index('</style>')+len('</style>')]
header = src[src.index('<header class="wrap cover-zone">'):src.index('\n</header>', src.index('<header class="wrap cover-zone">'))+len('\n</header>')]
footer = src[src.index('<footer class="wrap">'):src.index('\n</footer>', src.index('<footer class="wrap">'))+len('\n</footer>')]
scrolltop = src[src.index('<script>'):src.index('</script>')+len('</script>')]

n = len(posts)
order = sorted(posts, key=lambda p: p['when'])
for i, p in enumerate(order, 1): p['no'] = i
newest = sorted(order, key=lambda p: p['when'], reverse=True)
def when_label(s):
    d = datetime.datetime.fromisoformat(s)
    h = d.hour % 12 or 12
    return f"{d.strftime('%b')} {d.day} · {h} {'AM' if d.hour < 12 else 'PM'}"
first, last = order[0]['when'], order[-1]['when']
fd, ld = datetime.datetime.fromisoformat(first), datetime.datetime.fromisoformat(last)
span = f"{fd.strftime('%b')} {fd.day} – {ld.strftime('%b')} {ld.day}, {ld.year}"

# top binder copy for the archive
header = header.replace('<span>101 Cards</span>', f'<span>{n} posts</span>')
header = re.sub(r'<p>The trading card game news channel.*?</p>',
    '<p>The archive. Every clip Zia and Luna have posted, sleeved and numbered, newest first. Tap any card to flip it and play the story.</p>', header, flags=re.S)
header = header.replace('<a class="btn" href="#set" id="seeLatest">See the latest</a>', '<a class="btn" href="index.html">Back to the binder</a>')

e = html.escape
cards = []
for k, p in enumerate(newest):
    num = f"{p['no']:03d}"
    cls = 'tcg holo secret flip clipcard' if k == 0 else 'tcg flip clipcard'
    sym, rt = ('✦', 'Secret rare') if k == 0 else ('◆', 'Uncommon')
    symc = 'sec' if k == 0 else 'unc'
    c = p.get('clip')
    yt = p.get('yt')
    if yt and not c:
        art = f'<div class="art clip ytart" data-p="img/yt-{yt}.jpg"></div>'
        btn = f'<a class="snd ytwatch" href="https://www.youtube.com/shorts/{yt}" target="_blank" rel="noopener" aria-label="Watch {e(p["title"])} on YouTube">▶ Watch</a>'
    else:
        art = f'<div class="art clip" data-p="img/{c}.jpg"><video src="img/{c}-s.mp4" data-full="img/{c}.mp4" data-poster="img/{c}.jpg" muted loop playsinline preload="none"></video></div>'
        btn = '<button class="snd" type="button" aria-pressed="false" aria-label="Turn sound on">Sound off</button>'
    cards.append(f'''        <div class="pocket" data-host="{e(p['host'])}" data-game="{e(p['game'])}"><div class="{cls}" role="button" tabindex="0" aria-pressed="false" aria-label="Clip: {e(p['title'])}, {e(p['game'])}, post {num}. Tap to flip and play">
          <div class="inner">
            <div class="face back"><em>{num}/{n:03d}</em><span>Tap to flip</span></div>
            <div class="face front">
              <header class="nm"><h3>{e(p['title'])}</h3><span class="cost">{e(p['game'])}</span></header>
              {art}
              {btn}
              <div class="typeline"><span>Clip · {e(p['host'])} · {when_label(p['when'])}</span><i class="setsym {symc}" aria-hidden="true">{sym}</i></div>
              <div class="txt">
                <p>{e(p['blurb'])}</p>
                <p class="flav">{e(p.get('quip',''))}</p>
                <p class="src">Source: {e(p['source'])}</p>
              </div>
              <footer class="foot"><span>1CZ · Post {num}</span><span class="rar" title="{rt}">{sym}</span></footer>
            </div>
          </div>
          <div class="shine"></div><div class="glare"></div>
        </div></div>''')

hosts = sorted({p['host'] for p in posts}, key=lambda h: (h != 'Zia', h))
games = sorted({p['game'] for p in posts})
chips = ['<button type="button" class="chip mono" data-f="all" aria-pressed="true">All</button>']
chips += [f'<button type="button" class="chip mono" data-f="host:{e(h)}" aria-pressed="false">{e(h)}</button>' for h in hosts]
chips.append('<span class="chip-sep" aria-hidden="true"></span>')
chips += [f'<button type="button" class="chip mono" data-f="game:{e(g)}" aria-pressed="false">{e(g)}</button>' for g in games]

extra_css = '''<style>
.snd.ytwatch{text-decoration:none;display:inline-flex;align-items:center;gap:4px}
.art.ytart::after{content:"";position:absolute;top:0;bottom:0;left:50%;width:calc(62cqw * 9 / 16);transform:translateX(-50%);background:var(--p) center/cover no-repeat;z-index:1}
/* archive page */
.arch .pockets{grid-template-columns:repeat(auto-fill,minmax(210px,1fr))}
@media (max-width:900px){.arch .pockets{grid-template-columns:repeat(auto-fill,minmax(170px,1fr))}}
@media (max-width:560px){.arch .pockets{grid-template-columns:repeat(auto-fill,minmax(140px,1fr))}}
.arch .pocket[hidden]{display:none}
.chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;align-items:center;flex-basis:100%}
.chip{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#c9cfe4;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:999px;padding:8px 14px;cursor:pointer}
.chip:hover{border-color:rgba(233,196,106,.6)}
.chip[aria-pressed="true"]{background:var(--foil);border-color:var(--foil);color:var(--cover)}
.chip-sep{width:1px;height:20px;background:rgba(255,255,255,.18);margin:0 4px}
.btn.ghost{background:transparent;color:var(--foil);box-shadow:inset 0 0 0 1px rgba(233,196,106,.6)}
.arch-empty{grid-column:1/-1;text-align:center;color:#8c93ad;padding:40px 0}
</style>'''

body = f'''{header}

<main>
  <section class="wrap arch" id="set" aria-labelledby="set-h">
    <div class="sheet-head">
      <h2 id="set-h">Stories</h2>
      <p>Every news clip from the 8 AM and 8 PM drops, {n} so far ({span}). The rows fit your screen, so widen the window for more cards per row. Tap a card to flip it, then tap Sound to hear the story.</p>
      <div class="chips" role="group" aria-label="Filter posts">{"".join(chips)}</div>
      <div class="sheet-tools">
        <a class="btn ghost" href="index.html">Back to the binder</a>
        <button class="btn" id="flipAll" type="button" aria-pressed="false">Flip all cards</button>
      </div>
    </div>
    <div class="page">
      <div class="pockets" id="archGrid">
{chr(10).join(cards)}
        <p class="arch-empty mono" id="archEmpty" hidden>No posts match this filter yet.</p>
      </div>
      <div class="sheet-foot mono"><span>Archive · newest first</span><span id="archCount">Set 1CZ · posts 001–{n:03d}</span></div>
    </div>
  </section>
</main>

{footer}
'''

js = r'''<script>
(function(){
  const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.tcg').forEach(card=>{
    card.addEventListener('pointermove',e=>{if(reduce)return;
      const r=card.getBoundingClientRect(),px=(e.clientX-r.left)/r.width,py=(e.clientY-r.top)/r.height;
      card.style.setProperty('--mx',px*100+'%');card.style.setProperty('--my',py*100+'%');
      card.style.setProperty('--rx',((.5-py)*16).toFixed(2)+'deg');card.style.setProperty('--ry',((px-.5)*20).toFixed(2)+'deg');card.style.setProperty('--o','1')});
    card.addEventListener('pointerleave',()=>{['--mx','--my'].forEach(k=>card.style.setProperty(k,'50%'));
      card.style.setProperty('--rx','0deg');card.style.setProperty('--ry','0deg');card.style.setProperty('--o','0')});
  });
  document.querySelectorAll('.cover').forEach(cov=>{const ch=cov.querySelector('.cover-holo');if(reduce||!ch)return;
    cov.addEventListener('pointermove',e=>{const r=cov.getBoundingClientRect();cov.classList.add('hover');
      ch.style.setProperty('--hx',((e.clientX-r.left)/r.width*100).toFixed(1)+'%');ch.style.setProperty('--hy',((e.clientY-r.top)/r.height*100).toFixed(1)+'%')});
    cov.addEventListener('pointerleave',()=>{cov.classList.remove('hover');ch.style.removeProperty('--hx');ch.style.removeProperty('--hy')})});

  /* flip */
  const flips=[...document.querySelectorAll('.pockets .flip')],all=document.getElementById('flipAll');
  const shownFlips=()=>flips.filter(f=>!f.closest('.pocket').hidden);
  const setF=(el,on)=>el.setAttribute('aria-pressed',on?'true':'false');
  const sync=()=>{const s=shownFlips(),up=s.length&&s.every(f=>f.getAttribute('aria-pressed')==='true');all.textContent=up?'Turn all face down':'Flip all cards';all.setAttribute('aria-pressed',up?'true':'false')};
  flips.forEach(f=>{f.addEventListener('click',()=>{setF(f,f.getAttribute('aria-pressed')!=='true');sync()});
    f.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();f.click()}})});
  all.addEventListener('click',()=>{const on=all.getAttribute('aria-pressed')!=='true',s=shownFlips();
    s.forEach((f,i)=>setTimeout(()=>{setF(f,on);if(i===s.length-1)sync()},reduce?0:i*90))});

  /* filters */
  const chips=[...document.querySelectorAll('.chip')],empty=document.getElementById('archEmpty'),cnt=document.getElementById('archCount'),total=flips.length;
  chips.forEach(c=>c.addEventListener('click',()=>{chips.forEach(x=>x.setAttribute('aria-pressed',String(x===c)));
    const [k,v]=c.dataset.f.split(':');let shown=0;
    document.querySelectorAll('.pockets .pocket').forEach(p=>{const ok=k==='all'||p.dataset[k]===v;p.hidden=!ok;if(ok)shown++});
    empty.hidden=shown>0;cnt.textContent=k==='all'?'Set 1CZ · posts 001–'+String(total).padStart(3,'0'):shown+' of '+total+' posts · '+v;sync();schedule()}));

  /* videos: face-up cards on screen play, at most 3 at once */
  const MAXPLAY=3,vis=new Set();let raf=0;
  function schedule(){if(!raf)raf=requestAnimationFrame(()=>{raf=0;update()})}
  function update(){const mid=innerHeight/2;
    const cand=flips.filter(c=>vis.has(c)&&!c.closest('.pocket').hidden&&c.getAttribute('aria-pressed')==='true'&&!reduce)
      .map(c=>{const r=c.getBoundingClientRect();return{c,d:Math.abs(r.top+r.height/2-mid)+(c.querySelector('.snd[aria-pressed="true"]')?-1e5:0)}})
      .sort((a,b)=>a.d-b.d).slice(0,MAXPLAY).map(o=>o.c);
    flips.forEach(c=>{const v=c.querySelector('video');if(!v)return;if(cand.includes(c)){if(v.paused){const pr=v.play();if(pr)pr.catch(()=>{})}}else if(!v.paused)v.pause()})}
  const io=new IntersectionObserver(es=>{es.forEach(e=>e.isIntersecting?vis.add(e.target):vis.delete(e.target));schedule()},{threshold:.35});
  flips.forEach(c=>{io.observe(c);new MutationObserver(schedule).observe(c,{attributes:true,attributeFilter:['aria-pressed']})});
  addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);
  function setSound(c,on){const b=c.querySelector('.snd'),v=c.querySelector('video');
    if(on&&v.dataset.full&&!v.src.endsWith(v.dataset.full)){const t=v.currentTime;v.src=v.dataset.full;v.addEventListener('loadedmetadata',()=>{try{v.currentTime=t}catch(e){}},{once:true})}
    v.muted=!on;b.setAttribute('aria-pressed',String(on));b.textContent=on?'Sound on':'Sound off';b.setAttribute('aria-label',on?'Turn sound off':'Turn sound on')}
  flips.forEach(c=>{const b=c.querySelector('.snd');
    if(!c.querySelector('video')){b.addEventListener('click',e=>e.stopPropagation());b.addEventListener('keydown',e=>e.stopPropagation());return}
    b.addEventListener('click',e=>{e.stopPropagation();const on=b.getAttribute('aria-pressed')!=='true';
      flips.forEach(o=>{if(o!==c&&o.querySelector('video')&&o.querySelector('.snd').getAttribute('aria-pressed')==='true')setSound(o,false)});
      setSound(c,on);if(on&&c.getAttribute('aria-pressed')!=='true')c.setAttribute('aria-pressed','true');schedule();
      if(on){const pr=c.querySelector('video').play();if(pr)pr.catch(()=>{})}});
    b.addEventListener('keydown',e=>e.stopPropagation())});
  function hydrate(c){const v=c.querySelector('video[data-poster]');if(v&&!v.poster)v.poster=v.dataset.poster;
    const a=c.querySelector('.art[data-p]');if(a&&!a.style.getPropertyValue('--p'))a.style.setProperty('--p','url('+a.dataset.p+')')}
  flips.forEach(c=>new MutationObserver(()=>{if(c.getAttribute('aria-pressed')==='true')hydrate(c)}).observe(c,{attributes:true,attributeFilter:['aria-pressed']}));

  /* binder videos: top first, bottom last */
  (function(){const v=document.querySelector('video.top-cover');if(!v)return;v.src=v.dataset.src;if(!reduce){v.autoplay=true;const pr=v.play();if(pr)pr.catch(()=>{})}})();
  document.querySelectorAll('video.lazy-cover').forEach(v=>{
    const go=()=>{if(v.dataset.loaded)return;v.dataset.loaded=1;v.poster=v.dataset.poster;v.src=v.dataset.src;if(!reduce){v.autoplay=true;const pr=v.play();if(pr)pr.catch(()=>{})}};
    const later=()=>{const idle=window.requestIdleCallback||(f=>setTimeout(f,1500));idle(go,{timeout:4000})};
    if(document.readyState==='complete')later();else addEventListener('load',later,{once:true})});

  /* barcode */
  const bc=document.getElementById('barcode');let seed=1209;
  for(let i=0;i<46;i++){seed=(seed*9301+49297)%233280;const w=1+Math.floor(seed/233280*3.5);const el=document.createElement('i');el.style.width=w+'px';el.style.marginRight=(i%3?1:2)+'px';bc.appendChild(el)}

  /* next drop + top card */
  const p2=n=>String(n).padStart(2,'0');
  const HOSTS={zia:{name:'Zia',time:'8:00 AM',img:'img/zia.webp',pos:'50% 14%',edition:'Reporter · Special edition',line:'“Zia here!”'},
               luna:{name:'Luna',time:'8:00 PM',img:'img/luna.webp',pos:'50% 12%',edition:'Librarian · Limited edition',line:'“Luna here!”'}};
  let shown=null;
  function next(now){const d=new Date(now);d.setUTCMinutes(0,0,0);
    if(d.getUTCHours()<12){d.setUTCHours(12);return{at:d,host:'Luna · 8 PM',who:'luna'}}
    d.setUTCHours(24);return{at:d,host:'Zia · 8 AM',who:'zia'}}
  function clock(){const n=next(Date.now()),t=Math.max(0,Math.floor((n.at-Date.now())/1000));
    const txt=`${p2(Math.floor(t/3600))}:${p2(Math.floor(t/60)%60)}:${p2(t%60)}`;
    document.getElementById('coverCount').textContent=txt;document.getElementById('coverWho').textContent=n.host;document.getElementById('ncCount').textContent=txt;
    if(n.who!==shown){shown=n.who;const h=HOSTS[n.who];
      document.getElementById('ncName').textContent=h.name;const nt=document.getElementById('ncTime');nt.textContent=h.time;nt.dataset.g=h.time.endsWith('AM')?'☀':'☾';
      const im=document.getElementById('ncImg');im.src=h.img;im.alt=h.name+', the next host';im.style.objectPosition=h.pos;
      document.getElementById('ncEdition').textContent=h.edition;document.getElementById('ncLine').textContent=h.line;
      document.getElementById('coverCard').setAttribute('aria-label',`Up next: ${h.name} at ${h.time} Hong Kong time. Tap to flip back`)}}
  const cc=document.getElementById('coverCard'),cw=document.getElementById('coverWin');
  if(!reduce){cw.addEventListener('pointermove',e=>{const r=cw.getBoundingClientRect(),px=(e.clientX-r.left)/r.width,py=(e.clientY-r.top)/r.height;
      cw.style.setProperty('--mx',px*100+'%');cw.style.setProperty('--my',py*100+'%');
      cw.style.setProperty('--rx',((.5-py)*16).toFixed(2)+'deg');cw.style.setProperty('--ry',((px-.5)*20).toFixed(2)+'deg');cw.style.setProperty('--o','1')});
    cw.addEventListener('pointerleave',()=>{['--mx','--my'].forEach(k=>cw.style.setProperty(k,'50%'));cw.style.setProperty('--rx','0deg');cw.style.setProperty('--ry','0deg');cw.style.setProperty('--o','0')})}
  /* two-step flip (turn to edge, swap sides, turn back): no 3D back-faces, so Safari draws it cleanly */
  let ccBusy=false;const FAN=420;
  function doFlip(to,done){const set=()=>{cc.setAttribute('aria-pressed',String(to));cc.dataset.face=to?'front':'back'};
    if(reduce){set();done&&done();return}
    cc.style.transition='transform .26s cubic-bezier(.5,0,.9,.6)';cc.style.transform='perspective(900px) rotateY(90deg)';
    setTimeout(()=>{set();cc.style.transition='none';cc.style.transform='perspective(900px) rotateY(-90deg)';void cc.offsetWidth;
      cc.style.transition='transform .4s cubic-bezier(.15,.6,.3,1)';cc.style.transform='perspective(900px) rotateY(0deg)';
      setTimeout(()=>{done&&done()},410)},260)}
  /* fan on hover (mouse) or on tap, flip after the fan */
  let hov=false;const canHover=matchMedia('(hover: hover)').matches;
  if(canHover){cw.addEventListener('pointerenter',()=>{hov=true;cw.classList.add('fanned')});
    cw.addEventListener('pointerleave',()=>{hov=false;if(!ccBusy&&cc.getAttribute('aria-pressed')!=='true')cw.classList.remove('fanned')})}
  cc.addEventListener('click',()=>{if(ccBusy)return;ccBusy=true;const to=cc.getAttribute('aria-pressed')!=='true';
    if(to){const wait=(cw.classList.contains('fanned')||reduce)?0:FAN;cw.classList.add('fanned');setTimeout(()=>doFlip(true,()=>{ccBusy=false}),wait)}
    else{doFlip(false,()=>{if(!hov)cw.classList.remove('fanned');setTimeout(()=>{ccBusy=false;if(!hov)cw.classList.remove('fanned')},reduce?0:FAN)})}});
  cc.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();cc.click()}});
  clock();setInterval(clock,1000);
})();
</script>'''

out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + head + style + '\n' + extra_css + '\n</head>\n<body>\n' + body + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
(root/'archive.html').write_text(out)
print('archive.html', len(out), 'bytes,', n, 'posts')
