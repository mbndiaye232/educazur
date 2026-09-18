"""Voix off des vidéos de la médiathèque Educazur.

Pour chaque vidéo, les textes sont calés sur ce que montre l'image (seconde de
départ de chaque segment). Le script :
  1. synthétise chaque segment (voix neuronale Microsoft via edge-tts) ;
  2. vérifie qu'aucun segment ne déborde sur le suivant ni sur la fin ;
  3. mixe la voix (et le son d'ambiance à bas niveau, s'il existe) ;
  4. remultiplexe avec la vidéo étalonnée, sans réencoder l'image ;
  5. écrit les sous-titres WebVTT correspondants.

Usage, depuis la racine du dépôt :
    python tools/voix_off.py            # toutes les vidéos
    python tools/voix_off.py couloirs   # une seule

Prérequis : pip install edge-tts ; ffmpeg dans le PATH ou FFMPEG=...
Les faits cités viennent de docs/presentation*.txt et des affiches de résultats
filmées (BAC 2026) : ne rien ajouter qui ne soit pas établi.
"""
import asyncio
import os
import re
import subprocess
import sys
import tempfile

import edge_tts

VOIX = "fr-FR-VivienneMultilingualNeural"
DEBIT = "+2%"
MARGE = 0.6          # silence minimal entre deux segments (s)
AMBIANCE = 0.22      # niveau du son d'origine sous la voix, pour les vidéos sonores

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "build", "video")   # sorties de tools/encode_videos.sh
OUT = os.path.join(ROOT, "assets", "video")
FF = os.environ.get("FFMPEG", "ffmpeg")

TEL = "77, 657, 42, 31"

# La voix lit la forme parlée ; les sous-titres affichent la forme écrite.
# « B F E M » en lettres espacées : avec des points, la voix avale le E.
ECRIT = {
    TEL: "77 657 42 31",
    "B F E M": "BFEM",
    "série S un": "série S1",
    "série S deux": "série S2",
    "deux mille vingt-six, deux mille vingt-sept": "2026-2027",
    "deux cent sept": "207",
    "soixante-dix virgule quarante et un pour cent": "70,41 %",
    "quatre-vingt-trois pour cent": "83 %",
    "quatre-vingt-cinq pour cent": "85 %",
    "Cent pour cent": "100 %",
    "quatre cent cinquante mille": "450 000",
    "kilomètre seize": "Km 16",
}

