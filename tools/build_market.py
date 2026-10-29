#!/usr/bin/env python3
"""Build market.html (the Market page) from index.html's styles and binders + data/market.json.
Run after build_archive.py (it reuses archive.html's binder script)."""
import json, re, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root/'index.html').read_text()
arch = (root/'archive.html').read_text()
data = json.loads((root/'data'/'market.json').read_text())

head = src[:src.index('<style>')]
head = re.sub(r'<title>.*?</title>', '<title>1 Cardz Market</title>', head)
head = re.sub(r'<link rel="preload"[^>]*>\n', '', head)
head = head.replace('href="https://1cardz.news/"', 'href="https://1cardz.news/market.html"')
head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="Market Watch: daily trading card market prices for sealed product and chase singles across seven games.">', head)
style = src[src.index('<style>'):src.index('</style>')+len('</style>')]
hs = src.index('<header class="wrap cover-zone">'); header = src[hs:src.index('\n</header>', hs)+len('\n</header>')]
fs = src.index('<footer class="wrap">'); footer = src[fs:src.index('\n</footer>', fs)+len('\n</footer>')]
scrolltop = src[src.index('<script>'):src.index('</script>')+len('</script>')]
header = re.sub(r'<p>The trading card game news channel.*?</p>',
    '<p>Market Watch. Daily market prices for sealed product and chase singles from the newest sets across seven games.</p>', header, flags=re.S)
header = header.replace('<a class="btn" href="#set" id="seeLatest">See the latest</a>', '<a class="btn" href="index.html">Back to the binder</a>')

# cover behaviour (videos, barcode, clock, fan + flip) reused from the archive page script
a_js = arch[arch.rindex('<script>'):]
cover_js = a_js[a_js.index('  /* binder videos: top first, bottom last */'):a_js.rindex('})();')]

pool = data.get('pool') or data['items']
games = sorted({i['game'] for i in pool})

extra_css = '''<style>
/* market page */
.mkt .sheet-head p{max-width:60ch}
.mkt .chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;align-items:center;flex-basis:100%}
.chip{font-family:var(--f-mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#c9cfe4;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:999px;padding:8px 14px;cursor:pointer}
.chip:hover{border-color:rgba(233,196,106,.6)}
.chip[aria-pressed="true"]{background:var(--foil);border-color:var(--foil);color:var(--cover)}
.chip-sep{width:1px;height:20px;background:rgba(255,255,255,.18);margin:0 4px}
.btn.ghost{background:transparent;color:var(--foil);box-shadow:inset 0 0 0 1px rgba(233,196,106,.6)}
.mkt .gd.mw{margin-top:8px}
@media (min-width:1100px){
  .mkt .mw-list{display:grid;grid-template-columns:1fr 1fr;column-gap:0}
  .mkt .mw-list .mw-row:nth-child(odd){border-right:1px solid rgba(255,255,255,.06)}
  .mkt .mw-head{grid-template-columns:minmax(0,1.3fr) minmax(0,1.6fr) 110px minmax(0,1.3fr) minmax(0,1.6fr) 110px}
}
.mkt-count{color:#8c93ad}
.mw-head-2{display:none}
@media (min-width:1100px){.mkt .mw-head-2{display:block}}
/* Market box: arcade cabinet style (neon bezel + blurred studio + scanlines) */
.mkt .gd.mw.mkt-arcade{border:0 !important;border-radius:20px !important;overflow:hidden;background:#0b0912;backdrop-filter:none;-webkit-backdrop-filter:none;
  box-shadow:0 0 0 10px #0d0b16,0 0 0 13px #2a2340,0 0 24px 13px rgba(255,62,165,.35) !important;margin-top:22px}
.mkt-arcade::before,.mkt-arcade::after{display:none !important}
.mkt-arcade .mkt-bg,.mkt-arcade .mkt-fx{position:absolute;inset:0;pointer-events:none;border-radius:inherit}
.mkt-arcade .mkt-bg{z-index:0;background:url(img/cover-poster.jpg) center/cover;filter:blur(10px) saturate(1.3) brightness(.38);transform:scale(1.1)}
.mkt-arcade .mkt-fx{z-index:5;box-shadow:inset 0 0 0 2px #ff3ea5,inset 0 0 22px rgba(255,62,165,.55);background:repeating-linear-gradient(0deg,rgba(0,0,0,.18) 0 1px,transparent 1px 3px)}
.mkt-arcade>*:not(.mkt-bg):not(.mkt-fx){position:relative;z-index:4}
.mkt-arcade .mw-label{font-family:"Press Start 2P",var(--f-mono);font-size:9px;letter-spacing:.06em;color:#ff8ad8;text-shadow:0 0 8px #ff3ea5}
.mkt-arcade .mw-label i{background:#ff3ea5;box-shadow:0 0 10px #ff3ea5}
.mkt-arcade .mw-row{border-top-color:rgba(255,62,165,.12)}
@media (max-width:560px){.mkt .gd.mw.mkt-arcade{box-shadow:0 0 0 7px #0d0b16,0 0 0 9px #2a2340,0 0 18px 9px rgba(255,62,165,.35) !important}}
</style>'''

