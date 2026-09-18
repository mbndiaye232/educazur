# Vidéo du publi-reportage

Vidéo de présentation d'Educazur réalisée avec [Remotion](https://www.remotion.dev) :
les images de `docs/images videos/` défilent pendant qu'une voix féminine lit
**intégralement** le texte de `docs/images videos/publi-reportage.txt`.

## Produire la vidéo

```bash
cd video
npm install
python scripts/prepare.py      # voix, images, chronologie (public/)
npm run render                 # out/educazur-publi-reportage.mp4
```

`npm run studio` ouvre l'aperçu interactif de Remotion.

### Version publiée sur le site

Le rendu (`out/educazur-publi-reportage.mp4`, 1080p, 68 Mo) dépasse la limite de
25 Mo par fichier de Cloudflare Pages. Le site utilise une version 720p :

```bash
ffmpeg -i out/educazur-publi-reportage.mp4   -vf "scale=1280:720:flags=lanczos:in_range=full:out_range=tv,format=yuv420p"   -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv   -c:v libx264 -preset slow -crf 24 -maxrate 900k -bufsize 1800k   -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -b:a 128k -movflags +faststart   ../assets/video/publi-reportage.mp4
ffmpeg -ss 3.2 -i out/educazur-publi-reportage.mp4 -frames:v 1   -vf "scale=1280:720" -q:v 3 ../assets/img/video-publi-reportage.jpg
```

Résultat : 14 Mo, son à -16 LUFS. Elle est présentée sur l'accueil (section
« Le nouveau visage d'Educazur », juste après l'annonce d'inscription) et en tête
des vidéos de la médiathèque.

**En cas de nouveau rendu, changer le nom du fichier** (`publi-reportage-v2.mp4`
par exemple) : les vidéos sont mises en cache un jour chez les visiteurs.

Prérequis : Node 18+, Python avec `pip install edge-tts`, ffmpeg dans le PATH
(ou `FFMPEG=...`).

## Fonctionnement

`scripts/prepare.py` découpe le texte en phrases, rattache chacune à sa séquence
(ouverture, couloirs, salle informatique, bibliothèque, infirmerie, cour, plans
larges, conclusion, écran final), synthétise la voix phrase par phrase et écrit
`public/timeline.json`. La composition (`src/PubliReportage.tsx`) suit cette
chronologie : les images changent au rythme de la voix, les chiffres clés
apparaissent pendant la phrase qui les cite, chaque phrase est sous-titrée.

- **Intégralité** : le script refuse de continuer si une ligne du texte n'est
  pas lue. Les indications de mise en scène (« Ouverture — logo + façade… ») ne
  sont pas lues ; le titre, tout le texte entre guillemets et l'écran final le
  sont.
- **Prononciation** : quelques formes écrites sont réécrites pour la voix
  (« 6e » → « sixième », « BFEM » → « B F E M », « S1 » → « S un »,
  « 2027 » → « deux mille vingt-sept »). Les sous-titres gardent l'écrit.
- **Images** : celles de `docs/images videos/`, choisies par séquence dans
  `SEQUENCES`. Le dossier ne contenant ni la bibliothèque ni une salle de
  classe, ces deux plans viennent des photos du site (`assets/img/`).
- **Polices** : Newsreader et Inter, embarquées via `@fontsource` (le rendu ne
  dépend pas de Google Fonts).
- **Écran final** : coordonnées avec les libellés fournis par l'école (site web,
  e-mail, mobiles, fixe) et adresse à Diamaguène SICAP Mbao ; il reste affiché
  7 s après la dernière phrase, le temps de noter un numéro.

## Licence de la voix

Comme pour les vidéos de la médiathèque, la voix vient d'`edge-tts`, qui n'est
pas sous licence commerciale : avant une diffusion publicitaire, régénérer la
voix via Azure AI Speech (même voix, `fr-FR-VivienneMultilingualNeural`).
