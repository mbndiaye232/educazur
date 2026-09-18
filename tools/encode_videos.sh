#!/usr/bin/env bash
# Réencode les vidéos de la médiathèque : LUT de resaturation des bleus + H.264 web.
#
# Prérequis : ffmpeg dans le PATH (ou FFMPEG=... en variable d'environnement)
# et les LUT générées au préalable, depuis la racine du dépôt :
#
#   for g in 1.25 1.41 1.65 1.68 1.85 2.07; do
#     python tools/make_lut.py --gain $g --hue-pull 0.35 --out tools/lut/g$g.cube
#   done
#
# Puis :  bash tools/encode_videos.sh                 # toutes les vidéos
#         bash tools/encode_videos.sh bibliotheque    # seulement celles nommées
#
# Le gain diffère d'une vidéo à l'autre parce qu'elles ne partent pas du même
# niveau de saturation ; voir le tableau du README. Gain 0 : pas de correction.
set -euo pipefail

FF="${FFMPEG:-ffmpeg}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/docs/videos"
SRC_NOUVEAU="$ROOT/docs/nouveau"
LUT="$ROOT/tools/lut"
OUT="$ROOT/build/video"      # intermédiaire : tools/voix_off.py produit la version publiée
POSTER="$ROOT/assets/img"
CHOIX=("$@")

mkdir -p "$OUT"

# vrai si la vidéo fait partie de la sélection (ou si rien n'est sélectionné)
voulu() {
  [ ${#CHOIX[@]} -eq 0 ] && return 0
  local s; for s in "${CHOIX[@]}"; do [ "$s" = "$1" ] && return 0; done
  return 1
}

# filtre lut3d ; sous Windows (Git Bash), ffmpeg attend un chemin C\:/...
filtre_lut() {
  local cube="$LUT/g$1.cube"
  [ -f "$cube" ] || { echo "LUT manquante : $cube" >&2; exit 1; }
  command -v cygpath >/dev/null && cube="$(cygpath -m "$cube" | sed 's|^\([A-Za-z]\):|\1\\:|')"
  echo "lut3d=file='${cube}'"
}

H264=(-c:v libx264 -preset medium -crf 26 -maxrate 560k -bufsize 1120k
      -profile:v high -level 4.0 -pix_fmt yuv420p -movflags +faststart)

# encode <fichier-source> <slug> <gain> <muet:0|1> <seconde-de-l-affiche>
encode() {
  local src="$SRC/$1" slug="$2" gain="$3" muet="$4" tposter="$5"
  voulu "$slug" || return 0
  local lut; lut="$(filtre_lut "$gain")"
  echo ">>> $slug  (gain $gain, muet=$muet)"

  local audio=(-an)
  [ "$muet" = "0" ] && audio=(-c:a aac -b:a 96k -ac 1)

  "$FF" -y -hide_banner -loglevel error -i "$src" -vf "$lut" \
    "${H264[@]}" "${audio[@]}" "$OUT/$slug.mp4"

  # affiche du lecteur, LUT appliquée elle aussi
  "$FF" -y -hide_banner -loglevel error -i "$src" -ss "$tposter" -frames:v 1 \
    -vf "$lut,scale=1280:-2" -q:v 4 "$POSTER/video-$slug.jpg"
}

# monte <fichier-source> <slug> <gain|0> <seconde-de-l-affiche> <début:fin>...
# Ne garde que les plages indiquées (son compris) et les met bout à bout :
# sert à retirer les passages ratés d'une prise au téléphone.
monte() {
  local src="$SRC_NOUVEAU/$1" slug="$2" gain="$3" tposter="$4"; shift 4
  voulu "$slug" || return 0
  echo ">>> $slug  (gain $gain, plages : $*)"

  local fc="" liste="" n=0 plage debut fin
  for plage in "$@"; do
    debut="${plage%%:*}"; fin="${plage##*:}"
    local vt="trim=start=$debut" at="atrim=start=$debut"
    [ -n "$fin" ] && { vt="$vt:end=$fin"; at="$at:end=$fin"; }
    fc+="[0:v]$vt,setpts=PTS-STARTPTS[v$n];[0:a]$at,asetpts=PTS-STARTPTS[a$n];"
    liste+="[v$n][a$n]"; n=$((n + 1))
  done
  local post="null"
  [ "$gain" != "0" ] && post="$(filtre_lut "$gain")"
  fc+="${liste}concat=n=$n:v=1:a=1[vc][ac];[vc]$post[v]"

  "$FF" -y -hide_banner -loglevel error -i "$src" -filter_complex "$fc" \
    -map "[v]" -map "[ac]" "${H264[@]}" -c:a aac -b:a 96k -ac 1 "$OUT/$slug.mp4"

  # affiche, prise dans la vidéo montée
  "$FF" -y -hide_banner -loglevel error -ss "$tposter" -i "$OUT/$slug.mp4" \
    -frames:v 1 -vf "scale=1280:-2" -q:v 4 "$POSTER/video-$slug.jpg"
}

encode "2 principal résultats.mp4"        "facade-et-resultats" 2.07 1 100
encode "1 cour et salles de classes.mp4"  "cour-et-classes"     1.65 1 122
encode "3 Général infirmerie.mp4"         "preau-et-infirmerie" 1.85 1 95
encode "interieur.mp4"                    "couloirs"            1.41 0 4
encode "de haut.mp4"                      "jardin-vu-du-haut"   1.68 0 8
encode "cour.mp4"                          "allees-du-jardin"   1.41 0 2

# Prises du 18/09/2026. Seule la bibliothèque est corrigée : ses murs sortaient
# plus ternes que sur la photo de la même pièce (saturation 0,39 contre 0,49).
# Salle informatique et infirmerie concordent déjà avec leurs photos.
monte "WhatsApp Video 2026-09-18 at 10.32.16.mp4" "salle-informatique" 0    2   0:6.8 11.0:
monte "WhatsApp Video 2026-09-18 at 10.32.17.mp4" "infirmerie"         0    12  0:17.3 18.9:
monte "WhatsApp Video 2026-09-18 at 10.34.23.mp4" "bibliotheque"       1.25 3   0:

echo
du -ch "$OUT"/*.mp4 | tail -1
