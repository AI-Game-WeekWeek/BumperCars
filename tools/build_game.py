#!/usr/bin/env python3
"""Build dist/BumperCars.html, one self-contained game file, from game/game.src.html and assets/.

    pip install pillow numpy scipy
    python3 tools/build_game.py

Every image is shrunk to the size the game actually draws and embedded as WebP/JPEG, so the file works offline
(except the Google Fonts link, which falls back to a system font).
"""
import base64, io, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = ROOT + '/assets/'


def enc(im, fmt='WEBP', q=85):
    b = io.BytesIO()
    if fmt == 'JPEG':
        im.convert('RGB').save(b, 'JPEG', quality=q, optimize=True)
        mime = 'jpeg'
    else:
        im.save(b, 'WEBP', quality=q, method=6)
        mime = 'webp'
    return 'data:image/%s;base64,%s' % (mime, base64.b64encode(b.getvalue()).decode())


def load(path, maxw=None, maxh=None):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    s = 1.0
    if maxw:
        s = min(s, maxw / w)
    if maxh:
        s = min(s, maxh / h)
    if s < 1:
        im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    return im


def hole(im):
    """Centre and radius (px) of the biggest fully enclosed transparent hole (the profile-picture slot, a ring's middle)."""
    a = np.array(im)[..., 3] > 16
    hole_mask = ndi.binary_fill_holes(a) & ~a
    lab, n = ndi.label(hole_mask)
    if n == 0:
        return None
    areas = ndi.sum(hole_mask, lab, range(1, n + 1))
    k = int(np.argmax(areas)) + 1
    ys, xs = np.where(lab == k)
    return float(xs.mean()), float(ys.mean()), float(np.sqrt(len(ys) / np.pi))


def asset(rel, **kw):
    im = load(A + rel, **kw)
    d = {'u': enc(im), 'w': im.size[0], 'h': im.size[1]}
    return d, im


def with_tb(rel, n=1, band=False, bmin=140, **kw):
    d, im = asset(rel, **kw)
    if band:
        d['tb'] = band_box(im)
    else:
        bs = cream_boxes(im, n, bmin)
        if n == 1:
            d['tb'] = bs[0]
        else:
            d['tbs'] = sorted(bs, key=lambda b: b[0])
    return d


def with_hole(rel, **kw):
    d, im = asset(rel, **kw)
    hl = hole(im)
    if hl:
        d['hx'], d['hy'], d['hr'] = hl
    else:
        d['hx'], d['hy'], d['hr'] = d['w'] / 2, d['h'] / 2, min(d['w'], d['h']) * .25
    return d