# slug source -> (fichier de sortie, segments (seconde de départ, texte))
VIDEOS = {
    "facade-et-resultats": [
        (0.8, "Bienvenue au Groupe Scolaire Educazur. Ici, les résultats parlent "
              "d'eux-mêmes : deux cent sept nouveaux bacheliers cette année, et "
              "soixante-dix virgule quarante et un pour cent de réussite au Baccalauréat."),
        (15.5, "Ces noms affichés à l'entrée sont ceux d'élèves qui ont cru en leur "
               "avenir, et d'une équipe qui les a accompagnés jusqu'à la réussite."),
        (33.0, "Depuis plus d'un quart de siècle, Educazur accueille les familles de "
               "Pikine, sur la Nationale 1, au kilomètre seize. Une adresse connue, "
               "facile d'accès, au plus près de chez vous."),
        (52.5, "Un établissement de référence, qui propose un cycle complet, de la "
               "sixième à la Terminale : tout le parcours secondaire de votre enfant, "
               "dans un même environnement éducatif."),
        (66.0, "Moins de trajets, moins de dépenses de transport et de restauration "
               "pour les familles : c'est aussi cela, une école de proximité."),
        (80.0, "Derrière cette façade, un projet ambitieux. Porté par le GIE Vision "
               "Azur, un investissement de près d'un demi-milliard de francs CFA a "
               "permis de créer un cadre moderne, fonctionnel et propice à l'excellence."),
        (97.0, "Dans une zone de près de quatre cent cinquante mille habitants, "
               "majoritairement jeune, Educazur s'engage à offrir une éducation de "
               "qualité, dans un environnement sécurisé et accueillant."),
        (116.0, "Et cet engagement se mesure."),
        (123.5, "Cent pour cent de réussite en série S un. Trente-deux mentions, dont "
                "deux mentions Très bien. Et une distinction particulière : le premier "
                "du jury en série S deux, au centre du Lycée de Mbao."),
        (140.0, "Au B F E M, quatre-vingt-trois pour cent de réussite, avec les cinq "
                "premiers du centre. Et de la sixième à la Première, plus de "
                "quatre-vingt-cinq pour cent des élèves passent en classe supérieure."),
        (156.5, "Franchissez le portail : place à la sérénité. Allées ombragées, "
                "espaces verts entretenus, bancs pour se retrouver entre deux cours. "
                "Ici, tout est pensé pour que l'élève se sente bien, et ait envie "
                "d'apprendre."),
        (175.5, "Salles de classe rénovées, couloirs nouvellement carrelés, "
                "bibliothèque et infirmerie entièrement refaites : Educazur investit "
                "dans le cadre de vie de ses élèves."),
        (190.0, f"Rentrée deux mille vingt-six, deux mille vingt-sept : les "
                f"inscriptions sont ouvertes, et le nombre de places est limité. "
                f"Appelez le {TEL}. Groupe Scolaire Educazur : l'excellence est "
                f"notre credo."),
    ],
    "cour-et-classes": [
        (0.8, "Bienvenue dans la cour du Groupe Scolaire Educazur. Sous les grands "
              "arbres, les élèves disposent d'un espace ombragé, calme et verdoyant, "
              "au cœur de l'établissement."),
        (18.5, "Au fond, le préau à arcades, aux couleurs bleu et blanc de l'école : "
               "le lieu de rassemblement de toute la communauté éducative."),
        (33.0, "Depuis plus d'un quart de siècle, Educazur accompagne les jeunes de "
               "Pikine vers la réussite. Une longévité qui repose sur une exigence "
               "constante de qualité."),
        (48.0, "Car l'excellence ne se mesure pas uniquement aux résultats. Elle se "
               "construit aussi dans la qualité de l'environnement offert aux élèves."),
        (65.0, "Ces dernières années, d'importants investissements ont transformé le "
               "cadre de vie scolaire. Espaces verts, allées aménagées, lieux de "
               "détente : tout l'environnement a été repensé."),
        (76.5, "Parce qu'un cadre agréable contribue aussi au bien-être, et à la "
               "réussite de l'élève."),
        (88.0, "Les couloirs ont été entièrement carrelés. Propres, lumineux, ouverts "
               "sur la verdure, ils offrent aux élèves comme aux enseignants de "
               "meilleures conditions de travail."),
        (102.5, "Un cadre agréable, sécurisé et accueillant : c'est la promesse "
                "d'Educazur aux familles qui lui confient leurs enfants."),
        (116.0, "Entre deux cours, chacun trouve ici un coin d'ombre pour souffler, "
                "réviser ou échanger."),
        (128.0, "De la sixième à la Terminale, Educazur propose un cycle complet. "
                "Votre enfant effectue tout son parcours secondaire dans un même "
                "établissement, avec des repères stables."),
        (145.0, "Et les résultats suivent : plus de quatre-vingt-cinq pour cent de "
                "passage en classe supérieure, quatre-vingt-trois pour cent de "
                "réussite au B F E M, et deux cent sept nouveaux bacheliers."),
        (156.5, "Des résultats qui sont le fruit du travail conjugué des élèves, "
                "des enseignants et de toute la communauté éducative."),
        (172.0, "Voici nos salles de classe, rénovées pour offrir de meilleures "
                "conditions d'apprentissage. Ici, un corps professoral de qualité "
                "accompagne chaque élève vers la réussite."),
        (188.5, f"Les inscriptions pour la rentrée deux mille vingt-six, deux mille "
                f"vingt-sept sont ouvertes. Places limitées. Appelez le {TEL}. "
                f"Educazur : l'excellence est notre credo."),
    ],
    "preau-et-infirmerie": [
        (0.8, "Voici le cœur du Groupe Scolaire Educazur : son préau à arcades. Un "
              "lieu emblématique, où se retrouvent chaque jour les élèves, les "
              "enseignants et toute l'équipe éducative."),
        (15.0, "Autour, des bancs, de l'ombre et de la verdure. Parce qu'un élève "
               "apprend mieux lorsqu'il évolue dans un environnement qui lui donne "
               "envie d'apprendre."),
        (26.0, "Un cadre pensé pour le bien-être, au plus près du domicile des "
               "familles de Pikine."),
        (41.0, "Les allées du jardin intérieur ont été entièrement aménagées : haies "
               "taillées, pavés, arbres. Un havre de calme au cœur de la ville."),
        (57.0, "Educazur, c'est plus d'un quart de siècle d'histoire au kilomètre "
               "seize de la Nationale 1. Et une ambition intacte : préparer chaque "
               "élève à réussir son avenir."),
        (73.0, "Pour faire grandir ce projet, le GIE Vision Azur a investi près d'un "
               "demi-milliard de francs CFA. Une conviction : la qualité de "
               "l'éducation dépend aussi du cadre dans lequel l'élève grandit."),
        (96.0, "Sous le préau, les colonnes de pierre, les plantes et le carrelage en "
               "damier donnent à l'établissement un caractère unique, chaleureux et "
               "soigné."),
        (110.5, "Chaque détail compte. Car l'excellence, à Educazur, se voit aussi "
                "dans le soin apporté aux lieux."),
        (123.0, "Les couloirs, entièrement carrelés, relient les salles de classe "
                "dans un environnement propre et ordonné."),
        (136.5, "Parce que le bien-être de l'élève est au cœur de nos "
                "préoccupations, l'établissement dispose d'une infirmerie "
                "entièrement rénovée, pour une prise en charge attentive et "
                "rassurante."),
        (156.0, "De la sixième à la Terminale, un parcours complet dans un même "
                "établissement, suivi par une administration rigoureuse et un corps "
                "professoral de qualité."),
        (172.0, "Cent pour cent de réussite en série S un, deux cent sept nouveaux "
                "bacheliers : année après année, l'exigence paie."),
        (185.0, f"Les inscriptions pour la rentrée deux mille vingt-six, deux mille "
                f"vingt-sept sont ouvertes. Places limitées. Appelez le {TEL}. "
                f"Educazur : l'excellence est notre credo."),
    ],
    "couloirs": [
        (0.5, "Bienvenue à l'intérieur d'Educazur. Les couloirs carrelés mènent aux "
              "salles de classe, à l'administration et à la surveillance."),
        (10.5, "Un encadrement présent, une organisation rigoureuse : vos enfants "
               "sont entre de bonnes mains."),
        (18.5, f"Inscriptions ouvertes, places limitées. Appelez le {TEL}."),
    ],
    "jardin-vu-du-haut": [
        (0.5, "Vu de l'étage, le jardin d'Educazur dévoile ses allées, ses haies et "
              "ses bancs."),
        (8.0, "Un espace vert au cœur de l'école, pour apprendre et grandir en toute "
              "sérénité. Educazur : l'excellence est notre credo."),
    ],
    "allees-du-jardin": [
        (0.3, "Les allées du jardin mènent au préau, cœur de la vie scolaire. "
              "Educazur : un environnement digne des ambitions de votre enfant."),
    ],
    # Prises du 18/09/2026, montées par tools/encode_videos.sh (plans ratés retirés)
    "salle-informatique": [
        (0.4, "Voici la salle informatique d'Educazur. Parce que l'école de demain "
              "est ouverte au numérique, Educazur accorde une place importante aux "
              "outils technologiques."),
    ],
    "infirmerie": [
        (0.4, "Parce que le bien-être de l'élève est au cœur de nos préoccupations, "
              "Educazur dispose d'une infirmerie entièrement rénovée."),
        (8.3, "Lits de repos, table d'examen, bureau : tout est pensé pour accueillir "
              "et soigner les élèves dans de bonnes conditions."),
        (14.8, f"Votre enfant est entre de bonnes mains. Appelez le {TEL}."),
    ],
    "bibliotheque": [
        (0.4, "Bienvenue à la bibliothèque d'Educazur, entièrement rénovée."),
        (4.4, "Un espace de lecture, de recherche et d'enrichissement intellectuel, "
              "où les travaux des élèves sont à l'honneur."),
    ],
}


