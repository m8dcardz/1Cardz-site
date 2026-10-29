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
header = header.replace('<a class="btn" href="#set">Open the binder</a>', '<a class="btn" href="index.html">Back to the binder</a>')

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
.mkt-count{color:#8c93ad}
/* market card grid: each item is a glass tile in the Market box style */
.mkt-grid{list-style:none;margin:0;padding:clamp(14px,2vw,22px);display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;position:relative;z-index:4}
.mkt-tile{position:relative;border-radius:14px;padding:16px 16px 14px;display:flex;flex-direction:column;gap:8px;min-width:0;overflow:hidden;
  background:linear-gradient(160deg,rgba(255,255,255,.09),rgba(255,255,255,.025));box-shadow:inset 0 0 0 1px rgba(255,255,255,.13),0 14px 30px rgba(0,0,0,.3);
  transition:transform .2s,box-shadow .2s}
.mkt-tile::before{content:"";position:absolute;left:0;top:0;right:0;height:3px;background:var(--c,#7cf3ff);opacity:.9}
.mkt-tile:hover{transform:translateY(-3px);box-shadow:inset 0 0 0 1px rgba(255,255,255,.22),0 20px 38px rgba(0,0,0,.42)}
.mkt-tile .t-top{display:flex;justify-content:space-between;align-items:center;gap:8px}
.mkt-tile .t-kind{font-family:var(--f-mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:#8c93ad}
.mkt-tile .t-name{color:#fff;font-weight:700;font-size:16px;line-height:1.25;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.5em}
.mkt-tile .t-set{color:#aab1c9;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mkt-tile .t-price{font-family:"Oxanium",var(--f-display);font-weight:700;font-size:28px;line-height:1;color:#fff;font-variant-numeric:tabular-nums;margin-top:2px}
.mkt-tile .mw-track{height:8px;flex:none}
.mkt-tile .t-trend{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:2px}
.mkt-tile .t-trend svg{width:96px;height:26px;flex:none}
.mkt-tile .t-low{font-size:12px;color:#8c93ad}
.mkt-empty{grid-column:1/-1;color:#8c93ad;text-align:center;padding:30px 0}
@media (max-width:560px){.mkt-grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;padding:12px}.mkt-tile{padding:12px 12px 10px}.mkt-tile .t-price{font-size:22px}.mkt-tile .t-name{font-size:14px}.mkt-tile .t-trend svg{width:52px}.mkt-tile .t-kind{font-size:9px;letter-spacing:.06em;white-space:nowrap}.mkt-tile .mw-chg{font-size:10.5px;white-space:nowrap}.mkt-tile .mw-game{font-size:9.5px;padding:2px 6px}.mkt-tile .t-trend{gap:6px}}
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
      <p>The newest sets across seven games: their top sealed products and the chase singles worth $20 or more, at today's market price (recent sold average, USD), refreshed every day.</p>
      <div class="chips" role="group" aria-label="Filter the list">{"".join(chips)}</div>
      <div class="sheet-tools"><a class="btn ghost" href="index.html">Back to the binder</a><a class="btn ghost" href="archive.html">Stories</a></div>
    </div>
    <div class="gd mw">
      <div class="mw-top">
        <span class="mono mw-label"><i></i><span>Market Watch</span></span>
        <span class="mono mkt-count" id="mktCount">—</span>
        <span class="mono mw-upd" id="mwUpd">—</span>
      </div>
      <ol class="mkt-grid" id="mwList"></ol>
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
  function render(){
    const all=(data.pool||data.items||[]).filter(i=>i.price!=null);
    const items=all.filter(i=>(kind==='all'||i.kind===kind)&&(game==='all'||i.game===game)).sort((a,b)=>b.price-a.price);
    const max=Math.max(1,...items.map(i=>i.price));
    const GC={"Pokémon":"#ffd23f","Magic":"#ff8a5c","One Piece":"#ff5c7a","Lorcana":"#9d8cff","Yu-Gi-Oh!":"#c58cff","Riftbound":"#5ce1ff","Gundam":"#9fe870"};
    list.innerHTML=items.length?items.map(i=>'<li class="mkt-tile" tabindex="0" style="--c:'+(GC[i.game]||'#7cf3ff')+'">'+
      '<div class="t-top"><span class="mw-game">'+i.game+'</span><span class="t-kind">'+(i.kind==='sealed'?'Sealed':'Chase single')+'</span></div>'+
      '<div class="t-name" title="'+i.name.replace(/"/g,'&quot;')+'">'+i.name+'</div><div class="t-set">'+i.set+'</div>'+
      '<div class="t-price">'+usd(i.price)+'</div>'+
      '<div class="mw-track"><div class="mw-fill" style="width:0%" data-w="'+Math.max(2,i.price/max*100).toFixed(1)+'"></div></div>'+
      '<div class="t-trend">'+spark(i.history)+chg(i.history)+'</div>'+
      '<div class="t-low">Lowest listing '+usd(i.low)+'</div></li>').join(''):'<li class="mkt-empty">Nothing in this filter today.</li>';
    requestAnimationFrame(()=>list.querySelectorAll('.mw-fill').forEach(f=>f.style.width=f.dataset.w+'%'));
    upd.textContent='Prices as of '+fmtDate(data.updated);
    cnt.textContent=items.length+' of '+all.length+' items';
  }
  const chips=[...document.querySelectorAll('.chip')];
  chips.forEach(c=>c.addEventListener('click',()=>{
    if(c.dataset.k){kind=c.dataset.k;chips.filter(x=>x.dataset.k).forEach(x=>x.setAttribute('aria-pressed',String(x===c)))}
    else{game=c.dataset.g;chips.filter(x=>x.dataset.g).forEach(x=>x.setAttribute('aria-pressed',String(x===c)))}
    render()}));
  render();
  fetch('data/market.json?v='+Date.now()).then(r=>r.ok?r.json():null).then(d=>{if(d&&(d.pool||d.items)){data=d;render()}}).catch(()=>{});

__COVER__})();
</script>'''.replace('__SNAP__', snap).replace('__COVER__', cover_js)

out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + head + style + '\n' + extra_css + '\n</head>\n<body>\n' + body + '\n' + scrolltop + '\n' + js + '\n</body>\n</html>\n')
(root/'market.html').write_text(out)
print('market.html', len(out), 'bytes,', len(pool), 'items')
