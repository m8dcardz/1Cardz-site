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
import html, json, pathlib, re, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://1cardz.news/'
OG_IMG = SITE + 'img/og-1cardz.jpg'
GOOGLE_VERIFY = 'Qn2aus3288fPHtNy3uGq67lvfgMzjwkNacnNeF72rlY'  # Google Search Console (HTML tag method, Nov 3, 2026)
SOCIAL = ['https://www.instagram.com/1cardz_news/', 'https://www.youtube.com/@1Cardzcom', 'https://www.tiktok.com/@1cardz.com']
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
    web = {'@type': 'CollectionPage' if page in ('news.html', 'archive.html') else 'WebPage', 'name': title, 'description': desc,
           'url': SITE + page, 'isPartOf': {'@type': 'WebSite', 'name': '1Cardz.news', 'url': SITE}, 'publisher': org}
    if page == 'news.html' and news:
        items = sorted(news, key=lambda n: n.get('when', ''), reverse=True)[:30]
        web['mainEntity'] = {'@type': 'ItemList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'item': {'@type': 'NewsArticle', 'headline': n.get('title', '')[:110],
             'description': n.get('summary', ''), 'datePublished': iso(n.get('when', '')), 'url': SITE + 'news.html',
             'image': OG_IMG, 'author': {'@id': SITE + '#org'}, 'publisher': {'@id': SITE + '#org'}}}
            for i, n in enumerate(items)]}
        return [org, web]
    if page == 'archive.html' and posts:
        vids = []
        for p in sorted(posts, key=lambda p: p.get('when', ''), reverse=True):
            c = p.get('clip')
            if not c or not (ROOT / 'img' / f'{c}.jpg').exists():
                continue
            v = {'@type': 'VideoObject', 'name': f"{p.get('title', '')} | {p.get('game', '')} news with {p.get('host', '')}",
                 'description': p.get('blurb') or p.get('title', ''), 'thumbnailUrl': SITE + f'img/{c}.jpg',
                 'uploadDate': iso(p.get('when', '')), 'contentUrl': SITE + f'img/{c}.mp4', 'embedUrl': SITE + 'archive.html',
                 'publisher': {'@id': SITE + '#org'}}
            vids.append({k: x for k, x in v.items() if x})
        web['hasPart'] = vids
        return [org, web]
    return [org, web]

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
        if not re.search(r'<div class="sheet-head">\s*<h1', s):
            s = re.sub(r'(<div class="sheet-head">\s*)<h2([^>]*)>(.*?)</h2>', r'\1<h1\2>\3</h1>', s, count=1, flags=re.S)
    p.write_text(s)

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
    for f in sorted(ROOT.glob('news-2*.html'), reverse=True):    # one page per story (built by build_news.py)
        urls += f'  <url><loc>{SITE}{f.name}</loc><lastmod>{f.name[5:15]}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
    (ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '</urlset>\n')
    (ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: /tools/*.py\n\nSitemap: {SITE}sitemap.xml\n')
    print('seo: pages, sitemap.xml and robots.txt updated')

if __name__ == '__main__':
    main()