chips = ['<button type="button" class="chip" data-k="all" aria-pressed="true">All</button>',
         '<button type="button" class="chip" data-k="sealed" aria-pressed="false">Sealed</button>',
         '<button type="button" class="chip" data-k="single" aria-pressed="false">Chase singles</button>',
         '<span class="chip-sep" aria-hidden="true"></span>',
         '<button type="button" class="chip" data-g="all" aria-pressed="true">Every game</button>']
chips += [f'<button type="button" class="chip" data-g="{g}" aria-pressed="false">{g}</button>' for g in games]

body = f'''{header}

<main>
  <section class="wrap mkt" aria-labelledby="mkt-h">
    <div class="sheet-head">
      <h2 id="mkt-h">Market Watch</h2>
      <p>Fifteen picks from the newest sets across seven games, sealed products and chase singles at today's market price (recent sold average, USD). Prices refresh every day and the picks rotate daily.</p>
      <div class="chips" role="group" aria-label="Filter the list">{"".join(chips)}</div>
      <div class="sheet-tools"><a class="btn ghost" href="index.html">Back to the binder</a><a class="btn ghost" href="archive.html">Stories</a></div>
    </div>
    <div class="gd mw mkt-arcade">
      <div class="mkt-bg" aria-hidden="true"></div><div class="mkt-fx" aria-hidden="true"></div>
      <div class="mw-top">
        <span class="mono mw-label"><i></i><span>Market Watch</span></span>
        <span class="mono mkt-count" id="mktCount">—</span>
        <span class="mono mw-upd" id="mwUpd">—</span>
      </div>
      <div class="mw-head mono" aria-hidden="true"><span>Item</span><span>Market price</span><span>Trend</span><span class="mw-head-2">Item</span><span class="mw-head-2">Market price</span><span class="mw-head-2">Trend</span></div>
      <ol class="mw-list" id="mwList"></ol>
      <p class="mw-foot">Market price is the recent sold average in US dollars, refreshed daily. Prices move fast; this is a snapshot, not buying or selling advice.</p>
    </div>
  </section>
</main>

{footer}
'''

