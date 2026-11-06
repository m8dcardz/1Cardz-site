#!/usr/bin/env python3
"""SEO pass for 1cardz.news (Nov 3, 2026). Run after the page builders:
    python3 tools/seo.py
It is safe to run any number of times. For every page it:
  - sets a search-friendly <title> and description
  - adds share previews (Open Graph + Twitter card), favicon/app icons, theme colour, robots hints
  - adds structured data (JSON-LD): news organisation + website (Home), headline list (Headlines),
    one VideoObject per clip (Library), WebPage for the others
  - gives each inner page its own <h1> (the page title) and turns the binder's "TCG News" into a styled <div>
It also writes sitemap.xml and robots.txt.
Every page builder (build_*.py) calls it at the end, so the daily runs keep it current.
"""
import html, json, pathlib, re, datetime, sys, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import site_parts

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://1cardz.news/'
OG_IMG = SITE + 'img/og-1cardz.jpg'
GOOGLE_VERIFY = 'Qn2aus3288fPHtNy3uGq67lvfgMzjwkNacnNeF72rlY'  # Google Search Console (HTML tag method, Nov 3, 2026)
SOCIAL = ['https://www.instagram.com/1cardzcom/', 'https://www.youtube.com/@1Cardzcom', 'https://www.tiktok.com/@1cardz.com']
GAMES = 'Pokémon, Magic: The Gathering, One Piece, Yu-Gi-Oh!, Lorcana, Flesh and Blood and more'

PAGES = {
    'index.html': ('1Cardz.news: Daily TCG News for Pokémon, Magic, One Piece & More',
                   f'Daily trading card game news in two short clips a day from hosts Zia and Luna: {GAMES}. Headlines, market prices and a free weekly newsletter.'),
    'news.html': ('TCG News Headlines Today | 1Cardz.news',
                  'The latest trading card game news, newest first: set releases, bans, auctions and events for Pokémon, Magic, One Piece, Lorcana, Yu-Gi-Oh! and more.'),
    'archive.html': ('TCG News Clips Library | Zia & Luna | 1Cardz.news',
                     'Every 1Cardz.news video clip from hosts Zia and Luna: short trading card game news for Pokémon, Magic, One Piece, Flesh and Blood and more.'),
    'market.html': ('TCG Market Prices Today: Sealed Product & Chase Singles | 1Cardz.news',
                    'Daily trading card game market prices for booster boxes and chase singles from the newest sets across seven games, with recent price changes.'),
    'newsletter.html': ('Free Weekly TCG Newsletter | 1Cardz.news',
                        "The week in trading card game news in one free email every Sunday: top stories, release dates and Market Watch picks. Read this week's issue."),
    'board.html': ('TCG Fan Message Board | 1Cardz.news',
                   'The 1Cardz.news arcade hall of fame: trading card fans post their best pulls, hot takes and shout-outs to Zia and Luna.'),
}

e = lambda t: html.escape(str(t), quote=True)

