"""Prépare les médias de la vidéo du publi-reportage Educazur.

  1. lit docs/images videos/publi-reportage.txt et en extrait le texte parlé
     (les indications de mise en scène ne sont pas lues) ;
  2. vérifie qu'aucune ligne de texte n'est oubliée ;
  3. synthétise chaque phrase (edge-tts, voix féminine Vivienne) ;
  4. copie les images retenues dans public/ ;
  5. écrit public/timeline.json, que la composition Remotion suit.

Usage, depuis video/ :  python scripts/prepare.py
Prérequis : pip install edge-tts ; ffmpeg dans le PATH ou FFMPEG=...
"""
import asyncio
import json
import os
import re
import shutil
import subprocess

import edge_tts

VOIX = "fr-FR-VivienneMultilingualNeural"
DEBIT = "+0%"
FPS = 30
PAUSE_LIGNE = 0.45       # silence entre deux phrases (s)
PAUSE_SECTION = 1.0      # silence entre deux séquences (s)
INTRO = 1.6              # logo seul avant la première phrase (s)
FIN = 7.0                # écran final après la dernière phrase : le temps de lire les coordonnées (s)

VIDEO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(VIDEO)
DOSSIER = os.path.join(ROOT, "docs", "images videos")
TEXTE = os.path.join(DOSSIER, "publi-reportage.txt")
PUBLIC = os.path.join(VIDEO, "public")
FF = os.environ.get("FFMPEG", "ffmpeg")

# Forme parlée : ce que la voix lit quand l'écrit prête à confusion.
# « B F E M » en lettres espacées : avec des points ou attaché, le E est avalé.
PARLE = {
    "6e": "sixième",
    "BFEM": "B F E M",
    "série S1": "série S un",
    "Rentrée scolaire 2027": "Rentrée scolaire deux mille vingt-sept",
    "L’EXCELLENCE EST NOTRE CREDO.": "L’excellence est notre credo.",
    "GROUPE SCOLAIRE EDUCAZUR": "Groupe Scolaire Educazur.",
    " — ": " : ",
}

# Séquences, dans l'ordre du texte. « cle » : début de la ligne d'indication.
# Les images viennent de docs/images videos, sauf mention « site: ».
SEQUENCES = [
    dict(cle="🎬 PUBLI-REPORTAGE", id="titre", titre="",
         images=["Vue extérieure de l'école.jpeg"]),
    dict(cle="Ouverture", id="ouverture", titre="Une année de résultats",
         # une liste d'images par phrase : les chiffres doivent tomber sur les bons plans
         par_ligne=[
             ["preau-arcades.jpg"],
             ["portail.jpg", "video-cour-et-classes.jpg"],
             ["couloir-classes.jpg"],
             ["facade.jpg"],
             ["banderole-bac.jpg", "affiche-resultats.jpg"],
             ["couloir-eleves.jpg", "video-preau-et-infirmerie.jpg"],
         ],
         chiffres=[
             None,
             None,
             [["85,48 %", "de passage en classe supérieure"]],
             [["83 %", "de réussite au BFEM"], ["5", "premiers du centre"]],
             [["70,41 %", "au Baccalauréat"], ["100 %", "en série S1"]],
             None,
         ]),
    dict(cle="Transition", id="couloirs", titre="Un cadre repensé",
         images=["couloir-arcade.jpg", "couloir-classes.jpg", "site:salle-classe.jpg",
                 "video-couloirs.jpg"]),
    dict(cle="Salle informatique", id="informatique", titre="Salle informatique",
         images=["video-salle-informatique.jpg", "site:media/salle-informatique.jpg"]),
    dict(cle="Bibliothèque", id="bibliotheque", titre="Bibliothèque",
         images=["site:media/bibliotheque.jpg"]),
    dict(cle="Infirmerie", id="infirmerie", titre="Infirmerie",
         images=["video-infirmerie.jpg", "infirmerie.jpg"]),
    dict(cle="Cour, espaces verts", id="cour", titre="Cour et espaces verts",
         images=["cour-allee.jpg", "jardin-allee.jpg", "vue-jardin-haut.jpg",
                 "cour-arbres.jpg"]),
    dict(cle="Plans larges", id="plans", titre="Un établissement qui avance",
         images=["facade-nationale.jpg", "video-facade-et-resultats.jpg"]),
    dict(cle="Conclusion", id="conclusion", titre="",
         images=["preau-arcades.jpg"]),
    dict(cle="GROUPE SCOLAIRE EDUCAZUR", id="final", titre="", images=[]),
]