def duree(chemin):
    """Durée d'un fichier média, lue dans la sortie de ffmpeg."""
    err = subprocess.run([FF, "-hide_banner", "-i", chemin],
                         capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if not m:
        raise RuntimeError(f"durée illisible : {chemin}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def a_de_l_audio(chemin):
    err = subprocess.run([FF, "-hide_banner", "-i", chemin],
                         capture_output=True, text=True).stderr
    return "Audio:" in err


async def synthese(texte, chemin, debit=DEBIT):
    await edge_tts.Communicate(texte, VOIX, rate=debit).save(chemin)


def horodatage(t):
    h, reste = divmod(t, 3600)
    m, s = divmod(reste, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def traiter(slug, segments, tmp):
    video = os.path.join(SRC, slug + ".mp4")
    total = duree(video)
    print(f"\n=== {slug}  ({total:.1f} s, {len(segments)} segments)")

    pistes = []
    for i, (debut, texte) in enumerate(segments):
        fin_max = segments[i + 1][0] - MARGE if i + 1 < len(segments) else total - 0.8
        chemin = os.path.join(tmp, f"{slug}_{i:02d}.mp3")
        # accélère légèrement un segment trop long, dans la limite du naturel
        for debit in (DEBIT, "+8%", "+13%"):
            asyncio.run(synthese(texte, chemin, debit))
            d = duree(chemin)
            if debut + d <= fin_max:
                break
        statut = "ok" if debut + d <= fin_max else "DEBORDE"
        print(f"  {debut:6.1f}s  {d:5.1f}s  -> {debut + d:6.1f}s  "
              f"(limite {fin_max:6.1f}s, débit {debit})  {statut}")
        if statut != "ok":
            raise SystemExit(f"{slug} : le segment {i} déborde, raccourcir le texte")
        pistes.append((debut, d, chemin, texte))

    # --- mixage : chaque segment placé à sa seconde de départ
    entrees = ["-i", video]
    for _, _, chemin, _ in pistes:
        entrees += ["-i", chemin]
    filtres, etiquettes = [], []
    for k, (debut, _, _, _) in enumerate(pistes, start=1):
        ms = int(debut * 1000)
        filtres.append(f"[{k}:a]aresample=48000,adelay={ms}|{ms}[v{k}]")
        etiquettes.append(f"[v{k}]")
    n = len(pistes)
    if a_de_l_audio(video):
        filtres.append(f"[0:a]aresample=48000,volume={AMBIANCE}[amb]")
        etiquettes.append("[amb]")
        n += 1
    filtres.append(
        f"{''.join(etiquettes)}amix=inputs={n}:duration=longest:normalize=0,"
        # apad : sur une vidéo muette, la piste s'arrêterait avec la dernière
        # phrase et -shortest couperait la fin de l'image
        f"loudnorm=I=-16:TP=-1.5:LRA=11,apad,atrim=0:{total:.3f}[mix]")

    sortie = os.path.join(OUT, slug + "-commentee.mp4")
    subprocess.run(
        [FF, "-y", "-hide_banner", "-loglevel", "error", *entrees,
         "-filter_complex", ";".join(filtres),
         "-map", "0:v", "-map", "[mix]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "112k", "-ar", "48000",
         "-movflags", "+faststart", sortie],
        check=True)

    # --- sous-titres
    vtt = os.path.join(OUT, slug + "-commentee.fr.vtt")
    with open(vtt, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("WEBVTT\n\n")
        for k, (debut, d, _, texte) in enumerate(pistes, start=1):
            lisible = texte
            for parle, ecrit in ECRIT.items():
                lisible = lisible.replace(parle, ecrit)
            fh.write(f"{k}\n{horodatage(debut)} --> {horodatage(debut + d)}\n"
                     f"{lisible}\n\n")

    parle = sum(d for _, d, _, _ in pistes)
    print(f"  -> {os.path.basename(sortie)}  "
          f"{os.path.getsize(sortie) / 1048576:.1f} Mo, "
          f"voix {parle:.0f} s sur {total:.0f} s ({parle / total:.0%})")


def main():
    choix = sys.argv[1:] or list(VIDEOS)
    with tempfile.TemporaryDirectory() as tmp:
        for slug in choix:
            traiter(slug, VIDEOS[slug], tmp)


if __name__ == "__main__":
    main()
