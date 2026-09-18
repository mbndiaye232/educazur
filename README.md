# Site web — Groupe Scolaire Educazur

Site vitrine statique du Groupe Scolaire Educazur (Km 16, Nationale 1 — Diamaguène SICAP Mbao, Dakar),
en ligne sur <https://educazur.net>.
Aucun framework, aucune étape de build : ce sont des fichiers HTML, CSS et JS servis tels quels.

## Pages

| Fichier | Contenu |
|---|---|
| `index.html` | Accueil — l'annonce d'inscription est mise en avant juste sous le héros |
| `notre-ecole.html` | Histoire, projet du GIE Vision Azur, les trois objectifs, transformations |
| `resultats.html` | BAC 2026 par série, mentions, distinction, BFEM, taux de passage |
| `cadre-de-vie.html` | Salles, couloirs, numérique, bibliothèque, infirmerie, cour |
| `mediatheque.html` | Photos, neuf séquences vidéo commentées, affiches et résultats officiels |
| `inscriptions.html` | Modalités, formulaire de demande, coordonnées et accès |
| `404.html` | Page d'erreur |
| `/admin/demandes` | Consultation des demandes d'inscription (mot de passe) |

## Coordonnées

| | |
|---|---|
| Mobiles | 77 657 42 31 · 76 699 47 94 |
| Fixe | 33 834 77 80 |
| E-mail | gs.educazur@yahoo.fr |
| Adresse | Km 16, Route de Rufisque (Nationale 1) — Diamaguène SICAP Mbao, Dakar |
| Site | <https://educazur.net> |

## Déploiement sur Cloudflare Pages

Connecter le dépôt GitHub `mbndiaye232/educazur`, puis :

| Réglage | Valeur |
|---|---|
| Framework preset | `None` |
| Build command | *(laisser vide)* |
| Build output directory | `/` |
| Root directory | *(laisser vide)* |

Chaque `git push` sur `main` déclenche un nouveau déploiement.
`_headers` définit le cache et quelques en-têtes de sécurité : les pages `.html`
sont revalidées à chaque visite, le CSS et le JS toutes les 5 minutes, les images
et les vidéos une fois par jour.

**Ne pas remettre de cache « immutable »** : aucun nom de fichier ne contient
d'empreinte de contenu, un fichier modifié garderait donc sa version périmée chez
les visiteurs pendant toute la durée du cache. C'est arrivé : `main.js` et
`style.css` ont été servis un temps avec un cache d'un an. Les pages les appellent
désormais par `style.css?v=2` et `main.js?v=2`, une adresse nouvelle qui échappe à
ces copies périmées — **ne pas retirer ce `?v=2`**.

### Domaine

Le site est servi sur **<https://educazur.net>**, rattaché au projet Pages ;
`educazur.pages.dev` continue de répondre. Les balises `canonical` et `og:*`,
les données structurées, `sitemap.xml` et `robots.txt` déclarent
`https://educazur.net`. En cas de changement de domaine, les mettre à jour
ensemble.

`www.educazur.net` ne répond pas : il faut l'ajouter comme domaine personnalisé
du projet Pages, ou le rediriger vers `educazur.net`.

## Formulaire d'inscription

Le site est statique, mais les demandes ne passent par **aucun service externe** :
elles sont reçues par une *Cloudflare Pages Function* et écrites dans une base
**D1** du même projet. Les données ne quittent pas votre infrastructure.

```
Navigateur du visiteur ──POST /api/inscription──▶ Pages Function ──▶ base D1
                                                                        │
                            /admin/demandes (mot de passe) ◀────────────┘
```

| Fichier | Rôle |
|---|---|
| `functions/api/inscription.js` | reçoit le POST, valide, bride les envois répétés, enregistre |
| `functions/admin/demandes.js` | page de consultation protégée par mot de passe |
| `schema.sql` | table `demandes` |

### Mise en service

**1. Créer la base et sa table**

```bash
npx wrangler d1 create educazur-demandes
npx wrangler d1 execute educazur-demandes --remote --file=schema.sql
```

Reporter le `database_id` renvoyé dans `wrangler.toml`.

**2. Attacher la base au projet Pages**

Tableau de bord Cloudflare → le projet → *Settings* → *Bindings* → *Add* →
*D1 database binding*, nom de variable **`DB`**, puis redéployer.

**3. Définir les secrets**

*Settings* → *Variables and Secrets* :

| Nom | Type | Rôle |
|---|---|---|
| `ADMIN_USER` | variable | identifiant de la page de consultation |
| `ADMIN_PASSWORD` | secret | mot de passe de la page de consultation |
| `IP_SALT` | secret | sel de l'empreinte d'adresse IP (une chaîne aléatoire) |

**4. Consulter les demandes**

<https://educazur.net/admin/demandes> — le navigateur demande
l'identifiant et le mot de passe. Filtre « À traiter » par défaut, bouton
« Marquer traitée » sur chaque ligne.

