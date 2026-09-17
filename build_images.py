"""Génère les images web du site Educazur à partir des captures vidéo retenues.

Usage : python build_images.py <dossier-des-captures>

Le dossier passé en argument contient les sous-dossiers `cand/` et `cand2/`
avec les images extraites de docs/videos/ (voir README).
"""
import os
import sys
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
SC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "frames")
OUT = os.path.join(ROOT, "assets", "img")
SRC_IMG = os.path.join(ROOT, "docs", "images")

# (fichier source, nom de sortie, largeur cible)
FRAMES = [
    ("cand/b02_preau.png",          "preau-arcades",    1800),
    ("cand2/jar_50.png",            "jardin-allee",     1800),
    ("cand/d02_courallee.png",      "cour-allee",       1800),
    ("cand/b03_preauplantes.png",   "preau-plantes",    1400),
    ("cand/b06_couloirarcade.png",  "couloir-arcade",   1400),
    ("cand/b04_couloir.png",        "couloir-carrele",  1400),
    ("cand/c03_couloirclasses.png", "couloir-classes",  1400),
    ("cand/c05_classe2.png",        "salle-classe",     1400),
    ("cand/c04_classe1.png",        "salle-classe-2",   1400),
    ("cand/c02_courarbres.png",     "cour-arbres",      1400),
    ("cand/d01_vuehaut.png",        "vue-jardin-haut",  1400),
    ("cand/a02_portail.png",        "portail",          1400),
    ("cand2/fac_86.png",            "facade",           1800),
    ("cand2/fac_110.png",           "facade-nationale", 1400),
    ("cand/a01_bacheliers.png",     "banderole-bac",    1400),
    ("cand2/aff_132.png",           "affiche-resultats",1400),
    ("cand/a05_admis.png",          "liste-admis",      1400),
    ("cand2/inf_147.png",           "infirmerie",       1400),
    ("cand/e01_couloireleves.png",  "couloir-eleves",   1400),
]


def enhance(im):
    """Remonte légèrement le contraste, la couleur et le piqué d'une capture vidéo."""
    im = ImageEnhance.Color(im).enhance(1.14)
    im = ImageEnhance.Contrast(im).enhance(1.10)
    im = ImageEnhance.Brightness(im).enhance(1.03)
    return im


def upscale(im, width):
    if width <= im.width:
        return im.resize((width, round(width * im.height / im.width)), Image.LANCZOS)
    # deux passes de Lanczos : moins d'artefacts qu'un agrandissement direct
    mid = Image.LANCZOS
    step = im
    while step.width * 2 <= width:
        step = step.resize((step.width * 2, step.height * 2), mid)
    if step.width != width:
        step = step.resize((width, round(width * im.height / im.width)), mid)
    return step


def save_jpg(im, name, width):
    im = enhance(im.convert("RGB"))
    im = upscale(im, width)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=105, threshold=3))
    path = os.path.join(OUT, name + ".jpg")
    im.save(path, "JPEG", quality=84, optimize=True, progressive=True)
    return path, im.size, os.path.getsize(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for src, name, w in FRAMES:
        im = Image.open(os.path.join(SC, src))
        p, size, nbytes = save_jpg(im, name, w)
        total += nbytes
        print(f"{name:20s} {size[0]}x{size[1]:<5d} {nbytes/1024:6.0f} Ko")

    # Annonce d'inscription : source déjà nette, on ne fait que recompresser
    an = Image.open(os.path.join(SRC_IMG, "annonce inscription.jpeg")).convert("RGB")
    an.save(os.path.join(OUT, "annonce-inscription.jpg"), "JPEG",
            quality=88, optimize=True, progressive=True)
    print(f"{'annonce-inscription':20s} {an.width}x{an.height:<5d} "
          f"{os.path.getsize(os.path.join(OUT, 'annonce-inscription.jpg'))/1024:6.0f} Ko")

    # Logo : masque circulaire pour retirer le fond blanc et l'ombre portée
    lg = Image.open(os.path.join(SRC_IMG, "logo.jfif")).convert("RGB")
    lg = lg.crop((4, 4, 213, 213))
    lg = lg.resize((512, 512), Image.LANCZOS)
    lg = ImageEnhance.Color(lg).enhance(1.08)
    lg = lg.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
    mask = Image.new("L", (2048, 2048), 0)
    ImageDraw.Draw(mask).ellipse((10, 10, 2038, 2038), fill=255)
    mask = mask.resize((512, 512), Image.LANCZOS)
    logo = lg.convert("RGBA")
    logo.putalpha(mask)
    logo.save(os.path.join(OUT, "logo.png"), "PNG", optimize=True)
    logo.resize((180, 180), Image.LANCZOS).save(
        os.path.join(OUT, "logo-180.png"), "PNG", optimize=True)
    print("logo.png + logo-180.png")

    # Favicon
    logo.resize((64, 64), Image.LANCZOS).save(
        os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("favicon.ico")
    print(f"\nTotal photos : {total/1024/1024:.2f} Mo")


if __name__ == "__main__":
    main()