def duree(chemin):
    err = subprocess.run([FF, "-hide_banner", "-i", chemin],
                         capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def nettoie(ligne):
    """Retire guillemets, astérisques et espaces parasites."""
    return re.sub(r"\s+", " ", ligne.replace("«", "").replace("»", "")
                  .replace("*", "")).strip()


def decoupe(texte):
    """Rattache chaque ligne de texte parlé à sa séquence."""
    lignes = [l.strip() for l in texte.splitlines() if l.strip()]
    courante, par_seq, indications = None, {}, []
    for l in lignes:
        seq = next((s for s in SEQUENCES if l.startswith(s["cle"])), None)
        if seq:
            courante = seq["id"]
            par_seq.setdefault(courante, [])
            if seq["id"] == "titre":
                # le titre est entre guillemets sur la même ligne
                par_seq[courante].append(nettoie(l.split("—", 1)[1]))
            elif seq["id"] == "final":
                par_seq[courante].append(nettoie(l))
            else:
                indications.append(l)
            continue
        par_seq[courante].append(nettoie(l))
    return par_seq, indications


def parle(ecrit):
    for a, b in PARLE.items():
        ecrit = ecrit.replace(a, b)
    return ecrit


async def synthese(texte, chemin):
    await edge_tts.Communicate(texte, VOIX, rate=DEBIT).save(chemin)


def image(nom):
    """Copie une image dans public/img et renvoie son chemin public."""
    if nom.startswith("site:"):
        src = os.path.join(ROOT, "assets", "img", nom[5:])
    else:
        src = os.path.join(DOSSIER, nom)
    cible = re.sub(r"[^a-z0-9.-]+", "-", os.path.basename(nom[5:] if nom.startswith("site:") else nom)
                   .lower().replace("é", "e").replace("è", "e").replace("'", "-")).strip("-")
    if nom.startswith("site:"):
        cible = "site-" + cible
    shutil.copyfile(src, os.path.join(PUBLIC, "img", cible))
    return "img/" + cible


def main():
    os.makedirs(os.path.join(PUBLIC, "img"), exist_ok=True)
    os.makedirs(os.path.join(PUBLIC, "voix"), exist_ok=True)
    shutil.copyfile(os.path.join(ROOT, "assets", "img", "logo.png"),
                    os.path.join(PUBLIC, "img", "logo.png"))

    brut = open(TEXTE, encoding="utf-8").read()
    par_seq, indications = decoupe(brut)

    # --- contrôle d'intégralité : chaque ligne de texte doit être lue
    lues = [l for s in SEQUENCES for l in par_seq.get(s["id"], [])]
    attendues = [nettoie(l) for l in brut.splitlines()
                 if l.strip() and l.strip() not in indications]
    attendues[0] = nettoie(brut.splitlines()[0].split("—", 1)[1])
    assert lues == attendues, "des lignes du texte ne sont pas lues"
    print(f"{len(lues)} phrases à lire, {len(indications)} indications de mise en scène ignorées")

    t = INTRO
    sequences = []
    n = 0
    for seq in SEQUENCES:
        lignes_seq = par_seq.get(seq["id"], [])
        debut_seq = t
        lignes = []
        for i, ecrit in enumerate(lignes_seq):
            chemin = os.path.join(PUBLIC, "voix", f"{n:02d}.mp3")
            asyncio.run(synthese(parle(ecrit), chemin))
            d = duree(chemin)
            ligne = dict(texte=ecrit, audio=f"voix/{n:02d}.mp3",
                         debut=round(t, 3), duree=round(d, 3))
            if "par_ligne" in seq:
                ligne["images"] = [image(x) for x in seq["par_ligne"][i]]
                ch = seq["chiffres"][i]
                if ch:
                    ligne["chiffres"] = ch
            lignes.append(ligne)
            print(f"  {t:6.1f}s  {d:5.1f}s  {ecrit[:70]}")
            t += d + PAUSE_LIGNE
            n += 1
        t += PAUSE_SECTION - PAUSE_LIGNE
        sequences.append(dict(
            id=seq["id"], titre=seq["titre"], debut=round(debut_seq, 3),
            fin=round(t, 3), lignes=lignes,
            images=[image(x) for x in seq.get("images", [])]))

    total = t - PAUSE_SECTION + FIN
    timeline = dict(fps=FPS, total=round(total, 3),
                    titre=par_seq["titre"][0], sequences=sequences)
    with open(os.path.join(PUBLIC, "timeline.json"), "w", encoding="utf-8") as fh:
        json.dump(timeline, fh, ensure_ascii=False, indent=1)
    print(f"\nDurée totale : {total:.1f} s  ({int(total * FPS)} images à {FPS} i/s)")


if __name__ == "__main__":
    main()
