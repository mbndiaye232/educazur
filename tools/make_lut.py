"""Genere une LUT 3D (.cube) qui resature les bleus des videos Educazur.

Diagnostic : le bleu des murs filme est a S~0.45 / V~0.64 ; le meme bleu sur
l'affiche de l'ecole est a S~0.99 / V~0.66. La valeur est bonne, la saturation
manque. La LUT agit donc uniquement sur la saturation, et seulement dans la
plage de teintes bleues, en preservant :
  - la valeur (pas d'assombrissement),
  - les cremes, les verts et les rouges (poids nul hors des bleus),
  - le ciel surexpose (poids reduit au-dela de V=0.86).
"""
import argparse
import colorsys
import os

import numpy as np

# Reference mesuree sur le mur peint de l'affiche (#023AA8)
REF_HUE = 220.0 / 360.0   # teinte du bleu de reference


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def hue_weight(h):
    """1 au coeur des bleus (200-245 deg), retour a 0 vers 175 et 275 deg."""
    deg = h * 360.0
    montee = smoothstep(deg, 175.0, 202.0)
    descente = 1.0 - smoothstep(deg, 246.0, 276.0)
    return np.minimum(montee, descente)


def build(size, gain, hue_pull):
    """Retourne le tableau (size^3, 3) de la LUT, ordre BGR-major comme .cube."""
    grid = np.linspace(0.0, 1.0, size)
    out = np.zeros((size ** 3, 3), dtype=float)
    i = 0
    for b in grid:
        for g in grid:
            for r in grid:
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                w = hue_weight(np.array(h))
                # n'agit que sur des pixels deja colores, pas sur les gris/blancs
                w = w * smoothstep(s, 0.10, 0.28)
                # protege le ciel brule et les hautes lumieres
                w = w * (1.0 - smoothstep(v, 0.86, 0.99))
                w = float(w)

                if w > 0.0:
                    s_new = min(1.0, s * (1.0 + w * (gain - 1.0)))
                    h_new = h + w * hue_pull * (REF_HUE - h)
                    r2, g2, b2 = colorsys.hsv_to_rgb(h_new % 1.0, s_new, v)
                else:
                    r2, g2, b2 = r, g, b

                out[i] = (r2, g2, b2)
                i += 1
    return out


def write_cube(path, table, size, title):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f'TITLE "{title}"\n')
        fh.write(f"LUT_3D_SIZE {size}\n")
        fh.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        fh.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        for r, g, b in table:
            fh.write(f"{r:.6f} {g:.6f} {b:.6f}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gain", type=float, default=2.0)
    ap.add_argument("--hue-pull", type=float, default=0.35)
    ap.add_argument("--size", type=int, default=33)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    out = a.out or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"educazur_bleu_g{a.gain:.2f}_h{a.hue_pull:.2f}.cube")
    table = build(a.size, a.gain, a.hue_pull)
    write_cube(out, table, a.size, "Educazur - resaturation des bleus")
    print(out)
