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
