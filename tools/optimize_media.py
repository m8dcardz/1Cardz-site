#!/usr/bin/env python3
"""Shrink the site's videos and images (Nov 2, 2026).

Safe to run any number of times: each file is only re-encoded while it is still
above its target size, so already-optimised files are skipped.
    python3 tools/optimize_media.py           # everything
    python3 tools/optimize_media.py --clips   # only the Library clip previews + posters (used by build_archive.py)
Needs ffmpeg/ffprobe and Pillow. If either is missing it prints a note and does nothing.
"""
import json, pathlib, shutil, subprocess, sys

IMG = pathlib.Path(__file__).resolve().parent.parent / 'img'

def probe(p):
    try:
        out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                              'stream=width,bit_rate', '-show_entries', 'format=bit_rate', '-of', 'json', str(p)],
                             capture_output=True, text=True, timeout=30).stdout
        d = json.loads(out); s = d['streams'][0]
        br = int(s.get('bit_rate') or d.get('format', {}).get('bit_rate') or 0)
        return int(s['width']), br
    except Exception:
        return None, None

def encode(p, width, crf, fps=None, denoise=True):
    tmp = p.with_suffix('.tmp.mp4')
    vf = (['hqdn3d=2:2:4:4'] if denoise else []) + [f'scale={width}:-2:flags=lanczos'] + ([f'fps={fps}'] if fps else [])
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(p), '-vf', ','.join(vf), '-c:v', 'libx264', '-preset', 'slow',
           '-crf', str(crf), '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', str(tmp)]
    try:
        subprocess.run(cmd, check=True, timeout=600)
    except Exception as e:
        tmp.unlink(missing_ok=True); print('  skip', p.name, e); return
    if tmp.stat().st_size < p.stat().st_size * 0.95:
        old = p.stat().st_size; tmp.replace(p); print(f'  {p.name}: {old//1024}K -> {p.stat().st_size//1024}K')
    else:
        tmp.unlink(); print('  kept', p.name)

def videos(only_clips=False):
    for p in sorted(IMG.glob('clip*-s.mp4')):           # Library card previews: shown about 180x320
        w, _ = probe(p)
        if w and w > 300: encode(p, 288, 31, fps=24)
    if only_clips: return
    for p in sorted(IMG.glob('loop-*.mp4')):            # binder pocket card loops: shown about 286 wide
        w, _ = probe(p)
        if w and w > 400: encode(p, 360, 30)
    p = IMG / 'globe.mp4'                               # card-back globe: shown about 125x125
    if p.exists():
        w, _ = probe(p)
        if w and w > 260: encode(p, 240, 30)
    for p in sorted(IMG.glob('cover-loop-v*.mp4')):     # top binder clip
        w, br = probe(p)
        if w and br and br > 800_000: encode(p, w, 28)

def images(only_clips=False):
    from PIL import Image
    def jpg(p, q, limit):
        if p.stat().st_size <= limit: return
        old = p.stat().st_size; tmp = p.with_suffix('.tmp.jpg')
        Image.open(p).convert('RGB').save(tmp, 'JPEG', quality=q, optimize=True, progressive=True)
        if tmp.stat().st_size < old * 0.9: tmp.replace(p); print(f'  {p.name}: {old//1024}K -> {p.stat().st_size//1024}K')
        else: tmp.unlink()
    for p in sorted(IMG.glob('clip*.jpg')): jpg(p, 72, 42_000)          # Library + pop-up posters
    if only_clips: return
    for pat in ('yt-*.jpg', 'loop-*.jpg'):
        for p in sorted(IMG.glob(pat)): jpg(p, 72, 42_000)
    for name in ('cover-poster.jpg', 'cover-holo-poster.jpg', 'footer-tap2.jpg', 'globe-poster.jpg'):
        p = IMG / name
        if p.exists(): jpg(p, 76, 50_000)
    def webp(p, q, maxw, limit):
        if not p.exists() or p.stat().st_size <= limit: return
        old = p.stat().st_size; im = Image.open(p)
        if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
        tmp = p.with_suffix('.tmp.webp'); im.save(tmp, 'WEBP', quality=q, method=6)
        if tmp.stat().st_size < old * 0.9: tmp.replace(p); print(f'  {p.name}: {old//1024}K -> {p.stat().st_size//1024}K')
        else: tmp.unlink()
    webp(IMG / 'studio-card.webp', 78, 600, 120_000)                    # shown about 286 wide
    for name in ('zia.webp', 'luna.webp'): webp(IMG / name, 78, 640, 60_000)

def main():
    only = '--clips' in sys.argv
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        print('optimize_media: ffmpeg not found, skipped'); return
    try:
        import PIL  # noqa
    except ImportError:
        print('optimize_media: Pillow not found, skipped'); return
    videos(only); images(only)

if __name__ == '__main__':
    main()
