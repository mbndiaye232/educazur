# Site web — Groupe Scolaire Educazur

Site vitrine statique du Groupe Scolaire Educazur (Km 16, Nationale 1 — Pikine, Dakar).
Aucun framework, aucune étape de build : ce sont des fichiers HTML, CSS et JS servis tels quels.

## Pages

| Fichier | Contenu |
|---|---|
| `index.html` | Accueil — l'annonce d'inscription est mise en avant juste sous le héros |
| `notre-ecole.html` | Histoire, projet du GIE Vision Azur, les trois objectifs, transformations |
| `resultats.html` | BAC 2026 par série, mentions, distinction, BFEM, taux de passage |
| `cadre-de-vie.html` | Salles, couloirs, numérique, bibliothèque, infirmerie, cour |
| `mediatheque.html` | Photos, six séquences vidéo, affiches et résultats officiels |
| `inscriptions.html` | Modalités, formulaire de demande, coordonnées et accès |
| `404.html` | Page d'erreur |

## Coordonnées

| | |
|---|---|
| Mobiles | 77 657 42 31 · 76 699 47 94 |
| Fixe | 33 834 77 80 |
| E-mail | gs.educazur@yahoo.fr |
| Adresse | Km 16, Route de Rufisque (Nationale 1) — Pikine, Dakar |

## Déploiement sur Cloudflare Pages

Connecter le dépôt GitHub `mbndiaye232/educazur`, puis :

| Réglage | Valeur |
|---|---|
| Framework preset | `None` |
| Build command | *(laisser vide)* |
| Build output directory | `/` |
| Root directory | *(laisser vide)* |

Chaque `git push` sur `main` déclenche un nouveau déploiement.
`_headers` définit le cache (1 an sur `/assets/*`, revalidation sur les `.html`) et
quelques en-têtes de sécurité.

### Après la mise en ligne

Remplacer `https://educazur.pages.dev` par le domaine définitif dans :

- les balises `<link rel="canonical">` et `og:*` de chaque page ;
- `sitemap.xml` ;
- `robots.txt`.

## Formulaire de contact

Le site étant statique, le formulaire de `inscriptions.html` passe par
[Web3Forms](https://web3forms.com) (gratuit, sans compte : la clé arrive par e-mail).

1. Sur web3forms.com, saisir l'adresse e-mail qui doit recevoir les demandes.
2. Récupérer la clé d'accès dans l'e-mail de confirmation.
3. Dans `inscriptions.html`, remplacer `VOTRE_CLE_WEB3FORMS` :

```html
<input type="hidden" name="access_key" value="VOTRE_CLE_WEB3FORMS">
```

Tant que la clé n'est pas renseignée, le formulaire affiche un message invitant à
appeler le secrétariat — il n'échoue pas silencieusement.

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

Manquent encore : la **salle informatique** et la **bibliothèque**, absentes des
sources. Leurs sections existent en texte, sans photo.

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

`assets/video/` contient six séquences réencodées en H.264 (848 × 480, CRF 26,
débit plafonné à 560 kb/s, `faststart`), pour 43 Mo au total — le plus gros
fichier fait 13,7 Mo, sous la limite de 25 Mo par fichier de Cloudflare Pages.

Les trois séquences longues (3 min 28) sont **muettes à la source** (−91 dB
mesuré) : leur piste audio a été retirée et la médiathèque l'indique. Les trois
séquences courtes conservent leur son d'origine.

`docs/videos/TRAVAUX/Project 1.mp4` n'est pas exploitable : son canal bleu est
corrompu (moyenne 242/255, toute l'image vire au violet).

## Outils

| Fichier | Rôle |
|---|---|
| `build_media_images.py` | photos de la médiathèque depuis `docs/images/new/` |
| `build_images.py` | images éditoriales depuis les captures vidéo |
| `tools/make_lut.py` | génère la LUT 3D de resaturation des bleus |
| `tools/encode_videos.sh` | applique la LUT et réencode les six vidéos |

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
├── index.html, notre-ecole.html, resultats.html,
│   cadre-de-vie.html, inscriptions.html, 404.html
├── assets/
│   ├── css/style.css        feuille de style unique
│   ├── js/main.js           menu, apparitions, visionneuse, formulaire
│   └── img/                 photos, logo, affiche
├── docs/                    sources : textes du reportage, images d'origine
├── _headers                 en-têtes Cloudflare Pages
├── favicon.ico
├── robots.txt
└── sitemap.xml
```