def iso(when):
    try:
        return datetime.datetime.fromisoformat(when).replace(tzinfo=datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    except Exception:
        return None

def load(name):
    try:
        return json.loads((ROOT / 'tools' / name).read_text())
    except Exception:
        return []

def jsonld(page, posts, news):
    org = {'@type': 'NewsMediaOrganization', '@id': SITE + '#org', 'name': '1Cardz.news', 'url': SITE,
           'logo': {'@type': 'ImageObject', 'url': SITE + 'img/icon-512.png', 'width': 512, 'height': 512}, 'sameAs': SOCIAL}
    if page == 'index.html':
        return [org, {'@type': 'WebSite', '@id': SITE + '#site', 'name': '1Cardz.news', 'url': SITE, 'publisher': {'@id': SITE + '#org'},
                      'inLanguage': 'en'}]
    title, desc = PAGES[page]
    crumbs = {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE},
        {'@type': 'ListItem', 'position': 2, 'name': title.split(' | ')[0], 'item': SITE + page}]}
    web = {'@type': 'CollectionPage' if page in ('news.html', 'archive.html') else 'WebPage', 'name': title, 'description': desc,
           'url': SITE + page, 'isPartOf': {'@type': 'WebSite', 'name': '1Cardz.news', 'url': SITE}, 'publisher': org}
    if page == 'news.html' and news:
        items = sorted(news, key=lambda n: n.get('when', ''), reverse=True)[:30]
        web['mainEntity'] = {'@type': 'ItemList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'item': {'@type': 'NewsArticle', 'headline': n.get('title', '')[:110],
             'description': n.get('summary', ''), 'datePublished': iso(n.get('when', '')), 'url': SITE + site_parts.story_url(n),
             'image': OG_IMG, 'author': {'@id': SITE + '#org'}, 'publisher': {'@id': SITE + '#org'}}}
            for i, n in enumerate(items)]}
        return [org, web, crumbs]
    if page == 'archive.html' and posts:
        vids = []
        for p in sorted(posts, key=lambda p: p.get('when', ''), reverse=True):
            c = p.get('clip')
            if not c or not (ROOT / 'img' / f'{c}.jpg').exists():
                continue
            v = {'@type': 'VideoObject', 'name': f"{p.get('title', '')} | {p.get('game', '')} news with {p.get('host', '')}",
                 'description': p.get('blurb') or p.get('title', ''), 'thumbnailUrl': SITE + f'img/{c}.jpg',
                 'uploadDate': iso(p.get('when', '')), 'contentUrl': SITE + f'img/{c}.mp4', 'embedUrl': SITE + site_parts.clip_page(p, news),
                 'url': SITE + site_parts.clip_page(p, news),
                 'publisher': {'@id': SITE + '#org'}}
            vids.append({k: x for k, x in v.items() if x})
        web['hasPart'] = vids
        return [org, web, crumbs]
    return [org, web, crumbs]

def head_block(page, posts, news):
    title, desc = PAGES[page]
    url = SITE + ('' if page == 'index.html' else page)
    data = {'@context': 'https://schema.org', '@graph': jsonld(page, posts, news)}
    return '\n'.join([
        '<!--seo-->',
        '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">',
        '<meta name="theme-color" content="#0b1030">',
        f'<meta name="google-site-verification" content="{GOOGLE_VERIFY}">',
        '<link rel="icon" type="image/png" sizes="32x32" href="img/favicon-32.png">',
        '<link rel="icon" type="image/png" sizes="192x192" href="img/icon-192.png">',
        '<link rel="apple-touch-icon" href="img/apple-touch-icon.png">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="1Cardz.news">',
        '<meta property="og:locale" content="en_US">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{e(url)}">',
        f'<meta property="og:image" content="{OG_IMG}">',
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="Hosts Zia and Luna in the 1Cardz.news arcade-library studio">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(title)}">',
        f'<meta name="twitter:description" content="{e(desc)}">',
        f'<meta name="twitter:image" content="{OG_IMG}">',
        '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + '</script>',
        '<!--/seo-->'])

def fix_page(page, posts, news):
    p = ROOT / page
    if not p.exists():
        return
    s = p.read_text()
    s = re.sub(r'<!--seo-->.*?<!--/seo-->\n?', '', s, flags=re.S)
    title, desc = PAGES[page]
    # title + description are replaced where they already sit (so the page builders still find them in index.html)
    t = f'<title>{e(title)}</title>'
    s = re.sub(r'<title>.*?</title>', lambda m: t, s, count=1, flags=re.S) if '<title>' in s else s.replace('</head>', t + '\n</head>', 1)
    d = f'<meta name="description" content="{e(desc)}">'
    s = re.sub(r'<meta name="description"[^>]*>', lambda m: d, s, count=1) if '<meta name="description"' in s else s.replace('</head>', d + '\n</head>', 1)
    s = s.replace('</head>', head_block(page, posts, news) + '\n</head>', 1)
    if page != 'index.html':
        # one <h1> per page = that page's own title; the binder's "TCG News" becomes a styled <div class="h1x">
        s = re.sub(r'<h1 class="foil">(.*?)</h1>', r'<div class="foil h1x">\1</div>', s, count=1, flags=re.S)
        if not re.search(r'<div class="sheet-head">\s*(<div class="sheet-title">\s*)?<h1', s):
            s = re.sub(r'(<div class="sheet-head">\s*(?:<div class="sheet-title">\s*)?)<h2([^>]*)>(.*?)</h2>', r'\1<h1\2>\3</h1>', s, count=1, flags=re.S)
    p.write_text(s)

INDEXNOW_KEY = '1cardz9f3e6b2a7d4c4f81a0e5b9c2d7f6a3e1'

