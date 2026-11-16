"""Newsletter page: the week's issue as a flip-through magazine (style C "Classic glossy", Nov 4, 2026;
layout v2, Nov 16, 2026: every story gets a full-page studio photo with its text in the clear space beside the reporter).

render(iss, root) -> (html, css, js). Issue JSON (tools/newsletters/issue-NN.json, newsletter_latest.json = the current one):
  no, vol, date ("Sunday, November 15, 2026"), title, opening, cover_clip, cover{main, sub, lines[[title, sub]..]}, vol_pos?,
  pull?, signoff[..], radar[[date, what]..],
  stories: [{game, title, summary, source, clip, host?, quip?, when?, details?{facts[], why, url}}, ..]   (first = the big one)
  sections: the email sections ({h:'Coming up this week', li:[[date, text, status]..]} feeds the week-ahead page)
Older issues without "stories" are read from their sections (The big one / Top stories this week + clips).
Each story is matched to tools/news.json and tools/posts.json (by clip) to fill in details, quip, host and its story page.

Pages: 1 cover · 2 contents · 3 Inside 1Cardz.news · cover story (photo page + "The details" page) · one photo page per
top story · Overheard in the studio · The week ahead (next 7 days + further ahead) · back cover.
The inside pages are kept even (Inside 1Cardz.news is dropped if needed) so every page has a facing page.

Images: img/nl-cover-<clip>.jpg (cover) and img/nl-p-<clip>.jpg (3:4 story photos, 540x720) are cut from img/<clip>.mp4
with ffmpeg the first time. For story photos a frame is picked where the reporter's face (OpenCV) can sit to one side;
the text goes on the other side. Choices are cached in tools/nl_photos.json."""
import html, json, re, shutil, subprocess, pathlib, datetime, unicodedata

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

def _photo(root, clip):
    """(src, side) for a story's full-page photo. side = 'l' or 'r': where the text goes (the reporter is on the other side)."""
    if not clip:
        return '', 'r', None
    root = pathlib.Path(root)
    cache_f = root / 'tools' / 'nl_photos.json'
    try:
        cache = json.loads(cache_f.read_text())
    except Exception:
        cache = {}
    out = root / 'img' / f'nl-p-{clip}.jpg'
    if out.exists() and clip in cache:
        return 'img/' + out.name, cache[clip].get('side', 'r'), cache[clip].get('face')
    src = root / 'img' / f'{clip}.mp4'
    best = None
    if src.exists() and shutil.which('ffmpeg'):
        try:
            import cv2, numpy as np
            casc = cv2.CascadeClassifier(str(root / 'tools' / 'haarcascade_frontalface_default.xml'))   # OpenCV's own file, kept in the repo
            for t in (0.8, 1.4, 2.2, 3.2, 4.4, 5.6, 6.8):
                raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', str(src), '-frames:v', '1',
                                      '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, timeout=60).stdout
                if not raw:
                    continue
                fr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
                H, W = fr.shape[:2]
                cw, ch = int(W * 0.75), int(W * 0.75 * 4 / 3)          # 540x720 from a 720x1280 clip
                ymax = max(0, int(H * 0.62) - ch)                      # stay above the burned-in captions
                faces = casc.detectMultiScale(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), 1.1, 6, minSize=(int(W * .06), int(W * .06)))
                faces = [f for f in faces if f[1] + f[3] / 2 < H * 0.55]
                if len(faces) == 0:
                    continue
                fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                cx, cy = fx + fw / 2, fy + fh / 2
                for side, want in (('r', 0.30), ('l', 0.70)):          # text right -> face at 30%, text left -> face at 70%
                    x0 = int(min(max(cx - want * cw, 0), W - cw))
                    p = (cx - x0) / cw
                    y0 = int(min(max(cy - 0.30 * ch, 0), ymax))
                    off = abs(p - 0.5)                                   # how far the face sits from the middle
                    size = fw / cw
                    score = off * 3 - max(0, size - 0.22) * 10 - max(0, 0.08 - size) * 6 - (0.02 if t < 1 else 0)
                    if (side == 'r' and p > 0.5) or (side == 'l' and p < 0.5):
                        score -= 1
                    if best is None or score > best[0]:
                        best = (score, t, side, x0, y0, cw, ch, [round((cx - x0) / cw, 3), round((cy - y0) / ch, 3), round(fw / cw, 3), round(fh / ch, 3)])
        except Exception as _x:
            print('nl photo: face check skipped for', clip, _x)
        try:
            if best:
                _, t, side, x0, y0, cw, ch, face = best
                vf = f'crop={cw}:{ch}:{x0}:{y0}'
            else:
                t, side, vf, face = 2.2, 'r', 'crop=iw*0.75:iw:iw*0.125:0', None
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(src), '-frames:v', '1', '-vf', vf,
                            '-q:v', '3', str(out)], timeout=60)
            if out.exists():
                cache[clip] = {'side': side, 't': t, 'face': face}
                cache_f.write_text(json.dumps(cache, indent=1, sort_keys=True) + '\n')
                return 'img/' + out.name, side, face
        except Exception:
            pass
    im = _img(root, clip)
    return im, 'r', None

def _wrap(side, face):
    """A float whose curved edge follows the reporter's outline (head, neck, shoulders), so the story text
    wraps around her (Nov 16). face = [x, y, w, h] as fractions of the photo; the text box is the page minus
    5.5% top/9% bottom/5.5% sides, so photo fractions are mapped into it."""
    px, py, fw, fh = face if face else ([0.3, 0.3, 0.2, 0.15] if side == 'r' else [0.7, 0.3, 0.2, 0.15])
    pad = 0.035
    # outline offsets from the face centre, as (y in face heights, x in face widths), top to bottom
    prof = [(-9, .25), (-2.2, .35), (-1.5, .62), (-.8, .78), (0, .8), (.6, .72), (1.0, .6), (1.4, .9), (1.9, 1.35), (2.6, 1.6), (4, 1.75), (20, 1.8)]
    T, B, S = 4.5 / 133.3, 9 / 133.3, 0.055      # text box inset as fractions of the page (top, bottom, side)
    pts = []
    for dy, dx in prof:
        y = py + dy * fh
        x = px + dx * fw + pad if side == 'r' else px - dx * fw - pad
        y = (min(max(y, 0), 1) - T) / (1 - T - B)
        x = (x - S) / (1 - 2 * S)
        x = min(max(x, 0.30), 0.62) if side == 'r' else min(max(x, 0.38), 0.70)
        pts.append((x, min(max(y, 0), 1)))
    pts[0] = (pts[0][0], 0); pts[-1] = (pts[-1][0], 1)
    if side == 'r':
        poly = ['0% 0%'] + [f'{x * 100:.1f}% {y * 100:.1f}%' for x, y in pts] + ['0% 100%']
        return f'<i class="wrap" style="float:left;shape-outside:polygon({",".join(poly)})"></i>'
    poly = ['100% 0%'] + [f'{x * 100:.1f}% {y * 100:.1f}%' for x, y in pts] + ['100% 100%']
    return f'<i class="wrap" style="float:right;shape-outside:polygon({",".join(poly)})"></i>'

