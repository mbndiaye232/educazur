"""Prepare les photos de la mediatheque Educazur.

Source : docs/images/new/ (photos 1280x851, nettement meilleures que les
captures video de build_images.py).

Une seule photo demande une correction : le portail. Son enseigne imprimee,
qui est dans le bleu de la marque (teinte 211,8 deg mesuree sur l'affiche),
y ressort a 266 deg et les piliers a 240 deg : la photo a une rotation de
teinte sur les couleurs saturees, alors que sa balance des blancs est
correcte (point blanc neutre mesure a 212/218/212). Les dix autres photos
sont dans +/-11 deg de la reference, ce qui est la variation normale de la
peinture reelle selon la lumiere : elles ne sont pas retouchees.

Le recalage ramene la teinte des bleus-violets vers 213 deg en preservant
saturation et clarte, ce qui laisse intacts le portail noir, le sable et la
vegetation.
"""
import os

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "docs", "images", "new")
OUT = os.path.join(ROOT, "assets", "img", "media")

TEINTE_MARQUE = 213.0    # bleu de la marque, mesure sur l'affiche
LARGE, VIGNETTE = 1600, 700

# (fichier source, slug, recalage de teinte)
PHOTOS = [
    ("WhatsApp Image 2026-09-17 at 19.01.18.jpeg",     "preau-arcades-bancs",   False),
    ("WhatsApp Image 2026-09-17 at 19.01.18 (1).jpeg", "preau-arcades-large",   False),
    ("WhatsApp Image 2026-09-17 at 19.01.20 (1).jpeg", "preau-escalier",        False),
    ("WhatsApp Image 2026-09-17 at 19.01.20 (2).jpeg", "couloir-portes-bleues", False),
    ("WhatsApp Image 2026-09-17 at 19.01.20.jpeg",     "jardin-allee-rose",     False),
    ("WhatsApp Image 2026-09-17 at 19.01.21.jpeg",     "jardin-vue-haute",      False),
    ("WhatsApp Image 2026-09-17 at 19.01.21 (2).jpeg", "cour-arbres-preau",     False),
    ("WhatsApp Image 2026-09-17 at 19.01.21 (3).jpeg", "jardin-banc-bleu",      False),
    ("WhatsApp Image 2026-09-17 at 19.01.21 (4).jpeg", "salle-classe-tables",   False),
    ("WhatsApp Image 2026-09-17 at 19.01.22 (1).jpeg", "portail-entree",        True),
    ("WhatsApp Image 2026-09-17 at 19.01.22.jpeg",     "facade-route",          False),
    # prises du 18/09/2026 (docs/nouveau) : couleurs conformes, pas de recalage
    ("../../nouveau/WhatsApp Image 2026-09-18 at 10.32.17.jpeg",     "salle-informatique", False),
    ("../../nouveau/WhatsApp Image 2026-09-18 at 10.34.23.jpeg",     "bibliotheque",       False),
    ("../../nouveau/WhatsApp Image 2026-09-18 at 10.32.17 (1).jpeg", "infirmerie-lits",    False),
    ("../../nouveau/WhatsApp Image 2026-09-18 at 10.32.17 (2).jpeg", "infirmerie-examen",  False),
]


def rgb2hsv(a):
    a = a / 255.0
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.zeros_like(mx)
    m = d > 1e-6
    i = m & (mx == r); h[i] = ((g - b)[i] / d[i]) % 6
    i = m & (mx == g); h[i] = ((b - r)[i] / d[i]) + 2
    i = m & (mx == b); h[i] = ((r - g)[i] / d[i]) + 4
    return h * 60.0, np.where(mx > 0, d / np.maximum(mx, 1e-6), 0), mx


def hsv2rgb(h, s, v):
    h = np.mod(h, 360.0) / 60.0
    c = v * s
    x = c * (1 - np.abs(np.mod(h, 2) - 1))
    m = v - c
    z = np.zeros_like(h)
    i = h.astype(int)
    cond = [i == 0, i == 1, i == 2, i == 3, i == 4, i >= 5]
    r = np.select(cond, [c, x, z, z, x, c])
    g = np.select(cond, [x, c, c, x, z, z])
    b = np.select(cond, [z, z, x, c, c, x])
    return np.clip(np.stack([r + m, g + m, b + m], -1) * 255.0, 0, 255)


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def recale_teinte(im, cible=TEINTE_MARQUE):
    """Ramene les bleus-violets satures vers la teinte de la marque."""
    a = np.asarray(im).astype(np.float32)
    h, s, v = rgb2hsv(a)
    poids = np.minimum(smoothstep(h, 196.0, 214.0), 1.0 - smoothstep(h, 250.0, 300.0))
    poids = poids * smoothstep(s, 0.18, 0.34)      # epargne les gris et les noirs
    return Image.fromarray(hsv2rgb(h + poids * (cible - h), s, v).astype(np.uint8))


def mesure_teinte(im):
    a = np.asarray(im).reshape(-1, 3).astype(float)
    mx, mn = a.max(1), a.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = a[:, 0], a[:, 1], a[:, 2]
    sel = a[(sat > 0.25) & (mx > 70) & (b > r) & (b > g)]
    if len(sel) < 300:
        return None
    med = np.median(sel, axis=0)
    h, _, _ = rgb2hsv(med.reshape(1, 1, 3))
    return float(h[0, 0])


def ecrit(im, chemin, largeur, qualite):
    w = min(largeur, im.width)
    i = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
    if w < im.width:
        i = i.filter(ImageFilter.UnsharpMask(radius=1.1, percent=70, threshold=3))
    i.save(chemin, "JPEG", quality=qualite, optimize=True, progressive=True)
    return os.path.getsize(chemin)


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for src, slug, recale in PHOTOS:
        im = Image.open(os.path.join(SRC, src)).convert("RGB")
        if recale:
            avant = mesure_teinte(im)
            im = recale_teinte(im)
            apres = mesure_teinte(im)
            print(f"  recalage de teinte sur {slug} : "
                  f"{avant:.1f} deg -> {apres:.1f} deg (marque {TEINTE_MARQUE:.1f})")
        im = ImageEnhance.Color(im).enhance(1.06)
        im = ImageEnhance.Contrast(im).enhance(1.04)
        n1 = ecrit(im, os.path.join(OUT, slug + ".jpg"), LARGE, 84)
        n2 = ecrit(im, os.path.join(OUT, slug + "-vignette.jpg"), VIGNETTE, 80)
        total += n1 + n2
        print(f"{slug:24s} {n1/1024:6.0f} Ko + {n2/1024:5.0f} Ko")
    print(f"\nTotal : {total/1024/1024:.2f} Mo")


if __name__ == "__main__":
    main()