def indexnow(sm, old):
    """Tell Bing and other IndexNow search engines about new or changed pages (only when the sitemap changed)."""
    (ROOT / f'{INDEXNOW_KEY}.txt').write_text(INDEXNOW_KEY)
    new = re.findall(r'<loc>(.*?)</loc>', sm)
    was = set(re.findall(r'<loc>(.*?)</loc>', old))
    changed = [u for u in new if u not in was] or ([] if sm == old else new[:6])
    if not changed or __import__('os').environ.get('NO_PING'):
        return
    try:
        import urllib.request
        body = json.dumps({'host': '1cardz.news', 'key': INDEXNOW_KEY, 'keyLocation': f'{SITE}{INDEXNOW_KEY}.txt', 'urlList': changed[:1000]}).encode()
        req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
        print('indexnow:', urllib.request.urlopen(req, timeout=15).status, len(changed), 'urls')
    except Exception as x:
        print('indexnow skipped:', x)

def main():
    posts, news = load('posts.json'), load('news.json')
    for page in PAGES:
        fix_page(page, posts, news)
    today = datetime.date.today().isoformat()
    newest = lambda xs: max((x.get('when', '')[:10] for x in xs if x.get('when')), default=today)
    last = {'index.html': max(newest(posts), newest(news)), 'news.html': newest(news), 'archive.html': newest(posts),
            'market.html': today, 'newsletter.html': today, 'board.html': today}
    pri = {'index.html': '1.0', 'news.html': '0.9', 'archive.html': '0.9', 'market.html': '0.8', 'newsletter.html': '0.6', 'board.html': '0.5'}
    urls = ''.join(f'  <url><loc>{SITE}{"" if pg == "index.html" else pg}</loc><lastmod>{last[pg]}</lastmod><changefreq>daily</changefreq><priority>{pri[pg]}</priority></url>\n'
                   for pg in PAGES if (ROOT / pg).exists())
    # one page per story and per clip (built by build_news.py), each with its picture and video
    seen, fresh = set(), []
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    for n, p in site_parts.story_items(news, posts):
        u = site_parts.story_url(n)
        if u in seen or not (ROOT / u).exists():
            continue
        seen.add(u)
        x = ''
        c = (p or {}).get('clip')
        if c and (ROOT / 'img' / f'{c}.jpg').exists():
            x = (f'<image:image><image:loc>{SITE}img/{c}.jpg</image:loc></image:image>'
                 f'<video:video><video:thumbnail_loc>{SITE}img/{c}.jpg</video:thumbnail_loc><video:title>{e(n["title"])}</video:title>'
                 f'<video:description>{e((p.get("blurb") or n.get("summary") or n["title"])[:2000])}</video:description>'
                 f'<video:content_loc>{SITE}img/{c}.mp4</video:content_loc><video:publication_date>{iso(n["when"])}</video:publication_date>'
                 f'<video:family_friendly>yes</video:family_friendly></video:video>')
        urls += f'  <url><loc>{SITE}{u}</loc><lastmod>{n["when"][:10]}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority>{x}</url>\n'
        try:
            if now - datetime.datetime.fromisoformat(iso(n['when'])) < datetime.timedelta(days=2):
                fresh.append((u, n))
        except Exception:
            pass
    for f in sorted(ROOT.glob('news-2*.html'), reverse=True):   # any older story page still on the site
        if f.name not in seen:
            urls += f'  <url><loc>{SITE}{f.name}</loc><lastmod>{f.name[5:15]}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>\n'
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n' + urls + '</urlset>\n')
    old = (ROOT / 'sitemap.xml').read_text() if (ROOT / 'sitemap.xml').exists() else ''
    (ROOT / 'sitemap.xml').write_text(sm)
    # Google News sitemap: stories from the last 2 days
    nx = ''.join(f'  <url><loc>{SITE}{u}</loc><news:news><news:publication><news:name>1Cardz.news</news:name><news:language>en</news:language></news:publication>'
                 f'<news:publication_date>{iso(n["when"])}</news:publication_date><news:title>{e(n["title"])}</news:title></news:news></url>\n' for u, n in fresh)
    (ROOT / 'news-sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                                           'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n' + nx + '</urlset>\n')
    (ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: /tools/*.py\n\nSitemap: {SITE}sitemap.xml\nSitemap: {SITE}news-sitemap.xml\n')
    indexnow(sm, old)
    print('seo: pages, sitemap.xml and robots.txt updated')

if __name__ == '__main__':
    main()