def _vol_pos(root, img, vol):
    """Where the "Vol." block goes on the cover (Nov 8): the calmest, not-too-bright spot of the cover picture
    in the right-hand column, clear of the masthead, cover lines, headline and barcode.
    Returns CSS like "top:55cqw;right:4cqw". An issue can force it with "vol_pos" (e.g. {"top":50,"right":4})."""
    try:
        from PIL import Image, ImageFilter
        im = Image.open(root / img).convert('L')
    except Exception:
        return ''
    W, H = im.size
    s = (100 * 4 / 3) / H
    ox = (W * s - 100) / 2
    edges = im.filter(ImageFilter.FIND_EDGES)
    bw, bh = 7 * 0.62 * (len(f'Vol.{vol}')) + 2, 9
    best = None
    for top in range(38, 101, 2):
        for right in (4, 8, 12, 16):
            x0, x1 = 100 - right - bw, 100 - right
            if x0 < 36: continue
            box = tuple(int(v) for v in ((x0 + ox) / s, top / s, (x1 + ox) / s, (top + bh) / s))
            e_ = sum(edges.crop(box).getdata()) / max(1, (box[2] - box[0]) * (box[3] - box[1]))
            b_ = sum(im.crop(box).getdata()) / max(1, (box[2] - box[0]) * (box[3] - box[1]))
            score = e_ + max(0, b_ - 120) * 0.6 + abs(top - 58) * 0.15
            if best is None or score < best[0]:
                best = (score, top, right)
    return f'top:{best[1]}cqw;right:{best[2]}cqw' if best else ''

def story_url(when, title):
    t = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:70].rstrip('-')
    return f'news-{when[:10]}-{t}.html'

def stories(iss, root):
    """The issue's stories as dicts (first = the big one), filled in from news.json / posts.json."""
    root = pathlib.Path(root)
    try: news = json.loads((root / 'tools' / 'news.json').read_text())
    except Exception: news = []
    try: posts = json.loads((root / 'tools' / 'posts.json').read_text())
    except Exception: posts = []
    by_clip = {p.get('clip'): p for p in posts}
    by_when = {n.get('when'): n for n in news}
    out = [dict(s) for s in iss.get('stories', [])]
    if not out:                                                 # older issues: read the email sections
        secs = {s.get('h', ''): s for s in iss.get('sections', [])}
        big = (secs.get('The big one', {}).get('p') or [])
        if big:
            lead, txt, src = big[0]
            out.append({'title': lead.rstrip('.'), 'summary': txt, 'source': src, 'clip': iss.get('big_clip') or iss.get('cover_clip')})
        top = secs.get('Top stories this week', {})
        for n, (lead, txt, src) in enumerate(top.get('li', [])):
            g, _, t = lead.partition(': ')
            out.append({'game': g if t else '', 'title': (t or lead).rstrip('.'), 'summary': txt, 'source': src,
                        'clip': (top.get('clips') or [None] * 99)[n] if n < len(top.get('clips') or []) else None})
    for s in out:
        p = by_clip.get(s.get('clip')) or {}
        n = by_when.get(s.get('when') or p.get('when')) or {}
        s.setdefault('game', n.get('game') or p.get('game', ''))
        if not s.get('game'): s['game'] = n.get('game') or p.get('game', '')
        s.setdefault('host', p.get('host', ''))
        s.setdefault('quip', p.get('quip', ''))
        if not s.get('details') and n.get('details'): s['details'] = n['details']
        w = s.get('when') or n.get('when')
        if w and n and (root / story_url(w, n['title'])).exists():
            s['page'] = story_url(w, n['title'])
    return out

