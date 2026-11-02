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



BOARD_API = 'https://1cardz-signup.m8dcardz.workers.dev/board'
TURNSTILE_SITEKEY = ''  # public site key of the Turnstile widget; empty = no bot-check widget

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
/* live board (Nov 2) */
.board-tabs{display:flex;justify-content:center;gap:10px;margin:-6px 0 14px}
.board-tabs button{font:inherit;font-family:"Press Start 2P",ui-monospace,monospace;font-size:9px;letter-spacing:.1em;color:#8a90b8;background:none;border:1px solid #2b3f80;border-radius:6px;padding:7px 10px;cursor:pointer}
.board-tabs button[aria-pressed="true"]{color:#05040b;background:#7cf3ff;border-color:#7cf3ff;box-shadow:0 0 10px rgba(124,243,255,.6)}
.board li{grid-template-columns:4.4em 4.4em minmax(0,1fr) 7.6em 2.2em}
.board .lk{font:inherit;color:inherit;background:none;border:1px solid currentColor;border-radius:5px;padding:2px 0;cursor:pointer;opacity:.75;line-height:1.4}
.board .lk:hover,.board .lk.on{opacity:1;box-shadow:0 0 8px currentColor}
.board .lk.on{background:rgba(255,255,255,.12)}
.board .msg{white-space:normal;overflow-wrap:anywhere}
.board li.r8{color:#ff8ad8;text-shadow:0 0 8px rgba(255,138,216,.6)}.board li.r9{color:#fff;text-shadow:0 0 8px rgba(255,255,255,.5)}.board li.r10{color:#ffd23f;text-shadow:0 0 8px rgba(255,210,63,.5)}
.board.live .board-foot .soon,.board.live .board-foot .ins,.board.live .board-foot .ini{display:none}
.coin{display:none;justify-self:center;font:inherit;font-family:"Press Start 2P",ui-monospace,monospace;font-size:clamp(10px,1.3vw,13px);letter-spacing:.1em;color:#05040b;background:#ffd23f;border:0;border-radius:8px;padding:12px 16px;cursor:pointer;box-shadow:inset 0 -3px 0 rgba(0,0,0,.25),0 0 14px rgba(255,210,63,.55)}
.board.live .coin{display:inline-block}
.coin:active{transform:translateY(2px)}
.mb-form{display:none;margin-top:14px;text-align:left;font-family:"Press Start 2P",ui-monospace,monospace;font-size:clamp(9px,1.2vw,11px);color:#cfd4e6;gap:12px}
.mb-form.open{display:grid}
.mb-form label{display:grid;gap:8px;letter-spacing:.08em}
.mb-ini{display:flex;gap:8px}
.mb-ini input,.mb-form .mb-msg{font:inherit;font-family:"Press Start 2P",ui-monospace,monospace;text-transform:uppercase;color:#7cf3ff;background:#0a0f1c;border:1px solid #2b3f80;border-radius:6px;outline:none}
.mb-ini input{width:2.6em;height:2.6em;text-align:center;font-size:14px;padding:0}
.mb-form .mb-msg{width:100%;padding:12px 10px;font-size:11px}
.mb-ini input:focus,.mb-form .mb-msg:focus{border-color:#7cf3ff;box-shadow:0 0 10px rgba(124,243,255,.5)}
.mb-hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
.mb-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.mb-row .coin{display:inline-block}
.mb-cancel{font:inherit;font-family:"Press Start 2P",ui-monospace,monospace;font-size:10px;color:#8a90b8;background:none;border:0;cursor:pointer;padding:10px 6px}
.mb-note{font-size:.85em;color:#8a90b8;line-height:1.7;margin:0}
.mb-stat{min-height:1.4em;margin:0;color:#ffd23f;line-height:1.6}
.mb-admin{display:none;position:relative;z-index:2;max-width:760px;margin:22px auto 0;padding:16px;border-radius:12px;background:#05040b;border:1px dashed #ff8ad8;color:#e8ecf8;font-size:14px}
.mb-admin.on{display:block}
.mb-admin h4{margin:0 0 10px;font-family:"Press Start 2P",ui-monospace,monospace;font-size:11px;color:#ff8ad8}
.mb-admin input{font:inherit;padding:8px 10px;border-radius:6px;border:1px solid #2b3f80;background:#0a0f1c;color:#fff}
.mb-admin ul{list-style:none;padding:0;margin:12px 0 0;display:grid;gap:8px}
.mb-admin li{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px;border-radius:8px;background:rgba(255,255,255,.05)}
.mb-admin li span{flex:1 1 200px}
.mb-admin button{font:inherit;font-size:13px;padding:6px 10px;border-radius:6px;border:0;cursor:pointer;background:#58f08a;color:#05040b}
.mb-admin button.hide{background:#ff3b5c;color:#fff}
@media (max-width:760px){.board li{grid-template-columns:4.3em 4.3em minmax(0,1fr) 2.4em}}
</style>"""

header = header + '\n\n' + site_parts.navbar(src, 'board.html')
footer = site_parts.newsletter_section(src) + '\n' + footer + '\n\n' + site_parts.newsletter_script(src)
body = f"""{header}

<main>
  <section class="wrap mbp" aria-labelledby="mb-h">
    <div class="sheet-head">
      <h2 id="mb-h">Message Board</h2>
      <p>The arcade hall of fame. Post your best pulls, hot takes and shout-outs to Zia and Luna, and give your favourite posts a point.</p>
    </div>
    <div class="hall">
      <p class="hall-marquee">1CARDZ HALL OF FAME<small>MESSAGE BOARD</small></p>
      <div class="hall-row">
        <span class="cab" aria-hidden="true"></span>
        <div class="board" id="mbBoard" data-api="{e(BOARD_API)}" data-sitekey="{e(TURNSTILE_SITEKEY)}">
          <h3>HIGH SCORES</h3>
          <div class="board-tabs" hidden><button type="button" data-sort="top" aria-pressed="true">TOP</button><button type="button" data-sort="new" aria-pressed="false">NEW</button></div>
          <ol id="mbList">
            <li class="hd2"><span>RANK</span><span>NAME</span><span>MESSAGE</span><span class="sc">SCORE</span></li>
            {rows_html}
          </ol>
          <div class="board-foot">
            <span class="soon blink">COMING SOON</span>
            <span class="ins">INSERT COIN TO POST</span>
            <span class="ini">ENTER YOUR INITIALS: <b class="blink">A</b> _ _</span>
            <button type="button" class="coin blink" id="mbCoin">INSERT COIN TO POST</button>
          </div>
          <form class="mb-form" id="mbForm" novalidate>
            <label><span>ENTER YOUR INITIALS</span><span class="mb-ini"><input maxlength="1" aria-label="Initial 1" autocomplete="off"><input maxlength="1" aria-label="Initial 2" autocomplete="off"><input maxlength="1" aria-label="Initial 3" autocomplete="off"></span></label>
            <label><span>MESSAGE (60 MAX)</span><input class="mb-msg" maxlength="60" placeholder="YOUR PULL, TAKE OR SHOUT-OUT" autocomplete="off"></label>
            <input class="mb-hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
            <div class="mb-ts"></div>
            <div class="mb-row"><button type="submit" class="coin">POST</button><button type="button" class="mb-cancel">CANCEL</button></div>
            <p class="mb-note">NO LINKS. KEEP IT FRIENDLY. POSTS SHOW AFTER A QUICK CHECK.</p>
            <p class="mb-stat" role="status" aria-live="polite"></p>
          </form>
        </div>
        <span class="cab r" aria-hidden="true"></span>
      </div>
      <div class="mb-admin" id="mbAdmin"><h4>ADMIN · WAITING FOR APPROVAL</h4>
        <form id="mbAdminForm"><input type="password" placeholder="Admin key" autocomplete="current-password" aria-label="Admin key"> <button type="submit">Load</button></form>
        <ul id="mbPending"></ul></div>
      <div class="hall-cta"><span>Get the week's best posts in Sunday's email.</span><a class="btn" href="#newsletter">Get the newsletter</a></div>
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

board_js = r'''
<script id="board-js">
(function(){
  const bd=document.getElementById('mbBoard');if(!bd)return;
  const API=bd.dataset.api,SK=bd.dataset.sitekey,list=document.getElementById('mbList'),tabs=bd.querySelector('.board-tabs');
  const form=document.getElementById('mbForm'),coin=document.getElementById('mbCoin'),stat=form.querySelector('.mb-stat');
  const ini=[...form.querySelectorAll('.mb-ini input')],msg=form.querySelector('.mb-msg');
  const RK=['1ST','2ND','3RD','4TH','5TH','6TH','7TH','8TH','9TH','10TH'];
  let sort='top',liked={};try{liked=JSON.parse(localStorage.getItem('czLiked')||'{}')}catch(e){}
  const esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const score=p=>(p*1000).toString().padStart(6,'0').replace(/\B(?=(\d{3})+(?!\d))/g,',');
  function render(posts){
    const head=list.querySelector('.hd2').outerHTML.replace('</li>','<span></span></li>');
    list.innerHTML=head+posts.map((p,i)=>`<li class="r${i+1}"><span class="rk">${RK[i]}</span><span class="nm2">${esc(p.initials)}</span><span class="msg">${esc(p.msg)}</span><span class="sc">${score(p.points)}</span><button type="button" class="lk${liked[p.id]?' on':''}" data-id="${p.id}" aria-label="Give ${esc(p.initials)} a point">&#9650;</button></li>`).join('');
  }
  function load(){return fetch(API+'?sort='+sort,{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject()).then(d=>{if(!d.ok)throw 0;bd.classList.add('live');tabs.hidden=false;render(d.posts)})}
  load().catch(()=>{});
  tabs.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;sort=b.dataset.sort;tabs.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',x===b));load().catch(()=>{})});
  list.addEventListener('click',e=>{const b=e.target.closest('.lk');if(!b||b.disabled)return;b.disabled=true;
    fetch(API+'/like',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:+b.dataset.id})}).then(r=>r.json()).then(d=>{
      if(d.ok){liked[b.dataset.id]=1;try{localStorage.setItem('czLiked',JSON.stringify(liked))}catch(e){}b.classList.add('on');b.previousElementSibling.textContent=score(d.points)}}).catch(()=>{}).finally(()=>{b.disabled=false})});
  let tsReady=false,tsId=null;
  function turnstile(){if(!SK||tsReady)return;tsReady=true;
    window.czTsLoad=()=>{tsId=window.turnstile.render(form.querySelector('.mb-ts'),{sitekey:SK,theme:'dark'})};
    const s=document.createElement('script');s.src='https://challenges.cloudflare.com/turnstile/v0/api.js?onload=czTsLoad&render=explicit';s.async=true;document.head.appendChild(s)}
  coin.addEventListener('click',()=>{form.classList.add('open');coin.style.display='none';turnstile();ini[0].focus()});
  form.querySelector('.mb-cancel').addEventListener('click',()=>{form.classList.remove('open');coin.style.display='';stat.textContent=''});
  ini.forEach((inp,i)=>{inp.addEventListener('input',()=>{inp.value=inp.value.toUpperCase().replace(/[^A-Z0-9?!]/g,'');if(inp.value&&ini[i+1])ini[i+1].focus()});
    inp.addEventListener('keydown',e=>{if(e.key==='Backspace'&&!inp.value&&ini[i-1])ini[i-1].focus()})});
  form.addEventListener('submit',e=>{e.preventDefault();const btn=form.querySelector('button[type=submit]');
    const body={initials:ini.map(x=>x.value).join(''),msg:msg.value,website:form.querySelector('.mb-hp').value};
    if(!body.initials){stat.textContent='ENTER YOUR INITIALS';return}
    if(msg.value.trim().length<2){stat.textContent='WRITE A MESSAGE';return}
    if(SK){body.token=window.turnstile&&tsId!==null?window.turnstile.getResponse(tsId):'';if(!body.token){stat.textContent='TICK THE BOT CHECK FIRST';return}}
    btn.disabled=true;stat.textContent='SENDING...';
    fetch(API+'/post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(r=>r.json()).then(d=>{
      if(d.ok){stat.textContent='THANKS! YOUR POST SHOWS AFTER A QUICK CHECK.';msg.value='';ini.forEach(x=>x.value='')}
      else stat.textContent=String(d.error||'SOMETHING WENT WRONG').toUpperCase()}).catch(()=>{stat.textContent='BOARD OFFLINE. TRY AGAIN LATER.'})
      .finally(()=>{btn.disabled=false;if(SK&&window.turnstile&&tsId!==null)window.turnstile.reset(tsId)})});
  /* admin: board.html#admin */
  const adm=document.getElementById('mbAdmin');
  function admin(){if(location.hash!=='#admin')return;adm.classList.add('on')}
  admin();addEventListener('hashchange',admin);
  const af=document.getElementById('mbAdminForm'),pend=document.getElementById('mbPending');let KEY='';
  function loadPending(){pend.innerHTML='<li>Loading…</li>';fetch(API+'/admin',{headers:{'X-Admin-Key':KEY},cache:'no-store'}).then(r=>r.json()).then(d=>{
    if(!d.ok){pend.innerHTML='<li>'+esc(d.error||'Error')+'</li>';return}
    pend.innerHTML=d.posts.length?d.posts.map(p=>`<li><span><b>${esc(p.initials)}</b> · ${esc(p.msg)}</span><button data-a="approve" data-id="${p.id}">Approve</button><button class="hide" data-a="hide" data-id="${p.id}">Hide</button></li>`).join(''):'<li>Nothing waiting.</li>'}).catch(()=>{pend.innerHTML='<li>Board offline.</li>'})}
  af.addEventListener('submit',e=>{e.preventDefault();KEY=af.querySelector('input').value;loadPending()});
  pend.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;b.disabled=true;
    fetch(API+'/admin',{method:'POST',headers:{'Content-Type':'application/json','X-Admin-Key':KEY},body:JSON.stringify({id:+b.dataset.id,action:b.dataset.a})}).then(r=>r.json()).then(()=>{loadPending();load().catch(()=>{})}).catch(()=>{b.disabled=false})});
})();
</script>'''

out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + head + style + '\n' + extra_css + '\n</head>\n<body>\n' + body + '\n' + scrolltop + '\n' + js + '\n' + board_js + '\n</body>\n</html>\n')
(root/'board.html').write_text(out)
print('board.html', len(out), 'bytes')
