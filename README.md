# Site web — Groupe Scolaire Educazur

Site vitrine statique du Groupe Scolaire Educazur (Km 16, Nationale 1 — Pikine, Dakar).
Aucun framework, aucune étape de build : ce sont des fichiers HTML, CSS et JS servis tels quels.

## Pages

| Fichier | Contenu |
|---|---|
| `index.html` | Accueil — l'annonce d'inscription est mise en avant juste sous le héros |
| `notre-ecole.html` | Histoire, projet du GIE Vision Azur, les trois objectifs, transformations |
| `resultats.html` | BAC 2026 par série, mentions, distinction, BFEM, taux de passage |
| `cadre-de-vie.html` | Salles, couloirs, numérique, bibliothèque, infirmerie, cour + galerie |
| `inscriptions.html` | Modalités, formulaire de demande, coordonnées et accès |
| `404.html` | Page d'erreur |

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

Les photographies de `assets/img/` ont été extraites des vidéos du reportage de
l'école (`docs/videos/`, non versionnées car trop volumineuses), puis agrandies et
retouchées par `build_images.py`.

**Limite de qualité :** les vidéos sources sont en 848 × 480. Les images ont été
agrandies au Lanczos avec accentuation, ce qui donne un rendu correct mais reste en
dessous d'une vraie photo. Pour un résultat optimal, refaire des photos à l'appareil
ou au téléphone en haute résolution.

Manquent à la galerie : la **salle informatique** et la **bibliothèque**, absentes
des vidéos. Leurs sections existent en texte, sans photo.

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
