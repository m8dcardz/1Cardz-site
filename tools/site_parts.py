"""Shared page parts copied from index.html into every other page:
the holo nav bar (under the top binder) and the Newsletter box + its script (above the bottom binder)."""
import re

def _cut(src, start, end_marker):
    a = src.index(start); b = src.index(end_marker, a) + len(end_marker)
    return src[a:b]

def navbar(src, current):
    """The nav bar from index.html with aria-current on `current` (e.g. 'news.html')."""
    nav = _cut(src, '<div class="wrap navbar-wrap">', '</nav>\n</div>')
    nav = nav.replace(' aria-current="page"', '')
    return nav.replace(f'href="{current}"', f'href="{current}" aria-current="page"', 1)

def newsletter_section(src):
    """The Newsletter section from index.html (goes right before the footer so it joins the bottom binder)."""
    return _cut(src, '<section class="wrap signup-deck"', '</section>')

def newsletter_script(src):
    """The script that handles the Newsletter form (goes after the footer)."""
    return '<script>\n' + _cut(src, '  /* sign-up boxes:', '.finally(()=>{btn.disabled=false})})})})();') + '\n</script>'


# ---- one page per story / clip (shared by build_news, build_archive, seo) ----
import unicodedata as _ud
def story_url(n):
    """news-YYYY-MM-DD-<slug>.html (the Home headline box builds the same name in JS)"""
    t = _ud.normalize('NFKD', n['title']).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:70].rstrip('-')
    return f"news-{n['when'][:10]}-{t}.html"

def story_items(news, posts):
    """Every story that gets its own page: each news.json entry, plus each posted clip that has
    no news entry (older clips), so every clip is discoverable on its own URL.
    Returns [(item, post_or_None)] newest first."""
    pw = {p.get('when'): p for p in posts}
    nw = {n.get('when') for n in news}
    out = [(n, pw.get(n.get('when'))) for n in news]
    for p in posts:
        if p.get('when') not in nw and p.get('title') and p.get('clip'):
            out.append(({'title': p['title'], 'summary': p.get('blurb') or p['title'], 'game': p.get('game', ''),
                         'when': p['when'], 'source': p.get('source', '')}, p))
    out.sort(key=lambda x: x[0].get('when', ''), reverse=True)
    return out

def clip_page(p, news):
    """URL of the page that carries this clip."""
    for n in news:
        if n.get('when') == p.get('when'):
            return story_url(n)
    return story_url(p)