snap = json.dumps({"updated": data['updated'], "pool": pool}, ensure_ascii=False)
js = r'''<script>
(function(){
  const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.cover').forEach(cov=>{const ch=cov.querySelector('.cover-holo');if(reduce||!ch)return;
    cov.addEventListener('pointermove',e=>{const r=cov.getBoundingClientRect();cov.classList.add('hover');
      ch.style.setProperty('--hx',((e.clientX-r.left)/r.width*100).toFixed(1)+'%');ch.style.setProperty('--hy',((e.clientY-r.top)/r.height*100).toFixed(1)+'%')});
    cov.addEventListener('pointerleave',()=>{cov.classList.remove('hover');ch.style.removeProperty('--hx');ch.style.removeProperty('--hy')})});

  /* Market Watch: full list, embedded snapshot first, then the daily data file */
  const SNAP=__SNAP__;
  let data=SNAP,kind='all',game='all';
  const list=document.getElementById('mwList'),upd=document.getElementById('mwUpd'),cnt=document.getElementById('mktCount');
  const usd=v=>v==null?'—':'$'+v.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  const fmtDate=s=>{const d=new Date(String(s).slice(0,10)+'T12:00:00Z');return isNaN(d)?s:d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'})};
  function spark(h){
    if(!h||h.length<2)return '<svg viewBox="0 0 96 26" aria-hidden="true"><line x1="2" y1="13" x2="94" y2="13" stroke="rgba(255,255,255,.25)" stroke-width="2" stroke-dasharray="3 4"/></svg>';
    const v=h.map(x=>x[1]),mn=Math.min(...v),mx=Math.max(...v),r=mx-mn||1;
    const pts=v.map((y,i)=>[2+i*(92/(v.length-1)),22-((y-mn)/r)*18]);
    const up=v[v.length-1]>=v[0],c=up?'#5be39b':'#ff7a8a',l=pts[pts.length-1];
    return '<svg viewBox="0 0 96 26" aria-hidden="true"><polyline fill="none" stroke="'+c+'" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" points="'+pts.map(p=>p.map(n=>n.toFixed(1)).join(',')).join(' ')+'"/><circle cx="'+l[0].toFixed(1)+'" cy="'+l[1].toFixed(1)+'" r="3" fill="'+c+'"/></svg>';
  }
  function chg(h){
    if(!h||h.length<2)return '<span class="mw-chg new">trend from '+(h&&h[0]?fmtDate(h[0][0]).replace(/, \d{4}$/,''):'today')+'</span>';
    const a=h[0][1],b=h[h.length-1][1],p=(b-a)/a*100,cls=Math.abs(p)<0.05?'flat':p>0?'up':'down',ar=cls==='up'?'▲':cls==='down'?'▼':'■';
    return '<span class="mw-chg '+cls+'">'+ar+' '+Math.abs(p).toFixed(1)+'% · '+h.length+'d</span>';
  }
  /* 15 picks, rotated daily (Hong Kong date): round-robin across games, each game's list shifted by the day */
  const SHOW=15;
  function pick(F){const day=Math.floor((Date.now()+8*3600e3)/864e5),by={};F.forEach(i=>(by[i.game]=by[i.game]||[]).push(i));
    const gs=Object.keys(by).sort();gs.forEach((g,k)=>{const a=by[g].sort((x,y)=>y.price-x.price),o=(day+k)%a.length;by[g]=a.slice(o).concat(a.slice(0,o))});
    const n=Math.min(SHOW,F.length),out=[];for(let r=0;out.length<n;r++){for(let k=0;k<gs.length&&out.length<n;k++){const g=gs[(k+day)%gs.length];if(by[g][r])out.push(by[g][r])}}
    return out}
  function render(){
    const all=(data.pool||data.items||[]).filter(i=>i.price!=null);
    const pool=all.filter(i=>(kind==='all'||i.kind===kind)&&(game==='all'||i.game===game));
    const items=pick(pool).sort((a,b)=>b.price-a.price);
    const max=Math.max(1,...items.map(i=>i.price));
    list.innerHTML=items.length?items.map(i=>'<li class="mw-row" tabindex="0" data-tip="'+(i.name+' · '+i.set).replace(/"/g,'&quot;')+'|'+usd(i.price)+'|'+usd(i.low)+'">'+
      '<div class="mw-name"><span class="mw-title">'+i.name+'</span><div class="mw-meta"><span class="mw-game">'+i.game+'</span><span>'+i.set+(i.kind==='sealed'?' · sealed':'')+'</span></div></div>'+
      '<div class="mw-bar"><div class="mw-track"><div class="mw-fill" style="width:0%" data-w="'+Math.max(2,i.price/max*100).toFixed(1)+'"></div></div><span class="mw-price">'+usd(i.price)+'</span></div>'+
      '<div class="mw-trend">'+spark(i.history)+chg(i.history)+'</div></li>').join(''):'<li class="mw-row"><div class="mw-name"><span class="mw-title">Nothing in this filter today.</span></div></li>';
    requestAnimationFrame(()=>list.querySelectorAll('.mw-fill').forEach(f=>f.style.width=f.dataset.w+'%'));
    upd.textContent='Prices as of '+fmtDate(data.updated);
    cnt.textContent=items.length+' picks today · rotates daily';
  }
  const chips=[...document.querySelectorAll('.chip')];
  chips.forEach(c=>c.addEventListener('click',()=>{
    if(c.dataset.k){kind=c.dataset.k;chips.filter(x=>x.dataset.k).forEach(x=>x.setAttribute('aria-pressed',String(x===c)))}
    else{game=c.dataset.g;chips.filter(x=>x.dataset.g).forEach(x=>x.setAttribute('aria-pressed',String(x===c)))}
    render()}));
  const tip=document.createElement('div');tip.className='mw-tip';tip.hidden=true;document.querySelector('.mw').appendChild(tip);
  list.addEventListener('pointermove',e=>{const r=e.target.closest('.mw-row');if(!r||!r.dataset.tip){tip.hidden=true;return}
    const [n,p,l]=r.dataset.tip.split('|');tip.innerHTML='<b>'+n+'</b><br>Market '+p+' · Lowest listing '+l;tip.hidden=false;
    const box=document.querySelector('.mw').getBoundingClientRect();let x=e.clientX-box.left+14,y=e.clientY-box.top+14;
    x=Math.min(x,box.width-tip.offsetWidth-8);tip.style.left=x+'px';tip.style.top=y+'px'});
  list.addEventListener('pointerleave',()=>tip.hidden=true);
  render();
  fetch('data/market.json?v='+Date.now()).then(r=>r.ok?r.json():null).then(d=>{if(d&&(d.pool||d.items)){data=d;render()}}).catch(()=>{});

__COVER__})();
</script>'''.replace('__SNAP__', snap).replace('__COVER__', cover_js)

out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + head + style + '\n' + extra_css + '\n</head>\n<body>\n' + body + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
(root/'market.html').write_text(out)
print('market.html', len(out), 'bytes,', len(pool), 'items')