Tant que la base n'est pas attachée, le formulaire n'échoue pas en silence : il
affiche un message invitant à appeler le 77 657 42 31.

### Protections

- **Piège anti-robot** : un champ masqué qu'un humain ne remplit jamais.
- **Bride anti-répétition** : 5 envois maximum par tranche de 10 minutes et par
  origine. L'adresse IP n'est jamais stockée, seule une empreinte SHA-256
  tronquée l'est, salée par `IP_SALT`.
- **Page de consultation** : authentification HTTP Basic vérifiée côté serveur,
  comparaison à temps constant, `noindex` et exclusion dans `robots.txt`.
- **Échappement** : tout ce qui vient de la base est échappé avant affichage.
  Vérifié avec des charges d'injection : 0 élément `<script>` créé, 0 attribut
  `on*`, aucune boîte de dialogue déclenchée.

### Développement local

```bash
npx wrangler d1 execute educazur-demandes --local --file=schema.sql
npx wrangler pages dev . --port 8789
```

Les secrets locaux vont dans `.dev.vars` (non versionné) :

```
ADMIN_USER=secretariat
ADMIN_PASSWORD=un-mot-de-passe
IP_SALT=une-chaine-aleatoire
```

### Si vous voulez une notification par e-mail

L'envoi d'e-mail depuis Cloudflare exige un **domaine d'expédition vérifié** (l'offre
gratuite de MailChannels pour Workers s'est arrêtée en août 2024). Avec
`educazur.net`, cette condition peut désormais être remplie : la notification
pourra être ajoutée à `functions/api/inscription.js` sans passer par un tiers.

## Carte

La page d'inscription affiche une carte **OpenStreetMap** centrée sur le repère
exact de l'école (14.7466396, −17.3583659, relevé sur sa fiche Google Maps).
OpenStreetMap plutôt que Google Maps : l'intégration ne dépose pas de cookie de
suivi chez le visiteur. Le bouton « Ouvrir l'itinéraire » lance Google Maps avec
ces coordonnées pour destination ; les mêmes coordonnées figurent dans les
données structurées de l'accueil.

## Images

Deux jeux d'images, produits par deux scripts distincts.

### `assets/img/media/` — photos de la médiathèque

Produites par `build_media_images.py` depuis `docs/images/new/` (photos 1280 × 851).
Ce sont les meilleures images du site ; deux tailles sont générées par photo
(1600 px pour la visionneuse, 700 px pour la vignette).

### `assets/img/` — captures des vidéos

Produites par `build_images.py` depuis des images extraites de `docs/videos/`
(848 × 480), agrandies au Lanczos avec accentuation. Rendu correct mais en dessous
d'une vraie photo : ces images servent les héros et les pages éditoriales.

Les photos de la salle informatique, de la bibliothèque et de l'infirmerie
(`docs/nouveau/`, prises le 18/09/2026) passent par le même script.

## Correction du bleu

Le bleu des murs était délavé sur les vidéos. La mesure en HSV a montré que la
**clarté était déjà juste** (V ≈ 0,64, comme la référence) et que seule la
**saturation** manquait :

| | saturation | clarté |
|---|---|---|
| Mur peint sur l'affiche de l'école (référence, `#023AA8`) | 0,99 | 0,66 |
| Mur filmé, avant correction | 0,42 – 0,67 | 0,62 – 0,68 |
| Mur filmé, après correction | ≈ 0,95 | inchangée |

La correction passe par une LUT 3D générée par `make_lut.py` et appliquée avec le
filtre `lut3d` de ffmpeg. Elle n'agit que dans la plage des teintes bleues
(196–276°), épargne les gris, les noirs et le ciel surexposé, et **préserve la
clarté pixel par pixel** — mesuré : 0,622 avant, 0,622 après. Les cartons crème,
la végétation et le ciel ne bougent pas (dérive mesurée : 0,0 à 0,2 sur 255).

Le gain est calculé par vidéo, puisqu'elles ne partent pas du même niveau :

| Vidéo publiée | Gain de saturation |
|---|---|
| `facade-et-resultats.mp4` | 2,07 |
| `preau-et-infirmerie.mp4` | 1,85 |
| `jardin-vu-du-haut.mp4` | 1,68 |
| `cour-et-classes.mp4` | 1,65 |
| `couloirs.mp4`, `allees-du-jardin.mp4` | 1,41 |

La photo du portail (`portail-entree`) subit une correction différente : son
enseigne imprimée, qui est dans le bleu de la marque (211,8°), y ressortait à
266° et ses piliers à 240°, alors que sa balance des blancs est correcte. Le
recalage de teinte de `build_media_images.py` la ramène à 214°. Les dix autres
photos sont dans ±11° de la référence et ne sont pas retouchées.

## Vidéos

`assets/video/` contient les neuf séquences **commentées** (`*-commentee.mp4`) et
leurs sous-titres (`*-commentee.fr.vtt`), pour 51 Mo au total — le plus gros
fichier fait 15,3 Mo, sous la limite de 25 Mo par fichier de Cloudflare Pages.