def render(iss, root):
    root = pathlib.Path(root)
    no = iss.get('no', '')
    cv = iss.get('cover', {})
    cover_img = iss.get('cover_image') or _img(root, iss.get('cover_clip'), cover=True) or iss.get('image', '')   # cover_image: a supplied picture (Nov 16)
    short = iss.get('date', '').split(', ', 1)[-1] if iss.get('date') else ''
    try:
        idate = datetime.datetime.strptime(iss.get('date', ''), '%A, %B %d, %Y').date()
    except Exception:
        idate = datetime.date.today()
    wk0 = (idate - datetime.timedelta(days=6)).isoformat(); wk1 = idate.isoformat()
    try:
        posts = [x for x in json.loads((root / 'tools' / 'posts.json').read_text()) if wk0 <= x.get('when', '')[:10] <= wk1]
    except Exception:
        posts = []

    # ---- cover (unchanged) ----
    vp = iss.get('vol_pos')
    vol_style = (f' style="top:{vp.get("top", 55)}cqw;right:{vp.get("right", 4)}cqw"' if isinstance(vp, dict)
                 else (lambda c: f' style="{c}"' if c else '')(_vol_pos(root, cover_img, iss.get('vol', 1)) if cover_img else ''))
    lines = ''.join(f'<div><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in cv.get('lines', [])[:3])
    cover = f'''<div class="mz-page mz-cover" role="img" aria-label="Magazine cover: {e(cv.get('main') or iss.get('title'))}">
  <div class="ph"><img src="{e(cover_img)}" alt="" loading="lazy"></div>
  <div class="mhd"><div class="mast" aria-label="1Cardz"><span class="sh">1Cardz</span><span class="sv">1Cardz</span><span class="ho" aria-hidden="true">1Cardz</span></div>
  <div class="wm">Weekly Magazine</div></div>
  <div class="vol"{vol_style}>Vol.{e(str(iss.get('vol', 1)))}</div>
  <div class="tag">Issue {e(no)} · {e(short)}</div>
  <div class="side{' three' if len(cv.get('lines', [])) > 2 else ''}">{lines}</div>
  <div class="big"><b>{e(cv.get('main') or iss.get('title'))}</b><span>{e(cv.get('sub', '')).replace(chr(10), '<br>')}</span></div>
  <div class="bar"><i></i>1CZ-{e(no)}</div>
</div>'''

    run = lambda a, b: f'<div class="run"><span>{e(a)}</span><span>{e(b)}</span></div>'
    st = stories(iss, root)
    body = []          # (key, toc title, toc sub, html-without-folio)

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

    def photo_page(s, kick, extra=''):
        im, side, face = _photo(root, s.get('clip'))
        d = s.get('details') or {}
        facts = d.get('facts') or []
        link = f' · <a href="{e(s["page"])}">Read the full story ›</a>' if s.get('page') else ''
        return (f'<img class="bg" src="{e(im)}" alt="" loading="lazy"><div class="shade"></div><div class="mzt">{_wrap(side, face)}'
                f'<p class="kick">{e(kick)}</p><h3>{e(s.get("title", ""))}</h3><p class="sum">{e(s.get("summary", ""))}</p>{extra}'
                + (f'<ul class="facts">{"".join(f"<li>{e(x)}</li>" for x in facts[1:4])}</ul>' if facts and not extra else '')
                + (f'<p class="why"><b>Why it matters</b>{e(d["why"])}</p>' if d.get('why') else '')
                + (f'<p class="quip">“{e(s["quip"])}”<span>{e(s.get("host", ""))}</span></p>' if s.get('quip') and (extra or not d.get('why')) else '')
                + f'<p class="src">Source: {e(s.get("source", ""))}{link}</p></div>'), side

    if st:
        b0 = st[0]
        h_, side = photo_page(b0, 'Cover story · ' + (b0.get('game') or 'The big one'), extra=' ')
        body.append(('photo t-' + side, b0.get('title', ''), 'Cover story', h_))
        d = b0.get('details') or {}
        facts = ''.join(f'<li>{e(x)}</li>' for x in (d.get('facts') or []))
        pull = iss.get('pull') if iss.get('pull') and iss.get('pull') != b0.get('quip') else ''
        watch_im = _img(root, b0.get('clip'))
        body.append(('detail', b0.get('title', ''), 'Cover story', f"""{run('Cover story', b0.get('source', ''))}<p class="kick">The big one</p><h3>{'The details' if facts else e(b0.get('title', ''))}</h3>
""" + (f'<ul class="dets">{facts}</ul>' if facts else f'<p>{e(b0.get("summary", ""))}</p>')
            + (f'<div class="pull">“{e(pull)}”</div>' if pull else '')
            + f'<p class="src">Source: {e(b0.get("source", ""))}' + (f' · <a href="{e(b0["page"])}">Read the full story ›</a>' if b0.get('page') else '') + '</p>'
            + (f'<a class="watch" href="archive.html"><img src="{e(watch_im)}" alt="" loading="lazy"><span><b>Watch the report</b>{e(b0.get("host") or "The 1Cardz")} on this story, in the Library. ▶</span></a>' if watch_im else '')))
        # top stories in spreads (Nov 16): a photo page on the left, a regular written page on the right
        for k, s in enumerate(st[1:5]):        # 3 photo sets per issue (Nov 16): the cover story + 2 top-story spreads
            if k % 2 == 0:
                h_, side = photo_page(s, ' · '.join(x for x in (s.get('game'), 'Top story') if x))
                body.append(('photo t-' + side, s.get('title', ''), s.get('game') or 'Top story', h_))
                continue
            d = s.get('details') or {}
            facts = ''.join(f'<li>{e(x)}</li>' for x in (d.get('facts') or [])[1:])
            im = _img(root, s.get('clip'))
            body.append(('story', s.get('title', ''), s.get('game') or 'Top story',
                f"""{run(s.get('game') or 'Top story', s.get('source', ''))}<p class="kick">{e(s.get('game') or 'Top story')}</p><h3>{e(s.get('title', ''))}</h3>
<p class="first">{e(s.get('summary', ''))}</p>""" + (f'<ul class="dets">{facts}</ul>' if facts else '')
                + (f'<p class="why"><b>Why it matters</b>{e(d["why"])}</p>' if d.get('why') else '')
                + (f'<div class="pull">“{e(s["quip"])}”<span>{e(s.get("host", ""))}</span></div>' if s.get('quip') else '')
                + f'<p class="src">Source: {e(s.get("source", ""))}' + (f' · <a href="{e(s["page"])}">Read the full story ›</a>' if s.get('page') else '') + '</p>'
                + (f'<a class="watch" href="archive.html"><img src="{e(im)}" alt="" loading="lazy"><span><b>Watch the report</b>{e(s.get("host") or "The 1Cardz")} on this story, in the Library. ▶</span></a>' if im else '')))

        # sets 1 and 3 have the photo on the right-hand page (Nov 16): swap their two pages
        ph = [n for n, b in enumerate(body) if b[0].startswith('photo')]
        for j in (ph[0:1] + ph[2:3]):
            if j + 1 < len(body):
                body[j], body[j + 1] = body[j + 1], body[j]

        # after the 3 sets (Nov 16): the earlier top-stories style, 2 per page with the clip photo, up to 4 pages
        rest = st[5:13]
        npages = (len(rest) + 1) // 2
        for k in range(0, len(rest), 2):
            cards = ''
            for s in rest[k:k + 2]:
                im = _img(root, s.get('clip'))
                link = f' · <a href="{e(s["page"])}">Read the full story ›</a>' if s.get('page') else ''
                cards += (f'<div class="st">' + (f'<img src="{e(im)}" alt="" loading="lazy">' if im else '') +
                          f'<span class="g">{e(s.get("game", ""))}</span><b>{e(s.get("title", ""))}</b><p>{e(s.get("summary", ""))}</p><small>Source: {e(s.get("source", ""))}{link}</small></div>')
            body.append(('top', ' & '.join(x.get('game') or x.get('title', '') for x in rest[k:k + 2]), 'Top stories',
                         f'{run("Top stories", f"{k // 2 + 1} of {npages}")}<div class="stories">{cards}</div>'))

    q = [x for x in posts if x.get('quip')]
    if q:
        quips = ''.join(f'<blockquote><p>“{e(x["quip"])}”</p><cite>{e(x["host"])} on {e(x["title"])}</cite></blockquote>' for x in q[-6:])
        body.append(('quips', 'Overheard in the studio', 'The best lines', f"""{run('Overheard in the studio', 'The best lines')}<p class="kick">Said on air</p><h3>Overheard in the studio</h3><div class="quips">{quips}</div>"""))

    # The week ahead + release radar on one page (Nov 16): next 7 days first, then "Further ahead"
    secs = {s.get('h', ''): s for s in iss.get('sections', [])}
    cal = secs.get('Coming up this week', {}).get('li', [])
    radar = [[re.sub(r',? ' + str(idate.year) + r'$', '', d_), t_] for d_, t_ in (iss.get('radar') or [])]
    def _h(d_, t_):
        return max(-(-len(t_) // 58), -(-len(d_) // 13), 1) * 3.8 + 3.4
    room, keep_c, keep_r = 94.0, [], []
    for c in cal:
        need = _h(c[0], c[1] + ' ' + c[2] + '   ')
        if room - need < 0: break
        room -= need; keep_c.append(c)
    room -= 7 if radar else 0
    for r_ in radar:
        need = _h(*r_)
        if room - need < 0: break
        room -= need; keep_r.append(r_)
    if keep_c or keep_r:
        rows = ''.join(f'<div><b>{e(c[0].rstrip(":"))}</b><span>{e(c[1])}<i>{e(c[2])}</i></span></div>' for c in keep_c)
        rr = ''.join(f'<div><b>{e(d_)}</b><span>{e(t_)}</span></div>' for d_, t_ in keep_r)
        body.append(('cal', 'The week ahead', 'Calendar', f"""{run('The week ahead', 'Save the dates')}<p class="kick">Mark your calendar</p><h3>The week ahead</h3>"""
                     + (f'<p class="sub">Next 7 days</p><div class="cal">{rows}</div>' if keep_c else '')
                     + (f'<p class="sub">Further ahead</p><div class="cal radar">{rr}</div>' if keep_r else '')))

    # keep the inside pages even (contents + body): drop "Inside 1Cardz.news" if the count is odd
    if (len(body) + 1) % 2 and body and body[0][0] == 'about':
        body = body[1:]

    sign = '<br>'.join(e(x) for x in iss.get('signoff', [])[:2]) or 'Shuffle up,<br>Zia &amp; Luna'
    back_html = f"""<div class="mz-page mz-back"><p class="kick">See you next Sunday</p><h3>Never miss an issue</h3>
<p>One free email every Sunday with the week in cards and what's coming up. New clips every day at 8 AM (Zia) and 8 PM (Luna).</p>
<div class="links"><a href="archive.html">Watch the clips</a><a href="news.html">All headlines</a></div>
<div class="sign">{sign}</div><p class="small">1Cardz.news · Instagram @1cardzcom · YouTube @1Cardzcom · TikTok @1cardz.com</p></div>"""

    # contents (page 2), then the body pages from page 3
    toc = ''; seen = set()
    for n, (key, t, sub, _) in enumerate(body):
        if key == 'about' or (key.startswith('photo') and sub == 'Cover story'): continue
        if key == 'top':
            if 'top' in seen: continue
            seen.add('top'); t = 'More top stories'; sub = f'{len(st[5:13])} stories'
        toc += f'<li><div><span>{e(sub)}</span><b>{e(t)}</b></div><em>{3 + n}</em></li>'
    pages = [f'<div class="mz-page">{run("1Cardz Weekly", "No. " + no)}<p class="kick">In this issue</p><h3>Contents</h3><ol class="toc">{toc}</ol><div class="folio">2</div></div>']
    for n, (key, _, _, h) in enumerate(body):
        pages.append(f'<div class="mz-page mz-{key}">{h}<div class="folio">{3 + n}</div></div>')

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
.mz-book{display:grid;grid-template-columns:minmax(0,1fr);max-width:560px;margin:0 auto;border-radius:0;overflow:hidden;box-shadow:0 26px 54px rgba(0,0,0,.55)}
.mz-book.two{grid-template-columns:minmax(0,1fr) minmax(0,1fr);max-width:1120px}
.mz-book.mini .mz-page{cursor:zoom-in}.mz-book.zoom .mz-page{cursor:zoom-out}
@media (max-width:759px){.mz{padding-left:22px;padding-right:22px}}
.mz-ctl{display:flex;justify-content:center;align-items:center;gap:14px;margin-top:16px}
.mz-ctl button{font:inherit;font-size:22px;width:44px;height:44px;border-radius:50%;border:0;background:var(--foil,#e9c46a);color:#12162b;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,.35)}
.mz-ctl button:disabled{opacity:.3;cursor:default}
.mz-no{font-family:var(--f-mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#aab1c9;min-width:130px;text-align:center}
.mz-page{position:relative;aspect-ratio:3/4;overflow:hidden;container-type:inline-size;background:#fbf8f1;color:#7a7a7a;padding:5.5% 6.5% 4.5%;font-family:var(--f-body);display:flex;flex-direction:column}
.mz-page .folio{margin-top:auto;padding-top:2cqw}
.mz-page+.mz-page{box-shadow:inset 1.4cqw 0 2cqw -1cqw rgba(0,0,0,.35)}
.mz-page .run{display:flex;justify-content:space-between;font-family:var(--f-mono);font-size:2.3cqw;letter-spacing:.14em;text-transform:uppercase;color:#6a6878;border-bottom:.3cqw solid #d8d1c3;padding-bottom:2cqw;margin-bottom:4cqw;flex:none}
.mz-page .kick{font-family:var(--f-mono);font-size:2.6cqw;letter-spacing:.2em;text-transform:uppercase;color:#c8102e;margin:0 0 2cqw}
.mz-page h3{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:8.6cqw;line-height:.98;margin:0 0 4cqw;color:#7a7a7a;text-transform:none;letter-spacing:0}
.mz-page p{font-size:3.3cqw;line-height:1.6;margin:0 0 3cqw;color:#7a7a7a;max-width:none}
.mz-page p.first::first-letter{float:left;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:12cqw;line-height:.8;padding:1cqw 1.6cqw 0 0;color:#c8102e}
.mz-page .pull{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:6cqw;line-height:1.08;border-top:.6cqw solid #1b1a22;border-bottom:.6cqw solid #1b1a22;padding:2.6cqw 0;margin:3.5cqw 0}
.mz-page .toc{list-style:none;margin:0;padding:0;counter-reset:t;flex:1;display:flex;flex-direction:column;justify-content:space-between}
.mz-page .toc li{display:grid;grid-template-columns:8cqw 1fr auto;align-items:baseline;gap:3cqw;padding:.9cqw 0 1.4cqw;border-bottom:.25cqw solid #d8d1c3;counter-increment:t}.mz-page .toc li:last-child{border-bottom:0}
.mz-page .toc li::before{content:counter(t,decimal-leading-zero);font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:4.4cqw;color:#c8102e;line-height:1}
.mz-page .toc b{display:block;font-size:3.2cqw;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mz-page .toc li>div{min-width:0}.mz-page .toc span{display:block;font-family:var(--f-mono);font-size:2cqw;letter-spacing:.12em;text-transform:uppercase;color:#6a6878}.mz-page .toc em{font-style:normal;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:3.6cqw;color:#7a7a7a}
.mz-page .sub{font-family:var(--f-mono);font-size:2.4cqw;letter-spacing:.16em;text-transform:uppercase;color:#1b1a22;border-bottom:.6cqw solid #1b1a22;padding-bottom:1.2cqw;margin:1cqw 0 0}.mz-page .cal+.sub{margin-top:4cqw}
.mz-page .cal div{display:grid;grid-template-columns:21cqw 1fr;gap:3cqw;padding:1.7cqw 0;border-top:.25cqw solid #d8d1c3;font-size:2.8cqw;line-height:1.35}.mz-page .cal div:first-child{border-top:0}
.mz-page .cal b{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:3.3cqw;color:#c8102e;line-height:1.1}
.mz-page .cal i{display:inline;font-style:normal;font-family:var(--f-mono);font-size:2.1cqw;letter-spacing:.1em;text-transform:uppercase;color:#6a6878;margin-left:1.6cqw;white-space:nowrap}
.mz-page .folio{text-align:center;font-family:var(--f-mono);font-size:2.2cqw;color:#6a6878;flex:none}
.mz-page .folio.light{color:#fff}
.mz-page .src{font-size:2.6cqw;color:#6a6878;font-style:italic}
.mz-page .hosts{display:flex;gap:3cqw;margin:0 0 4cqw;align-items:center}.mz-page .hosts img{flex:none;width:23cqw;height:23cqw;border-radius:50%;object-fit:cover;object-position:50% 15%;box-shadow:0 0 0 .5cqw #fff,0 1cqw 2cqw rgba(0,0,0,.2)}
.mz-page .hosts p{margin:0;font-size:3.3cqw;line-height:1.5}
.mz-page .about{display:grid;grid-template-columns:1fr 1fr;gap:3cqw 5cqw;margin-top:1cqw;flex:1;align-content:space-evenly;border-top:.6cqw solid #1b1a22;padding-top:2cqw}
.mz-page .about a{text-decoration:none}.mz-page .about b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:4.6cqw;color:#c8102e;line-height:1.1}
.mz-page .about span{display:block;font-size:3.1cqw;line-height:1.45;margin-top:.8cqw;color:#7a7a7a}
.mz-page .note{font-size:2.6cqw;color:#6a6878;margin-top:3cqw}.mz-page .note a{color:#c8102e}
.mz-page .quips{display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:1fr;gap:4cqw;flex:1;min-height:0}
.mz-page blockquote{margin:0;padding:3cqw;border-left:1cqw solid #c8102e;background:#f2ecdf;display:flex;flex-direction:column;justify-content:space-between}
.mz-page blockquote p{font-family:"Playfair Display",Georgia,serif;font-style:italic;font-weight:700;font-size:3.8cqw;line-height:1.25;margin:0 0 1.5cqw;color:#7a7a7a}
.mz-page blockquote cite{font-style:normal;font-family:var(--f-mono);font-size:2.2cqw;letter-spacing:.1em;text-transform:uppercase;color:#6a6878}
.mz-back{background:linear-gradient(160deg,#1b2a6b 0%,#0e1640 55%,#060a22 100%);color:#fff;justify-content:center}.mz-back .folio{position:absolute;left:0;right:0;bottom:4%}
.mz-page .watch{margin-top:auto;display:grid;grid-template-columns:26% 1fr;gap:4cqw;align-items:center;text-decoration:none;color:#7a7a7a;background:#f2ecdf;border-radius:1.4cqw;padding:2.4cqw}.mz-page .watch img{width:100%;aspect-ratio:4/3;object-fit:cover;object-position:50% 15%;border-radius:1cqw}.mz-page .watch span{font-size:2.9cqw;line-height:1.4}.mz-page .watch b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:5cqw;color:#c8102e}.mz-back .kick{color:#7cf3ff}.mz-back h3{color:#fff;font-size:11cqw}.mz-back p{color:#fff}
.mz-back .links{display:flex;flex-direction:column;gap:3cqw;margin:4cqw 0}
.mz-back .links a{font-family:var(--f-mono);font-size:3.2cqw;letter-spacing:.12em;text-transform:uppercase;color:#0e1640;background:#fff;padding:3cqw 4cqw;border-radius:1.2cqw;text-decoration:none;text-align:center}
.mz-back .sign{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:6cqw;line-height:1.05;margin:2cqw 0}
.mz-back .small{font-size:2.5cqw;opacity:.85}.mz-back .folio{color:#9fb3ff}
/* layout v2 (Nov 16): story photo pages, text in the clear space beside the reporter */
.mz-photo{padding:0;color:#fff;background:#120e1f}
.mz-photo .bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.mz-photo .shade{position:absolute;inset:0;z-index:1}
.mz-photo.t-r .shade{background:linear-gradient(90deg,transparent 22%,rgba(12,9,24,.43) 42%,rgba(12,9,24,.6) 70%)}
.mz-photo.t-l .shade{background:linear-gradient(270deg,transparent 22%,rgba(12,9,24,.43) 42%,rgba(12,9,24,.6) 70%)}
.mz-photo .mzt{position:absolute;z-index:2;top:4.5%;bottom:9%;left:5.5%;right:5.5%;display:block;overflow:hidden;text-shadow:0 .2cqw .8cqw rgba(0,0,0,.6)}
.mz-photo .wrap{display:block;width:100%;height:100%;shape-margin:1.2cqw}
.mz-photo .mzt>*:not(.wrap){position:relative}
.mz-photo .kick{color:#ffd23f;font-size:2.3cqw;margin-bottom:1.6cqw}
.mz-photo h3{color:#fff;font-size:5.6cqw;line-height:1.02;margin:0 0 2.4cqw}
.mz-photo p{color:#eef0f6;font-size:2.9cqw;line-height:1.45;margin:0 0 2.2cqw}
.mz-photo .facts{list-style:none;margin:0 0 2.2cqw;padding:0}
.mz-photo .facts li{font-size:2.6cqw;line-height:1.4;color:#eef0f6;padding:0;margin:0 0 1.4cqw}
.mz-photo .facts li::before{content:"";display:inline-block;width:1.3cqw;height:1.3cqw;background:#ffd23f;margin-right:1.4cqw;vertical-align:.15em}
.mz-photo .why{font-size:2.7cqw}
.mz-photo .why b{display:block;font-family:var(--f-mono);font-weight:400;font-size:2.1cqw;letter-spacing:.14em;text-transform:uppercase;color:#ffd23f;margin-bottom:.6cqw}
.mz-photo .quip{font-family:"Playfair Display",Georgia,serif;font-style:italic;font-weight:700;font-size:3.8cqw;line-height:1.2;color:#fff}
.mz-photo .quip span{display:block;font-family:var(--f-mono);font-style:normal;font-weight:400;font-size:2.1cqw;letter-spacing:.14em;text-transform:uppercase;color:#ffd23f;margin-top:1cqw}
.mz-photo .src{margin-top:2.4cqw;margin-bottom:0;font-size:2.3cqw;color:#c9cde0;font-style:italic}
.mz-page .src a{color:#c8102e;font-style:normal;font-weight:700;text-decoration:none}
.mz-photo .mzt .src a{color:#ffd23f}
.mz-photo .folio{position:absolute;left:0;right:0;bottom:3.5cqw;z-index:2;color:#fff}
.mz-page .dets{list-style:none;margin:0 0 3cqw;padding:0;counter-reset:d}
.mz-page .dets li{position:relative;counter-increment:d;font-size:3.1cqw;line-height:1.45;padding:1.8cqw 0 1.8cqw 7cqw;border-top:.25cqw solid #d8d1c3}
.mz-page .dets li::before{content:counter(d,decimal-leading-zero);position:absolute;left:0;top:1.5cqw;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:4cqw;color:#c8102e}
.mz-detail .pull{font-size:4.8cqw;margin:1cqw 0 3cqw}
.mz-detail .watch{margin-top:auto}
.mz-detail p.first{font-size:3.1cqw}

.mz-photo.t-r .mzt{text-align:right}.mz-photo.t-l .mzt{text-align:left}
.mz-story .first{font-size:3.2cqw}
.mz-story .why,.mz-detail .why{font-size:3.1cqw;line-height:1.45;background:#f2ecdf;border-left:1cqw solid #c8102e;padding:2.4cqw 3cqw;margin:0 0 3cqw}
.mz-story .why b,.mz-detail .why b{display:block;font-family:var(--f-mono);font-weight:400;font-size:2.2cqw;letter-spacing:.14em;text-transform:uppercase;color:#c8102e;margin-bottom:.8cqw}
.mz-story .pull{font-size:4.6cqw;margin:0 0 3cqw}.mz-story .pull span,.mz-detail .pull span{display:block;font-family:var(--f-mono);font-weight:400;font-size:2.1cqw;letter-spacing:.14em;text-transform:uppercase;color:#c8102e;margin-top:1.2cqw}
.mz-story .watch{margin-top:auto}

.mz-page .stories{display:grid;grid-template-rows:1fr 1fr;gap:4cqw;flex:1;min-height:0}
.mz-page .st{display:grid;grid-template-columns:44% 1fr;grid-template-rows:auto auto auto 1fr;column-gap:4cqw;align-content:start;align-items:start;border-bottom:.25cqw solid #d8d1c3;padding-bottom:4cqw;min-height:0;overflow:hidden}.mz-page .st:last-child{border-bottom:0}
.mz-page .st img{display:block;width:100%;aspect-ratio:3/4;object-fit:cover;object-position:50% 12%;border-radius:1.2cqw;grid-row:span 4}
.mz-page .st .g{font-family:var(--f-mono);font-size:2.5cqw;letter-spacing:.14em;text-transform:uppercase;color:#c8102e}
.mz-page .st b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:5.2cqw;line-height:1.05;margin:1cqw 0 2cqw}
.mz-page .st p{font-size:3.1cqw;line-height:1.45;margin:0}
.mz-page .st small{display:block;font-size:2.5cqw;color:#8a8796;font-style:italic;margin-top:1cqw}
.mz-page .st small a{color:#c8102e;font-style:normal;font-weight:700;text-decoration:none}
/* cover */
.mz-cover{display:block;padding:0;background:#f4efe4;cursor:pointer;isolation:isolate}
.mz-cover .ph{position:absolute;inset:0;z-index:0}.mz-cover .ph img{width:100%;height:100%;object-fit:cover;object-position:50% 0}
.mz-cover .ph::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,16,30,.35) 0%,transparent 22%,transparent 58%,rgba(20,16,30,.75) 100%)}
.mz-cover .mhd{position:absolute;left:0;right:0;top:4cqw;z-index:2;display:grid;justify-content:center}
.mz-cover .vol{position:absolute;right:4cqw;top:55.35cqw;z-index:2;font-family:"Playfair Display",Georgia,serif;font-style:normal;font-weight:900;font-size:7cqw;line-height:1;color:#fff;text-shadow:0 .4cqw 1.2cqw rgba(0,0,0,.7)}
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

/* three cover lines (Nov 16): same column, a little tighter so it clears the main headline */
.mz-cover .side.three{top:40cqw;gap:3cqw}.mz-cover .side.three b{font-size:5cqw}.mz-cover .side.three span{line-height:1.25;margin-top:.5cqw}
/* side shelves of past issues (Nov 8): 6 per side, straight down; each cover cased like a graded card */
/* Nov 16: the past-issue shelves sit under the magazine as rows on every screen; the magazine is bigger */
.mz-desk{position:relative;z-index:4;display:grid;padding:0 clamp(14px,2vw,26px);grid-template-columns:minmax(0,1fr);gap:clamp(14px,1.6vw,22px);align-items:start}
.mz-desk>.mz-mid{order:1}.mz-shelf.l{order:2}.mz-shelf.r{order:3}
.mz-shelf{display:flex;flex-direction:row;flex-wrap:wrap;justify-content:center;gap:16px;padding-top:0}
.mz-shelf .mz-slot{flex:0 0 178px;width:178px}
.mz-slot{position:relative;display:block;width:100%;padding:0;border:0;background:none;color:inherit;font:inherit;text-align:left;cursor:pointer;transition:transform .2s ease}
.mz-slot .slab{display:block;padding:4px 4px 6px;border-radius:6px;background:linear-gradient(135deg,rgba(255,255,255,.30),rgba(255,255,255,.07) 38%,rgba(255,255,255,.04) 62%,rgba(255,255,255,.20));
  border:1px solid rgba(255,255,255,.5);box-shadow:inset 0 0 0 2px rgba(255,255,255,.08),inset 0 1px 0 rgba(255,255,255,.6),0 10px 20px rgba(0,0,0,.5)}
.mz-slot .lbl{display:block;margin-bottom:3px;padding:1px 3px;font-size:8px;background:#f6f4ee;border:1px solid #c8102e;border-radius:2px;text-align:center;font-family:var(--f-mono);text-transform:uppercase;line-height:1.25;color:#12162b;overflow:hidden;white-space:nowrap}
.mz-slot .lbl b{display:inline;font-size:8px;letter-spacing:.06em;font-weight:700}
.mz-slot .lbl i{display:inline;margin-left:.6em;font-style:normal;font-size:8px;letter-spacing:.04em;color:#c8102e;overflow:hidden;text-overflow:ellipsis}
.mz-slot .cv{display:block;min-width:168px;border-radius:0;overflow:hidden;box-shadow:0 0 0 1px rgba(0,0,0,.35)}
.mz-slot .mz-page{pointer-events:none}
.mz-slot .mz-cover .mast .ho{display:none}
.mz-slot .tab{position:absolute;top:50%;right:-17px;transform:translateY(-50%);width:17px;padding:10px 0;border-radius:0 5px 5px 0;background:#ffd23f;color:#12162b;
  font-family:var(--f-mono);font-size:9px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;writing-mode:vertical-rl;text-align:center;box-shadow:0 4px 10px rgba(0,0,0,.4)}
.mz-shelf.r .mz-slot .tab{right:auto;left:-17px;border-radius:5px 0 0 5px;transform:translateY(-50%) rotate(180deg)}
.mz-slot:hover,.mz-slot:focus-visible{transform:translateY(-3px)}
.mz-slot.on .slab{border-color:#ffd23f;box-shadow:0 0 0 2px #ffd23f,0 0 18px rgba(255,210,63,.5)}
.mz-slot.empty{cursor:default;opacity:.35}.mz-slot.empty:hover{transform:none}
.mz-slot.empty .slab{border-style:dashed;background:rgba(255,255,255,.03);box-shadow:none}
.mz-slot.empty .lbl{background:none;border:1px dashed rgba(255,255,255,.35)}
.mz-slot.empty .cv{aspect-ratio:3/4;box-shadow:none;border:1px dashed rgba(255,255,255,.25)}
.mz-home{display:block;margin:0 auto 10px;font:inherit;font-family:var(--f-mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#12162b;background:#ffd23f;border:0;border-radius:999px;padding:8px 14px;cursor:pointer}
.mz-home[hidden]{display:none}
@media (max-width:759px){.mz-desk{grid-template-columns:minmax(0,1fr);padding:0}
  .mz-shelf{flex-direction:row;flex-wrap:nowrap;justify-content:flex-start;gap:12px;padding:14px 22px 4px;overflow-x:auto;scrollbar-width:thin}
  .mz-slot{flex:0 0 178px}
  .mz-slot .tab,.mz-shelf.r .mz-slot .tab{position:static;display:block;width:auto;margin-top:4px;padding:4px 0;border-radius:4px;transform:none;writing-mode:horizontal-tb}
  .mz-desk>.mz-mid{order:1}.mz-shelf.l{order:2}.mz-shelf.r{order:3}}
.mz-cover .tag{position:absolute;left:0;right:0;top:34.5cqw;z-index:2;text-align:center;font-family:var(--f-mono);font-size:2.3cqw;letter-spacing:.25em;text-transform:uppercase;color:#fff;text-shadow:0 .3cqw .8cqw rgba(0,0,0,.6)}
.mz-cover .side{position:absolute;left:4cqw;top:46cqw;z-index:2;width:30cqw;display:flex;flex-direction:column;gap:4cqw}
.mz-cover .side b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:5.6cqw;line-height:1;color:#fff;text-shadow:0 .4cqw 1.2cqw rgba(0,0,0,.75)}
.mz-cover .side span{display:block;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-size:3cqw;color:#fde8c2;text-shadow:0 .3cqw .8cqw rgba(0,0,0,.8)}
.mz-cover .big{position:absolute;left:4cqw;right:30cqw;bottom:4cqw;z-index:2;color:#fff}
.mz-cover .big b{display:block;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:9cqw;line-height:.92;text-shadow:0 .4cqw 1.2cqw rgba(0,0,0,.6)}
.mz-cover .big span{display:block;font-family:"Playfair Display",Georgia,serif;font-style:italic;font-size:3.6cqw;line-height:1.15;margin-top:1.5cqw;color:#fde8c2}
.mz-cover .bar{position:absolute;right:3.5cqw;bottom:3.5cqw;z-index:2;background:#fff;color:#8a8f99;padding:1.4cqw 2cqw 1cqw;font-family:var(--f-mono);font-size:2.2cqw;text-align:center;line-height:1.2}
.mz-cover .bar i{display:block;width:22cqw;height:7cqw;background:repeating-linear-gradient(90deg,#000 0 .5cqw,#fff .5cqw .8cqw,#000 .8cqw 1.1cqw,#fff 1.1cqw 1.9cqw,#000 1.9cqw 2.6cqw,#fff 2.6cqw 3cqw);margin-bottom:.6cqw}
'''

JS = r'''<script id="mz-js">
(function(){const mz=document.getElementById('mz');if(!mz)return;
  const book=document.getElementById('mzBook'),prev=mz.querySelector('.mz-prev'),next=mz.querySelector('.mz-next'),no=mz.querySelector('.mz-no');
  let cover,back,pgs,total;
  function read(){cover=document.getElementById('mzCover').innerHTML;back=(document.getElementById('mzBack')||{}).innerHTML||'';pgs=[...mz.querySelectorAll('template.mzPg')].map(t=>t.innerHTML);total=pgs.length+1+(back?1:0)}
  read();
  const two=()=>matchMedia('(min-width:760px)').matches;
  /* views: cover alone, inside pages in spreads (or singles on phones), back page alone */
  function views(){const v=[{h:cover,first:1,n:1,cov:1}],st=2;for(let i=0;i<pgs.length;i+=st)v.push({h:pgs.slice(i,i+st).join(''),first:i+2,n:Math.min(st,pgs.length-i)});
    if(back)v.push({h:back,first:pgs.length+2,n:1});return v}
  let idx=0,firstShown=1,zoom=null;   /* phones: spreads shown small; tap a page to open it full size (zoom = 0 left, 1 right) */
  function view(){const v=views();idx=Math.max(0,Math.min(idx,v.length-1));const c=v[idx];firstShown=c.first;
    if(two()||c.n!==2)zoom=null;
    const z=zoom!==null,h=z?pgs[c.first-2+zoom]:c.h,n=z?1:c.n;
    book.classList.toggle('two',n===2);book.classList.toggle('mini',n===2&&!two());book.classList.toggle('zoom',z);book.innerHTML=h;
    no.textContent=c.cov?'Cover · tap to open':z?`Page ${c.first+zoom} · tap to close`:(c.n===2?(two()?`Pages ${c.first}–${c.first+1} of ${total}`:`Pages ${c.first}–${c.first+1} · tap a page`):(idx===v.length-1&&back?'Back cover':`Page ${c.first} of ${total}`));
    prev.disabled=idx===0&&!z;next.disabled=idx===v.length-1&&!z;
    /* story photo pages (Nov 16): if the text doesn't fit, drop facts from the end, then "why it matters", then the summary's tail */
    book.querySelectorAll('.mz-photo .mzt').forEach(t=>{const f=[...t.querySelectorAll('.facts li')];while(t.scrollHeight>t.clientHeight+1&&f.length)f.pop().remove();
      const fl=t.querySelector('.facts');if(fl&&!fl.children.length)fl.remove();const w=t.querySelector('.why,.quip');if(t.scrollHeight>t.clientHeight+1&&w)w.remove()});
    book.querySelectorAll('.mz-detail,.mz-story').forEach(pg=>{const f=[...pg.querySelectorAll('.dets li')];const w=pg.querySelector('.watch'),p=pg.querySelector('.pull');
      const fits=()=>pg.scrollHeight<=pg.clientHeight+1;if(!fits()&&w)w.remove();if(!fits()&&p){p.remove();if(w){pg.querySelector('.folio').before(w);if(!fits())w.remove()}}while(!fits()&&f.length>2)f.pop().remove()});
    /* the week ahead page: drop "Further ahead" rows from the end until it fits (Nov 16) */
    book.querySelectorAll('.mz-cal').forEach(pg=>{const r=[...pg.querySelectorAll('.radar div')];while(pg.scrollHeight>pg.clientHeight+1&&r.length)r.pop().remove();
      const rd=pg.querySelector('.radar');if(rd&&!rd.children.length){rd.previousElementSibling.remove();rd.remove()}});
    if(c.cov){const el=book.querySelector('.mz-cover');if(el)el.addEventListener('click',()=>go(1))}}
  function go(d){if(zoom!==null){zoom+=d>0?1:-1;if(zoom>1){idx++;zoom=0}else if(zoom<0){idx--;zoom=1}}else idx+=d>0?1:-1;view()}
  book.addEventListener('click',e=>{if(two())return;const c=views()[idx];const pg=e.target.closest('.mz-page');if(!pg||c.cov||c.n!==2)return;
    if(zoom===null){e.preventDefault();zoom=[...book.children].indexOf(pg);if(zoom<0)zoom=null;view();book.scrollIntoView({block:'nearest'})}
    else if(!e.target.closest('a')){zoom=null;view()}});
  addEventListener('resize',()=>{const v=views();idx=v.findIndex(x=>x.first<=firstShown&&firstShown<x.first+x.n);if(idx<0)idx=0;view()});
  prev.addEventListener('click',()=>go(-1));next.addEventListener('click',()=>go(1));
  addEventListener('keydown',e=>{const r=book.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight)return;if(e.key==='ArrowRight')go(1);if(e.key==='ArrowLeft')go(-1)});
  let sx=null;book.addEventListener('touchstart',e=>{sx=e.touches[0].clientX},{passive:true});
  book.addEventListener('touchend',e=>{if(sx===null)return;const dx=e.changedTouches[0].clientX-sx;sx=null;if(Math.abs(dx)>50)go(dx<0?1:-1)},{passive:true});
  /* past issues on the side shelves (Nov 8): tap a cover to open that issue here; "This week's issue" comes back */
  const cur=[...mz.querySelectorAll('template')].map(t=>t.outerHTML).join(''),dt=document.getElementById('mzDate'),dt0=dt?dt.textContent:'',home=document.getElementById('mzHome');
  function load(tpl,date,slot){mz.querySelectorAll('template').forEach(t=>t.remove());mz.insertAdjacentHTML('beforeend',tpl);read();idx=0;zoom=null;view();
    if(dt)dt.textContent=date||dt0;document.querySelectorAll('.mz-slot').forEach(b=>b.classList.toggle('on',b===slot));if(home)home.hidden=!slot}
  document.querySelectorAll('.mz-slot[data-src]').forEach(b=>b.addEventListener('click',async()=>{
    try{const r=await fetch(b.dataset.src);if(!r.ok)throw 0;load(await r.text(),b.dataset.date,b);mz.scrollIntoView({behavior:'smooth',block:'nearest'})}catch(_){location.href=b.dataset.src}}));
  if(home)home.addEventListener('click',()=>load(cur,'',null));
  view()})();
</script>'''