def cream_boxes(im, n=1, bmin=140):
    """Text areas (x, y, w, h in px of im): the biggest pale cream regions, shrunk away from stitching and borders."""
    a = np.array(im)
    rgb = a[..., :3].astype(int)
    mask = (a[..., 3] > 200) & (rgb[..., 0] > 225) & (rgb[..., 1] > 200) & (rgb[..., 2] > bmin)
    lab, k = ndi.label(mask)
    comps = []
    for i in range(1, k + 1):
        m = lab == i
        area = int(m.sum())
        if area < im.size[0] * im.size[1] * 0.004:
            continue
        d = ndi.distance_transform_edt(m)
        ys, xs = np.where(d >= max(4, 0.05 * np.sqrt(area)))
        if len(ys):
            comps.append((area, xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    comps.sort(reverse=True)
    return [[int(x0), int(y0), int(x1 - x0), int(y1 - y0)] for _, x0, y0, x1, y1 in comps[:n]]


def band_box(im):
    """Text area of a golden ribbon band: the rows where the yellow region is nearly as wide as at its widest."""
    a = np.array(im)
    rgb = a[..., :3].astype(int)
    mask = (a[..., 3] > 200) & (rgb[..., 0] > 235) & (rgb[..., 1] > 175) & (rgb[..., 2] < 150)
    cnt = mask.sum(axis=1)
    rows = np.where(cnt >= 0.75 * cnt.max())[0]
    ys = rows
    xs = np.where(mask[ys[0]:ys[-1] + 1].any(axis=0))[0]
    # the trophy sits over the top centre of the band, so the name goes in the lower part
    y0, y1 = ys[0] + int(0.30 * (ys[-1] - ys[0])), ys[-1] - int(0.04 * (ys[-1] - ys[0]))
    return [int(xs.min() + 0.06 * (xs.max() - xs.min())), int(y0), int(0.88 * (xs.max() - xs.min())), int(y1 - y0)]


def main():
    out = {'maps': {}, 'ui': {}, 'gifts': {}, 'bots': []}
    for m in ['fair', 'frog', 'desert', 'pig', 'cock', 'bey']:
        e = {'floor': asset(m + '/floor.png', maxw=640)[0],
             'badge': asset(m + '/badge.png', maxw=160)[0],
             'backdrop': asset(m + '/backdrop.png', maxw=540)[0],
             'rim': None,
             'cars': [with_hole('%s/cars/car_%d.png' % (m, i), maxw=200) for i in range(1, 7)]}
        if os.path.exists(A + m + '/rim.png'):
            d = with_hole(m + '/rim.png', maxw=640)
            d['inner'] = d['hr'] / (d['w'] / 2)
            e['rim'] = d
        out['maps'][m] = e
    u = out['ui']
    u['items'] = {k: asset('ui/items/%s.png' % k, maxw=128)[0] for k in ['speed', 'heal', 'range']}
    u['effects'] = {k: asset('ui/effects/%s.png' % k, maxw=160)[0] for k in ['hit_spark', 'shield', 'ice', 'speed_lines', 'heal', 'poof']}
    u['digits'] = [asset('ui/digits/%d.png' % i, maxh=200)[0] for i in range(10)]
    u['badges'] = {k: asset('ui/badges/%s.png' % k, maxw=96)[0] for k in ['attack_x2', 'speed']}
    u['callouts'] = {'starburst': with_tb('ui/callouts/starburst.png', maxw=640),
                     'crown': asset('ui/callouts/crown.png', maxw=300)[0],
                     'winner_ribbon': with_tb('ui/callouts/winner_ribbon.png', band=True, maxw=800)}
    u['hud'] = {'round_plate': with_tb('ui/hud/round_plate.png', maxw=300),
                'map_banner': with_tb('ui/hud/map_banner.png', maxw=560),
                'alive_plate': with_tb('ui/hud/alive_plate.png', maxw=280)}
    u['cats'] = {k: with_tb('ui/%s.png' % k, bmin=(40 if k == 'cat_flip' else 140), maxw=900) for k in ['cat_turn', 'cat_aim', 'cat_guard', 'cat_fight', 'cat_map', 'cat_flip', 'cat_free']}
    u['howto'] = with_tb('ui/howto_strip.png', n=4, maxw=1100)
    u['avatar_frame'] = with_hole('ui/avatar_frame.png', maxw=520)
    gift_files = {'gg': 'GG.png', 'tiktok': 'TikTok.png', 'rose': 'Rose.png', 'donut': 'Doughnut.png', 'ice': 'Ice Cream Cone.png',
                  'love': 'Love you so much.png', 'awesome': "You're awesome.png", 'th_frog': 'Tiny Diny.png',
                  'th_beetle': 'Finger Heart.png', 'th_pig': 'G.O.A.T. Busker.png', 'th_cock': 'Mishka Bear.png', 'th_bey': 'Hat and Mustache.png'}
    for k, f in gift_files.items():
        im = load(ROOT + '/' + f, maxw=96)
        out['gifts'][k] = enc(im)
    # funny bot profile pictures (square crops around the face)
    for f, cx, cy, frac in [('B2I.png', .5, .45, .8), ('Cat.jpg', .5, .3, .9), ('b1.jpg', .5, .5, 1), ('h1.jpg', .52, .55, .5), ('nu1.jpg', .5, .55, .85), ('nu2.png', .5, .5, .95)]:
        im = Image.open(ROOT + '/' + f).convert('RGB')
        w, h = im.size
        s = int(min(w, h) * frac)
        x = int(min(max(cx * w - s / 2, 0), w - s))
        y = int(min(max(cy * h - s / 2, 0), h - s))
        out['bots'].append(enc(im.crop((x, y, x + s, y + s)).resize((96, 96), Image.LANCZOS), 'JPEG', 82))
    src = open(ROOT + '/game/game.src.html', encoding='utf-8').read()
    html = src.replace('__ASSETS__', json.dumps(out, ensure_ascii=False, separators=(',', ':')))
    os.makedirs(ROOT + '/dist', exist_ok=True)
    path = ROOT + '/dist/BumperCars.html'
    open(path, 'w', encoding='utf-8').write(html)
    print('wrote', path, round(len(html) / 1024 / 1024, 2), 'MB')


if __name__ == '__main__':
    main()