Chaîne de production :

```
docs/videos/*.mp4  ──encode_videos.sh──▶ build/video/*.mp4 ──voix_off.py──▶ assets/video/*-commentee.mp4
docs/nouveau/*.mp4    LUT, coupes, H.264     (sans voix)            voix + sous-titres
```

Les sources vidéo et `build/` ne sont pas versionnés. L'image est copiée sans
réencodage à la dernière étape : même nombre d'images que la vidéo montée,
vérifié pour les neuf.

**Prises du 18/09/2026** (salle informatique, infirmerie, bibliothèque) : filmées
au téléphone, elles sont montées par la fonction `monte` d'`encode_videos.sh`,
qui retire les passages ratés — la caméra qui plonge vers le sol dans la salle
informatique (7 à 11 s), un panoramique flou dans l'infirmerie (17,3 à 18,9 s).

Les murs intérieurs sont peints d'un **bleu-gris pâle réel**, confirmé par les
photos prises dans les mêmes pièces : ils ne sont pas ramenés au bleu de l'affiche.
Chaque vidéo est comparée à la photo de sa propre pièce. Seule la bibliothèque
sortait plus terne que sa photo (saturation 0,39 contre 0,49) : gain de 1,25.
Salle informatique et infirmerie concordaient déjà, elles ne sont pas corrigées.

`docs/videos/TRAVAUX/Project 1.mp4` n'est pas exploitable : son canal bleu est
corrompu (moyenne 242/255, toute l'image vire au violet).

## Voix off

`tools/voix_off.py` contient les textes, calés seconde par seconde sur ce que
montre chaque vidéo, et produit les versions commentées :

```bash
python tools/voix_off.py              # toutes les vidéos
python tools/voix_off.py couloirs     # une seule
```

- **Voix** : `fr-FR-VivienneMultilingualNeural`, voix féminine neuronale.
- **Calage** : chaque segment a une seconde de départ ; le script refuse de
  produire une vidéo si un segment déborde sur le suivant.
- **Mixage** : la voix est normalisée à −16 LUFS ; sur les trois séquences
  courtes, le son d'origine reste audible en fond (22 %).
- **Sous-titres** : générés depuis les mêmes textes, en forme écrite (« BFEM »,
  « 2026-2027 », « 77 657 42 31 ») alors que la voix lit la forme parlée.
- **Contenu** : uniquement des faits établis — `docs/presentation*.txt` et les
  affiches de résultats du BAC 2026 filmées à l'entrée.

La prononciation a été contrôlée en faisant retranscrire l'audio par un modèle
de reconnaissance vocale. Un défaut a été corrigé ainsi : écrit « B.F.E.M. »
avec des points, le sigle perdait son E ; il est écrit « B F E M ».

### Licence de la voix — à régler avant une diffusion commerciale

Le script utilise `edge-tts`, qui passe par le service de lecture à voix haute
du navigateur Edge. Ce n'est **pas une API sous licence** : pour une vidéo
promotionnelle publiée, il faut générer l'audio via **Azure AI Speech**, qui
propose la même voix sous licence commerciale. Le volume est minime —
7 354 caractères pour les neuf vidéos. Seule la fonction `synthese()` est à
remplacer.

## Outils

| Fichier | Rôle |
|---|---|
| `build_media_images.py` | photos de la médiathèque depuis `docs/images/new/` |
| `build_images.py` | images éditoriales depuis les captures vidéo |
| `tools/make_lut.py` | génère la LUT 3D de resaturation des bleus |
| `tools/encode_videos.sh` | corrige, monte et réencode les vidéos dans `build/video/` |
| `tools/voix_off.py` | textes de la voix off, synthèse, mixage et sous-titres |
| `video/` | vidéo du publi-reportage (Remotion) — voir `video/README.md` |

Les LUT (`tools/lut/*.cube`, 1 Mo chacune) ne sont pas versionnées : elles se
régénèrent avec `make_lut.py`.

## Développement local

```bash
python -m http.server 8788
```

Puis ouvrir <http://127.0.0.1:8788>.

## Structure

```
.
├── index.html, notre-ecole.html, resultats.html, cadre-de-vie.html,
│   mediatheque.html, inscriptions.html, 404.html
├── assets/
│   ├── css/style.css        feuille de style unique
│   ├── js/main.js           menu, apparitions, visionneuse, formulaire
│   ├── img/                 photos, logo, affiches
│   └── video/               neuf séquences commentées + sous-titres
├── functions/
│   ├── api/inscription.js   réception et enregistrement des demandes
│   └── admin/demandes.js    page de consultation protégée
├── schema.sql               table D1 des demandes
├── wrangler.toml            liaison D1
├── video/                   vidéo du publi-reportage (Remotion)
├── docs/                    sources : textes du reportage, images d'origine
├── _headers                 en-têtes Cloudflare Pages
├── favicon.ico
├── robots.txt
└── sitemap.xml
```
