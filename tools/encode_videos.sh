#!/usr/bin/env bash
# Réencode les vidéos de la médiathèque : LUT de resaturation des bleus + H.264 web.
#
# Prérequis : ffmpeg dans le PATH (ou FFMPEG=... en variable d'environnement)
# et les LUT générées au préalable, depuis la racine du dépôt :
#
#   for g in 1.41 1.65 1.68 1.85 2.07; do
#     python tools/make_lut.py --gain $g --hue-pull 0.35 --out tools/lut/g$g.cube
#   done
#
# Puis :  bash tools/encode_videos.sh
#
# Le gain diffère d'une vidéo à l'autre parce qu'elles ne partent pas du même
# niveau de saturation ; voir le tableau du README.
set -euo pipefail

FF="${FFMPEG:-ffmpeg}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/docs/videos"
LUT="$ROOT/tools/lut"
OUT="$ROOT/build/video"      # intermédiaire : tools/voix_off.py produit la version publiée
POSTER="$ROOT/assets/img"

mkdir -p "$OUT"

# encode <fichier-source> <slug> <gain> <muet:0|1> <seconde-de-l-affiche>
encode() {
  local src="$SRC/$1" slug="$2" gain="$3" muet="$4" tposter="$5"
  local cube="$LUT/g$gain.cube"

  [ -f "$cube" ] || { echo "LUT manquante : $cube" >&2; exit 1; }
  echo ">>> $slug  (gain $gain, muet=$muet)"

  local audio=(-an)
  [ "$muet" = "0" ] && audio=(-c:a aac -b:a 96k -ac 1)

  "$FF" -y -hide_banner -loglevel error -i "$src" \
    -vf "lut3d=file='${cube}'" \
    -c:v libx264 -preset medium -crf 26 -maxrate 560k -bufsize 1120k \
    -profile:v high -level 4.0 -pix_fmt yuv420p -movflags +faststart \
    "${audio[@]}" "$OUT/$slug.mp4"

  # affiche du lecteur, LUT appliquée elle aussi
  "$FF" -y -hide_banner -loglevel error -i "$src" -ss "$tposter" -frames:v 1 \
    -vf "lut3d=file='${cube}',scale=1280:-2" -q:v 4 "$POSTER/video-$slug.jpg"
}

encode "2 principal résultats.mp4"        "facade-et-resultats" 2.07 1 100
encode "1 cour et salles de classes.mp4"  "cour-et-classes"     1.65 1 122
encode "3 Général infirmerie.mp4"         "preau-et-infirmerie" 1.85 1 95
encode "interieur.mp4"                    "couloirs"            1.41 0 4
encode "de haut.mp4"                      "jardin-vu-du-haut"   1.68 0 8
encode "cour.mp4"                          "allees-du-jardin"   1.41 0 2

echo
du -ch "$OUT"/*.mp4 | tail -1
